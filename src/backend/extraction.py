# src/backend/extraction.py
# Extraction Functions Module
# Created for RenExtract WebView

"""
Module d'extraction des textes depuis les fichiers Ren'Py
Implémentation complète du flux d'extraction avec protection des codes et gestion des doublons
"""

import os
import re
import time
import json
from collections import OrderedDict
from typing import Dict, List, Any, Optional, Tuple
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PlaceholderGenerator:
    """Générateur de placeholders pour la protection des codes"""
    
    def __init__(self, pattern: str):
        self.original_pattern = self._normalize_pattern(pattern)
        self.counter = 1
        self.pattern_type = None
        self.format_info = {}
        self._analyze_pattern()
    
    def _normalize_pattern(self, pattern: str) -> str:
        """Normalise le pattern en convertissant les minuscules en majuscules"""
        try:
            # Pattern alphanumérique entre parenthèses : (c1) -> (C1)
            paren_match = re.match(r'^\(([a-z])(\d+)\)$', pattern)
            if paren_match:
                letter = paren_match.group(1).upper()
                number = paren_match.group(2)
                return f"({letter}{number})"
            
            # Pattern avec underscore et lettre : code_c1 -> code_C1
            underscore_match = re.match(r'^(.+)_([a-z])(\d+)$', pattern)
            if underscore_match:
                prefix = underscore_match.group(1)
                letter = underscore_match.group(2).upper()
                number = underscore_match.group(3)
                return f"{prefix}_{letter}{number}"
            
            return pattern
        except Exception as e:
            logger.error(f"Erreur normalisation pattern: {e}")
            return pattern
    
    def _analyze_pattern(self):
        """Analyse le pattern et configure le générateur"""
        try:
            # Pattern 1: Numérique avec underscore (RENPY_CODE_001)
            underscore_match = re.match(r'^(.+)_(\d+)$', self.original_pattern)
            if underscore_match:
                self.pattern_type = 'underscore_numeric'
                self.prefix = underscore_match.group(1)
                self.counter = int(underscore_match.group(2))
                self.format_info = {
                    'digits': len(underscore_match.group(2)),
                    'separator': '_'
                }
                return
            
            # Pattern 2: Alphanumérique entre parenthèses (B01), (C01)
            alpha_paren_match = re.match(r'^\(([A-Z])(\d+)\)$', self.original_pattern)
            if alpha_paren_match:
                self.pattern_type = 'alpha_numeric_paren'
                self.prefix = ""
                self.counter = int(alpha_paren_match.group(2))
                self.format_info = {
                    'letter': alpha_paren_match.group(1),
                    'digits': len(alpha_paren_match.group(2))
                }
                return
            
            # Pattern 3: Numérique avec parenthèses (CODE(01))
            paren_match = re.match(r'^(.+)\((\d+)\)$', self.original_pattern)
            if paren_match:
                self.pattern_type = 'paren_numeric'
                self.prefix = paren_match.group(1)
                self.counter = int(paren_match.group(2))
                self.format_info = {
                    'digits': len(paren_match.group(2))
                }
                return
            
            # Pattern 4: Juste des chiffres entre parenthèses ((01))
            only_paren_match = re.match(r'^\((\d+)\)$', self.original_pattern)
            if only_paren_match:
                self.pattern_type = 'only_paren_numeric'
                self.prefix = ""
                self.counter = int(only_paren_match.group(1))
                self.format_info = {
                    'digits': len(only_paren_match.group(1))
                }
                return
            
            # Fallback
            self.pattern_type = 'simple_prefix'
            self.prefix = self.original_pattern
            self.counter = 1
            self.format_info = {'digits': 3}
            
        except Exception as e:
            logger.error(f"Erreur analyse pattern '{self.original_pattern}': {e}")
            self.pattern_type = 'simple_prefix'
            self.prefix = self.original_pattern
            self.counter = 1
            self.format_info = {'digits': 3}
    
    def next_placeholder(self) -> str:
        """Génère le prochain placeholder selon le pattern détecté"""
        try:
            if self.pattern_type == 'underscore_numeric':
                digits = self.format_info['digits']
                result = f"{self.prefix}_{self.counter:0{digits}d}"
            elif self.pattern_type == 'alpha_numeric_paren':
                letter = self.format_info['letter']
                digits = self.format_info['digits']
                result = f"({letter}{self.counter:0{digits}d})"
            elif self.pattern_type == 'paren_numeric':
                digits = self.format_info['digits']
                result = f"{self.prefix}({self.counter:0{digits}d})"
            elif self.pattern_type == 'only_paren_numeric':
                digits = self.format_info['digits']
                result = f"({self.counter:0{digits}d})"
            else:  # simple_prefix
                digits = self.format_info['digits']
                result = f"{self.prefix}_{self.counter:0{digits}d}"
            
            self.counter += 1
            return result
            
        except Exception as e:
            logger.error(f"Erreur génération placeholder: {e}")
            result = f"{self.prefix}_{self.counter:03d}"
            self.counter += 1
            return result


class DuplicateManager:
    """Gestionnaire pour la détection et la gestion des textes dupliqués"""
    
    def __init__(self):
        self.seen_texts = set()
        self.duplicate_texts_for_translation = []
    
    def check_and_add(self, text: str) -> bool:
        """
        Vérifie si le texte est un doublon et l'ajoute si nécessaire
        Retourne True si c'est un doublon, False si c'est unique
        """
        if text in self.seen_texts:
            # C'est un doublon
            if text not in self.duplicate_texts_for_translation:
                self.duplicate_texts_for_translation.append(text)
            return True
        else:
            # Texte unique
            self.seen_texts.add(text)
            return False


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


def ensure_game_structure(game_name: str) -> Dict[str, str]:
    """Crée la structure de dossiers pour l'extraction"""
    try:
        # Dossier temporaire principal (utiliser le dossier existant de l'application)
        temp_dir = "01_Temporary"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
        # Dossier du jeu
        game_dir = os.path.join(temp_dir, game_name)
        if not os.path.exists(game_dir):
            os.makedirs(game_dir)
        
        # Dossier fichiers à traduire
        translate_dir = os.path.join(game_dir, "fichiers_a_traduire")
        if not os.path.exists(translate_dir):
            os.makedirs(translate_dir)
        
        # Dossier fichiers à référencer
        reference_dir = os.path.join(game_dir, "fichiers_a_referencer")
        if not os.path.exists(reference_dir):
            os.makedirs(reference_dir)
        
        return {
            'temp_dir': temp_dir,
            'game_dir': game_dir,
            'translate_dir': translate_dir,
            'reference_dir': reference_dir
        }
    except Exception as e:
        logger.error(f"Erreur création structure: {e}")
        raise


class TextExtractor:
    """Classe principale pour l'extraction des textes Ren'Py"""
    
    def __init__(self):
        """Initialise l'extracteur avec les préfixes par défaut"""
        self.file_content = []
        self.original_path = None
        self.extraction_time = 0
        
        # Charger les préfixes par défaut
        self._load_default_prefixes()
        
        # Paramètres d'extraction
        self.detect_duplicates = True
        
        # Initialiser les données d'extraction
        self._reset_extraction_data()
    
    def _load_default_prefixes(self):
        """Charge les préfixes par défaut pour les placeholders"""
        try:
            # Préfixes par défaut
            self.code_generator = PlaceholderGenerator("RENPY_CODE_001")
            self.asterisk_generator = PlaceholderGenerator("RENPY_ASTERISK_001")
            self.tilde_generator = PlaceholderGenerator("RENPY_TILDE_001")
            self.empty_prefix = "RENPY_EMPTY"
            
            logger.info("Préfixes par défaut chargés")
        except Exception as e:
            logger.error(f"Erreur chargement préfixes: {e}")
            # Valeurs de fallback
            self.code_generator = PlaceholderGenerator("(01)")
            self.asterisk_generator = PlaceholderGenerator("(B1)")
            self.tilde_generator = PlaceholderGenerator("(C1)")
            self.empty_prefix = "RENPY_EMPTY"
    
    def load_file_content(self, content: List[str], filepath: str):
        """Charge le contenu du fichier à extraire"""
        if not content or not isinstance(content, list):
            raise ValueError("Contenu de fichier invalide ou manquant")
        
        self.file_content = content[:]
        self.original_path = filepath
        self._reset_extraction_data()
    
    def _reset_extraction_data(self):
        """Réinitialise toutes les données d'extraction"""
        # Mappings de protection
        self.mapping = OrderedDict()
        self.asterix_mapping = OrderedDict()
        self.tilde_mapping = OrderedDict()
        self.empty_mapping = OrderedDict()
        
        # Textes extraits
        self.extracted_texts = []
        self.asterix_texts = []
        self.tilde_texts = []
        self.empty_texts = []
        
        # Métadonnées pour reconstruction
        self.all_contents_linear = []
        self.line_to_content_indices = {}
        self.original_lines_with_translations = {}
        self.line_suffixes = []
        self.line_content_prefixes = []
        self.line_content_suffixes = []
        
        # Gestionnaire de doublons
        self.duplicate_manager = DuplicateManager()
        
        # Compteurs
        self.extracted_count = 0
        self.asterix_count = 0
        self.tilde_count = 0
        self.empty_count = 0
    
    def extract_texts(self) -> Dict[str, Any]:
        """
        Fonction principale d'extraction des textes
        Implémente le flux complet : protection -> extraction -> sauvegarde
        """
        start_time = time.time()
        logger.info("📤 Début de l'extraction")
        
        # Réinitialisation
        self._reset_extraction_data()
        
        logger.info(f"  - Détection doublons: {'✅ ACTIVÉE' if self.detect_duplicates else '❌ DÉSACTIVÉE'}")
        
        # ÉTAPE 1: Protection des codes/variables
        self._build_code_mapping()
        
        # ÉTAPE 2: Protection des textes vides
        self._apply_empty_text_protection()
        
        # ÉTAPE 3: Protection des astérisques
        self._build_asterix_mapping_with_stack()
        
        # ÉTAPE 4: Protection des tildes
        self._build_tilde_mapping_two_pass()
        
        # ÉTAPE 5: Extraction des dialogues
        if self.detect_duplicates:
            self._extract_dialogue_and_handle_duplicates()
        else:
            self._extract_dialogue_simple()
        
        # ÉTAPE 6: Sauvegarde des fichiers
        self.extraction_time = time.time() - start_time
        result = self._save_extraction_files()
        
        # Mise à jour des compteurs
        self.extracted_count = len(self.extracted_texts)
        self.asterix_count = len(self.asterix_texts)
        self.tilde_count = len(self.tilde_texts)
        self.empty_count = len(self.empty_texts)
        
        result['extracted_count'] = self.extracted_count
        result['asterix_count'] = self.asterix_count
        result['tilde_count'] = self.tilde_count
        result['empty_count'] = self.empty_count
        result['duplicate_count'] = len(self.duplicate_manager.duplicate_texts_for_translation)
        
        # Statistiques finales
        doublons_count = len(self.duplicate_manager.duplicate_texts_for_translation) if self.detect_duplicates else 0
        logger.info(f"  Dialogues: {self.extracted_count} | Astérisques: {self.asterix_count} | Tildes: {self.tilde_count} | Vides: {self.empty_count} | Doublons: {doublons_count}")
        
        return result
    
    def _should_process_line(self, stripped_line: str) -> bool:
        """Détermine si une ligne doit être traitée pour les protections"""
        # Ignorer les commentaires
        if stripped_line.startswith('#'):
            return False
        # Ignorer les directives Ren'Py
        if stripped_line.lower().startswith(('translate', 'old', 'voice')):
            return False
        # Traiter les lignes new (pour les choix)
        if stripped_line.startswith('new '):
            return True
        # Traiter les lignes avec guillemets (dialogues)
        if '"' in stripped_line:
            return True
        return False
    
    def _is_dialogue_line(self, stripped_line: str) -> bool:
        """Détermine si une ligne contient des dialogues"""
        # Lignes de dialogue classiques
        if '"' in stripped_line and not stripped_line.startswith('#'):
            return True
        # Lignes new (choix)
        if stripped_line.startswith('new '):
            return True
        return False
    
    def _build_code_mapping(self):
        """Protection des codes/variables Ren'Py"""
        try:
            # Patterns à protéger
            patterns = [
                # Variables entre crochets [player_name], [color=#ff0000]
                (r'\[[^\]]+\]', 'bracket_variables'),
                # Variables de formatage %s, %d, %(name)s
                (r'%(?:\([^)]+\))?[sdifcxo]', 'format_variables'),
                # Échappements \n, \t, \r, \\, \"
                (r'\\[ntr\\"]', 'escapes'),
                # Balises HTML <b>, <i>, <color=#xxx>
                (r'<[^>]+>', 'html_tags'),
                # Balises accolades {color=#xxx}, {size=24}
                (r'\{[^}]+\}', 'brace_tags'),
                # Codes spéciaux Ren'Py {w}, {nw}, {p}, {fast}
                (r'\{[wnpf][a-z]*\}', 'special_codes'),
            ]
            
            for pattern, pattern_type in patterns:
                self._protect_pattern_in_content(pattern, pattern_type)
            
            logger.info(f"✅ Codes protégés: {len(self.mapping)} patterns")
            
        except Exception as e:
            logger.error(f"Erreur protection codes: {e}")
            raise
    
    def _protect_pattern_in_content(self, pattern: str, pattern_type: str):
        """Protège un pattern spécifique dans tout le contenu"""
        for i, line in enumerate(self.file_content):
            if not self._should_process_line(line.strip()):
                continue
            
            matches = re.findall(pattern, line)
            for match in matches:
                if match not in self.mapping:
                    placeholder = self.code_generator.next_placeholder()
                    self.mapping[match] = placeholder
                    logger.debug(f"Variable protégée: '{match}' -> {placeholder}")
            
            # Remplacer dans la ligne
            for original, placeholder in self.mapping.items():
                if original in line:
                    self.file_content[i] = line.replace(original, placeholder)
    
    def _apply_empty_text_protection(self):
        """Protection des chaînes vides"""
        try:
            for i, line in enumerate(self.file_content):
                if not self._should_process_line(line.strip()):
                    continue
                
                # Rechercher les chaînes vides ""
                matches = re.findall(r'""', line)
                for match in matches:
                    placeholder = f"{self.empty_prefix}_{len(self.empty_mapping) + 1:03d}"
                    if placeholder not in self.empty_mapping:
                        self.empty_mapping[placeholder] = ""
                        self.empty_texts.append("")
                        logger.debug(f"Empty protégé: {placeholder}")
                    
                    self.file_content[i] = line.replace(match, placeholder)
            
            logger.info(f"✅ Textes vides protégés: {len(self.empty_mapping)}")
            
        except Exception as e:
            logger.error(f"Erreur protection textes vides: {e}")
            raise
    
    def _build_asterix_mapping_with_stack(self):
        """Protection des astérisques avec gestion de pile"""
        try:
            for i, line in enumerate(self.file_content):
                if not self._should_process_line(line.strip()):
                    continue
                
                # Rechercher les patterns * "texte"
                pattern = r'\*\s*"([^"]*)"'
                matches = re.findall(pattern, line)
                
                for match in matches:
                    full_pattern = f'* "{match}"'
                    if full_pattern not in self.asterix_mapping:
                        placeholder = self.asterisk_generator.next_placeholder()
                        self.asterix_mapping[full_pattern] = placeholder
                        self.asterix_texts.append(match + '\n')
                        logger.debug(f"Asterix protégé: '{full_pattern}' -> {placeholder}")
                    
                    # Remplacer dans la ligne
                    self.file_content[i] = line.replace(full_pattern, f'* {self.asterix_mapping[full_pattern]}')
            
            logger.info(f"✅ Astérisques protégés: {len(self.asterix_mapping)}")
            
        except Exception as e:
            logger.error(f"Erreur protection astérisques: {e}")
            raise
    
    def _build_tilde_mapping_two_pass(self):
        """Protection des tildes en deux passes"""
        try:
            for i, line in enumerate(self.file_content):
                if not self._should_process_line(line.strip()):
                    continue
                
                # Rechercher les patterns ~ "texte"
                pattern = r'~\s*"([^"]*)"'
                matches = re.findall(pattern, line)
                
                for match in matches:
                    full_pattern = f'~ "{match}"'
                    if full_pattern not in self.tilde_mapping:
                        placeholder = self.tilde_generator.next_placeholder()
                        self.tilde_mapping[full_pattern] = placeholder
                        self.tilde_texts.append(match + '\n')
                        logger.debug(f"Tilde protégé: '{full_pattern}' -> {placeholder}")
                    
                    # Remplacer dans la ligne
                    self.file_content[i] = line.replace(full_pattern, f'~ {self.tilde_mapping[full_pattern]}')
            
            logger.info(f"✅ Tildes protégés: {len(self.tilde_mapping)}")
            
        except Exception as e:
            logger.error(f"Erreur protection tildes: {e}")
            raise
    
    def _extract_dialogue_and_handle_duplicates(self):
        """Extraction des dialogues avec gestion des doublons"""
        try:
            for idx, line in enumerate(self.file_content):
                stripped = line.strip()
                if not self._is_dialogue_line(stripped):
                    continue
                
                analysis = self._analyze_and_decompose_line(line)
                if analysis['decomposed_parts']:
                    self.line_to_content_indices[idx] = []
                    
                    for part in analysis['decomposed_parts']:
                        # Ignorer les placeholders vides structurels
                        if part['text'].startswith(f'{self.empty_prefix}_'):
                            continue
                        
                        # Vérifier les doublons
                        is_duplicate = self.duplicate_manager.check_and_add(part['text'])
                        
                        # Stocker l'index
                        content_index = len(self.all_contents_linear)
                        self.all_contents_linear.append(part['text'])
                        self.line_to_content_indices[idx].append(content_index)
                        
                        # Ajouter au fichier de traduction seulement si pas doublon
                        if not is_duplicate:
                            self.extracted_texts.append(part['text'] + '\n')
                    
                    # Sauvegarder les métadonnées
                    if self.line_to_content_indices[idx]:
                        self.original_lines_with_translations[idx] = line
                        self.line_suffixes.append(analysis.get('line_suffix', ''))
                        self.line_content_prefixes.append([p['prefix'] for p in analysis['decomposed_parts']])
                        self.line_content_suffixes.append([p['suffix'] for p in analysis['decomposed_parts']])
            
            logger.info(f"✅ Extraction terminée: {len(self.extracted_texts)} dialogues")
            
        except Exception as e:
            logger.error(f"Erreur extraction dialogues: {e}")
            raise
    
    def _extract_dialogue_simple(self):
        """Version simplifiée sans détection de doublons"""
        try:
            for idx, line in enumerate(self.file_content):
                stripped = line.strip()
                if not self._is_dialogue_line(stripped):
                    continue
                
                analysis = self._analyze_and_decompose_line(line)
                if analysis['decomposed_parts']:
                    self.line_to_content_indices[idx] = []
                    
                    for part in analysis['decomposed_parts']:
                        # Ignorer les placeholders vides structurels
                        if part['text'].startswith(f'{self.empty_prefix}_'):
                            continue
                        
                        # Ajouter tous les textes (pas de vérification doublons)
                        text_to_add = part['text'] if part['text'].strip() else "◊"
                        
                        content_index = len(self.all_contents_linear)
                        self.all_contents_linear.append(text_to_add)
                        self.line_to_content_indices[idx].append(content_index)
                        
                        self.extracted_texts.append(text_to_add + '\n')
                    
                    # Sauvegarder les métadonnées
                    if self.line_to_content_indices[idx]:
                        self.original_lines_with_translations[idx] = line
                        self.line_suffixes.append(analysis.get('line_suffix', ''))
                        self.line_content_prefixes.append([p['prefix'] for p in analysis['decomposed_parts']])
                        self.line_content_suffixes.append([p['suffix'] for p in analysis['decomposed_parts']])
            
            logger.info(f"✅ Extraction terminée: {len(self.extracted_texts)} dialogues")
            
        except Exception as e:
            logger.error(f"Erreur extraction dialogues: {e}")
            raise
    
    def _analyze_and_decompose_line(self, line: str) -> Dict[str, Any]:
        """Analyse et décompose une ligne en parties"""
        try:
            # Extraire les textes entre guillemets
            pattern = r'"([^"]*)"'
            matches = re.findall(pattern, line)
            
            decomposed_parts = []
            for match in matches:
                # Identifier préfixe et suffixe basiques
                prefix = ""
                suffix = ""
                
                # Extraire les préfixes {tags}
                while True:
                    prefix_match = re.match(r'^(\{[^}]*\})', match)
                    if prefix_match:
                        prefix += prefix_match.group(1)
                        match = match[len(prefix_match.group(1)):]
                    else:
                        break
                
                # Extraire les suffixes {tags}
                while True:
                    suffix_match = re.search(r'(\{[^}]*\})$', match)
                    if suffix_match:
                        suffix = suffix_match.group(1) + suffix
                        match = match[:-len(suffix_match.group(1))]
                    else:
                        break
                
                decomposed_parts.append({
                    'text': match,
                    'prefix': prefix,
                    'suffix': suffix
                })
            
            # Extraire le suffixe de ligne (paramètres, etc.)
            line_suffix = ""
            if '(' in line and ')' in line:
                suffix_match = re.search(r'\s+\([^)]*\)\s*$', line)
                if suffix_match:
                    line_suffix = suffix_match.group(0)
            
            return {
                'decomposed_parts': decomposed_parts,
                'line_suffix': line_suffix
            }
            
        except Exception as e:
            logger.error(f"Erreur analyse ligne: {e}")
            return {'decomposed_parts': [], 'line_suffix': ''}
    
    def _save_extraction_files(self) -> Dict[str, Any]:
        """Sauvegarde tous les fichiers d'extraction"""
        try:
            # Déterminer le dossier de sortie
            game_name = extract_game_name(os.path.dirname(self.original_path))
            file_base = get_file_base_name(self.original_path)
            
            structure = ensure_game_structure(game_name)
            
            files_created = {
                'dialogue_file': None,
                'doublons_file': None,
                'asterix_file': None,
                'positions_file': None,
                'output_folder': structure['translate_dir']
            }
            
            # Fichier 1: Positions et métadonnées (JSON)
            positions_file = os.path.join(structure['reference_dir'], f"{file_base}_positions.json")
            positions_data = {
                'line_to_content_indices': self.line_to_content_indices,
                'original_lines': self.original_lines_with_translations,
                'all_contents_linear': self.all_contents_linear,
                'suffixes': self.line_suffixes,
                'content_prefixes': self.line_content_prefixes,
                'content_suffixes': self.line_content_suffixes,
                'mapping': dict(self.mapping),
                'asterix_mapping': dict(self.asterix_mapping),
                'tilde_mapping': dict(self.tilde_mapping),
                'empty_mapping': dict(self.empty_mapping)
            }
            
            with open(positions_file, 'w', encoding='utf-8') as f:
                json.dump(positions_data, f, ensure_ascii=False, indent=2)
            
            files_created['positions_file'] = positions_file
            logger.info(f"Fichier positions créé: {positions_file}")
            
            # Fichier 2: Dialogues principaux
            dialogue_file = os.path.join(structure['translate_dir'], f"{file_base}_dialogue.txt")
            with open(dialogue_file, 'w', encoding='utf-8') as f:
                for text in self.extracted_texts:
                    if not text.endswith('\n'):
                        text += '\n'
                    f.write(text)
            
            files_created['dialogue_file'] = dialogue_file
            logger.info(f"Fichier dialogue créé: {dialogue_file} ({len(self.extracted_texts)} lignes)")
            
            # Fichier 3: Doublons (si détectés)
            if self.detect_duplicates and self.duplicate_manager.duplicate_texts_for_translation:
                doublons_file = os.path.join(structure['translate_dir'], f"{file_base}_doublons.txt")
                with open(doublons_file, 'w', encoding='utf-8') as f:
                    for text in self.duplicate_manager.duplicate_texts_for_translation:
                        if not text.endswith('\n'):
                            text += '\n'
                        f.write(text)
                
                files_created['doublons_file'] = doublons_file
                logger.info(f"Fichier doublons créé: {doublons_file} ({len(self.duplicate_manager.duplicate_texts_for_translation)} lignes)")
            
            # Fichier 4: Astérisques et tildes (si détectés)
            combined_special_texts = self.asterix_texts + self.tilde_texts
            if combined_special_texts:
                asterix_file = os.path.join(structure['translate_dir'], f"{file_base}_asterix.txt")
                with open(asterix_file, 'w', encoding='utf-8') as f:
                    for text in combined_special_texts:
                        if not text.endswith('\n'):
                            text += '\n'
                        f.write(text)
                
                files_created['asterix_file'] = asterix_file
                logger.info(f"Fichier asterix créé: {asterix_file} ({len(combined_special_texts)} lignes)")
            
            logger.info("Fichiers d'extraction sauvegardés")
            return files_created
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde fichiers: {e}")
            raise


# Instance globale de l'extracteur
extraction_manager = TextExtractor()


def extract_texts_from_file(file_content: List[str], filepath: str, detect_duplicates: bool = True) -> Dict[str, Any]:
    """
    Fonction principale d'extraction pour l'API
    """
    try:
        # Créer une nouvelle instance d'extracteur
        extractor = TextExtractor()
        extractor.detect_duplicates = detect_duplicates
        extractor.load_file_content(file_content, filepath)
        
        # Lancer l'extraction
        result = extractor.extract_texts()
        
        return {
            'success': True,
            'result': result,
            'extraction_time': extractor.extraction_time
        }
        
    except Exception as e:
        logger.error(f"Erreur extraction: {e}")
        return {
            'success': False,
            'error': str(e),
            'extraction_time': 0
        }
