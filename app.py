#!/usr/bin/env python3
"""
Main application using pywebview with Flask backend
"""
import json
import os
import subprocess
from subprocess import CalledProcessError
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from subprocess import CalledProcessError
from tkinter import filedialog
from typing import Callable, List, Optional, Tuple

import webview
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.backend.backup_manager import BackupManager
from src.backend.config import AppConfig
from src.backend.routes.backup_routes import backup_bp, init_backup_manager
from src.backend.routes.file_dialog_routes import file_dialog_bp
from src.backend.routes.settings_routes import init_settings, settings_bp
from src.backend.routes.translator_routes import translator_bp
from src.backend.routes.update_routes import init_update_manager, update_bp
from src.backend.update_manager import UpdateManager
from src.backend.project import project_manager
from src.backend.extraction import extract_texts_from_file
from src.backend.reconstruction import (
    reconstruct_from_translations,
    validate_translation_files,
    fix_translation_errors_in_txt
)
from src.backend.coherence import (
    check_coherence_unified,
    set_coherence_options,
    get_coherence_options
)

# Load environment variables
load_dotenv()


def initialize_application_folders():
    """Crée les dossiers nécessaires au premier lancement de l'application"""
    try:
        # Déterminer le répertoire de base (où se trouve l'exécutable)
        if getattr(sys, 'frozen', False):
            # Mode exécutable (build)
            base_dir = os.path.dirname(sys.executable)
        else:
            # Mode développement
            base_dir = os.path.dirname(os.path.abspath(__file__))

        # Dossiers à créer
        folders = ['01_Temporary', '02_Reports', '03_Backups', '04_Configs']

        created_folders = []
        for folder in folders:
            folder_path = os.path.join(base_dir, folder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                created_folders.append(folder)
                print(f"DEBUG: Created folder: {folder_path}")
            else:
                print(f"DEBUG: Folder already exists: {folder_path}")

        if created_folders:
            print(
                f"DEBUG: Created {
                    len(created_folders)} new folders: {created_folders}")
        else:
            print("DEBUG: All folders already exist")

        return base_dir

    except (OSError, PermissionError) as e:
        print(f"ERROR: Failed to initialize folders: {e}")
        return None


# Initialiser les dossiers au démarrage
app_base_dir = initialize_application_folders()

# Determine the path to static files based on execution context


def get_static_path():
    """Determine the path to static files based on execution context"""
    if getattr(sys, 'frozen', False):
        # Mode exécutable - les fichiers statiques sont dans _MEIPASS
        base_path = Path(sys._MEIPASS)  # pylint: disable=protected-access
        static_path = base_path
    else:
        # Mode développement
        static_path = Path('dist')
    return str(static_path)


# Flask configuration
app = Flask(__name__, static_folder=get_static_path(), static_url_path='')
CORS(app)

# Global variables for communication
api_data = {
    'message': 'Hello from Python backend!',
    'counter': 0,
    'items': []
}

# Initialiser les gestionnaires
backup_manager = BackupManager()

# Initialiser la configuration
AppConfig.ensure_directories()

# Valider la configuration
config_errors = AppConfig.validate_config()
if config_errors:
    print("⚠️  Erreurs de configuration détectées:")
    for error in config_errors:
        print(f"   - {error}")
    print("   Veuillez configurer les variables d'environnement ou modifier src/backend/config.py")

# Initialiser le gestionnaire de mise à jour
update_manager = UpdateManager(
    AppConfig.GITHUB_REPO_OWNER,
    AppConfig.GITHUB_REPO_NAME,
    AppConfig.APP_VERSION
)

# Enregistrer les blueprints
app.register_blueprint(settings_bp)
app.register_blueprint(file_dialog_bp)
app.register_blueprint(update_bp)
app.register_blueprint(backup_bp)
app.register_blueprint(translator_bp)

# Initialiser les gestionnaires pour les blueprints
init_backup_manager(backup_manager)
init_update_manager(update_manager)
init_settings(app_base_dir)


@app.route('/api/backups/create', methods=['POST'])
def create_backup():
    """Crée une nouvelle sauvegarde"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        source_path = data.get('source_path')
        backup_type = data.get('backup_type', 'security')
        description = data.get('description', '')

        if not source_path:
            return jsonify({
                'success': False,
                'error': 'Chemin source requis'
            }), 400

        if not os.path.exists(source_path):
            return jsonify({
                'success': False,
                'error': f'Fichier source introuvable: {source_path}'
            }), 404

        # Créer le backup
        result = backup_manager.create_backup(
            source_path=source_path,
            backup_type=backup_type,
            description=description
        )

        if result['success']:
            return jsonify({
                'success': True,
                'backup_id': result.get('backup_id'),
                'backup_path': result.get('backup_path'),
                'message': 'Sauvegarde créée avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'error': result.get('error', 'Erreur lors de la création du backup')
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health')
def health_check():
    """Check API status"""
    return jsonify({
        'status': 'ok',
        'message': 'Python API is working correctly',
        'timestamp': time.time()
    })


@app.route('/api/message')
def get_message():
    """Get message from backend"""
    return jsonify({
        'message': api_data['message'],
        'counter': api_data['counter']
    })


@app.route('/api/message', methods=['POST'])
def update_message():
    """Update message"""
    data = request.get_json()
    if data and 'message' in data:
        api_data['message'] = data['message']
        api_data['counter'] += 1
        return jsonify({
            'success': True,
            'message': 'Message updated',
            'data': api_data
        })
    return jsonify({'success': False, 'error': 'Message required'}), 400


@app.route('/api/items')
def get_items():
    """Get items list"""
    return jsonify({
        'items': api_data['items']
    })


@app.route('/api/items', methods=['POST'])
def add_item():
    """Add new item"""
    data = request.get_json()
    if data and 'name' in data:
        new_item = {
            'id': len(api_data['items']) + 1,
            'name': data['name'],
            'timestamp': time.time()
        }
        api_data['items'].append(new_item)
        return jsonify({
            'success': True,
            'item': new_item
        })
    return jsonify({'success': False, 'error': 'Name required'}), 400


@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    """Delete item"""
    for i, item in enumerate(api_data['items']):
        if item['id'] == item_id:
            deleted_item = api_data['items'].pop(i)
            return jsonify({
                'success': True,
                'deleted_item': deleted_item
            })
    return jsonify({'success': False, 'error': 'Item not found'}), 404


# TranslationToolsIA integration
@app.route('/api/translator/health', methods=['GET'])
def translator_health():
    """Vérifie la présence du dépôt TranslationToolsIA et retourne des infos basiques."""
    try:
        repo_path = Path('external/TranslationToolsIA')
        exists = repo_path.exists()
        head = None
        if exists:
            try:
                # Lire le commit courant si git est présent
                result = subprocess.run(
                    ['git', '-C', str(repo_path), 'rev-parse',
                     '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                head = result.stdout.strip()
            except (CalledProcessError, FileNotFoundError):
                head = None

        return jsonify({
            'success': True,
            'exists': exists,
            'gitHead': head
        })
    except (OSError, ValueError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translator/run', methods=['POST'])
def translator_run():
    """Lance la traduction via TranslationToolsIA pour un dossier Ren'Py."""
    try:
        data = request.get_json() or {}
        input_folder = data.get('inputFolder')
        recursive = bool(data.get('recursive', True))
        model_path = data.get('modelPath', 'virusf/nllb-renpy-rory-v4')
        source_lang = data.get('sourceLang', 'auto')
        target_lang = data.get('targetLang', 'fra_Latn')

        if not input_folder or not os.path.isdir(input_folder):
            return jsonify(
                {'success': False, 'error': 'Dossier source invalide'}), 400

        repo_path = Path('external/TranslationToolsIA')
        if not repo_path.exists():
            return jsonify({
                'success': False,
                'error': (
                    'TranslationToolsIA non installé. '
                    'Exécutez pnpm run ttia:clone'
                )
            }), 400

        # Choisir le script de batch pour un dossier entier, tel que documenté dans le README
        # Fallback: traducteur_renpy_jeu_complet.py si présent, sinon
        # traducteur_renpy.py
        candidate_scripts = [
            repo_path / 'script' / 'traducteur_renpy_jeu_complet.py',
            repo_path / 'script' / 'traducteur_renpy.py',
        ]
        script_path = None
        for c in candidate_scripts:
            if c.exists():
                script_path = c
                break
        if script_path is None:
            return jsonify({
                'success': False,
                'error': 'Script de traduction introuvable dans TranslationToolsIA'
            }), 500

        # Construire la commande Python
        # On suppose que le script accepte des arguments standards; si
        # différent, on adaptera
        cmd = [
            sys.executable,
            str(script_path),
            '--input-folder', input_folder,
            '--recursive', str(int(recursive)),
            '--model', model_path,
            '--source', source_lang,
            '--target', target_lang
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        success = proc.returncode == 0
        return jsonify({
            'success': success,
            'returncode': proc.returncode,
            'stdout': proc.stdout[-5000:],
            'stderr': proc.stderr[-5000:],
        }), (200 if success else 500)
    except (OSError, ValueError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# Settings endpoints - Structure mise à jour
settings_data = {
    'language': 'fr',
    'theme': 'auto',
    'debugActive': False,  # false=Level 3, true=Level 4
    'translatorFeature': False,
    'autoOpenings': {
        'files': True,
        'folders': True,
        'reports': True,
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
        'encoding': 'UTF-8',
        'detectDuplicates': True,
        'projectProgressTracking': False,
        'lineLimit': 1000,
        'defaultSaveMode': 'new_file',
        'patterns': {
            'code': 'RENPY_CODE_001',
            'asterisk': 'RENPY_ASTERISK_001',
            'tilde': 'RENPY_TILDE_001'
        }
    },
    'reconstruction': {
        'saveMode': 'new_file'
    },
    'coherence': {
        'checkVariables': True,
        'checkTags': True,
        'checkUntranslated': True,
        'checkEscapeSequences': True,
        'checkPercentages': True,
        'checkQuotations': True,
        'checkParentheses': True,
        'checkSyntax': True,
        'checkDeeplEllipsis': True,
        'checkIsolatedPercent': True,
        'checkFrenchQuotes': True,
        'checkDoubleDashEllipsis': True,
        'checkSpecialCodes': False,
        'checkLineStructure': True,
        'customExclusions': ['OK', 'Menu', 'Continue', 'Yes', 'No', 'Level', '???', '!!!', '...']
    },
    'lastProject': {
        'path': '',
        'language': '',
        'mode': 'project'
    }
}

# Fichier de configuration persistant
settings_file_path = Path(app_base_dir or '.') / \
    '04_Configs' / 'app_settings.json'


def load_settings_from_disk():
    """Charge les paramètres depuis le disque si disponible."""
    try:
        if settings_file_path.exists():
            with open(settings_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    sanitized = sanitize_settings_payload(data)
                    # Mise à jour superficielle (shallow merge) avec données
                    # propres
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
        picked = pick_strs(extraction_obj, ['placeholderFormat', 'encoding', 'defaultSaveMode'])
        # Ajouter les booleans
        if isinstance(extraction_obj.get('detectDuplicates'), bool):
            picked['detectDuplicates'] = extraction_obj['detectDuplicates']
        if isinstance(extraction_obj.get('projectProgressTracking'), bool):
            picked['projectProgressTracking'] = extraction_obj['projectProgressTracking']
        # Ajouter lineLimit
        if isinstance(extraction_obj.get('lineLimit'), int):
            picked['lineLimit'] = extraction_obj['lineLimit']
        # Ajouter les patterns
        if isinstance(extraction_obj.get('patterns'), dict):
            patterns = pick_strs(extraction_obj['patterns'], ['code', 'asterisk', 'tilde'])
            if patterns:
                picked['patterns'] = patterns
        if picked:
            result['extraction'] = picked

    reconstruction_obj = payload.get('reconstruction')
    if isinstance(reconstruction_obj, dict):
        picked_reconstruction = {}
        if 'saveMode' in reconstruction_obj and reconstruction_obj['saveMode'] in ['overwrite', 'new_file']:
            picked_reconstruction['saveMode'] = reconstruction_obj['saveMode']
        if picked_reconstruction:
            result['reconstruction'] = picked_reconstruction

    # coherence object
    coherence_obj = payload.get('coherence')
    if isinstance(coherence_obj, dict):
        picked_coherence = pick_bools(coherence_obj, [
            'checkVariables', 'checkTags', 'checkUntranslated', 'checkEscapeSequences',
            'checkPercentages', 'checkQuotations', 'checkParentheses', 'checkSyntax',
            'checkDeeplEllipsis', 'checkIsolatedPercent', 'checkFrenchQuotes',
            'checkDoubleDashEllipsis', 'checkSpecialCodes', 'checkLineStructure'
        ])
        # Ajouter customExclusions
        if isinstance(coherence_obj.get('customExclusions'), list):
            exclusions = [str(x) for x in coherence_obj['customExclusions'] if isinstance(x, str)]
            picked_coherence['customExclusions'] = exclusions
        if picked_coherence:
            result['coherence'] = picked_coherence

    # lastProject object
    last_project_obj = payload.get('lastProject')
    if isinstance(last_project_obj, dict):
        picked = pick_strs(last_project_obj, ['path', 'language', 'mode'])
        if picked:
            result['lastProject'] = picked

    return result


# Charger dès le démarrage
load_settings_from_disk()


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings"""
    return jsonify({
        'success': True,
        'data': settings_data
    })


@app.route('/api/settings', methods=['POST'])
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


@app.route('/api/file-dialog/save', methods=['POST'])
def get_save_dialog():
    """Open Windows save file dialog (asksaveasfilename equivalent)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données requises'
            }), 400

        # Paramètres du dialogue de sauvegarde
        title = data.get('title', 'Enregistrer sous...')
        initialfile = data.get('initialfile', '')
        defaultextension = data.get('defaultextension', '')
        filetypes = data.get('filetypes', [("Tous les fichiers", "*.*")])

        print(
            f"DEBUG: Save dialog params - title: {title}, initialfile: {initialfile}, \
              defaultextension: {defaultextension}")

        # Détecter WSL
        is_wsl = False
        try:
            if hasattr(os, 'uname'):
                is_wsl = 'microsoft' in os.uname().release.lower()
            is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
        except (AttributeError, OSError):
            is_wsl = False

        if is_wsl:
            # En WSL, retourner une erreur indiquant qu'il faut utiliser
            # l'endpoint POST avec le chemin
            return jsonify({
                'success': False,
                'error': 'WSL_MODE',
                'message': ('En mode WSL, le dialogue de sauvegarde n\'est pas '
                           'disponible. Utilisez POST /api/file-dialog/save avec '
                            'le chemin en paramètre')
            }), 400

        # En mode normal, utiliser le dialogue natif
        file_path = open_dialog_hybrid(
            dialog_type='save',
            title=title,
            initialfile=initialfile,
            defaultextension=defaultextension,
            filetypes=filetypes
        )

        print(f"DEBUG: Save dialog returned: '{file_path}'")

        return jsonify({
            'success': True,
            'path': file_path
        })

    except (OSError, ValueError, KeyError) as e:
        print(f"DEBUG: Save dialog error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/file-dialog/save-path', methods=['POST'])
def set_save_path():
    """Set save file path manually (for WSL mode)."""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin requis'
            }), 400

        file_path = data['path']
        print(f"DEBUG: Manual save path set: '{file_path}'")

        return jsonify({
            'success': True,
            'path': file_path
        })
    except (ValueError, KeyError) as e:
        print(f"DEBUG: Manual save path error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


def is_wsl_environment():
    """Détecte si on est en environnement WSL"""
    try:
        if hasattr(os, 'uname'):
            if 'microsoft' in os.uname().release.lower():
                return True
        return 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
    except (AttributeError, OSError):
        return False


def wsl_mode_response(endpoint):
    """Retourne une réponse pour le mode WSL"""
    return jsonify({
        'success': False,
        'error': 'WSL_MODE',
        'message': f'En mode WSL, le dialogue natif n\'est pas disponible. Veuillez fournir le chemin dans le body JSON.'
    }), 400


@app.route('/api/file-dialog/open', methods=['POST'])
def open_dialog_unified():
    """Endpoint unifié pour ouvrir un fichier ou un dossier.

    Body JSON attendu:
    {
      "type": "file" | "folder",
      "path"?: string  # utilisé en WSL quand le dialogue natif n'est pas disponible
    }
    """
    try:
        data = request.get_json() or {}
        # Accepter 'type' et 'dialog_type' (alias)
        dialog_type = data.get('type') or data.get('dialog_type')
        manual_path = data.get('path')
        title = data.get('title')
        initialdir = data.get('initialdir')
        filetypes = data.get('filetypes')
        initialfile = data.get('initialfile')
        defaultextension = data.get('defaultextension')
        must_exist = data.get('must_exist')
        validate = data.get('validate')

        if dialog_type not in {'file', 'folder', 'save'}:
            return jsonify({
                'success': False,
                'error': 'TYPE_INVALID',
                'message': "Le champ 'type'/'dialog_type' doit valoir 'file', 'folder' ou 'save'"
            }), 400

        # WSL: accepter un path fourni, sinon demander au client de le fournir
        if is_wsl_environment():
            if isinstance(manual_path, str) and manual_path.strip():
                return jsonify({'success': True, 'path': manual_path})
            return jsonify({
                'success': False,
                'error': 'WSL_PATH_REQUIRED',
                'message': "Environnement WSL : le chemin doit être fourni par le client."
            }), 400

        # Mode normal: ouvrir le dialogue natif selon le type
        path = open_dialog_hybrid(
            dialog_type=dialog_type,
            title=title,
            initialdir=initialdir,
            filetypes=filetypes,
            initialfile=initialfile,
            defaultextension=defaultextension,
            must_exist=must_exist,
            validate=validate,
        )

        return jsonify({'success': True, 'path': path})
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def open_dialog_hybrid(  # pylint: disable=too-many-arguments
    dialog_type: str,
    *,
    title: Optional[str] = None,
    initialdir: Optional[str] = None,
    filetypes: Optional[List[Tuple[str, str]]] = None,
    initialfile: Optional[str] = None,
    defaultextension: Optional[str] = None,
    must_exist: bool = True,
    validate: Optional[Callable[[str], bool]] = None,
) -> str:
    """Ouvre un dialogue (fichier ou dossier) avec tkinter, sinon fallback web.

    - dialog_type: 'file' ou 'folder'
    - title: titre de la fenêtre
    - initialdir: répertoire initial
    - filetypes: liste de filtres (uniquement pour 'file')
    - must_exist: contraint la sélection à des chemins existants
    - validate: fonction de validation supplémentaire; si False, retourne ""
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale

        path: str
        if dialog_type == 'folder':
            path = filedialog.askdirectory(
                title=title,
                initialdir=initialdir,
                mustexist=must_exist,
            ) or ""
        elif dialog_type == 'file':
            path = filedialog.askopenfilename(
                title=title,
                initialdir=initialdir,
                filetypes=filetypes,
            ) or ""
        else:  # 'save'
            path = filedialog.asksaveasfilename(
                title=title,
                initialfile=initialfile,
                defaultextension=defaultextension,
                filetypes=filetypes,
            ) or ""

        root.destroy()

        if not path:
            return ""
        if validate is not None and not validate(path):
            return ""
        return path
    except (tk.TclError, OSError) as e:
        print(f"Tkinter dialog failed: {e}")
        return ""


# Update management endpoints
@app.route('/api/updates/check', methods=['GET'])
def check_for_updates():
    """Vérifie s'il y a des mises à jour disponibles"""
    try:
        result = update_manager.check_for_updates()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la vérification: {str(e)}'
        }), 500


@app.route('/api/updates/download', methods=['POST'])
def download_update():
    """Télécharge la mise à jour disponible"""
    try:
        data = request.get_json()
        if not data or 'download_url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL de téléchargement requise'
            }), 400

        download_url = data['download_url']

        # Fonction de callback pour le progrès (optionnel)
        def progress_callback(progress, downloaded, total):
            # Ici on pourrait envoyer des événements WebSocket ou stocker le progrès
            print(
                f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)")

        result = update_manager.download_update(
            download_url, progress_callback)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors du téléchargement: {str(e)}'
        }), 500


@app.route('/api/updates/install', methods=['POST'])
def install_update():
    """Installe la mise à jour téléchargée"""
    try:
        data = request.get_json()
        if not data or 'extract_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin d\'extraction requis'
            }), 400

        extract_path = data['extract_path']
        result = update_manager.install_update(extract_path)
        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'installation: {str(e)}'
        }), 500


@app.route('/api/updates/config', methods=['GET'])
def get_update_config():
    """Récupère la configuration des mises à jour"""
    try:
        config = update_manager.get_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération de la config: {str(e)}'
        }), 500


@app.route('/api/updates/config', methods=['POST'])
def update_update_config():
    """Met à jour la configuration des mises à jour"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Configuration requise'
            }), 400

        update_manager.set_config(data)
        return jsonify({
            'success': True,
            'message': 'Configuration mise à jour avec succès',
            'config': update_manager.get_config()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour de la config: {str(e)}'
        }), 500


@app.route('/api/updates/auto-check', methods=['GET'])
def should_auto_check():
    """Vérifie si on doit faire une vérification automatique"""
    try:
        should_check = update_manager.should_check_for_updates()
        return jsonify({
            'success': True,
            'should_check': should_check
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la vérification auto: {str(e)}'
        }), 500


# ==================== PROJECT MANAGEMENT ENDPOINTS ====================

@app.route('/api/project/validate', methods=['POST'])
def validate_project():
    """Valide un chemin de projet Ren'Py"""
    try:
        data = request.get_json()
        if not data or 'project_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de projet requis'
            }), 400

        project_path = data['project_path']
        result = project_manager.validate_project(project_path)

        return jsonify({
            'success': True,
            'validation': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/find-root', methods=['POST'])
def find_project_root():
    """Trouve la racine d'un projet à partir d'un sous-dossier"""
    try:
        data = request.get_json()
        if not data or 'subdir_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de sous-dossier requis'
            }), 400

        subdir_path = data['subdir_path']
        max_levels = data.get('max_levels', 10)

        root_path = project_manager.find_project_root(subdir_path, max_levels)

        if root_path:
            return jsonify({
                'success': True,
                'root_path': root_path
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Racine du projet introuvable'
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/languages', methods=['POST'])
def scan_project_languages():
    """Scanne les langues disponibles dans un projet"""
    try:
        data = request.get_json()
        if not data or 'project_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de projet requis'
            }), 400

        project_path = data['project_path']
        languages = project_manager.scan_languages(project_path)

        # Mettre à jour l'état interne
        project_manager.available_languages = languages

        return jsonify({
            'success': True,
            'languages': languages
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/files', methods=['POST'])
def scan_language_files():
    """Scanne les fichiers d'une langue spécifique"""
    try:
        data = request.get_json()
        if not data or 'project_path' not in data or 'language' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de projet et langue requis'
            }), 400

        project_path = data['project_path']
        language = data['language']
        exclusions = data.get('exclusions', [])

        files = project_manager.scan_language_files(
            project_path, language, exclusions
        )

        # Mettre à jour l'état interne
        project_manager.available_files = files
        project_manager.current_language = language

        return jsonify({
            'success': True,
            'files': files
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/load-file', methods=['POST'])
def load_file_content():
    """Charge le contenu d'un fichier"""
    try:
        data = request.get_json()
        if not data or 'filepath' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de fichier requis'
            }), 400

        filepath = data['filepath']
        result = project_manager.load_file_content(filepath)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/summary', methods=['POST'])
def get_project_summary():
    """Obtient un résumé du projet"""
    try:
        data = request.get_json()
        if not data or 'project_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de projet requis'
            }), 400

        project_path = data['project_path']
        summary = project_manager.get_project_summary(project_path)

        return jsonify({
            'success': True,
            'summary': summary
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/set-current', methods=['POST'])
def set_current_project():
    """Définit le projet actuel"""
    try:
        data = request.get_json()
        if not data or 'project_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de projet requis'
            }), 400

        project_path = data['project_path']
        mode = data.get('mode', 'project')

        result = project_manager.set_current_project(project_path, mode)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/project/state', methods=['GET'])
def get_project_state():
    """Obtient l'état actuel du gestionnaire de projet"""
    try:
        state = project_manager.get_state()
        return jsonify({
            'success': True,
            'state': state
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== EXTRACTION ENDPOINTS ====================

@app.route('/api/extraction/extract', methods=['POST'])
def extract_texts():
    """Extrait les textes d'un fichier Ren'Py"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        file_content = data.get('file_content', [])
        filepath = data.get('filepath', '')
        detect_duplicates = data.get('detect_duplicates', True)

        if not file_content or not filepath:
            return jsonify({
                'success': False,
                'error': 'Contenu de fichier et chemin requis'
            }), 400

        # Lancer l'extraction
        result = extract_texts_from_file(
            file_content, filepath, detect_duplicates)

        if result['success']:
            return jsonify({
                'success': True,
                'result': result['result'],
                'extraction_time': result['extraction_time']
            })
        else:
            return jsonify({
                'success': False,
                'error': result['error']
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extraction/validate-file', methods=['POST'])
def validate_extraction_file():
    """Valide un fichier pour l'extraction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        filepath = data.get('filepath', '')
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Chemin de fichier requis'
            }), 400

        # Validation basique
        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'validation': {
                    'valid': False,
                    'message': 'Fichier non trouvé'
                }
            })

        if not filepath.lower().endswith('.rpy'):
            return jsonify({
                'success': False,
                'validation': {
                    'valid': False,
                    'message': 'Type de fichier non supporté. Veuillez sélectionner un fichier .rpy.'
                }
            })

        file_size = os.path.getsize(filepath)
        max_size_mb = 50
        max_size_bytes = max_size_mb * 1024 * 1024

        if file_size > max_size_bytes:
            return jsonify({
                'success': False,
                'validation': {
                    'valid': False,
                    'message': f'Le fichier est trop volumineux ({file_size / (1024*1024):.1f} Mo). La taille maximale est de {max_size_mb} Mo.'
                }
            })

        if file_size == 0:
            return jsonify({
                'success': False,
                'validation': {
                    'valid': False,
                    'message': 'Le fichier est vide.'
                }
            })

        return jsonify({
            'success': True,
            'validation': {
                'valid': True,
                'message': 'Fichier valide',
                'size': file_size,
                'filename': os.path.basename(filepath)
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extraction/get-settings', methods=['GET'])
def get_extraction_settings():
    """Obtient les paramètres d'extraction actuels"""
    try:
        settings = {
            'detect_duplicates': True,  # Valeur par défaut
            'code_prefix': 'RENPY_CODE_001',
            'asterisk_prefix': 'RENPY_ASTERISK_001',
            'tilde_prefix': 'RENPY_TILDE_001',
            'empty_prefix': 'RENPY_EMPTY'
        }

        return jsonify({
            'success': True,
            'settings': settings
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extraction/set-settings', methods=['POST'])
def set_extraction_settings():
    """Définit les paramètres d'extraction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        # Pour l'instant, on retourne juste un succès
        # Dans une version future, on pourrait sauvegarder ces paramètres
        return jsonify({
            'success': True,
            'message': 'Paramètres d\'extraction mis à jour'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extraction/open-file', methods=['POST'])
def open_extraction_file():
    """Ouvre un fichier avec l'application système par défaut"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        filepath = data.get('filepath', '')
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Chemin de fichier requis'
            }), 400

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404

        # Ouvrir le fichier avec l'application système par défaut
        try:
            if os.name == 'nt':  # Windows
                os.startfile(filepath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', filepath])
            else:  # Linux
                subprocess.call(['xdg-open', filepath])

            return jsonify({
                'success': True,
                'message': f'Fichier ouvert: {os.path.basename(filepath)}'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Impossible d\'ouvrir le fichier: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/extraction/open-folder', methods=['POST'])
def open_extraction_folder():
    """Ouvre un dossier avec l'explorateur de fichiers système"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        folderpath = data.get('folderpath', '')
        if not folderpath:
            return jsonify({
                'success': False,
                'error': 'Chemin de dossier requis'
            }), 400

        if not os.path.exists(folderpath):
            return jsonify({
                'success': False,
                'error': 'Dossier non trouvé'
            }), 404

        # Ouvrir le dossier avec l'explorateur de fichiers
        try:
            if os.name == 'nt':  # Windows
                os.startfile(folderpath)
            elif sys.platform == 'darwin':  # macOS
                subprocess.call(['open', folderpath])
            else:  # Linux
                subprocess.call(['xdg-open', folderpath])

            return jsonify({
                'success': True,
                'message': f'Dossier ouvert: {os.path.basename(folderpath)}'
            })

        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Impossible d\'ouvrir le dossier: {str(e)}'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== RECONSTRUCTION ENDPOINTS ====================

@app.route('/api/reconstruction/validate', methods=['POST'])
def validate_reconstruction_files():
    """Valide les fichiers de traduction avant reconstruction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        filepath = data.get('filepath', '')
        extracted_count = data.get('extracted_count', 0)
        asterix_count = data.get('asterix_count', 0)
        tilde_count = data.get('tilde_count', 0)

        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Chemin de fichier requis'
            }), 400

        # Valider les fichiers
        result = validate_translation_files(
            filepath, extracted_count, asterix_count, tilde_count)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reconstruction/fix-quotes', methods=['POST'])
def fix_quotes_in_file():
    """Corrige les guillemets non-échappés dans un fichier"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        filepath = data.get('filepath', '')
        if not filepath:
            return jsonify({
                'success': False,
                'error': 'Chemin de fichier requis'
            }), 400

        if not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fichier non trouvé'
            }), 404

        # Corriger les guillemets
        corrections = fix_translation_errors_in_txt(filepath)

        return jsonify({
            'success': True,
            'corrections': corrections,
            'message': f'{corrections} correction(s) appliquée(s)'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/reconstruction/reconstruct', methods=['POST'])
def reconstruct_file():
    """Reconstruit un fichier traduit"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        file_content = data.get('file_content', [])
        filepath = data.get('filepath', '')
        save_mode = data.get('save_mode', 'new_file')

        if not file_content or not filepath:
            return jsonify({
                'success': False,
                'error': 'Contenu de fichier et chemin requis'
            }), 400

        # Lancer la reconstruction
        result = reconstruct_from_translations(
            file_content, filepath, save_mode)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ==================== COHÉRENCE ====================

@app.route('/api/coherence/check', methods=['POST'])
def check_coherence():
    """Vérifie la cohérence d'un fichier ou dossier"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        target_path = data.get('target_path', '')
        return_details = data.get('return_details', True)
        selection_info = data.get('selection_info')

        if not target_path:
            return jsonify({
                'success': False,
                'error': 'Chemin cible requis'
            }), 400

        # Lancer la vérification
        result = check_coherence_unified(target_path, return_details, selection_info)
        return jsonify({'success': True, 'result': result})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/coherence/options', methods=['GET'])
def get_coherence_options_api():
    """Récupère les options de vérification de cohérence"""
    try:
        options = get_coherence_options()
        return jsonify({'success': True, 'options': options})
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/coherence/options', methods=['POST'])
def set_coherence_options_api():
    """Configure les options de vérification de cohérence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        options = data.get('options', {})
        set_coherence_options(options)
        return jsonify({'success': True, 'message': 'Options mises à jour'})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/coherence/open-report', methods=['POST'])
def open_coherence_report():
    """Ouvre un rapport de cohérence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données JSON manquantes'
            }), 400

        report_path = data.get('report_path', '')

        if not report_path or not os.path.exists(report_path):
            return jsonify({
                'success': False,
                'error': 'Rapport introuvable'
            }), 400

        # Ouvrir le rapport dans le navigateur par défaut
        import webbrowser
        webbrowser.open(f'file://{os.path.abspath(report_path)}')

        return jsonify({'success': True, 'message': 'Rapport ouvert'})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/coherence/open-folder', methods=['POST'])
def open_coherence_folder():
    """Ouvre le dossier des rapports"""
    try:
        reports_folder = "02_Reports"

        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        # Ouvrir le dossier dans l'explorateur
        import subprocess
        import platform

        if platform.system() == "Windows":
            subprocess.run(["explorer", os.path.abspath(reports_folder)])
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", os.path.abspath(reports_folder)])
        else:  # Linux
            subprocess.run(["xdg-open", os.path.abspath(reports_folder)])

        return jsonify({'success': True, 'message': 'Dossier ouvert'})

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/')
def index():
    """Serve Svelte application"""
    return app.send_static_file('index.html')


def start_flask():
    """Start Flask server in background"""
    app.run(host='127.0.0.1', port=5000, debug=True, use_reloader=False)


def main():
    """Main function"""
    # Check if we're in WSL or if PyWebView is not available
    is_wsl = False
    try:
        if hasattr(os, 'uname'):
            is_wsl = 'microsoft' in os.uname().release.lower()
        # Also check environment variables
        is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
    except (AttributeError, OSError):
        is_wsl = False

    # Debug information
    print(f"DEBUG: is_wsl = {is_wsl}")
    print(f"DEBUG: platform = {sys.platform}")
    print(f"DEBUG: frozen = {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        print(
            f"DEBUG: _MEIPASS = {
                sys._MEIPASS}")  # pylint: disable=protected-access
        print(f"DEBUG: static_path = {get_static_path()}")

    try:
        # Try to start PyWebView
        if not is_wsl:
            # Start Flask in a separate thread
            flask_thread = threading.Thread(target=start_flask, daemon=True)
            flask_thread.start()

            # Wait for Flask to be ready
            time.sleep(2)

            # pywebview window configuration
            window_config = {
                'title': 'PyWebView + Svelte Application',
                'url': 'http://127.0.0.1:5000',
                'width': 1300,
                'height': 815,
                'min_size': (700, 500),
                'resizable': True,
                'fullscreen': False,
                'on_top': False,
                'focus': True
            }

            # Create and start window
            webview.create_window(**window_config)
            webview.start(debug=True)
        else:
            raise RuntimeError("WSL detected - web server mode only")
    except (RuntimeError, ImportError, OSError, AttributeError) as e:
        print(f"⚠️  PyWebView not available: {e}")
        print("🌐 Starting in web server mode only...")
        print("📱 Open your browser at: http://127.0.0.1:5000")
        print("🛑 Press Ctrl+C to stop")

        # Start Flask in main mode
        app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()
