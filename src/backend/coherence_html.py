#!/usr/bin/env python3
"""
Générateur de rapport HTML pour la cohérence - Design moderne
"""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional

def generate_modern_html_report(issues_by_file: Dict[str, List[Dict]], target_path: str, selection_info: Optional[Dict], stats: Dict[str, Any]) -> str:
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
    
    # Grouper les problèmes par type
    issues_by_type_actual = {}
    for file_path, file_issues in issues_by_file.items():
        for issue in file_issues:
            issue_type = issue.get('type', 'unknown')
            if issue_type not in issues_by_type_actual:
                issues_by_type_actual[issue_type] = []
            issues_by_type_actual[issue_type].append(issue)
    
    # Générer les cartes de statistiques
    stats_cards = ""
    if total_issues == 0:
        stats_cards = f"""
        <div class="card">
            <h3>🎉 Aucun problème détecté</h3>
            <p style="color: var(--success); font-size: 1.1rem; margin: 0;">
                Votre traduction est parfaite !
            </p>
        </div>
        """
    else:
        stats_cards = f"""
        <div class="card">
            <h3>📊 Statistiques générales</h3>
            <div class="stat"><span>Problèmes totaux:</span> <span class="stat-value">{total_issues}</span></div>
            <div class="stat"><span>Fichiers analysés:</span> <span class="stat-value">{files_analyzed}</span></div>
            <div class="stat"><span>Types d'erreurs:</span> <span class="stat-value">{len(issues_by_type_actual)}</span></div>
        </div>
        """
        
        # Ajouter une carte pour chaque type d'erreur
        for issue_type, type_issues in issues_by_type_actual.items():
            count = len(type_issues)
            badge_class = _get_badge_class(issue_type)
            description = _get_issue_description(issue_type)
            
            stats_cards += f"""
            <div class="card">
                <h3><span class="error-type-badge {badge_class}">{count}</span> {description}</h3>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {(count/total_issues)*100:.1f}%"></div>
                </div>
                <p style="font-size: 0.9rem; opacity: 0.8; margin: 8px 0 0 0;">
                    {count} occurrence(s) • {(count/total_issues)*100:.1f}% du total
                </p>
            </div>
            """
    
    # Générer les sections d'erreurs par type
    error_sections = ""
    for issue_type, type_issues in issues_by_type_actual.items():
        description = _get_issue_description(issue_type)
        badge_class = _get_badge_class(issue_type)
        
        # Grouper par fichier pour ce type
        issues_by_file_type = {}
        for issue in type_issues:
            file_path = issue['file']
            if file_path not in issues_by_file_type:
                issues_by_file_type[file_path] = []
            issues_by_file_type[file_path].append(issue)
        
        file_sections = ""
        for file_path, file_issues in issues_by_file_type.items():
            file_name = os.path.basename(file_path)
            
            issue_items = ""
            for issue in file_issues:
                issue_items += f"""
                <div class="issue-item">
                    <div class="issue-header">
                        <h4 class="issue-line">Ligne {issue.get('line_number', '?')}</h4>
                        <span class="open-in-editor" onclick="openInEditor('{file_path}', {issue.get('line_number', 0)})">
                            <svg viewBox="0 0 24 24" fill="currentColor">
                                <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z"/>
                            </svg>
                            Ouvrir dans l'éditeur
                        </span>
                    </div>
                    <div class="issue-description">{issue.get('message', 'Aucune description')}</div>
                    {_generate_content_comparison(issue)}
                </div>
                """
            
            file_sections += f"""
            <div class="file-section">
                <div class="file-header">
                    📄 {file_name} ({len(file_issues)} problème{'' if len(file_issues) == 1 else 's'})
                </div>
                {issue_items}
            </div>
            """
        
        error_sections += f"""
        <div class="error-type-section">
            <div class="error-type-header collapsible-toggle" onclick="toggleSection(this)">
                <div>
                    <span class="error-type-badge {badge_class}">{len(type_issues)}</span>
                    {description}
                </div>
                <div class="stats-overview">
                    <span class="mini-stat">{len(issues_by_file_type)} fichier{'' if len(issues_by_file_type) == 1 else 's'}</span>
                </div>
            </div>
            <div class="error-type-content">
                {file_sections}
            </div>
        </div>
        """
    
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
    border-bottom: 1px solid var(--sep);
  }}
  
  .card {{
    background: var(--card-bg); border: 1px solid var(--sep); 
    border-radius: 12px; padding: 20px; transition: transform 0.2s;
  }}
  .card:hover {{ transform: translateY(-2px); }}
  
  .card h3 {{ margin-top: 0; font-size: 1.1rem; }}
  
  .stat {{ display: flex; justify-content: space-between; margin: 8px 0; }}
  .stat-value {{ font-weight: bold; color: var(--info); }}
  
  .progress-bar {{
    background: var(--sep); height: 8px; border-radius: 4px; overflow: hidden;
    margin: 10px 0;
  }}
  .progress-fill {{ 
    height: 100%; background: var(--danger); 
    transition: width 0.3s ease;
  }}
  
  .error-type-section {{
    margin: 20px; background: var(--card-bg); border-radius: 12px;
    border: 1px solid var(--sep); overflow: hidden; transition: all 0.2s;
  }}
  .error-type-section:hover {{ transform: translateY(-1px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }}
  
  .error-type-header {{
    background: var(--hdr); padding: 15px 20px; font-weight: bold;
    cursor: pointer; user-select: none;
    display: flex; justify-content: space-between; align-items: center;
    border-bottom: 1px solid var(--sep);
  }}
  
  .error-type-content {{ padding: 20px; display: none; }}
  .error-type-content.expanded {{ display: block; }}
  
  .error-type-badge {{
    padding: 4px 12px; border-radius: 16px; font-size: 0.8rem; 
    font-weight: bold; color: white;
  }}
  
  .badge-variable {{ background: var(--error-variable); }}
  .badge-tag {{ background: var(--error-tag); }}
  .badge-placeholder {{ background: var(--error-placeholder); }}
  .badge-special {{ background: var(--error-special); }}
  .badge-untranslated {{ background: var(--error-untranslated); color: #000; }}
  .badge-other {{ background: var(--error-other); }}
  
  .file-section {{
    background: var(--bg); border: 1px solid var(--sep); 
    border-radius: 8px; margin: 15px 0; overflow: hidden;
  }}
  
  .file-header {{
    background: rgba(255,255,255,0.02); padding: 12px 15px;
    font-weight: 600; color: var(--info); border-bottom: 1px solid var(--sep);
  }}
  
  .issue-item {{
    padding: 15px; border-bottom: 1px solid var(--sep);
    transition: background 0.2s;
  }}
  .issue-item:hover {{ background: var(--hover-bg); }}
  .issue-item:last-child {{ border-bottom: none; }}
  
  .issue-header{{display:flex;align-items:center;gap:10px;justify-content:space-between;flex-wrap:wrap}}
  .issue-line{{font-weight:bold;color:var(--warning);margin:0}}
  
  .open-in-editor {{
      display: inline-flex; align-items: center; gap: 6px;
      font-size: 12px; padding: 6px 10px; border-radius: 6px;
      border: 1px solid var(--sep); background: rgba(13,110,253,0.12);
      cursor: pointer; user-select: none;
      color: var(--fg);
  }}
  .open-in-editor:hover {{ 
      background: rgba(13,110,253,0.18); 
      color: var(--fg);
  }}
  .open-in-editor svg {{ 
      width: 14px; height: 14px; opacity: 0.9; 
      color: inherit;
  }}
  .issue-line {{ font-weight: bold; color: var(--warning); margin-bottom: 8px; }}
  .issue-description {{ margin-bottom: 12px; color: var(--fg); }}
  
  .content-comparison {{
    display: grid; grid-template-columns: 1fr 1fr; gap: 15px;
    margin-top: 10px;
  }}
  
  .content-block {{
    background: rgba(0,0,0,0.2); border-radius: 6px; padding: 12px;
    font-family: 'Consolas', 'Monaco', monospace; font-size: 0.9rem;
  }}
  
  .old-content {{ 
    border-left: 4px solid #ff6b6b;
    background: rgba(255, 107, 107, 0.1);
  }}
  .new-content {{ 
    border-left: 4px solid #51cf66;
    background: rgba(81, 207, 102, 0.1);
  }}
  
  .content-label {{
    font-size: 0.8rem; font-weight: bold; opacity: 0.8;
    margin-bottom: 6px; text-transform: uppercase;
  }}
  
  .filters {{
    padding: 15px 20px; background: var(--hdr); 
    border: 1px solid var(--sep); border-radius: 12px;
    display: flex; gap: 15px; align-items: center; flex-wrap: wrap;
    position: sticky; top: 290px; z-index: 90;
    margin: 0 20px 20px 20px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }}
  
  .filter-group {{ display: flex; gap: 8px; align-items: center; }}
  .filter-group label {{ font-size: 0.9rem; font-weight: 500; }}
  
  select, input {{
    background: var(--bg); color: var(--fg); border: 1px solid var(--sep);
    padding: 6px 10px; border-radius: 6px; outline: none; transition: border-color 0.2s;
  }}
  select:focus, input:focus {{ border-color: var(--info); }}
  
  .collapsible-toggle::after {{
    content: "▼"; transition: transform 0.2s; font-size: 0.8rem;
  }}
  .collapsible-toggle.collapsed::after {{
    transform: rotate(-90deg);
  }}
  
  .stats-overview {{
    display: flex; gap: 10px; flex-wrap: wrap; margin-top: 10px;
  }}
  
  .mini-stat {{
    padding: 4px 8px; background: rgba(255,255,255,0.1);
    border-radius: 4px; font-size: 0.8rem;
  }}
  
  @media (max-width: 768px) {{
    .summary-cards {{ grid-template-columns: 1fr; }}
    .header-meta {{ flex-direction: column; align-items: flex-start; }}
    .controls {{ margin-left: 0; }}
    .content-comparison {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>
    <div class="header">
        <h1>🔍 Rapport de Cohérence</h1>
        <div class="header-meta">
            <span>📁 Projet: {project_name}</span>
            <span>🌐 Langue: {language}</span>
            <span>📅 Généré le: {timestamp}</span>
        </div>
        <div class="controls">
            <button class="btn" onclick="toggleTheme()">🌙 Mode sombre</button>
            <button class="btn" onclick="window.print()">🖨️ Imprimer</button>
        </div>
    </div>

    <div class="summary-cards">
        {stats_cards}
    </div>

    {error_sections}

    <script>
        function toggleSection(header) {{
            const content = header.nextElementSibling;
            const isExpanded = content.classList.contains('expanded');
            
            if (isExpanded) {{
                content.classList.remove('expanded');
                header.classList.add('collapsed');
            }} else {{
                content.classList.add('expanded');
                header.classList.remove('collapsed');
            }}
        }}
        
        function toggleTheme() {{
            document.body.classList.toggle('light');
            const btn = event.target;
            btn.textContent = document.body.classList.contains('light') ? '🌙 Mode sombre' : '☀️ Mode clair';
        }}
        
        function openInEditor(filePath, lineNumber) {{
            // Cette fonction pourrait être étendue pour ouvrir le fichier dans un éditeur externe
            console.log('Ouvrir:', filePath, 'ligne:', lineNumber);
            alert('Fonctionnalité à implémenter: Ouvrir ' + filePath + ' à la ligne ' + lineNumber);
        }}
        
        // Ouvrir automatiquement la première section s'il y a des erreurs
        document.addEventListener('DOMContentLoaded', function() {{
            const firstSection = document.querySelector('.error-type-content');
            if (firstSection) {{
                firstSection.classList.add('expanded');
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html

def _get_badge_class(issue_type: str) -> str:
    """Retourne la classe CSS pour le badge selon le type d'erreur"""
    type_mapping = {
        # Variables
        'variable_missing': 'badge-variable',
        'variable_extra': 'badge-variable',
        'variable_mismatch': 'badge-variable',
        
        # Tags
        'tag_missing': 'badge-tag',
        'tag_extra': 'badge-tag',
        'tag_mismatch': 'badge-tag',
        'tag_count_mismatch': 'badge-tag',
        'tags_unbalanced': 'badge-tag',
        'tag_analysis_error': 'badge-tag',
        
        # Placeholders
        'placeholder_missing': 'badge-placeholder',
        'placeholder_extra': 'badge-placeholder',
        
        # Lignes non traduites
        'untranslated': 'badge-untranslated',
        
        # Caractères spéciaux et échappements
        'deepl_ellipsis': 'badge-special',
        'deepl_ellipsis_detected': 'badge-special',
        'isolated_percent': 'badge-special',
        'isolated_percent_in_source': 'badge-special',
        'isolated_percent_in_translation': 'badge-special',
        'french_quotes': 'badge-special',
        'french_quotes_detected': 'badge-special',
        'french_chevrons_detected': 'badge-special',
        'french_double_chevrons': 'badge-special',
        'double_quotes_at_end': 'badge-special',
        'double_quotes_detected': 'badge-special',
        'double_dash_ellipsis': 'badge-special',
        'special_code_detected': 'badge-special',
        
        # Échappements et formatage
        'escape_sequence': 'badge-special',
        'escape_sequence_mismatch': 'badge-special',
        'malformed_escape_sequence': 'badge-special',
        'escaped_quotes_mismatch': 'badge-special',
        'unescaped_quotes_mismatch': 'badge-special',
        
        # Pourcentages et variables de formatage
        'percentage': 'badge-special',
        'percentage_format_mismatch': 'badge-special',
        'percentage_type_mismatch': 'badge-special',
        'double_percent_mismatch': 'badge-special',
        'format_variables': 'badge-special',
        'format_types_mismatch': 'badge-special',
        
        # Parenthèses et délimiteurs
        'parentheses': 'badge-special',
        'parentheses_unbalanced': 'badge-special',
        'brackets_unbalanced': 'badge-special',
        'braces_unbalanced': 'badge-special',
        
        # Structure et syntaxe
        'line_structure': 'badge-other',
        'missing_new_line': 'badge-other',
        'orphan_new_line': 'badge-other',
        'length_discrepancy': 'badge-other',
        'special_char_mismatch': 'badge-other',
        'strings_syntax_error': 'badge-other',
        'unbalanced_quotes': 'badge-other',
        'empty_dialogue': 'badge-other',
        'analysis_error': 'badge-other',
    }
    return type_mapping.get(issue_type, 'badge-other')

def _get_issue_description(issue_type: str) -> str:
    """Retourne une description lisible du type d'erreur"""
    descriptions = {
        # Variables
        'variable_missing': 'Variables manquantes',
        'variable_extra': 'Variables en trop',
        'variable_mismatch': 'Variables incohérentes',
        
        # Tags
        'tag_missing': 'Tags manquants',
        'tag_extra': 'Tags en trop',
        'tag_mismatch': 'Tags incohérents',
        'tag_count_mismatch': 'Nombre de tags différent',
        'tags_unbalanced': 'Balises {} déséquilibrées',
        'tag_analysis_error': 'Erreur d\'analyse des tags',
        
        # Placeholders
        'placeholder_missing': 'Placeholders manquants',
        'placeholder_extra': 'Placeholders en trop',
        
        # Lignes non traduites
        'untranslated': 'Lignes non traduites',
        
        # Caractères spéciaux et échappements
        'deepl_ellipsis': 'Ellipses DeepL ([...])',
        'deepl_ellipsis_detected': 'Ellipses DeepL détectées',
        'isolated_percent': 'Pourcentages isolés (%)',
        'isolated_percent_in_source': 'Pourcentage isolé dans la source',
        'isolated_percent_in_translation': 'Pourcentage isolé dans la traduction',
        'french_quotes': 'Guillemets français («»)',
        'french_quotes_detected': 'Guillemets français détectés',
        'french_chevrons_detected': 'Chevrons doubles (<<>>)',
        'french_double_chevrons': 'Chevrons doubles détectés',
        'double_quotes_at_end': 'Guillemets doubles en fin',
        'double_quotes_detected': 'Guillemets doubles ("") détectés',
        'double_dash_ellipsis': 'Ellipses avec tirets (--)',
        'special_code_detected': 'Code spécial détecté',
        
        # Échappements et formatage
        'escape_sequence': 'Séquences d\'échappement',
        'escape_sequence_mismatch': 'Séquences \\n, \\t, \\r incohérentes',
        'malformed_escape_sequence': 'Séquence d\'échappement malformée',
        'escaped_quotes_mismatch': 'Guillemets échappés (\") incohérents',
        'unescaped_quotes_mismatch': 'Guillemets non échappés',
        
        # Pourcentages et variables de formatage
        'percentage': 'Problèmes de pourcentage',
        'percentage_format_mismatch': 'Variables de formatage incohérentes',
        'percentage_type_mismatch': 'Types de formatage différents',
        'double_percent_mismatch': 'Pourcentages doubles (%%) incohérents',
        'format_variables': 'Variables %s, %d incohérentes',
        'format_types_mismatch': 'Types de formatage incompatibles',
        
        # Parenthèses et délimiteurs
        'parentheses': 'Problèmes de parenthèses',
        'parentheses_unbalanced': 'Parenthèses () déséquilibrées',
        'brackets_unbalanced': 'Crochets [] déséquilibrés',
        'braces_unbalanced': 'Accolades {} déséquilibrées',
        
        # Structure et syntaxe
        'line_structure': 'Structure de ligne incorrecte',
        'missing_new_line': 'Ligne NEW manquante',
        'orphan_new_line': 'Ligne NEW sans OLD',
        'length_discrepancy': 'Différence de longueur importante',
        'special_char_mismatch': 'Caractères spéciaux incohérents',
        'strings_syntax_error': 'Erreur de syntaxe (strings)',
        'unbalanced_quotes': 'Guillemets déséquilibrés',
        'empty_dialogue': 'Dialogue vide',
        'analysis_error': 'Erreur d\'analyse',
    }
    return descriptions.get(issue_type, f'Erreur: {issue_type}')

def _generate_content_comparison(issue: Dict[str, Any]) -> str:
    """Génère la comparaison de contenu si disponible"""
    old_content = issue.get('old_content', '')
    new_content = issue.get('new_content', '')
    
    if not old_content and not new_content:
        return ""
    
    return f"""
    <div class="content-comparison">
        <div class="content-block old-content">
            <div class="content-label">Original</div>
            <div>{old_content or 'Non disponible'}</div>
        </div>
        <div class="content-block new-content">
            <div class="content-label">Traduit</div>
            <div>{new_content or 'Non disponible'}</div>
        </div>
    </div>
    """
