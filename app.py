#!/usr/bin/env python3
"""
Main application using pywebview with Flask backend
"""
import os
import sys
import threading
import time
from pathlib import Path

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
