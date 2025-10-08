# src/backend/reconstruction.py
# Reconstruction Functions Module
# Created for RenExtract WebView

"""
Module de reconstruction des fichiers traduits Ren'Py
Implémentation complète du flux de reconstruction avec restauration des placeholders
"""

import os
import re
import time
import json
import glob
import datetime
from collections import OrderedDict
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_file_base_name(filepath: str) -> str:
    """Récupère le nom de base du fichier sans extension"""
    if not filepath:
        return "fichier_inconnu"
    filename = os.path.basename(filepath)
    base_name = os.path.splitext(filename)[0]
    return re.sub(r'[<>:"/\\|?*]', '_', base_name)


def extract_game_name(project_path: str) -> str:
    """Extrait le nom du jeu depuis le chemin du projet"""
    try:
        # Extraire le nom du dossier du projet
        game_name = os.path.basename(project_path.rstrip(os.sep))
        
        # Nettoyer le nom (supprimer caractères spéciaux)
        game_name = re.sub(r'[<>:"/\\|?*]', '_', game_name)
        
        return game_name
    except Exception:
        return "jeu_inconnu"


def fix_translation_errors_in_txt(filepath: str) -> int:
    """
    Corrige automatiquement les erreurs courantes dans un fichier de traduction:
    1. Ellipses DeepL ([...], […]) → ...
    2. Guillemets français (« ») → \"
    3. Chevrons doubles (<< >>) → \" (sauf code Ren'Py <<<>>>)
    4. Pourcentages isolés (%) → %%
    5. Guillemets non-échappés → \"
    
    Retourne le nombre de corrections effectuées
    """
    try:
        if not os.path.exists(filepath):
            return 0
        
        corrections = 0
        fixed_lines = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                original_line = line
                fixed_line = line
                
                # CORRECTION 1: Ellipses DeepL → ...
                # Patterns: [...], [..], [.....], […], [……]
                if '[' in fixed_line and ']' in fixed_line:
                    # Détecter et remplacer les ellipses DeepL
                    import re
                    deepl_patterns = [
                        (r'\[\.{2,}\]', '...'),   # [...], [..], [....]
                        (r'\[…+\]', '...'),       # […], [……]
                    ]
                    
                    for pattern, replacement in deepl_patterns:
                        matches = re.findall(pattern, fixed_line)
                        if matches:
                            fixed_line = re.sub(pattern, replacement, fixed_line)
                            corrections += len(matches)
                
                # CORRECTION 2: Guillemets français → \"
                # Patterns: «bonjour» → \"bonjour\"
                if '«' in fixed_line or '»' in fixed_line:
                    import re
                    # Remplacer guillemets français par guillemets ASCII échappés
                    fixed_line = fixed_line.replace('«', '\\"')
                    fixed_line = fixed_line.replace('»', '\\"')
                    corrections += original_line.count('«') + original_line.count('»')
                
                # CORRECTION 3: Chevrons doubles << >> → \" (sauf code Ren'Py)
                # Pattern: << ou >> mais PAS <<< ou >>>
                if '<<' in fixed_line or '>>' in fixed_line:
                    import re
                    # Vérifier que ce n'est pas du code Ren'Py (<<<, >>>)
                    if not ('<<<' in fixed_line or '>>>' in fixed_line):
                        # Compter avant remplacement
                        chevrons_count = len(re.findall(r'(?<![<>])<<(?![<>])', fixed_line))
                        chevrons_count += len(re.findall(r'(?<![<>])>>(?![<>])', fixed_line))
                        
                        # Remplacer << par \" (mais pas <<<)
                        fixed_line = re.sub(r'(?<![<>])<<(?![<>])', '\\"', fixed_line)
                        # Remplacer >> par \" (mais pas >>>)
                        fixed_line = re.sub(r'(?<![<>])>>(?![<>])', '\\"', fixed_line)
                        
                        corrections += chevrons_count
                
                # CORRECTION 4: Pourcentages isolés % → %%
                # Pattern: % isolé (pas suivi de %% ou de variables %s, %d, %f, etc.)
                if '%' in fixed_line:
                    import re
                    # Pattern pour % isolé (pas dans %% ou %variable ou %(name)s)
                    pattern = r'(?<!%)%(?!%|[sdfioxXeEgGcr]|\([^)]+\))'
                    
                    matches = re.findall(pattern, fixed_line)
                    if matches:
                        # Remplacer % isolé par %%
                        fixed_line = re.sub(pattern, '%%', fixed_line)
                        corrections += len(matches)
                
                # CORRECTION 5: Guillemets non-échappés
                if '"' in fixed_line:
                    # Vérifier si guillemets non-échappés au milieu de la ligne
                    parts = fixed_line.split('"')
                    new_parts = []
                    for i, part in enumerate(parts):
                        if i < len(parts) - 1:  # Pas la dernière partie
                            # Si la partie ne se termine pas par \, ajouter échappement
                            if not part.endswith('\\'):
                                new_parts.append(part + '\\"')
                                if i > 0 or part:  # Correction effectuée
                                    corrections += 1
                            else:
                                new_parts.append(part + '"')
                        else:
                            new_parts.append(part)
                    fixed_line = ''.join(new_parts)
                
                fixed_lines.append(fixed_line)
        
        # Réécrire le fichier si corrections
        if corrections > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            logger.info(f"✅ {corrections} correction(s) appliquée(s) à {os.path.basename(filepath)}")
        
        return corrections
        
    except Exception as e:
        logger.error(f"Erreur correction automatique: {e}")
        return 0


class FileReconstructor:
    """Classe principale pour la reconstruction des fichiers traduits"""
    
    def __init__(self):
        """Initialise le reconstructeur"""
        self.file_content = []
        self.original_path = None
        self.reconstruction_time = 0
        
        # Préfixes par défaut (compatibles avec extraction)
        self.code_prefix = "RENPY_CODE"
        self.asterisk_prefix = "RENPY_ASTERISK"
        self.tilde_prefix = "RENPY_TILDE"
        self.empty_prefix = "RENPY_EMPTY"
        
        # Initialiser les données
        self._reset_reconstruction_data()
    
    def _reset_reconstruction_data(self):
        """Réinitialise toutes les données de reconstruction"""
        self.mapping = OrderedDict()
        self.empty_mapping = OrderedDict()
        self.asterix_mapping = OrderedDict()
        self.tilde_mapping = OrderedDict()
        
        self.translations = []
        self.duplicate_translations = []
        self.asterix_translations = []
        self.tilde_translations = []
        
        self.line_to_content_indices = {}
        self.original_lines = {}
        self.all_contents_linear = []
        self.suffixes = []
        self.content_prefixes = []
        self.content_suffixes = []
        self.asterix_metadata = {}
        self.tilde_metadata = {}
    
    def load_file_content(self, file_content: List[str], original_path: str):
        """Charge le fichier original et les données d'extraction"""
        if not file_content or not isinstance(file_content, list):
            raise ValueError("Contenu de fichier invalide ou manquant")
        
        # Essayer de charger le fichier avec placeholders (préféré pour reconstruction)
        file_base = get_file_base_name(original_path)
        game_name = extract_game_name(os.path.dirname(original_path))
        reference_folder = os.path.join("01_Temporary", game_name, "fichiers_a_referencer")
        placeholders_path = os.path.join(reference_folder, f'{file_base}_with_placeholders.rpy')
        
        if os.path.exists(placeholders_path):
            logger.info(f"📂 Chargement fichier avec placeholders: {placeholders_path}")
            with open(placeholders_path, 'r', encoding='utf-8') as f:
                self.file_content = f.readlines()
        else:
            logger.warning("⚠️ Fichier with_placeholders.rpy non trouvé, utilisation du fichier original")
            self.file_content = file_content[:]
        
        self.original_path = original_path
        
        # Charger les données de reconstruction
        self._load_data_for_reconstruction()
    
    def _load_data_for_reconstruction(self):
        """Charge les métadonnées JSON et les fichiers de traduction"""
        try:
            file_base = get_file_base_name(self.original_path)
            game_name = extract_game_name(os.path.dirname(self.original_path))
            
            # Utiliser le bon nom de dossier (fichiers_a_referencer dans le nouveau système)
            reference_folder = os.path.join("01_Temporary", game_name, "fichiers_a_referencer")
            translate_folder = os.path.join("01_Temporary", game_name, "fichiers_a_traduire")
            
            logger.info(f"📂 Dossier référence: {reference_folder}")
            logger.info(f"📂 Dossier traduction: {translate_folder}")
            
            # Charger le fichier positions.json
            positions_file = os.path.join(reference_folder, f'{file_base}_positions.json')
            
            if not os.path.exists(positions_file):
                raise FileNotFoundError(f"Fichier positions.json introuvable: {positions_file}")
            
            with open(positions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Charger les métadonnées
                self.line_to_content_indices = {int(k): v for k, v in data['line_to_content_indices'].items()}
                self.original_lines = {int(k): v for k, v in data['original_lines'].items()}
                self.all_contents_linear = data['all_contents_linear']
                self.suffixes = data['suffixes']
                self.content_prefixes = data.get('content_prefixes', [])
                self.content_suffixes = data.get('content_suffixes', [])
                
                # Charger les mappings
                self.mapping = data.get('mapping', {})
                self.asterix_mapping = data.get('asterix_mapping', {})
                self.tilde_mapping = data.get('tilde_mapping', {})
                self.empty_mapping = data.get('empty_mapping', {})
                
                # Charger les métadonnées
                self.asterix_metadata = data.get('asterix_metadata', {})
                self.tilde_metadata = data.get('tilde_metadata', {})
            
            # Charger les fichiers de traduction
            self._load_translation_files(translate_folder, file_base)
            
            total_dialogue = len(self.translations)
            total_asterix = len(self.asterix_translations)
            total_tilde = len(self.tilde_translations)
            total_lines = total_dialogue + total_asterix + total_tilde
            
            logger.info(f"📂 Chargement : {total_lines} lignes (dialogue:{total_dialogue}, astérisques:{total_asterix}, tildes:{total_tilde})")
            
        except Exception as e:
            logger.error(f"Erreur chargement données reconstruction: {e}")
            raise
    
    def _load_translation_files(self, translate_folder: str, file_base: str):
        """Charge tous les fichiers de traduction"""
        try:
            # Fichier dialogue principal
            dialogue_files = self._find_translation_files(translate_folder, f'{file_base}_dialogue.txt')
            if dialogue_files:
                raw_translations = self._load_multi_files(dialogue_files)
                self.translations = [line.rstrip('\n\r') for line in raw_translations]
            
            # Fichier doublons (optionnel)
            doublons_files = self._find_translation_files(translate_folder, f'{file_base}_doublons.txt')
            if doublons_files:
                raw_duplicates = self._load_multi_files(doublons_files)
                self.duplicate_translations = [line.rstrip('\n\r') for line in raw_duplicates]
            
            # Fichier astérisques/tildes combiné
            asterix_files = self._find_translation_files(translate_folder, f'{file_base}_asterix.txt')
            if asterix_files:
                raw_asterix_lines = self._load_multi_files(asterix_files)
                all_lines = [line.rstrip('\n\r') for line in raw_asterix_lines]
                
                # Séparer astérisques et tildes
                asterix_count = len(self.asterix_mapping)
                tilde_count = len(self.tilde_mapping)
                
                if asterix_count > 0:
                    self.asterix_translations = all_lines[:asterix_count]
                if tilde_count > 0:
                    self.tilde_translations = all_lines[asterix_count:asterix_count + tilde_count]
            
        except Exception as e:
            logger.error(f"Erreur chargement fichiers traduction: {e}")
            raise
    
    def _find_translation_files(self, folder: str, base_filename: str) -> List[str]:
        """Trouve tous les fichiers de traduction (avec support multi-fichiers)"""
        try:
            name, ext = os.path.splitext(base_filename)
            
            # Fichier principal
            main_file = os.path.join(folder, base_filename)
            
            # Fichiers numérotés
            numbered_pattern = os.path.join(folder, f"{name}_*{ext}")
            numbered_files = glob.glob(numbered_pattern)
            
            all_files = []
            
            if os.path.exists(main_file):
                all_files.append(main_file)
            
            all_files.extend(numbered_files)
            
            if all_files:
                # Trier par numéro
                all_files.sort(key=lambda x: self._extract_file_number(x, base_filename))
                return all_files
            
            return []
            
        except Exception:
            return []
    
    def _extract_file_number(self, filepath: str, base_filename: str) -> int:
        """Extrait le numéro d'un fichier pour le tri"""
        try:
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(base_filename)
            
            if filename == base_filename:
                return 0  # Fichier principal
            
            # Extraire le numéro
            pattern = f"{name}_"
            if filename.startswith(pattern):
                number_part = filename[len(pattern):-len(ext)]
                return int(number_part)
            
            return 999
            
        except Exception:
            return 999
    
    def _load_multi_files(self, files: List[str]) -> List[str]:
        """Charge et concatène plusieurs fichiers"""
        all_lines = []
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_lines.extend(f.readlines())
            except Exception as e:
                logger.error(f"Erreur lecture {file_path}: {e}")
        
        return all_lines
    
    def reconstruct_file(self, save_mode: str = 'new_file') -> Dict[str, Any]:
        """
        Reconstruit le fichier traduit
        save_mode: 'overwrite' ou 'new_file'
        """
        start_time = time.time()
        
        try:
            # Le fichier self.file_content contient déjà les placeholders (chargé depuis _with_placeholders.rpy)
            content = self.file_content.copy()
            
            # Remplacer seulement les placeholders de dialogue par les traductions
            content = self._replace_dialogue_placeholders(content)
            
            # Remplacer les autres placeholders (codes, astérisques, tildes, vides)
            content = self._replace_other_placeholders(content)
            
            # Ajouter marqueur de reconstruction
            content = self._add_reconstruction_marker(content)
            
            # Déterminer le chemin de sauvegarde
            if save_mode == 'overwrite':
                save_path = self.original_path
            else:  # new_file
                save_path = self.original_path.replace('.rpy', '_translated.rpy')
            
            # Écrire le fichier
            with open(save_path, 'w', encoding='utf-8', newline='') as f:
                f.writelines(content)
            
            self.reconstruction_time = time.time() - start_time
            logger.info(f"✅ Reconstruction réussie en {self.reconstruction_time:.2f}s")
            
            return {
                'success': True,
                'save_path': save_path,
                'save_mode': save_mode,
                'reconstruction_time': self.reconstruction_time
            }
            
        except Exception as e:
            logger.error(f"Erreur reconstruction: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _replace_dialogue_placeholders(self, content: List[str]) -> List[str]:
        """Remplace les placeholders de dialogue par les traductions"""
        try:
            # Pour chaque ligne qui contient des dialogues traduits
            for position_idx, content_indices in self.line_to_content_indices.items():
                if position_idx >= len(content):
                    continue
                    
                line = content[position_idx]
                
                # Vérifier si c'est une ligne de dialogue (contient des guillemets)
                if '"' in line and line.strip().startswith('"'):
                    # Construire la nouvelle ligne avec les traductions
                    new_line_parts = []
                    
                    # Récupérer l'indentation
                    indent_match = re.match(r'^(\s*)', line)
                    indent = indent_match.group(1) if indent_match else ''
                    
                    # Construire le contenu traduit
                    translated_content = ""
                    for content_idx in content_indices:
                        if content_idx < len(self.translations):
                            translation = self.translations[content_idx]
                            # Récupérer les préfixes et suffixes pour ce contenu
                            if position_idx < len(self.content_prefixes):
                                prefixes = self.content_prefixes[position_idx]
                                suffixes = self.content_suffixes[position_idx]
                                
                                prefix = prefixes[0] if prefixes else ''
                                suffix = suffixes[0] if suffixes else ''
                                
                                translated_content += prefix + translation + suffix
                            else:
                                translated_content += translation
                    
                    # Ajouter le suffixe de ligne
                    line_suffix = ""
                    if position_idx < len(self.suffixes):
                        line_suffix = self.suffixes[position_idx]
                    
                    # Construire la nouvelle ligne
                    new_line = indent + '"' + translated_content + '"' + line_suffix
                    if not new_line.endswith('\n'):
                        new_line += '\n'
                    
                    content[position_idx] = new_line
            
            logger.info(f"✅ {len(self.line_to_content_indices)} lignes de dialogue reconstruites")
            return content
            
        except Exception as e:
            logger.error(f"Erreur remplacement placeholders dialogue: {e}")
            raise
    
    def _replace_other_placeholders(self, content: List[str]) -> List[str]:
        """Remplace les autres placeholders (codes, astérisques, tildes, vides)"""
        try:
            content_str = ''.join(content)
            
            # 1. Remplacer les codes/variables (inverser le mapping)
            for original, placeholder in self.mapping.items():
                content_str = content_str.replace(placeholder, original)
            
            # 2. Remplacer les astérisques
            for i, (placeholder, metadata) in enumerate(self.asterix_mapping.items()):
                if i < len(self.asterix_translations):
                    translation = self.asterix_translations[i]
                    # Reconstruire avec le bon format d'astérisques
                    content_str = content_str.replace(placeholder, f'* "{translation}"')
            
            # 3. Remplacer les tildes
            for i, (placeholder, metadata) in enumerate(self.tilde_mapping.items()):
                if i < len(self.tilde_translations):
                    translation = self.tilde_translations[i]
                    # Reconstruire avec le bon format de tildes
                    content_str = content_str.replace(placeholder, f'~ "{translation}"')
            
            # 4. Remplacer les textes vides
            for placeholder in self.empty_mapping.keys():
                content_str = content_str.replace(placeholder, '""')
            
            # Reconvertir en liste de lignes
            return content_str.splitlines(keepends=True)
            
        except Exception as e:
            logger.error(f"Erreur remplacement autres placeholders: {e}")
            raise
    
    
    def _add_reconstruction_marker(self, content: List[str]) -> List[str]:
        """Ajoute un marqueur de reconstruction à la fin du fichier"""
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        marker = f"\n# Fichier reconstruit après traduction par RenExtract le {timestamp}\n"
        
        if content and not content[-1].endswith('\n'):
            content[-1] += '\n'
        
        content.append(marker)
        return content


def validate_translation_files(
    filepath: str,
    extracted_count: int,
    asterix_count: int = 0,
    tilde_count: int = 0
) -> Dict[str, Any]:
    """
    Valide que les fichiers de traduction sont cohérents
    """
    try:
        file_base = get_file_base_name(filepath)
        game_name = extract_game_name(os.path.dirname(filepath))
        
        translate_folder = os.path.join("01_Temporary", game_name, "fichiers_a_traduire")
        
        validation_results = {
            'overall_valid': True,
            'files_validated': {},
            'summary': {
                'total_expected': extracted_count + asterix_count + tilde_count,
                'total_found': 0,
                'errors': []
            }
        }
        
        # Valider fichier dialogue
        dialogue_file = os.path.join(translate_folder, f"{file_base}_dialogue.txt")
        if os.path.exists(dialogue_file):
            with open(dialogue_file, 'r', encoding='utf-8') as f:
                dialogue_lines = len(f.readlines())
            
            if dialogue_lines == extracted_count:
                validation_results['files_validated']['dialogue'] = {
                    'valid': True,
                    'expected': extracted_count,
                    'found': dialogue_lines
                }
                validation_results['summary']['total_found'] += dialogue_lines
            else:
                validation_results['overall_valid'] = False
                validation_results['files_validated']['dialogue'] = {
                    'valid': False,
                    'expected': extracted_count,
                    'found': dialogue_lines
                }
                validation_results['summary']['errors'].append(
                    f"Dialogue: {dialogue_lines} lignes trouvées, {extracted_count} attendues"
                )
        else:
            validation_results['overall_valid'] = False
            validation_results['summary']['errors'].append("Fichier dialogue manquant")
        
        # Valider fichier astérisques/tildes
        total_special = asterix_count + tilde_count
        if total_special > 0:
            asterix_file = os.path.join(translate_folder, f"{file_base}_asterix.txt")
            if os.path.exists(asterix_file):
                with open(asterix_file, 'r', encoding='utf-8') as f:
                    asterix_lines = len(f.readlines())
                
                if asterix_lines == total_special:
                    validation_results['files_validated']['asterix'] = {
                        'valid': True,
                        'expected': total_special,
                        'found': asterix_lines
                    }
                    validation_results['summary']['total_found'] += asterix_lines
                else:
                    validation_results['overall_valid'] = False
                    validation_results['files_validated']['asterix'] = {
                        'valid': False,
                        'expected': total_special,
                        'found': asterix_lines
                    }
                    validation_results['summary']['errors'].append(
                        f"Astérisques/Tildes: {asterix_lines} lignes trouvées, {total_special} attendues"
                    )
        
        return {
            'success': True,
            'validation': validation_results
        }
        
    except Exception as e:
        logger.error(f"Erreur validation: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# Instance globale
reconstruction_manager = FileReconstructor()


def reconstruct_from_translations(
    file_content: List[str],
    filepath: str,
    save_mode: str = 'new_file'
) -> Dict[str, Any]:
    """
    Fonction principale de reconstruction pour l'API
    """
    try:
        # Créer une nouvelle instance
        reconstructor = FileReconstructor()
        reconstructor.load_file_content(file_content, filepath)
        
        # Lancer la reconstruction
        result = reconstructor.reconstruct_file(save_mode)
        
        return result
        
    except Exception as e:
        logger.error(f"Erreur reconstruction: {e}")
        return {
            'success': False,
            'error': str(e)
        }
