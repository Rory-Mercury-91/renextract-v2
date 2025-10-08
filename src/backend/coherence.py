# src/backend/coherence.py
# Système de vérification de cohérence des traductions Ren'Py

import os
import re
import glob
import time
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict

logger = logging.getLogger(__name__)

# Options de vérification globales
coherence_options = {
    'check_variables': True,
    'check_tags': True,
    'check_untranslated': True,
    'check_ellipsis': True,
    'check_escape_sequences': True,
    'check_percentages': True,
    'check_quotations': True,
    'check_parentheses': True,
    'check_syntax': True,
    'check_deepl_ellipsis': True,
    'check_isolated_percent': True,
    'check_french_quotes': True,
    'check_double_dash_ellipsis': True,
    'check_special_codes': False,  # Désactivé par défaut (redondant avec autres contrôles)
    'check_line_structure': True,
    'custom_exclusions': ['OK', 'Menu', 'Continue', 'Yes', 'No', 'Level']
}

def set_coherence_options(options: Dict[str, Any]) -> None:
    """Configure les options de vérification"""
    global coherence_options
    coherence_options.update(options)
    logger.info(f"Options de cohérence mises à jour: {len(options)} paramètres")

def get_coherence_options() -> Dict[str, Any]:
    """Récupère les options de vérification actuelles"""
    return coherence_options.copy()

def check_coherence_unified(target_path: str, return_details: bool = False, selection_info: Optional[Dict] = None) -> Any:
    """
    Vérifie la cohérence des traductions Ren'Py
    
    Args:
        target_path: Chemin fichier ou dossier à analyser
        return_details: Si True, retourne les détails complets
        selection_info: Informations de sélection (projet, langue, fichiers)
    
    Returns:
        Si return_details=True:
            {
                'rapport_path': str,
                'stats': {
                    'files_analyzed': int,
                    'total_issues': int,
                    'issues_by_type': dict
                },
                'issues': list
            }
        Sinon:
            str (chemin du rapport)
    """
    start_time = time.time()
    
    try:
        logger.info(f"🔍 Début vérification cohérence: {target_path}")
        
        # 1. Déterminer les fichiers à analyser
        if os.path.isfile(target_path):
            files_to_check = [target_path]
        else:
            files_to_check = _find_translation_files(target_path, selection_info)
        
        logger.info(f"📂 {len(files_to_check)} fichier(s) à analyser")
        
        # 2. Analyser chaque fichier
        all_issues = []
        for file_path in files_to_check:
            issues = _check_file_coherence(file_path)
            all_issues.extend(issues)
        
        # 3. Calculer les statistiques
        stats = _calculate_statistics(all_issues, len(files_to_check))
        
        # 4. Générer le rapport
        rapport_path = _generate_coherence_report(all_issues, target_path, selection_info, stats)
        
        analysis_time = time.time() - start_time
        logger.info(f"✅ Vérification terminée en {analysis_time:.2f}s - {stats['total_issues']} problème(s)")
        
        # 5. Retourner les résultats
        if return_details:
            return {
                'rapport_path': rapport_path,
                'stats': stats,
                'issues': all_issues,
                'analysis_time': analysis_time
            }
        else:
            return rapport_path
            
    except Exception as e:
        logger.error(f"Erreur vérification cohérence: {e}")
        raise

def _find_translation_files(target_path: str, selection_info: Optional[Dict] = None) -> List[str]:
    """Trouve tous les fichiers de traduction dans un dossier"""
    try:
        if not os.path.exists(target_path):
            return []
        
        # Rechercher tous les fichiers .rpy dans le dossier
        pattern = os.path.join(target_path, "**", "*.rpy")
        files = glob.glob(pattern, recursive=True)
        
        # Filtrer selon les exclusions
        excluded_files = coherence_options.get('custom_exclusions', [])
        filtered_files = []
        
        for file_path in files:
            filename = os.path.basename(file_path)
            should_exclude = False
            
            for exclusion in excluded_files:
                if exclusion.lower() in filename.lower():
                    should_exclude = True
                    break
            
            if not should_exclude:
                filtered_files.append(file_path)
        
        return sorted(filtered_files)
        
    except Exception as e:
        logger.error(f"Erreur recherche fichiers: {e}")
        return []

def _check_file_coherence(file_path: str) -> List[Dict[str, Any]]:
    """Analyse la cohérence d'un fichier de traduction - ligne par ligne - CORRIGÉ"""
    try:
        issues = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        old_line = None
        old_line_num = 0
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Ignorer les commentaires de fichier (# game/...)
            if stripped.startswith('# ') and not stripped.startswith('# "'):
                continue
            
            # Détecter les lignes OLD (commentées avec # "...)
            if _is_old_line(stripped):
                # Ignorer les lignes voice
                if _is_voice_line(stripped):
                    continue
                old_line = stripped[3:-1]  # Extraire le texte entre # " et "
                old_line_num = i
                continue
            
            # Détecter les lignes NEW (commence par " sans #)
            if _is_new_line(stripped):
                # Ignorer les lignes voice
                if _is_voice_line(stripped):
                    continue
                
                new_line = stripped[1:-1] if stripped.endswith('"') else stripped[1:]
                
                if old_line:
                    # Vérifier la cohérence OLD/NEW
                    line_issues = _check_line_coherence(old_line, new_line, file_path, i)
                    issues.extend(line_issues)
                    
                    # Reset pour la prochaine paire
                    old_line = None
                    old_line_num = 0
        
        logger.debug(f"Fichier {os.path.basename(file_path)}: {len(issues)} problème(s)")
        return issues
        
    except Exception as e:
        logger.error(f"Erreur analyse fichier {file_path}: {e}")
        return []

def _check_line_coherence(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie la cohérence entre une ligne OLD et NEW - LOGIQUE SIMPLIFIÉE"""
    issues = []
    
    try:
        # Les lignes sont déjà nettoyées (sans # " et ")
        old_text = old_line.strip()
        new_text = new_line.strip()
        
        if not old_text or not new_text:
            return issues
        
        # Vérifier directement la cohérence entre les textes
        issues.extend(_check_content_coherence(
            old_text, new_text, file_path, line_number
        ))
    
    except Exception as e:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'analysis_error',
            'message': f"Erreur d'analyse: {str(e)}",
            'old_content': old_line,
            'new_content': new_line
        })
    
    return issues

def _parse_translation_blocks(lines: List[str]) -> List[List[str]]:
    """Parse les lignes en blocs de traduction (old/new)"""
    blocks = []
    current_block = []
    
    for line in lines:
        stripped = line.strip()
        
        # Détecter le début d'un bloc de traduction
        if stripped.startswith('translate') and ':' in stripped:
            if current_block:
                blocks.append(current_block)
            current_block = [line]
        elif current_block and (stripped.startswith('"') or stripped.startswith('#') or stripped == ''):
            current_block.append(line)
        elif current_block and stripped == '':
            current_block.append(line)
        elif current_block and not stripped:
            current_block.append(line)
        else:
            if current_block:
                blocks.append(current_block)
            current_block = []
    
    if current_block:
        blocks.append(current_block)
    
    return blocks

def _check_block_coherence(block: List[str], file_path: str, block_idx: int) -> List[Dict[str, Any]]:
    """Vérifie la cohérence d'un bloc de traduction"""
    issues = []
    
    # Extraire les lignes old et new
    old_line = None
    new_line = None
    
    for line in block:
        stripped = line.strip()
        # Chercher le commentaire qui contient le texte original
        if stripped.startswith('# "') and stripped.endswith('"'):
            old_line = stripped[3:-1]  # Enlever '# "' et '"'
        # Chercher la ligne traduite
        elif stripped.startswith('"') and not stripped.startswith('# '):
            new_line = stripped[1:-1] if stripped.endswith('"') else stripped[1:]  # Enlever les guillemets
    
    if old_line is None or new_line is None:
        return issues
    
    # Les lignes sont déjà nettoyées
    old_clean = old_line
    new_clean = new_line
    
    line_number = _get_line_number(block, file_path)
    
    # Appliquer les vérifications selon les options
    if coherence_options.get('check_variables', True):
        issues.extend(_check_variables(old_clean, new_clean, file_path, line_number))
    
    if coherence_options.get('check_tags', True):
        issues.extend(_check_tags(old_clean, new_clean, file_path, line_number))
    
    if coherence_options.get('check_untranslated', True):
        issues.extend(_check_untranslated(old_clean, new_clean, file_path, line_number))
    
    if coherence_options.get('check_escape_sequences', True):
        issues.extend(_check_escape_sequences(old_clean, new_clean, file_path, line_number))
    
    if coherence_options.get('check_percentages', True):
        issues.extend(_check_percentages(old_clean, new_clean, file_path, line_number))
    
    if coherence_options.get('check_parentheses', True):
        issues.extend(_check_parentheses(new_clean, file_path, line_number))
    
    if coherence_options.get('check_deepl_ellipsis', True):
        issues.extend(_check_deepl_ellipsis(new_clean, file_path, line_number))
    
    if coherence_options.get('check_isolated_percent', True):
        issues.extend(_check_isolated_percent(new_clean, file_path, line_number))
    
    if coherence_options.get('check_french_quotes', True):
        issues.extend(_check_french_quotes(new_clean, file_path, line_number))
    
    if coherence_options.get('check_double_dash_ellipsis', True):
        issues.extend(_check_double_dash_ellipsis(new_clean, file_path, line_number))
    
    if coherence_options.get('check_special_codes', False):  # Désactivé par défaut
        issues.extend(_check_special_codes(new_clean, file_path, line_number))
    
    # Note: check_line_structure désactivé - fonction non implémentée
    # if coherence_options.get('check_line_structure', True):
    #     issues.extend(_check_double_quotes_at_end(new_clean, file_path, line_number))
    
    return issues

def _extract_line_content(line):
    """Extrait le contenu d'une ligne (enlève # old, etc.) - DE L'ANCIEN SYSTÈME"""
    line = line.strip()
    
    if line.startswith('# old '):
        return line[6:].strip()
    elif line.startswith('old '):
        return line[4:].strip()
    elif line.startswith('new '):
        return line[4:].strip()
    else:
        # Ligne de dialogue normale (enlever le préfixe du personnage)
        # Exemple: n "Bonjour" -> "Bonjour"
        match = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s+"(.+)"', line)
        if match:
            return f'"{match.group(1)}"'
        return line

def _extract_quoted_content(line):
    """Extrait les contenus entre guillemets d'une ligne - DE L'ANCIEN SYSTÈME"""
    try:
        matches = []
        i = 0
        while i < len(line):
            if line[i] == '"':
                start = i + 1
                i += 1
                content = ""
                
                while i < len(line):
                    if line[i] == '\\' and i + 1 < len(line):
                        content += line[i:i+2]
                        i += 2
                    elif line[i] == '"':
                        matches.append(content)
                        break
                    else:
                        content += line[i]
                        i += 1
            else:
                i += 1
        
        return matches
    
    except Exception:
        return re.findall(r'"([^"]*)"', line)

def _check_content_coherence(old_text, new_text, file_path, line_number):
    """Vérifie la cohérence entre deux contenus textuels - DE L'ANCIEN SYSTÈME"""
    issues = []
    
    # 1. Vérifier les lignes non traduites (si activé)
    if coherence_options.get('check_untranslated', True) and _is_untranslated_line(old_text, new_text):
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'untranslated',
            'message': "Ligne potentiellement non traduite (contenu identique)",
            'old_content': old_text,
            'new_content': new_text
        })
        return issues  # Pas besoin de vérifier le reste si non traduit
    
    # 2. Vérifier les variables (si activé)
    if coherence_options.get('check_variables', True):
        var_issues = _check_variables_coherence(old_text, new_text, line_number)
        issues.extend(var_issues)
    
    # 3. Vérifier les balises (si activé)
    if coherence_options.get('check_tags', True):
        tag_issues = _check_tags_coherence(old_text, new_text, line_number)
        issues.extend(tag_issues)
    
    # 4. Vérifier les séquences d'échappement (si activé)
    if coherence_options.get('check_escape_sequences', True):
        escape_issues = _check_escape_sequences_coherence(old_text, new_text, line_number)
        issues.extend(escape_issues)
    
    # 5. Vérifier les pourcentages (si activé)
    if coherence_options.get('check_percentages', True):
        percent_issues = _check_percentages_coherence(old_text, new_text, line_number)
        issues.extend(percent_issues)
    
    # 6. Vérifier les guillemets (si activé)
    if coherence_options.get('check_quotations', True):
        quote_issues = _check_quotations_coherence(old_text, new_text, line_number)
        issues.extend(quote_issues)
    
    # 7. Vérifier les parenthèses (si activé)
    if coherence_options.get('check_parentheses', True):
        paren_issues = _check_parentheses_coherence(old_text, new_text, line_number)
        issues.extend(paren_issues)
    
    # 8. Vérifier la syntaxe (si activé)
    if coherence_options.get('check_syntax', True):
        syntax_issues = _check_syntax_coherence(old_text, new_text, line_number)
        issues.extend(syntax_issues)
    
    # 9. Vérifier les ellipses DeepL (si activé)
    if coherence_options.get('check_deepl_ellipsis', True):
        deepl_issues = _check_deepl_ellipsis_coherence(old_text, new_text, line_number)
        issues.extend(deepl_issues)
    
    # 10. Vérifier les pourcentages isolés (si activé)
    if coherence_options.get('check_isolated_percent', True):
        isolated_issues = _check_isolated_percent_coherence(old_text, new_text, line_number)
        issues.extend(isolated_issues)
    
    # 11. Vérifier les guillemets français (si activé)
    if coherence_options.get('check_french_quotes', True):
        french_issues = _check_french_quotes_coherence(old_text, new_text, line_number)
        issues.extend(french_issues)
    
    # 12. Vérifier les doubles tirets -- → ... (si activé)
    if coherence_options.get('check_double_dash_ellipsis', True):
        dash_issues = _check_double_dash_ellipsis_coherence(old_text, new_text, line_number)
        issues.extend(dash_issues)
    
    # 13. Vérifier la structure des lignes (si activé)
    if coherence_options.get('check_line_structure', True):
        structure_issues = _check_line_structure_coherence(old_text, new_text, line_number)
        issues.extend(structure_issues)
    
    return issues

def _get_line_number(block: List[str], file_path: str) -> int:
    """Estime le numéro de ligne du bloc (approximatif)"""
    # Pour simplifier, on utilise l'index du bloc
    return len(block) // 2

def _check_variables(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie la cohérence des variables [variable] - DE L'ANCIEN SYSTÈME"""
    issues = []
    
    try:
        old_vars = re.findall(r'\[[^\]]*\]', old_line)
        new_vars = re.findall(r'\[[^\]]*\]', new_line)
        
        # Normaliser les variables (enlever les fonctions !t, !u, etc.)
        old_vars_norm = [_normalize_variable(var) for var in old_vars]
        new_vars_norm = [_normalize_variable(var) for var in new_vars]
        
        if sorted(old_vars_norm) != sorted(new_vars_norm):
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': 'variable_mismatch',
                'message': f"Variables incohérentes => Attendu: {old_vars}, Présent: {new_vars}",
                'old_content': old_line,
                'new_content': new_line
            })
    
    except Exception:
        pass
    
    return issues

def _normalize_variable(variable):
    """Normalise une variable en enlevant les fonctions de traduction - DE L'ANCIEN SYSTÈME"""
    # Enlever les fonctions !t, !u, !l, !c
    normalized = re.sub(r'![tulc]', '', variable)
    return normalized

def _check_tags(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie que les balises {xxx} sont équilibrées"""
    issues = []
    
    # Vérifier l'équilibre des accolades
    old_open = old_line.count('{')
    old_close = old_line.count('}')
    new_open = new_line.count('{')
    new_close = new_line.count('}')
    
    if new_open != new_close:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'tags_unbalanced',
            'severity': 'error',
            'message': f"Balises déséquilibrées: {new_open} {{ mais {new_close} }}",
            'old_line': old_line,
            'new_line': new_line
        })
    
    # Vérifier les balises spécifiques
    tag_patterns = [
        (r'\{i\}', r'\{/i\}', 'i'),
        (r'\{b\}', r'\{/b\}', 'b'),
        (r'\{u\}', r'\{/u\}', 'u'),
        (r'\{color=[^}]+\}', r'\{/color\}', 'color'),
        (r'\{size=[^}]+\}', r'\{/size\}', 'size')
    ]
    
    for open_pattern, close_pattern, tag_name in tag_patterns:
        open_count = len(re.findall(open_pattern, new_line))
        close_count = len(re.findall(close_pattern, new_line))
        
        if open_count != close_count:
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': f'tag_{tag_name}_unbalanced',
                'severity': 'error',
                'message': f"Balise {{{tag_name}}} déséquilibrée: {open_count} ouvertures, {close_count} fermetures",
                'old_line': old_line,
                'new_line': new_line
            })
    
    return issues

def _check_untranslated(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les lignes identiques (non traduites)"""
    issues = []
    
    # Nettoyer les lignes pour comparaison
    old_clean = old_line.strip().lower()
    new_clean = new_line.strip().lower()
    
    # Exclure les lignes trop courtes
    if len(old_clean) < 3:
        return issues
    
    # Exclure les patterns de ponctuation répétée (???, !!!, ..., etc.)
    if _is_punctuation_pattern(old_clean):
        return issues
    
    # Exclure selon la liste d'exclusions
    exclusions = coherence_options.get('custom_exclusions', [])
    for exclusion in exclusions:
        if exclusion.lower() in old_clean:
            return issues
    
    # Comparer
    if old_clean == new_clean:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'untranslated',
            'severity': 'warning',
            'message': "Ligne identique à l'originale (probablement non traduite)",
            'old_line': old_line,
            'new_line': new_line
        })
    
    return issues

def _is_punctuation_pattern(text: str) -> bool:
    """Vérifie si le texte est un pattern de ponctuation répétée"""
    # Patterns de ponctuation répétée : ???, !!!, ..., ----, etc.
    punctuation_patterns = [
        r'^[\?\!\.]{2,}$',      # ???, !!!, ...
        r'^[\-_]{2,}$',         # ----, ____
        r'^[\.]{3,}$',          # ..., ...., .....
        r'^[\?\!]{2,}$',        # ???, !!!, ?!?!, etc.
        r'^[~]{2,}$',           # ~~~
        r'^[…]+$',              # … (ellipsis unicode)
    ]
    
    stripped = text.strip()
    for pattern in punctuation_patterns:
        if re.match(pattern, stripped):
            return True
    
    return False

def _check_escape_sequences(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie la cohérence des séquences d'échappement \\n, \\t, \\r, \\\\"""
    issues = []
    
    escape_sequences = [r'\\n', r'\\t', r'\\r', r'\\\\']
    
    for seq in escape_sequences:
        old_count = old_line.count(seq)
        new_count = new_line.count(seq)
        
        if old_count != new_count:
            seq_name = seq.replace('\\\\', '\\')
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': f'escape_sequence_{seq_name}',
                'severity': 'warning',
                'message': f"Séquence {seq_name} incohérente: {old_count} → {new_count}",
                'old_line': old_line,
                'new_line': new_line
            })
    
    return issues

def _check_percentages(old_line: str, new_line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie la cohérence des variables de formatage %s, %d, etc."""
    issues = []
    
    # Pattern pour %s, %d, %f, etc.
    pattern = r'%[sdfioxXeEgGcr]'
    
    old_formats = re.findall(pattern, old_line)
    new_formats = re.findall(pattern, new_line)
    
    if len(old_formats) != len(new_formats):
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'format_variables',
            'severity': 'error',
            'message': f"Variables de formatage incohérentes: {len(old_formats)} → {len(new_formats)}",
            'old_line': old_line,
            'new_line': new_line
        })
    
    # Vérifier que les types correspondent
    if old_formats != new_formats:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'format_types_mismatch',
            'severity': 'warning',
            'message': f"Types de formatage différents: {old_formats} → {new_formats}",
            'old_line': old_line,
            'new_line': new_line
        })
    
    return issues

def _check_parentheses(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie l'équilibre des parenthèses, crochets et accolades"""
    issues = []
    
    # Paires à vérifier
    pairs = [
        ('(', ')', 'parenthèses'),
        ('[', ']', 'crochets'),
        ('{', '}', 'accolades')
    ]
    
    for open_char, close_char, name in pairs:
        open_count = line.count(open_char)
        close_count = line.count(close_char)
        
        if open_count != close_count:
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': f'{name}_unbalanced',
                'severity': 'error',
                'message': f"{name.capitalize()} déséquilibrées: {open_count} ouvertures, {close_count} fermetures",
                'old_line': line,
                'new_line': line
            })
    
    return issues

def _check_deepl_ellipsis(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les ellipses DeepL [...] qui devraient être ..."""
    issues = []
    
    if '[...]' in line or '[…]' in line:
        count = line.count('[...]') + line.count('[…]')
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'deepl_ellipsis',
            'severity': 'warning',
            'message': f"Ellipse DeepL détectée ({count}x) - devrait être '...'",
            'old_line': line,
            'new_line': line
        })
    
    return issues

def _check_isolated_percent(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les % isolés qui devraient être %% - VERSION AMÉLIORÉE"""
    issues = []
    
    # Pattern pour % isolé (pas suivi de %% ou de variables %s, %d, %f, etc.)
    # Aussi exclure %(name)s et autres formats nommés
    pattern = r'(?<!%)%(?!%|[sdfioxXeEgGcr]|\([^)]+\))'
    
    matches = re.findall(pattern, line)
    
    if matches:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'isolated_percent',
            'severity': 'error',
            'message': f"Pourcentage isolé détecté ({len(matches)}x) - devrait être '%%'",
            'old_line': line,
            'new_line': line
        })
    
    return issues

def _check_french_quotes(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les guillemets français « » qui devraient être \" """
    issues = []
    
    # Détecter « et »
    if '«' in line or '»' in line:
        count = line.count('«') + line.count('»')
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'french_quotes',
            'severity': 'warning',
            'message': f"Guillemets français détectés ({count}x) - devraient être \\\"",
            'old_line': line,
            'new_line': line
        })
    
    # Détecter << et >>
    if '<<' in line or '>>' in line:
        # Exclure les cas où c'est du code Ren'Py (<<< >>>)
        if not ('<<<' in line or '>>>' in line):
            count = line.count('<<') + line.count('>>')
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': 'french_double_chevrons',
                'severity': 'warning',
                'message': f"Chevrons doubles détectés ({count}x) - devraient être \\\"",
                'old_line': line,
                'new_line': line
            })
    
    return issues

def _check_double_dash_ellipsis(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les doubles tirets -- qui devraient être ..."""
    issues = []
    
    # Détecter -- (mais pas --- ou plus, qui peuvent être du code/formatage)
    if '--' in line and '---' not in line:
        count = line.count('--')
        # Soustraire les occurrences de --- si présentes
        count -= line.count('---')
        
        if count > 0:
            issues.append({
                'file': file_path,
                'line_number': line_number,
                'type': 'double_dash_ellipsis',
                'severity': 'info',  # Léger, pas une erreur
                'message': f"Ellipse (-- → ...) détectée ({count}x) - recommandation : utiliser '...' pour cohérence",
                'old_line': line,
                'new_line': line
            })
    
    return issues

def _check_special_codes(line: str, file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Détecte les codes spéciaux, balises ou patterns inhabituels"""
    issues = []
    
    # Patterns suspects à détecter
    suspicious_patterns = []
    
    # 1. Balises HTML non standard (pas déjà protégées par Ren'Py)
    if re.search(r'<(?!/?[bius]|/?color|/?size|/?font)[^>]+>', line):
        suspicious_patterns.append('Balise HTML/XML inhabituelle')
    
    # 2. Caractères de contrôle Unicode suspects
    if re.search(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]', line):
        suspicious_patterns.append('Caractère de contrôle Unicode suspect')
    
    # 3. Séquences d'échappement non standard
    if re.search(r'\\[^ntr"\\]', line):
        suspicious_patterns.append('Séquence d\'échappement inhabituelle')
    
    # 4. Multiples espaces consécutifs (peut indiquer un problème)
    if '  ' in line and '   ' not in line:  # Doubles espaces mais pas triples+
        suspicious_patterns.append('Espaces doubles (peut-être intentionnel)')
    
    # 5. Caractères spéciaux rares
    rare_chars = ['§', '¶', '†', '‡', '•', '◦', '▪', '▫']
    found_rare = [c for c in rare_chars if c in line]
    if found_rare:
        suspicious_patterns.append(f'Caractères spéciaux rares: {", ".join(found_rare)}')
    
    # Si des patterns suspects sont détectés
    if suspicious_patterns:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'special_code_detected',
            'severity': 'info',  # Léger, juste informatif
            'message': f"Pattern(s) inhabituel(s) détecté(s): {' | '.join(suspicious_patterns)} - vérification manuelle recommandée",
            'old_line': line,
            'new_line': line
        })
    
    return issues

def _check_line_structure(block: List[str], file_path: str, line_number: int) -> List[Dict[str, Any]]:
    """Vérifie que chaque bloc a bien une ligne old et une ligne new"""
    issues = []
    
    # Un bloc doit avoir exactement 2 lignes de dialogue (old et new)
    dialogue_lines = [l for l in block if l.strip() and not l.strip().startswith('#')]
    
    if len(dialogue_lines) != 2:
        issues.append({
            'file': file_path,
            'line_number': line_number,
            'type': 'line_structure',
            'severity': 'error',
            'message': f"Structure incorrecte: {len(dialogue_lines)} ligne(s) au lieu de 2 (old + new)",
            'old_line': '',
            'new_line': ''
        })
    
    return issues

def _calculate_statistics(all_issues: List[Dict[str, Any]], files_analyzed: int) -> Dict[str, Any]:
    """Calcule les statistiques des problèmes détectés"""
    stats = {
        'files_analyzed': files_analyzed,
        'total_issues': len(all_issues),
        'issues_by_type': defaultdict(int),
        'issues_by_severity': defaultdict(int)
    }
    
    for issue in all_issues:
        issue_type = issue['type']
        severity = issue.get('severity', 'unknown')  # severity optionnel
        
        stats['issues_by_type'][issue_type] += 1
        stats['issues_by_severity'][severity] += 1
    
    # Convertir les defaultdict en dicts normaux
    stats['issues_by_type'] = dict(stats['issues_by_type'])
    stats['issues_by_severity'] = dict(stats['issues_by_severity'])
    
    return stats

def _generate_coherence_report(all_issues: List[Dict[str, Any]], target_path: str, selection_info: Optional[Dict], stats: Dict[str, Any]) -> str:
    """Génère un rapport HTML détaillé"""
    try:
        # Créer le dossier de rapports avec la structure correcte
        if selection_info and 'project_path' in selection_info:
            project_path = selection_info['project_path']
            project_name = os.path.basename(project_path)
            rapport_folder = os.path.join("02_Reports", project_name, "coherence")
        else:
            rapport_folder = "02_Reports"
        
        os.makedirs(rapport_folder, exist_ok=True)
        
        # Générer le nom du fichier avec le format de l'ancien système
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if selection_info:
            project_name = os.path.basename(selection_info.get('project_path', '')) or 'unknown'
            rapport_name = f"{project_name}_coherence_interactif_{timestamp}.html"
        else:
            rapport_name = f"coherence_interactif_{timestamp}.html"
        
        rapport_path = os.path.join(rapport_folder, rapport_name)
        
        # Grouper les problèmes par fichier
        issues_by_file = defaultdict(list)
        for issue in all_issues:
            file_path = issue['file']
            issues_by_file[file_path].append(issue)
        
        # Générer le HTML avec le design moderne
        from .coherence_html import generate_modern_html_report
        html_content = generate_modern_html_report(issues_by_file, target_path, selection_info, stats)
        
        # Sauvegarder
        with open(rapport_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"📊 Rapport de cohérence généré: {rapport_path}")
        return rapport_path
        
    except Exception as e:
        logger.error(f"Erreur génération rapport: {e}")
        raise

def _generate_html_report_old(issues_by_file: Dict[str, List[Dict]], target_path: str, selection_info: Optional[Dict], stats: Dict[str, Any]) -> str:
    """Génère le contenu HTML du rapport avec le design moderne de l'ancien système"""
    
    # Déterminer le nom du projet et de la langue
    if selection_info and 'project_path' in selection_info:
        project_name = os.path.basename(selection_info['project_path'])
        language = selection_info.get('language', 'unknown')
    else:
        project_name = os.path.basename(target_path)
        language = 'unknown'
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # Calculer les statistiques détaillées
    total_issues = stats.get('total_issues', 0)
    files_analyzed = stats.get('files_analyzed', 0)
    issues_by_type = stats.get('issues_by_type', {})
    
    html = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rapport de Cohérence - {project_name}</title>
    
<style>
  :root {{
    --bg: #121212; --fg: #eaeaea; --hdr: #1e1e1e; --sep: #262626;
    --success: #198754; --warning: #FFC107; --danger: #DC3545; --info: #0D6EFD;
    --card-bg: #1f1f1f; --hover-bg: rgba(255,255,255,0.06);
    --error-variable: #ff6b9d; --error-tag: #ffa726; --error-placeholder: #ab47bc;
    --error-special: #ef5350; --error-untranslated: #ffcc02; --error-other: #78909c;
  }}
  .light {{
    --bg: #fafafa; --fg: #222; --hdr: #fff; --sep: #ddd;
    --card-bg: #f8f9fa; --hover-bg: rgba(0,0,0,0.04);
  }}
  
  body {{ 
    font-family: ui-sans-serif, system-ui, -apple-system, 'Segoe UI', Roboto, Arial; 
    background: var(--bg); color: var(--fg); margin: 0; line-height: 1.6;
  }}
  
  .header {{
    background: var(--hdr); padding: 20px; border-bottom: 2px solid var(--sep);
    position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }}
  
  .header h1 {{ margin: 0 0 10px 0; font-size: 1.8rem; }}
  .header-meta {{ display: flex; gap: 20px; flex-wrap: wrap; align-items: center; }}
  .header-meta span {{ opacity: 0.9; font-size: 0.95rem; }}
  
  .controls {{ 
    display: flex; gap: 12px; align-items: center; margin-left: auto;
  }}
  
  .btn {{
    cursor: pointer; padding: 8px 12px; border-radius: 8px; 
    border: 1px solid var(--sep); background: transparent; color: var(--fg);
    transition: all 0.2s; font-size: 0.9rem;
  }}
  .btn:hover {{ background: var(--hover-bg); transform: translateY(-1px); }}
  
  .summary-cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 20px; padding: 20px; margin-bottom: 0px;
    background: var(--bg); 
    position: sticky; top: 82px; z-index: 95;
        }}
        .issue-type {{
            background: #6c757d;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-right: 10px;
        }}
        .issue-severity {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }}
        .severity-error {{ background: #dc3545; color: white; }}
        .severity-warning {{ background: #ffc107; color: #212529; }}
        .issue-message {{
            font-weight: bold;
            color: #495057;
        }}
        .code-block {{
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 4px;
            padding: 10px;
            margin: 10px 0;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            overflow-x: auto;
        }}
        .old-line {{ color: #dc3545; }}
        .new-line {{ color: #28a745; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #6c757d;
            border-top: 1px solid #e0e0e0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 Rapport de Cohérence</h1>
            <p>{target_name} • {timestamp}</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number {'success' if stats['total_issues'] == 0 else 'error'}">{stats['total_issues']}</div>
                <div class="stat-label">Problèmes Totaux</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats['files_analyzed']}</div>
                <div class="stat-label">Fichiers Analysés</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error">{stats['issues_by_severity'].get('error', 0)}</div>
                <div class="stat-label">Erreurs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number warning">{stats['issues_by_severity'].get('warning', 0)}</div>
                <div class="stat-label">Avertissements</div>
            </div>
        </div>
        
        <div class="content">
"""
    
    if stats['total_issues'] == 0:
        html += """
            <div style="text-align: center; padding: 40px; color: #27ae60;">
                <h2>✅ Aucun problème détecté !</h2>
                <p>Votre traduction est cohérente et de qualité.</p>
            </div>
        """
    else:
        # Afficher les problèmes par fichier
        for file_path, file_issues in issues_by_file.items():
            file_name = os.path.basename(file_path)
            html += f"""
            <div class="file-section">
                <div class="file-header">
                    📄 {file_name} ({len(file_issues)} problème(s))
                </div>
            """
            
            for issue in file_issues:
                severity_class = f"severity-{issue['severity']}"
                html += f"""
                <div class="issue">
                    <div class="issue-header">
                        <span class="issue-type">{issue['type']}</span>
                        <span class="issue-severity {severity_class}">{issue['severity']}</span>
                        <span class="issue-message">{issue['message']}</span>
                    </div>
                """
                
                if issue['old_line'] and issue['new_line']:
                    html += f"""
                    <div class="code-block">
                        <div class="old-line">Original: {issue['old_line']}</div>
                        <div class="new-line">Traduit:  {issue['new_line']}</div>
                    </div>
                    """
                
                html += "</div>"
            
            html += "</div>"
    
    html += """
        </div>
        
        <div class="footer">
            <p>Généré par RenExtract • Système de vérification de cohérence</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html

# ============================================================================
# FONCTIONS MANQUANTES DE L'ANCIEN SYSTÈME
# ============================================================================

def _is_untranslated_line(old_text, new_text):
    """Vérifie si une ligne est probablement non traduite - DE L'ANCIEN SYSTÈME"""
    if old_text.strip() != new_text.strip():
        return False
    
    text = old_text.strip()
    
    # Auto-exclusions (patterns techniques)
    if _is_auto_excluded(text):
        return False
    
    # Exclusions personnalisées
    custom_exclusions = coherence_options.get('custom_exclusions', [])
    if text in custom_exclusions:
        return False
    
    # Si le texte est court et contient peu de mots, probablement OK
    if len(text) <= 3 or len(text.split()) <= 1:
        return False
    
    # Sinon, considérer comme non traduit
    return True

def _is_auto_excluded(text):
    """Vérifie les auto-exclusions par défaut - DE L'ANCIEN SYSTÈME"""
    # Ellipsis (si activé)
    if coherence_options.get('check_ellipsis', True) and text in ['...', '…', '....', '.....']:
        return True
    
    # Variables seules
    if re.match(r'^\[[^\]]+\]', text):
        return True
    
    # Balises seules
    if re.match(r'^\{[^}]*\}', text):
        return True
    
    # Texte vide ou espaces
    if not text or text.isspace():
        return True
    
    # Ponctuations expressives (sauf ellipsis si désactivé)
    if coherence_options.get('check_ellipsis', True):
        # Si ellipsis activé, inclure les points dans les ponctuations expressives
        if re.match(r'^[!?…\.]+', text):
            return True
    else:
        # Si ellipsis désactivé, exclure les points des ponctuations expressives
        if re.match(r'^[!?…]+', text):
            return True
    
    # Onomatopées courtes (2-3 caractères)
    if len(text) <= 3 and re.match(r'^[A-Za-z]+[!?]*', text):
        return True
    
    return False

def _is_old_line(line):
    """Vérifie si une ligne est une ligne OLD - FORMAT CORRIGÉ"""
    # Format correct: # "texte original"
    return line.startswith('# "') and line.endswith('"')

def _is_new_line(line):
    """Vérifie si une ligne est une ligne NEW - FORMAT CORRIGÉ"""
    # Format correct: "texte traduit" ou personnage "texte traduit" (sans #)
    if line.startswith('# '):
        return False
    
    # Ligne avec personnage: personnage "texte"
    if '"' in line and not line.startswith('#'):
        return True
    
    return False

def _is_voice_line(line):
    """Vérifie si une ligne contient une instruction voice"""
    # Ignorer les lignes voice
    return 'voice ' in line and '"' in line

def _check_variables_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des variables [] - DE L'ANCIEN SYSTÈME"""
    issues = []
    
    try:
        old_vars = re.findall(r'\[[^\]]*\]', old_text)
        new_vars = re.findall(r'\[[^\]]*\]', new_text)
        
        # Normaliser les variables (enlever les fonctions !t, !u, etc.)
        old_vars_norm = [_normalize_variable(var) for var in old_vars]
        new_vars_norm = [_normalize_variable(var) for var in new_vars]
        
        if sorted(old_vars_norm) != sorted(new_vars_norm):
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'variable_mismatch',
                'message': f"Variables incohérentes => Attendu: {old_vars}, Présent: {new_vars}",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_tags_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des balises {} - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Analyser les balises dans chaque texte
        old_analysis = _analyze_brace_tags(old_text)
        new_analysis = _analyze_brace_tags(new_text)
        
        # Vérifier chaque type de balise
        all_tag_types = set(old_analysis.keys()) | set(new_analysis.keys())
        
        for tag_type in all_tag_types:
            old_count = old_analysis.get(tag_type, {'open': 0, 'close': 0})
            new_count = new_analysis.get(tag_type, {'open': 0, 'close': 0})
            
            # Vérifier l'équilibre des ouvertures/fermetures
            old_balanced = (old_count['open'] == old_count['close'])
            new_balanced = (new_count['open'] == new_count['close'])
            
            # Si l'ancien était équilibré mais le nouveau ne l'est pas
            if old_balanced and not new_balanced:
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'tag_mismatch',
                    'message': f"Balise {{{tag_type}}} déséquilibrée: {new_count['open']} ouverture(s), {new_count['close']} fermeture(s)",
                    'old_content': old_text,
                    'new_content': new_text
                })
            
            # Si le nombre total de balises a changé
            old_total = old_count['open'] + old_count['close']
            new_total = new_count['open'] + new_count['close']
            
            if old_total != new_total:
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'tag_count_mismatch',
                    'message': f"Nombre de balises {{{tag_type}}} différent: {old_total} → {new_total}",
                    'old_content': old_text,
                    'new_content': new_text
                })
    
    except Exception as e:
        issues.append({
            'file': '',  # Sera rempli par l'appelant
            'line_number': line_number,
            'type': 'tag_analysis_error',
            'message': f"Erreur analyse balises: {str(e)}",
            'old_content': old_text,
            'new_content': new_text
        })
    
    return issues

def _analyze_brace_tags(text):
    """Analyse les balises {} dans un texte et retourne les compteurs par type"""
    analysis = {}
    
    # Trouver toutes les balises
    tags = re.findall(r'\{[^}]*\}', text)
    
    for tag in tags:
        tag_content = tag[1:-1]  # Enlever { et }
        
        # Déterminer le type de balise
        if tag_content.startswith('/'):
            # Balise fermante {/i}, {/color}, etc.
            tag_type = tag_content[1:]  # Enlever le /
            tag_type = _normalize_tag_type(tag_type)
            
            if tag_type not in analysis:
                analysis[tag_type] = {'open': 0, 'close': 0}
            analysis[tag_type]['close'] += 1
        else:
            # Balise ouvrante {i}, {color=#ff0000}, etc.
            tag_type = _normalize_tag_type(tag_content)
            
            if tag_type not in analysis:
                analysis[tag_type] = {'open': 0, 'close': 0}
            analysis[tag_type]['open'] += 1
    
    return analysis

def _normalize_tag_type(tag_content):
    """Normalise le type de balise pour la comparaison"""
    # Enlever les paramètres pour les balises comme {color=#ff0000}
    if '=' in tag_content:
        tag_type = tag_content.split('=')[0]
    else:
        tag_type = tag_content
    
    return tag_type

def _check_escape_sequences_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des séquences d'échappement - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Compter les séquences d'échappement (sans \\ seul, mais avec \")
        escape_patterns = [r'\\n', r'\\t', r'\\r', r'\\"']
        
        for pattern in escape_patterns:
            old_count = len(re.findall(pattern, old_text))
            new_count = len(re.findall(pattern, new_text))
            
            if old_count != new_count:
                escape_name = {
                    r'\\n': '\\n (retours à la ligne)',
                    r'\\t': '\\t (tabulations)',
                    r'\\r': '\\r (retours chariot)',
                    r'\\"': '\\" (guillemets échappés)'
                }.get(pattern, pattern)
                
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'escape_sequence_mismatch',
                    'message': f"Séquence {escape_name} incohérente: {old_count} → {new_count}",
                    'old_content': old_text,
                    'new_content': new_text
                })
    
    except Exception:
        pass
    
    return issues

def _check_percentages_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des variables de formatage % - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Extraire toutes les variables de formatage
        old_format_vars = re.findall(r'%(?:\([^)]+\))?[sdfioxXeEgGcr]', old_text)
        new_format_vars = re.findall(r'%(?:\([^)]+\))?[sdfioxXeEgGcr]', new_text)
        
        # Vérifier le nombre de variables
        if len(old_format_vars) != len(new_format_vars):
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'percentage_format_mismatch',
                'message': f"Variables de formatage incohérentes: {len(old_format_vars)} → {len(new_format_vars)}",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Vérifier que les types correspondent (ordre et type)
        if old_format_vars != new_format_vars:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'percentage_type_mismatch',
                'message': f"Types de formatage différents: {old_format_vars} → {new_format_vars}",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Vérifier le double % échappé (pour les % littéraux)
        old_double_percent = old_text.count('%%')
        new_double_percent = new_text.count('%%')
        
        if old_double_percent != new_double_percent:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'double_percent_mismatch',
                'message': f"Double %% échappé incohérent: {old_double_percent} → {new_double_percent}",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_quotations_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des guillemets et échappements - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Guillemets échappés \"
        old_escaped_quotes = old_text.count('\\"')
        new_escaped_quotes = new_text.count('\\"')
        
        # Guillemets non échappés (dans le contenu, exclure les guillemets de début/fin)
        # On compte les " qui ne sont pas précédés d'un backslash
        old_content_quotes = len(re.findall(r'(?<!\\)"', old_text))
        new_content_quotes = len(re.findall(r'(?<!\\)"', new_text))
        
        # Vérifier les guillemets échappés
        if old_escaped_quotes != new_escaped_quotes:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'escaped_quotes_mismatch',
                'message': f"Guillemets échappés \\\" incohérents: {old_escaped_quotes} → {new_escaped_quotes}",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Vérifier les guillemets non échappés (danger potentiel)
        if old_content_quotes != new_content_quotes:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'unescaped_quotes_mismatch',
                'message': f"Guillemets non échappés \" incohérents: {old_content_quotes} → {new_content_quotes}",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Détecter les doubles guillemets dangereux "" (bug DeepL)
        if '""' in new_text and '""' not in old_text:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'double_quotes_detected',
                'message': f"Doubles guillemets \"\" détectés (probablement une erreur DeepL)",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_parentheses_coherence(old_text, new_text, line_number):
    """Vérifie la cohérence des parenthèses et crochets - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Vérifier l'équilibre des parenthèses dans NEW
        new_open_parens = new_text.count('(')
        new_close_parens = new_text.count(')')
        
        if new_open_parens != new_close_parens:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'parentheses_unbalanced',
                'message': f"Parenthèses déséquilibrées: {new_open_parens} ouverture(s), {new_close_parens} fermeture(s)",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Vérifier l'équilibre des crochets dans NEW
        new_open_brackets = new_text.count('[')
        new_close_brackets = new_text.count(']')
        
        if new_open_brackets != new_close_brackets:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'brackets_unbalanced',
                'message': f"Crochets déséquilibrés: {new_open_brackets} ouverture(s), {new_close_brackets} fermeture(s)",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Vérifier aussi l'équilibre des accolades dans NEW (bonus)
        new_open_braces = new_text.count('{')
        new_close_braces = new_text.count('}')
        
        if new_open_braces != new_close_braces:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'braces_unbalanced',
                'message': f"Accolades déséquilibrées: {new_open_braces} ouverture(s), {new_close_braces} fermeture(s)",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_syntax_coherence(old_text, new_text, line_number):
    """Vérifie la syntaxe Ren'Py et structure des lignes - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # 1. Vérifier l'équilibre des guillemets (syntaxe de base)
        old_quotes = old_text.count('"')
        new_quotes = new_text.count('"')
        
        # Les guillemets doivent être équilibrés (nombre pair)
        if new_quotes % 2 != 0:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'unbalanced_quotes',
                'message': f"Guillemets non équilibrés dans NEW ({new_quotes} guillemets)",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # 2. Vérifier les séquences d'échappement malformées
        # Pattern: backslash suivi d'un caractère qui n'est pas n, t, r, ", ou \
        malformed_escapes = re.findall(r'\\(?![ntr"\\])', new_text)
        if malformed_escapes:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'malformed_escape_sequence',
                'message': f"Séquence d'échappement malformée détectée: {set(malformed_escapes)}",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # 3. Détecter les blocs old/new mal formés (si présents)
        # Vérifier si c'est une ligne "old" ou "new" (blocs strings)
        if new_text.strip().startswith('old ') or new_text.strip().startswith('new '):
            # Vérifier la structure correcte: old "..." ou new "..."
            if not re.match(r'^\s*(old|new)\s+"[^"]*"\s*$', new_text):
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'strings_syntax_error',
                    'message': f"Structure old/new incorrecte (devrait être: old \"...\" ou new \"...\")",
                    'old_content': old_text,
                    'new_content': new_text
                })
        
        # 4. Vérifier que les lignes de dialogue ont une structure correcte
        # Pattern: Personnage "dialogue" ou "dialogue" seul
        if '"' in new_text and not new_text.strip().startswith('#'):
            # Extraire la partie entre guillemets
            dialogue_match = re.search(r'"([^"]*)"', new_text)
            if dialogue_match:
                dialogue_content = dialogue_match.group(1)
                
                # Vérifier que le dialogue n'est pas vide (sauf si c'est volontaire: "")
                if len(dialogue_content) == 0 and '""' not in old_text:
                    issues.append({
                        'file': '',  # Sera rempli par l'appelant
                        'line_number': line_number,
                        'type': 'empty_dialogue',
                        'message': f"Dialogue vide détecté (\"\")",
                        'old_content': old_text,
                        'new_content': new_text
                    })
    
    except Exception:
        pass
    
    return issues

def _check_deepl_ellipsis_coherence(old_text, new_text, line_number):
    """Vérifie les ellipses DeepL [...] et […] → ... - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Détecter les ellipses DeepL dans NEW : [...] ou […]
        # Pattern: [...] (3 points) ou [..] (2 points) ou [….] (unicode) ou […] (unicode seul)
        deepl_patterns = [
            r'\[\.{2,}\]',   # [...], [..], [....]
            r'\[…+\]',       # […], [……]
        ]
        
        new_deepl_count = 0
        for pattern in deepl_patterns:
            new_deepl_count += len(re.findall(pattern, new_text))
        
        # Si NEW contient des ellipses DeepL, c'est une erreur (DeepL les a ajoutées)
        if new_deepl_count > 0:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'deepl_ellipsis_detected',
                'message': f"Ellipse DeepL détectée ({new_deepl_count}x) - devrait être '...'",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_isolated_percent_coherence(old_text, new_text, line_number):
    """Vérifie les pourcentages isolés % → %% - VERSION AMÉLIORÉE
    
    Logique: Dans Ren'Py, TOUS les % doivent être échappés en %%
    - OLD ET NEW doivent avoir %% au lieu de % isolés
    - Un % isolé dans OLD ou NEW est une erreur
    """
    issues = []
    
    try:
        # Pattern pour % isolé (pas suivi de %% ou de variables %s, %d, %f, etc.)
        # Aussi exclure %(name)s et autres formats nommés
        pattern = r'(?<!%)%(?!%|[sdfioxXeEgGcr]|\([^)]+\))'
        
        old_isolated = len(re.findall(pattern, old_text))
        new_isolated = len(re.findall(pattern, new_text))
        
        # Si OLD contient des % isolés (erreur dans le fichier source)
        if old_isolated > 0:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'isolated_percent_in_source',
                'message': f"Pourcentage isolé dans OLD ({old_isolated}x) - devrait être doublé en %%",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Si NEW contient des % isolés (erreur dans la traduction)
        if new_isolated > 0:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'isolated_percent_in_translation',
                'message': f"Pourcentage isolé dans NEW ({new_isolated}x) - devrait être doublé en %%",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_french_quotes_coherence(old_text, new_text, line_number):
    """Vérifie les guillemets français «» et << >> → \" - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # Détecter les guillemets français DANS NEW (ajoutés par traduction)
        new_french_open = new_text.count('«')
        new_french_close = new_text.count('»')
        
        # Détecter les chevrons doubles DANS NEW (pas dans le code Ren'Py)
        # Pattern: << ou >> mais PAS <<< ou >>>
        new_chevron_open = len(re.findall(r'(?<![<>])<<(?![<>])', new_text))
        new_chevron_close = len(re.findall(r'(?<![<>])>>(?![<>])', new_text))
        
        # Si NEW contient des guillemets français
        if new_french_open > 0 or new_french_close > 0:
            total_french = new_french_open + new_french_close
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'french_quotes_detected',
                'message': f"Guillemets français détectés ({total_french}x) - devraient être \\\"",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Si NEW contient des chevrons doubles (pas du code)
        if new_chevron_open > 0 or new_chevron_close > 0:
            total_chevrons = new_chevron_open + new_chevron_close
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'french_chevrons_detected',
                'message': f"Chevrons doubles détectés ({total_chevrons}x) - devraient être \\\"",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_double_dash_ellipsis_coherence(old_text, new_text, line_number):
    """Vérifie les doubles tirets -- → ... - NOUVEAU CONTRÔLE"""
    issues = []
    
    try:
        # Détecter -- dans NEW (mais pas --- ou plus)
        new_double_dash = 0
        if '--' in new_text and '---' not in new_text:
            new_double_dash = new_text.count('--') - new_text.count('---')
        
        # Si NEW contient des --, c'est une suggestion de style (pas une erreur)
        if new_double_dash > 0:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'double_dash_ellipsis',
                'message': f"Ellipse (-- → ...) détectée ({new_double_dash}x) - recommandation : utiliser '...' pour cohérence",
                'old_content': old_text,
                'new_content': new_text
            })
    
    except Exception:
        pass
    
    return issues

def _check_line_structure_coherence(old_text, new_text, line_number):
    """Vérifie la structure des lignes old/new - VERSION AMÉLIORÉE"""
    issues = []
    
    try:
        # 1. Vérifier la structure old/new dans les blocs strings
        old_is_old_line = old_text.strip().startswith('old ')
        new_is_new_line = new_text.strip().startswith('new ')
        
        # Si OLD est une ligne "old", NEW DOIT être une ligne "new"
        if old_is_old_line and not new_is_new_line:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'missing_new_line',
                'message': f"Ligne OLD sans NEW correspondant (structure old/new incorrecte)",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # Si NEW est une ligne "new" mais OLD n'est pas "old"
        if new_is_new_line and not old_is_old_line:
            issues.append({
                'file': '',  # Sera rempli par l'appelant
                'line_number': line_number,
                'type': 'orphan_new_line',
                'message': f"Ligne NEW sans OLD correspondant",
                'old_content': old_text,
                'new_content': new_text
            })
        
        # 2. Vérifier la cohérence de longueur (approximative)
        old_length = len(old_text.strip())
        new_length = len(new_text.strip())
        
        # Si la différence est très importante (plus de 200% de différence)
        if old_length > 0 and new_length > 0:
            length_ratio = max(old_length, new_length) / min(old_length, new_length)
            if length_ratio > 3.0:  # Plus de 200% de différence (plus tolérant pour EN→FR)
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'length_discrepancy',
                    'message': f"Différence de longueur importante: OLD {old_length} chars, NEW {new_length} chars (ratio: {length_ratio:.1f}x)",
                    'old_content': old_text,
                    'new_content': new_text
                })
        
        # 3. Vérifier les caractères spéciaux non échappés
        special_chars = ['{', '}', '[', ']']
        for char in special_chars:
            old_count = old_text.count(char)
            new_count = new_text.count(char)
            if old_count != new_count:
                issues.append({
                    'file': '',  # Sera rempli par l'appelant
                    'line_number': line_number,
                    'type': 'special_char_mismatch',
                    'message': f"Caractère spécial '{char}' incohérent => Attendu: {old_count}, Présent: {new_count}",
                    'old_content': old_text,
                    'new_content': new_text
                })
    
    except Exception:
        pass
    
    return issues
