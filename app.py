#!/usr/bin/env python3
"""
Main application using pywebview with Flask backend
Structure réorganisée - Version 2.0
"""
import os
import sys
import threading
import time
from pathlib import Path

import webview
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

# Import de la nouvelle structure réorganisée
from src.backend.services.backup import BackupManager
from src.backend.services.config import AppConfig
from src.backend.api.routes import api_bp

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

        if created_folders:
            print(f"📁 Dossiers créés: {', '.join(created_folders)}")

        return base_dir

    except (OSError, IOError) as e:
        print(f"❌ Erreur création dossiers: {e}")
        return None


def get_static_path():
    """Détermine le chemin vers les fichiers statiques"""
    if getattr(sys, 'frozen', False):
        # Mode exécutable (build)
        # pylint: disable=protected-access
        static_path = Path(sys._MEIPASS) / 'dist'
    else:
        # Mode développement
        static_path = Path('dist')
    return str(static_path)


# Initialisation de l'application
app_base_dir = initialize_application_folders()

# Flask configuration
app = Flask(__name__, static_folder=get_static_path(), static_url_path='')
CORS(app)

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
    print("   Veuillez configurer les variables d'environnement ou \
    modifier src/backend/services/config.py")

# Enregistrer le blueprint principal consolidé
app.register_blueprint(api_bp)


def start_flask():
    """Démarre le serveur Flask"""
    app.run(host=AppConfig.FLASK_HOST, port=AppConfig.FLASK_PORT,
            debug=AppConfig.FLASK_DEBUG)


def main():
    """Fonction principale de l'application"""
    print("🚀 Démarrage de RenExtract v2 - Structure réorganisée")
    print("=" * 50)

    # Démarrer Flask dans un thread séparé
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()

    # Attendre que Flask démarre
    time.sleep(2)

    # Démarrer l'interface webview
    webview.create_window(
        'RenExtract v2',
        f'http://{AppConfig.FLASK_HOST}:{AppConfig.FLASK_PORT}',
        width=1200,
        height=800,
        resizable=True,
        min_size=(800, 600)
    )

    webview.start(debug=AppConfig.FLASK_DEBUG)


if __name__ == '__main__':
    main()
