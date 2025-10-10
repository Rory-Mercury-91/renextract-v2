#!/usr/bin/env python3
"""Configuration de l'application"""

import json
import os
from pathlib import Path
from typing import ClassVar


class AppConfig:
    """Configuration de l'application"""

    # Configuration par défaut
    DEFAULT_SETTINGS: ClassVar[dict] = {
        "language": "fr",
        "theme": "auto",
        "debugActive": False,  # false=Level 3, true=Level 4
        "translatorFeature": False,
        "autoOpenings": {"files": True, "folders": True, "reports": True, "outputField": False},
        "externalTools": {"textEditor": "VS Code", "translator": ""},
        "paths": {"renpySdk": "", "editor": ""},
        "folders": {
            "temporary": "01_Temporary/",
            "reports": "02_Reports/",
            "backups": "03_Backups/",
            "configs": "04_Configs/",
        },
        "extraction": {
            "placeholderFormat": "PLACEHOLDER_{n}",
            "encoding": "UTF-8",
            "detectDuplicates": True,
            "projectProgressTracking": False,
            "lineLimit": 1000,
            "defaultSaveMode": "new_file",
            "patterns": {
                "code": "RENPY_CODE_001",
                "asterisk": "RENPY_ASTERISK_001",
                "tilde": "RENPY_TILDE_001",
            },
        },
        "reconstruction": {"saveMode": "new_file"},
        "coherence": {
            "checkVariables": True,
            "checkTags": True,
            "checkUntranslated": True,
            "checkEscapeSequences": True,
            "checkPercentages": True,
            "checkQuotations": True,
            "checkParentheses": True,
            "checkSyntax": True,
            "checkDeeplEllipsis": True,
            "checkIsolatedPercent": True,
            "checkFrenchQuotes": True,
            "checkDoubleDashEllipsis": True,
            "checkSpecialCodes": False,
            "checkLineStructure": True,
            "customExclusions": [
                "OK",
                "Menu",
                "Continue",
                "Yes",
                "No",
                "Level",
                "???",
                "!!!",
                "...",
            ],
        },
        "lastProject": {"path": "", "language": "", "mode": "project"},
    }

    # Configuration GitHub pour les mises à jour
    GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER", "Rory-Mercury-91")
    GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME", "renextract-v2")

    # Version de l'application (doit correspondre à package.json)
    APP_VERSION = os.getenv("APP_VERSION", "0.9.0")

    # Configuration des mises à jour
    UPDATE_CHECK_INTERVAL_HOURS = int(os.getenv("UPDATE_CHECK_INTERVAL_HOURS", "24"))
    AUTO_CHECK_UPDATES = os.getenv("AUTO_CHECK_UPDATES", "true").lower() == "true"
    AUTO_DOWNLOAD_UPDATES = os.getenv("AUTO_DOWNLOAD_UPDATES", "false").lower() == "true"
    AUTO_INSTALL_UPDATES = os.getenv("AUTO_INSTALL_UPDATES", "false").lower() == "true"

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
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Configuration PyWebView
    WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"
    WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1300"))
    WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "815"))
    WINDOW_MIN_WIDTH = int(os.getenv("WINDOW_MIN_WIDTH", "700"))
    WINDOW_MIN_HEIGHT = int(os.getenv("WINDOW_MIN_HEIGHT", "500"))

    @classmethod
    def get_github_release_url(cls) -> str:
        """Retourne l'URL de l'API GitHub pour les releases"""
        return (
            f"https://api.github.com/repos/{cls.GITHUB_REPO_OWNER}/{cls.GITHUB_REPO_NAME}/releases"
        )

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
        directories = [cls.CONFIG_DIR, cls.BACKUP_DIR, cls.REPORTS_DIR, cls.TEMP_DIR]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @classmethod
    def validate_config(cls) -> list:
        """Valide la configuration et retourne une liste d'erreurs"""
        errors = []

        # Vérifier les informations GitHub
        if cls.GITHUB_REPO_OWNER == "votre-username":
            errors.append(
                "GITHUB_REPO_OWNER doit être configuré avec votre nom d'utilisateur GitHub",
            )

        # Note: renextract-v2 est maintenant un nom valide par défaut
        # if cls.GITHUB_REPO_NAME == 'renextract-v2':
        #     errors.append(
        #         "GITHUB_REPO_NAME doit être configuré avec le nom de votre dépôt")

        # Vérifier la version
        if not cls.APP_VERSION or cls.APP_VERSION == "2.0.0":
            errors.append(
                "APP_VERSION doit être configurée avec la version actuelle de votre application",
            )

        return errors

    @staticmethod
    def get_default_settings():
        """Récupère les paramètres par défaut"""
        return AppConfig.DEFAULT_SETTINGS.copy()

    @staticmethod
    def load_settings_from_disk(app_base_dir=None):
        """Charge les paramètres depuis le disque"""

        settings_file_path = Path(app_base_dir or ".") / "04_Configs" / "app_settings.json"
        settings = AppConfig.get_default_settings()

        try:
            if settings_file_path.exists():
                with open(settings_file_path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        # Mise à jour superficielle (shallow merge)
                        for key, value in data.items():
                            if (
                                key in settings
                                and isinstance(settings[key], dict)
                                and isinstance(value, dict)
                            ):
                                settings[key].update(value)
                            else:
                                settings[key] = value
        except (OSError, json.JSONDecodeError) as e:
            print(f"DEBUG: Failed to load settings: {e}")

        return settings

    @staticmethod
    def save_settings_to_disk(settings, app_base_dir=None):
        """Sauvegarde les paramètres sur le disque"""

        settings_file_path = Path(app_base_dir or ".") / "04_Configs" / "app_settings.json"

        try:
            settings_file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(settings_file_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except OSError as e:
            print(f"DEBUG: Failed to save settings: {e}")

    @staticmethod
    def sanitize_settings_payload(payload):
        """Nettoie et valide les paramètres reçus"""
        if not isinstance(payload, dict):
            return {}

        # Clés autorisées
        allowed_keys = {
            "language",
            "theme",
            "debugActive",
            "translatorFeature",
            "autoOpenings",
            "externalTools",
            "paths",
            "folders",
            "extraction",
            "reconstruction",
            "coherence",
            "lastProject",
        }

        # Filtrer les clés autorisées
        sanitized = {k: v for k, v in payload.items() if k in allowed_keys}

        # Validation des types
        if "language" in sanitized and not isinstance(sanitized["language"], str):
            del sanitized["language"]
        if "theme" in sanitized and not isinstance(sanitized["theme"], str):
            del sanitized["theme"]
        if "debugActive" in sanitized and not isinstance(sanitized["debugActive"], bool):
            del sanitized["debugActive"]
        if "translatorFeature" in sanitized and not isinstance(
            sanitized["translatorFeature"],
            bool,
        ):
            del sanitized["translatorFeature"]

        return sanitized
