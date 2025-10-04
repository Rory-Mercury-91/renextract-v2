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
from src.dialogs.hybrid_dialog import open_folder_dialog_hybrid, open_file_dialog_hybrid

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
            print(f"DEBUG: Created {len(created_folders)} new folders: {created_folders}")
        else:
            print("DEBUG: All folders already exist")
        
        return base_dir
        
    except Exception as e:
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
from src.backend.backup_manager import BackupManager

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
        from pathlib import Path
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
            except Exception as e:
                print(f"DEBUG: Failed to create target directory: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Impossible de créer le répertoire de destination: {target_dir}'
                }), 400
        
        # Copier le fichier vers la destination
        import shutil
        print(f"DEBUG: Copying from {backup['backup_path']} to {target_path}")
        shutil.copy2(backup['backup_path'], target_path)
        
        print(f"DEBUG: Restore successful")
        return jsonify({
            'success': True,
            'message': f'Fichier restauré vers {target_path}'
        })
        
    except Exception as e:
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

@app.route('/api/quit', methods=['POST'])
def quit_application():
    """Quit the application"""
    try:
        # Fermer l'application PyWebView
        import threading
        def close_app():
            time.sleep(0.5)  # Petit délai pour laisser la réponse se terminer
            if 'webview' in globals():
                webview.destroy_window()
            else:
                import sys
                sys.exit(0)
        
        # Lancer la fermeture dans un thread séparé
        threading.Thread(target=close_app, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': 'Application fermée'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


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
        # Détecter WSL
        is_wsl = False
        try:
            if hasattr(os, 'uname'):
                is_wsl = 'microsoft' in os.uname().release.lower()
            is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
        except:
            is_wsl = False
        
        if is_wsl:
            # En WSL, retourner un message indiquant qu'il faut utiliser l'endpoint POST
            return jsonify({
                'success': False,
                'error': 'WSL_MODE',
                'message': 'En mode WSL, utilisez POST /api/file-dialog/folder avec le chemin en paramètre'
            }), 400
        
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
    except Exception as e:
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
    except Exception as e:
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
        
        print(f"DEBUG: Save dialog params - title: {title}, initialfile: {initialfile}, defaultextension: {defaultextension}")
        
        # Détecter WSL
        is_wsl = False
        try:
            if hasattr(os, 'uname'):
                is_wsl = 'microsoft' in os.uname().release.lower()
            is_wsl = is_wsl or 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ
        except:
            is_wsl = False
        
        if is_wsl:
            # En WSL, retourner une erreur indiquant qu'il faut utiliser l'endpoint POST avec le chemin
            return jsonify({
                'success': False,
                'error': 'WSL_MODE',
                'message': 'En mode WSL, le dialogue de sauvegarde n\'est pas disponible. Utilisez POST /api/file-dialog/save avec le chemin en paramètre'
            }), 400
        
        # En mode normal, utiliser le dialogue natif
        from src.dialogs.hybrid_dialog import open_save_dialog_hybrid
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
        
    except Exception as e:
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
    except Exception as e:
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
    except:
        is_wsl = False

    # Debug information
    print(f"DEBUG: is_wsl = {is_wsl}")
    print(f"DEBUG: platform = {sys.platform}")
    print(f"DEBUG: frozen = {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        print(f"DEBUG: _MEIPASS = {sys._MEIPASS}")
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
    except (RuntimeError, ImportError, OSError) as e:
        print(f"⚠️  PyWebView not available: {e}")
        print("🌐 Starting in web server mode only...")
        print("📱 Open your browser at: http://127.0.0.1:5000")
        print("🛑 Press Ctrl+C to stop")

        # Start Flask in main mode
        app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()
