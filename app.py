#!/usr/bin/env python3
"""
Main application using pywebview with Flask backend
"""
import json
import os
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from subprocess import CalledProcessError

import webview
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.backend.backup_manager import BackupManager
from src.dialogs.file_dialog import (open_file_dialog_hybrid,
                                     open_folder_dialog_hybrid,
                                     open_save_dialog_hybrid)

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
        folders = [
            '01_Temporary',
            '02_Reports',
            '03_Backups',
            '04_Configs'
        ]

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

# Remplacer les lignes 41-49 dans app.py par :

# Importer le nouveau gestionnaire de backup

# Initialiser le gestionnaire
backup_manager = BackupManager()


@app.route('/api/backups', methods=['GET'])
def get_backups():
    """Liste toutes les sauvegardes avec filtres optionnels"""
    try:
        game_filter = request.args.get('game')
        type_filter = request.args.get('type')

        backups = backup_manager.list_all_backups(
            game_filter=game_filter,
            type_filter=type_filter
        )

        return jsonify({
            'success': True,
            'backups': backups
        })
    except (OSError, ValueError, KeyError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backups/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """Restaure une sauvegarde"""
    try:
        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]
        target_path = backup.get('source_path')

        if not target_path or not os.path.exists(os.path.dirname(target_path)):
            return jsonify({
                'success': False,
                'error': 'Chemin de destination invalide'
            }), 400

        # Copier le fichier
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(backup['backup_path'], target_path)

        # Supprimer la sauvegarde après restauration
        os.remove(backup['backup_path'])
        del backup_manager.metadata[backup_id]
        backup_manager.save_metadata()

        return jsonify({
            'success': True,
            'message': 'Sauvegarde restaurée avec succès'
        })

    except (OSError, KeyError, FileNotFoundError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backups/<backup_id>/restore-to', methods=['POST'])
def restore_backup_to(backup_id):
    """Restaure une sauvegarde vers un chemin spécifique"""
    try:
        data = request.get_json()
        print(f"DEBUG: restore_backup_to called with backup_id: {backup_id}")
        print(f"DEBUG: request data: {data}")

        if not data or 'target_path' not in data:
            print("DEBUG: Missing target_path in request data")
            return jsonify({
                'success': False,
                'error': 'Chemin de destination requis'
            }), 400

        target_path = data['target_path']
        print(f"DEBUG: Target path: {target_path}")

        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            print(f"DEBUG: Backup {backup_id} not found in metadata")
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]
        print(f"DEBUG: Backup found: {backup}")

        # Vérifier que le répertoire de destination existe
        target_path_obj = Path(target_path)
        target_dir = target_path_obj.parent
        print(f"DEBUG: Target directory: {target_dir}")
        print(f"DEBUG: Target directory exists: {target_dir.exists()}")

        if not target_dir.exists():
            print(f"DEBUG: Target directory does not exist: {target_dir}")
            # Créer le répertoire s'il n'existe pas
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Created target directory: {target_dir}")
            except (OSError, PermissionError) as e:
                print(f"DEBUG: Failed to create target directory: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Impossible de créer le répertoire de destination: {target_dir}'
                }), 400

        # Copier le fichier vers la destination
        print(f"DEBUG: Copying from {backup['backup_path']} to {target_path}")
        shutil.copy2(backup['backup_path'], target_path)

        print("DEBUG: Restore successful")
        return jsonify({
            'success': True,
            'message': f'Fichier restauré vers {target_path}'
        })

    except (OSError, KeyError, FileNotFoundError, ValueError) as e:
        print(f"DEBUG: Exception in restore_backup_to: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/backups/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """Supprime une sauvegarde"""
    try:
        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]

        # Supprimer le fichier
        if os.path.exists(backup['backup_path']):
            os.remove(backup['backup_path'])

        # Supprimer des métadonnées
        del backup_manager.metadata[backup_id]
        backup_manager.save_metadata()

        # Nettoyer les dossiers vides
        backup_manager.cleanup_empty_folders()

        return jsonify({
            'success': True,
            'message': 'Sauvegarde supprimée avec succès'
        })

    except (OSError, KeyError, FileNotFoundError) as e:
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
    },
    'colors': {
        'extractButton': '#3B82F6',
        'reconstructButton': '#10B981',
        'verifyButton': '#F59E0B',
        'accents': '#6366F1'
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
        picked = pick_strs(extraction_obj, ['placeholderFormat', 'encoding'])
        if picked:
            result['extraction'] = picked

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


@app.route('/api/file-dialog/folder', methods=['GET'])
def get_folder_dialog():
    """Open Windows folder selection dialog."""
    try:
        # Détecter WSL
        is_wsl = False
        try:
            if hasattr(os, 'uname'):
                is_wsl = 'microsoft' in os.uname().release.lower()
            is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
        except (AttributeError, OSError):
            is_wsl = False

        if is_wsl:
            # En WSL, retourner un message indiquant qu'il faut utiliser
            # l'endpoint POST
            return jsonify({
                'success': False,
                'error': 'WSL_MODE',
                'message': ('En mode WSL, utilisez POST /api/file-dialog/folder '
                           'avec le chemin en paramètre')
            }), 400

        folder_path = open_folder_dialog_hybrid()

        print(f"DEBUG: Folder dialog returned: '{folder_path}'")  # Debug log

        return jsonify({
            'success': True,
            'path': folder_path
        })
    except (OSError, subprocess.SubprocessError) as e:
        print(f"DEBUG: Folder dialog error: {e}")  # Debug log
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/file-dialog/folder', methods=['POST'])
def set_folder_path():
    """Set folder path manually (for WSL mode)."""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin requis'
            }), 400

        folder_path = data['path']
        print(f"DEBUG: Manual folder path set: '{folder_path}'")

        return jsonify({
            'success': True,
            'path': folder_path
        })
    except (ValueError, KeyError) as e:
        print(f"DEBUG: Manual folder path error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/file-dialog/file', methods=['GET'])
def get_file_dialog():
    """Open Windows file selection dialog."""
    try:
        file_path = open_file_dialog_hybrid()

        print(f"DEBUG: File dialog returned: '{file_path}'")  # Debug log

        return jsonify({
            'success': True,
            'path': file_path
        })
    except (OSError, subprocess.SubprocessError) as e:
        print(f"DEBUG: File dialog error: {e}")  # Debug log
        return jsonify({
            'success': False,
            'error': str(e)
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
        file_path = open_save_dialog_hybrid(
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
                'width': 1200,
                'height': 800,
                'min_size': (800, 600),
                'resizable': True,
                'fullscreen': False,
                'on_top': False,
                'focus': True
            }

            # Create and start window
            webview.create_window(**window_config)
            webview.start(debug=False)
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
