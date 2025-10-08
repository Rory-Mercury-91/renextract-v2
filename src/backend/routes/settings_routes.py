"""
Routes pour la gestion des paramètres de l'application
"""
import json
from pathlib import Path

from flask import Blueprint, jsonify, request

# Blueprint pour les paramètres
settings_bp = Blueprint('settings', __name__)

# Structure de données par défaut pour les paramètres
settings_data = {
    'language': 'fr',
    'theme': 'dark',
    'debugActive': False,  # false=Level 3, true=Level 4
    'translatorFeature': False,
    'autoOpenings': {
        'files': True,
        'folders': True,
        'reports': False,
        'outputField': False
    },
    'externalTools': {
        'textEditor': 'VS Code',
        'translator': ''
    },
    'paths': {
        'renpySdk': '',
        'editor': ''
    },
    'folders': {
        'temporary': '01_Temporary/',
        'reports': '02_Reports/',
        'backups': '03_Backups/',
        'configs': '04_Configs/'
    },
    'extraction': {
        'placeholderFormat': 'PLACEHOLDER_{n}',
        'encoding': 'UTF-8'
    }
}

# Variable globale pour le chemin du fichier de configuration
settings_file_path = None


def init_settings(app_base_dir):
    """Initialise le chemin du fichier de paramètres et charge les données"""
    global settings_file_path  # pylint: disable=global-statement
    settings_file_path = Path(app_base_dir or '.') / \
        '04_Configs' / 'app_settings.json'
    load_settings_from_disk()


def load_settings_from_disk():
    """Charge les paramètres depuis le disque si disponible."""
    try:
        if settings_file_path and settings_file_path.exists():
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    sanitized = sanitize_settings_payload(data)
                    # Mise à jour superficielle (shallow merge) avec données propres
                    for key, value in sanitized.items():
                        if key in settings_data and isinstance(
                                settings_data[key],
                                dict) and isinstance(
                                value,
                                dict):
                            settings_data[key].update(value)
                        else:
                            settings_data[key] = value
    except (OSError, json.JSONDecodeError) as e:
        print(f"DEBUG: Failed to load settings: {e}")


def save_settings_to_disk():
    """Sauvegarde les paramètres courants sur le disque."""
    try:
        if settings_file_path:
            settings_file_path.parent.mkdir(parents=True, exist_ok=True)
            # Écrire un JSON trié pour une diff plus lisible
            with open(settings_file_path, 'w', encoding='utf-8') as f:
                json.dump(settings_data, f, ensure_ascii=False,
                          indent=2, sort_keys=True)
    except (OSError, TypeError) as e:
        print(f"DEBUG: Failed to save settings: {e}")


def sanitize_settings_payload(payload: dict) -> dict:
    # pylint: disable=too-many-branches
    """Nettoie/valide un payload de paramètres et ne retourne que les clés supportées.

    - language: str non vide sinon ignore
    - theme: 'light' | 'dark' | 'auto'
    - debugActive: bool
    - translatorFeature: bool
    - autoOpenings: sous-clés booleans
    - externalTools: textEditor/translator str
    - paths: editor/renpySdk str
    - folders: temporary/reports/backups/configs str
    - extraction: placeholderFormat/encoding str
    """
    allowed_themes = {'light', 'dark', 'auto'}

    result = {}
    if not isinstance(payload, dict):
        return result

    # Simples
    if isinstance(payload.get('language'),
                  str) and payload.get('language').strip():
        result['language'] = payload['language'].strip()

    theme = payload.get('theme')
    if isinstance(theme, str) and theme in allowed_themes:
        result['theme'] = theme

    if isinstance(payload.get('debugActive'), bool):
        result['debugActive'] = payload['debugActive']

    if isinstance(payload.get('translatorFeature'), bool):
        result['translatorFeature'] = payload['translatorFeature']

    # Objets imbriqués
    def pick_bools(obj: dict, keys: list[str]) -> dict:
        return {
            k: bool(
                obj[k]) for k in keys if k in obj and isinstance(
                obj[k],
                bool)}

    def pick_strs(obj: dict, keys: list[str]) -> dict:
        picked = {}
        for k in keys:
            v = obj.get(k)
            if isinstance(v, str):
                picked[k] = v
        return picked

    auto_openings = payload.get('autoOpenings')
    if isinstance(auto_openings, dict):
        picked = pick_bools(
            auto_openings, ['files', 'folders', 'reports', 'outputField'])
        if picked:
            result['autoOpenings'] = picked

    external_tools = payload.get('externalTools')
    if isinstance(external_tools, dict):
        picked = pick_strs(external_tools, ['textEditor', 'translator'])
        if picked:
            result['externalTools'] = picked

    paths_obj = payload.get('paths')
    if isinstance(paths_obj, dict):
        picked = pick_strs(paths_obj, ['editor', 'renpySdk'])
        if picked:
            result['paths'] = picked

    folders_obj = payload.get('folders')
    if isinstance(folders_obj, dict):
        picked = pick_strs(
            folders_obj, ['temporary', 'reports', 'backups', 'configs'])
        if picked:
            result['folders'] = picked

    extraction_obj = payload.get('extraction')
    if isinstance(extraction_obj, dict):
        picked = pick_strs(extraction_obj, ['placeholderFormat', 'encoding'])
        if picked:
            result['extraction'] = picked

    return result


@settings_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify({
        'success': True,
        'data': settings_data
    })


@settings_bp.route('/api/settings', methods=['POST'])
def update_settings():
    """Update settings"""
    try:
        new_settings = request.get_json()
        if not new_settings:
            return jsonify(
                {'success': False, 'message': 'No settings provided'}), 400

        # Filtrer, normaliser et merger proprement
        clean = sanitize_settings_payload(new_settings)
        for key, value in clean.items():
            if key not in settings_data:
                continue
            if isinstance(
                    settings_data[key],
                    dict) and isinstance(
                    value,
                    dict):
                settings_data[key].update(value)
            else:
                settings_data[key] = value

        # Sauvegarde sur disque
        save_settings_to_disk()

        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': settings_data
        })

    except (ValueError, KeyError, OSError) as e:
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        }), 500
