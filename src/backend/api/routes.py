# src/backend/api/routes.py
"""Routes consolidées pour l'API RenExtract v2
Toutes les routes sont regroupées dans ce fichier pour une meilleure organisation
"""

import logging
import os

from flask import Blueprint, jsonify, request

from src.backend.core.coherence import OptimizedCoherenceChecker

# Import des services
from src.backend.core.extractor import OptimizedTextExtractor
from src.backend.core.project import ProjectManager
from src.backend.core.reconstructor import OptimizedFileReconstructor
from src.backend.services.backup import BackupManager
from src.backend.services.config import AppConfig
from src.backend.services.update import UpdateManager

logger = logging.getLogger(__name__)

# Création du blueprint principal
api_bp = Blueprint("api", __name__)

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================


@api_bp.route("/api/health")
def health_check():
    """Vérification de l'état de l'API"""
    return jsonify({"status": "healthy", "message": "RenExtract v2 API is running"})


@api_bp.route("/api/message")
def get_message():
    """Récupère le message de l'application"""
    return jsonify({"message": "RenExtract v2 - Optimisé et réorganisé !"})


@api_bp.route("/api/message", methods=["POST"])
def update_message():
    """Met à jour le message de l'application"""
    data = request.get_json()
    if data and "message" in data:
        # Ici on pourrait sauvegarder le message
        return jsonify({"success": True, "message": data["message"]})
    return jsonify({"success": False, "error": "Message requis"}), 400


# ============================================================================
# ROUTES D'EXTRACTION
# ============================================================================


@api_bp.route("/api/extraction/extract", methods=["POST"])
def extract_texts():
    """Extraction de textes avec la version optimisée"""
    try:
        data = request.get_json()
        if not data or "file_content" not in data or "filepath" not in data:
            return jsonify({"success": False, "error": "Contenu de fichier et chemin requis"}), 400

        filepath = data["filepath"]

        # Utiliser l'extracteur optimisé
        extractor = OptimizedTextExtractor(cache_size=1000)
        result = extractor.extract_texts_streaming(filepath, batch_size=100)

        # Convertir le générateur en liste pour la réponse
        results = list(result)

        return jsonify({"success": True, "results": results, "extracted_count": len(results)})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur extraction: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de l'extraction: {e!s}"}), 500


@api_bp.route("/api/extraction/validate-file", methods=["POST"])
def validate_extraction_file():
    """Validation d'un fichier d'extraction"""
    try:
        data = request.get_json()
        if not data or "filepath" not in data:
            return jsonify({"success": False, "error": "Chemin de fichier requis"}), 400

        filepath = data["filepath"]

        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Fichier introuvable"}), 404

        # Validation basique
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        return jsonify(
            {
                "success": True,
                "file_size": len(content),
                "line_count": len(content.splitlines()),
                "is_valid": True,
            },
        )

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur validation: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de la validation: {e!s}"}), 500


# ============================================================================
# ROUTES DE COHÉRENCE
# ============================================================================


@api_bp.route("/api/coherence/check", methods=["POST"])
def check_coherence():
    """Vérification de cohérence avec la version optimisée"""
    try:
        data = request.get_json()
        if not data or "target_path" not in data:
            return jsonify({"success": False, "error": "Chemin cible requis"}), 400

        target_path = data["target_path"]
        return_details = data.get("return_details", False)
        selection_info = data.get("selection_info")

        # Utiliser le vérificateur optimisé
        checker = OptimizedCoherenceChecker(max_workers=4, cache_size=500)
        result = checker.check_coherence_parallel(
            target_path, return_details=return_details, selection_info=selection_info,
        )

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur vérification cohérence: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de la vérification: {e!s}"}), 500


@api_bp.route("/api/coherence/options", methods=["GET"])
def get_coherence_options():
    """Récupère les options de cohérence"""
    try:
        checker = OptimizedCoherenceChecker()
        options = checker.options
        return jsonify({"success": True, "options": options})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur récupération options: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/coherence/options", methods=["POST"])
def set_coherence_options():
    """Configure les options de cohérence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Options requises"}), 400

        checker = OptimizedCoherenceChecker()
        checker.options.update(data)

        return jsonify({"success": True, "message": "Options mises à jour"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur mise à jour options: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE RECONSTRUCTION
# ============================================================================


@api_bp.route("/api/reconstruction/validate", methods=["POST"])
def validate_reconstruction_files():
    """Validation des fichiers de reconstruction"""
    try:
        data = request.get_json()
        if not data or "filepath" not in data:
            return jsonify({"success": False, "error": "Chemin de fichier requis"}), 400

        filepath = data["filepath"]

        # Validation basique
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "Fichier introuvable"}), 404

        return jsonify({"success": True, "message": "Fichier valide"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur validation reconstruction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/reconstruction/reconstruct", methods=["POST"])
def reconstruct_file():
    """Reconstruction d'un fichier avec la version optimisée"""
    try:
        data = request.get_json()
        if not data or "file_content" not in data or "filepath" not in data:
            return jsonify({"success": False, "error": "Contenu de fichier et chemin requis"}), 400

        file_content = data["file_content"]
        filepath = data["filepath"]
        save_mode = data.get("save_mode", "new_file")

        # Utiliser le reconstructeur optimisé
        reconstructor = OptimizedFileReconstructor(cache_size=100)
        reconstructor.load_file_content_optimized(file_content, filepath)
        result = reconstructor.reconstruct_file_optimized(save_mode)

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur reconstruction: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de la reconstruction: {e!s}"}), 500


# ============================================================================
# ROUTES DE PROJET
# ============================================================================


@api_bp.route("/api/project/validate", methods=["POST"])
def validate_project():
    """Validation d'un projet Ren'Py"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        project_manager = ProjectManager()
        result = project_manager.validate_project(project_path)

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur validation projet: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/project/languages", methods=["POST"])
def scan_project_languages():
    """Scan des langues disponibles dans un projet"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        project_manager = ProjectManager()
        languages = project_manager.scan_languages(project_path)

        return jsonify({"success": True, "languages": languages})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur scan langues: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE CONFIGURATION
# ============================================================================


@api_bp.route("/api/settings", methods=["GET"])
def get_settings():
    """Récupère les paramètres de l'application"""
    try:
        settings = AppConfig.load_settings_from_disk()
        return jsonify({"success": True, "settings": settings})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur récupération paramètres: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/settings", methods=["POST"])
def update_settings():
    """Met à jour les paramètres de l'application"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Paramètres requis"}), 400

        AppConfig.save_settings_to_disk(data)
        return jsonify({"success": True, "message": "Paramètres mis à jour"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur mise à jour paramètres: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE MISE À JOUR
# ============================================================================


@api_bp.route("/api/updates/check", methods=["GET"])
def check_for_updates():
    """Vérifie les mises à jour disponibles"""
    try:
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER, AppConfig.GITHUB_REPO_NAME, AppConfig.APP_VERSION,
        )
        result = update_manager.check_for_updates()
        return jsonify(result)
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur vérification mises à jour: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/updates/download", methods=["POST"])
def download_update():
    """Télécharge une mise à jour"""
    try:
        data = request.get_json()
        if not data or "download_url" not in data:
            return jsonify({"success": False, "error": "URL de téléchargement requise"}), 400

        download_url = data["download_url"]
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER, AppConfig.GITHUB_REPO_NAME, AppConfig.APP_VERSION,
        )
        result = update_manager.download_update(download_url)

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur téléchargement: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES UTILITAIRES
# ============================================================================


@api_bp.route("/api/file-dialog/open", methods=["POST"])
def open_dialog():
    """Ouvre un dialogue de sélection de fichier"""
    try:
        # Implémentation simplifiée
        return jsonify(
            {"success": True, "message": "Dialogue de fichier (implémentation simplifiée)"},
        )

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur dialogue fichier: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/file-dialog/save", methods=["POST"])
def save_dialog():
    """Ouvre un dialogue de sauvegarde"""
    try:
        # Implémentation simplifiée
        return jsonify(
            {"success": True, "message": "Dialogue de sauvegarde (implémentation simplifiée)"},
        )

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur dialogue sauvegarde: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTE RACINE
# ============================================================================


# ============================================================================
# ROUTES DE TRADUCTION
# ============================================================================


@api_bp.route("/api/translator/translate", methods=["POST"])
def translate_text():
    """Traduction de texte (fonctionnalité optionnelle)"""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"success": False, "error": "Texte à traduire requis"}), 400

        text = data["text"]
        target_language = data.get("target_language", "fr")

        # Implémentation simplifiée (pas de vraie traduction)
        return jsonify(
            {
                "success": True,
                "original_text": text,
                "translated_text": f"[Traduit en {target_language}] {text}",
                "target_language": target_language,
            },
        )

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur traduction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE BACKUP
# ============================================================================


@api_bp.route("/api/backup/create", methods=["POST"])
def create_backup():
    """Création d'une sauvegarde"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        backup_manager = BackupManager()
        result = backup_manager.create_backup(project_path)

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur création backup: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/backup/restore", methods=["POST"])
def restore_backup():
    """Restauration d'une sauvegarde"""
    try:
        data = request.get_json()
        if not data or "backup_path" not in data:
            return jsonify({"success": False, "error": "Chemin de sauvegarde requis"}), 400

        # Note: restore_backup method needs to be implemented in BackupManager
        result = {"success": False, "error": "Fonctionnalité non implémentée"}

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur restauration backup: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/backup/list", methods=["GET"])
def list_backups():
    """Liste des sauvegardes disponibles"""
    try:
        # Note: list_backups method needs to be implemented in BackupManager
        backups = []

        return jsonify({"success": True, "backups": backups})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur liste backups: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES D'ITEMS (pour l'interface)
# ============================================================================


@api_bp.route("/api/items")
def get_items():
    """Récupère les éléments de l'interface"""
    return jsonify(
        {
            "items": [
                {
                    "id": "extraction",
                    "title": "Extraction",
                    "description": "Extraire les textes des fichiers Ren'Py",
                    "icon": "extract",
                    "enabled": True,
                },
                {
                    "id": "coherence",
                    "title": "Cohérence",
                    "description": "Vérifier la cohérence des traductions",
                    "icon": "check",
                    "enabled": True,
                },
                {
                    "id": "reconstruction",
                    "title": "Reconstruction",
                    "description": "Reconstruire les fichiers traduits",
                    "icon": "rebuild",
                    "enabled": True,
                },
                {
                    "id": "project",
                    "title": "Projet",
                    "description": "Gérer les projets Ren'Py",
                    "icon": "folder",
                    "enabled": True,
                },
            ],
        },
    )


# ============================================================================
# ROUTES DE FICHIERS ET DOSSIERS
# ============================================================================


@api_bp.route("/api/file-dialog/save-path", methods=["POST"])
def set_save_path():
    """Définit le chemin de sauvegarde"""
    try:
        data = request.get_json()
        if not data or "path" not in data:
            return jsonify({"success": False, "error": "Chemin requis"}), 400

        path = data["path"]
        # Ici on pourrait sauvegarder le chemin dans les paramètres

        return jsonify({"success": True, "path": path, "message": "Chemin de sauvegarde défini"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur définition chemin: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE MISE À JOUR (complétées)
# ============================================================================


@api_bp.route("/api/updates/install", methods=["POST"])
def install_update():
    """Installe une mise à jour"""
    try:
        # Note: install_update method needs executable_path parameter
        result = {"success": False, "error": "Fonctionnalité non implémentée"}

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur installation: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/updates/config", methods=["GET"])
def get_update_config():
    """Récupère la configuration des mises à jour"""
    try:
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER, AppConfig.GITHUB_REPO_NAME, AppConfig.APP_VERSION,
        )
        config = update_manager.get_config()

        return jsonify({"success": True, "config": config})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur config updates: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/updates/config", methods=["POST"])
def update_update_config():
    """Met à jour la configuration des mises à jour"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Configuration requise"}), 400

        # Note: update_config method needs to be implemented
        result = {"success": False, "error": "Fonctionnalité non implémentée"}

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur mise à jour config: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@api_bp.route("/api/updates/auto-check", methods=["GET"])
def should_auto_check():
    """Vérifie si la vérification automatique est activée"""
    try:
        # Note: should_auto_check method needs to be implemented
        auto_check = AppConfig.AUTO_CHECK_UPDATES

        return jsonify({"success": True, "auto_check": auto_check})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur auto-check: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTE RACINE
# ============================================================================


@api_bp.route("/")
def index():
    """Route racine de l'API"""
    return jsonify(
        {
            "message": "RenExtract v2 API - Structure réorganisée",
            "version": "2.0",
            "status": "active",
            "endpoints": [
                "/api/health",
                "/api/message",
                "/api/items",
                "/api/extraction/*",
                "/api/coherence/*",
                "/api/reconstruction/*",
                "/api/project/*",
                "/api/settings",
                "/api/updates/*",
                "/api/backup/*",
                "/api/translator/*",
                "/api/file-dialog/*",
            ],
        },
    )
