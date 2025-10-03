#!/usr/bin/env python3
"""
Main application using pywebview with Flask backend
"""
import os
import sys
import threading
import time
from pathlib import Path
from flask import Flask, jsonify, request
from flask_cors import CORS
import webview
from dotenv import load_dotenv
from hybrid_dialog import open_folder_dialog_hybrid, open_file_dialog_hybrid

# Load environment variables
load_dotenv()

# Determine the path to static files based on execution context
def get_static_path():
    """Determine the path to static files based on execution context"""
    if getattr(sys, 'frozen', False):
        base_path = Path(sys._MEIPASS)  # pylint: disable=protected-access
        static_path = base_path
    else:
        # Development mode
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
from backup_manager import BackupManager

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
    except Exception as e:
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
        import shutil
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(backup['backup_path'], target_path)
        
        # Supprimer la sauvegarde après restauration
        os.remove(backup['backup_path'])
        del backup_manager.metadata[backup_id]
        backup_manager._save_metadata()
        
        return jsonify({
            'success': True,
            'message': 'Sauvegarde restaurée avec succès'
        })
        
    except Exception as e:
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
        backup_manager._save_metadata()
        
        # Nettoyer les dossiers vides
        backup_manager.cleanup_empty_folders()
        
        return jsonify({
            'success': True,
            'message': 'Sauvegarde supprimée avec succès'
        })
        
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


# Settings endpoints - Structure mise à jour
settings_data = {
    'language': 'fr',
    'theme': 'dark',
    'debugActive': False,  # false=Level 3, true=Level 4
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
        'vscode': '',
        'sublime': '',
        'notepad': '',
        'atom': ''
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
            return jsonify({'success': False, 'message': 'No settings provided'}), 400
            
        # Update settings (basic validation)
        for key, value in new_settings.items():
            if key in settings_data:
                settings_data[key] = value
                
        return jsonify({
            'success': True,
            'message': 'Settings updated successfully',
            'data': settings_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error updating settings: {str(e)}'
        }), 500

@app.route('/api/file-dialog/folder', methods=['GET'])
def get_folder_dialog():
    """Open Windows folder selection dialog."""
    try:
        folder_path = open_folder_dialog_hybrid()
        
        print(f"DEBUG: Folder dialog returned: '{folder_path}'")  # Debug log
        
        return jsonify({
            'success': True,
            'path': folder_path
        })
    except Exception as e:
        print(f"DEBUG: Folder dialog error: {e}")  # Debug log
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
    except Exception as e:
        print(f"DEBUG: File dialog error: {e}")  # Debug log
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
    is_wsl = 'microsoft' in os.uname().release.lower() if hasattr(os, 'uname') else False

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
    except (RuntimeError, ImportError, OSError) as e:
        print(f"⚠️  PyWebView not available: {e}")
        print("🌐 Starting in web server mode only...")
        print("📱 Open your browser at: http://127.0.0.1:5000")
        print("🛑 Press Ctrl+C to stop")

        # Start Flask in main mode
        app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()
