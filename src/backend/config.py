#!/usr/bin/env python3
"""
Configuration de l'application
"""
import os
from pathlib import Path


class AppConfig:
    """Configuration de l'application"""

    # Configuration GitHub pour les mises à jour
    GITHUB_REPO_OWNER = os.getenv('GITHUB_REPO_OWNER', 'Rory-Mercury-91')
    GITHUB_REPO_NAME = os.getenv('GITHUB_REPO_NAME', 'renextract-v2')

    # Version de l'application (doit correspondre à package.json)
    APP_VERSION = os.getenv('APP_VERSION', '0.9.0')

    # Configuration des mises à jour
    UPDATE_CHECK_INTERVAL_HOURS = int(
        os.getenv('UPDATE_CHECK_INTERVAL_HOURS', '24'))
    AUTO_CHECK_UPDATES = os.getenv(
        'AUTO_CHECK_UPDATES', 'true').lower() == 'true'
    AUTO_DOWNLOAD_UPDATES = os.getenv(
        'AUTO_DOWNLOAD_UPDATES', 'false').lower() == 'true'
    AUTO_INSTALL_UPDATES = os.getenv(
        'AUTO_INSTALL_UPDATES', 'false').lower() == 'true'

    # Configuration de l'application
    APP_NAME = "RenExtract"
    APP_DESCRIPTION = "Outil d'extraction et de reconstruction pour les jeux Ren'Py"

    # Chemins des dossiers
    BASE_DIR = Path(__file__).parent.parent.parent
    CONFIG_DIR = BASE_DIR / "04_Configs"
    BACKUP_DIR = BASE_DIR / "03_Backups"
    REPORTS_DIR = BASE_DIR / "02_Reports"
    TEMP_DIR = BASE_DIR / "01_Temporary"

    # Configuration Flask
    FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Configuration PyWebView
    WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
    WINDOW_WIDTH = int(os.getenv('WINDOW_WIDTH', '1300'))
    WINDOW_HEIGHT = int(os.getenv('WINDOW_HEIGHT', '815'))
    WINDOW_MIN_WIDTH = int(os.getenv('WINDOW_MIN_WIDTH', '700'))
    WINDOW_MIN_HEIGHT = int(os.getenv('WINDOW_MIN_HEIGHT', '500'))

    @classmethod
    def get_github_release_url(cls) -> str:
        """Retourne l'URL de l'API GitHub pour les releases"""
        return (f"https://api.github.com/repos/"
                f"{cls.GITHUB_REPO_OWNER}/{cls.GITHUB_REPO_NAME}/releases")

    @classmethod
    def get_github_latest_release_url(cls) -> str:
        """Retourne l'URL de l'API GitHub pour la dernière release"""
        return f"{cls.get_github_release_url()}/latest"

    @classmethod
    def get_github_repo_url(cls) -> str:
        """Retourne l'URL du dépôt GitHub"""
        return f"https://github.com/{cls.GITHUB_REPO_OWNER}/{cls.GITHUB_REPO_NAME}"

    @classmethod
    def ensure_directories(cls):
        """Crée les dossiers nécessaires s'ils n'existent pas"""
        directories = [
            cls.CONFIG_DIR,
            cls.BACKUP_DIR,
            cls.REPORTS_DIR,
            cls.TEMP_DIR
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls) -> list:
        """Valide la configuration et retourne une liste d'erreurs"""
        errors = []

        # Vérifier les informations GitHub
        if cls.GITHUB_REPO_OWNER == 'votre-username':
            errors.append(
                "GITHUB_REPO_OWNER doit être configuré avec votre nom d'utilisateur GitHub")

        # Note: renextract-v2 est maintenant un nom valide par défaut
        # if cls.GITHUB_REPO_NAME == 'renextract-v2':
        #     errors.append(
        #         "GITHUB_REPO_NAME doit être configuré avec le nom de votre dépôt")

        # Vérifier la version
        if not cls.APP_VERSION or cls.APP_VERSION == '2.0.0':
            errors.append(
                "APP_VERSION doit être configurée avec la version actuelle de votre application")

        return errors
