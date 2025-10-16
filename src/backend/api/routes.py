# src/backend/api/routes.py
"""Routes consolidées pour l'API RenExtract v2
Toutes les routes sont regroupées dans ce fichier pour une meilleure organisation
"""

import logging
import os
import platform
import subprocess
import tkinter as tk
from collections import defaultdict
from tkinter import filedialog

from flask import Blueprint, current_app, jsonify, request, send_from_directory

from src.backend.core.coherence import CoherenceChecker

# Import des services
from src.backend.core.extractor import TextExtractor
from src.backend.core.project import ProjectManager
from src.backend.core.reconstructor import FileReconstructor
from src.backend.services.backup import BackupManager
from src.backend.services.config import AppConfig
from src.backend.services.translator import translator_service
from src.backend.services.update import UpdateManager

logger = logging.getLogger(__name__)

# Création du blueprint principal
API = Blueprint("api", __name__)

# ============================================================================
# ROUTES PRINCIPALES
# ============================================================================


@API.route("/api/health")
def health_check():
    """Vérification de l'état de l'API"""
    return jsonify({"status": "healthy", "message": "RenExtract v2 API is running"})


# ============================================================================
# ROUTES D'EXTRACTION
# ============================================================================


@API.route("/api/extraction/extract", methods=["POST"])
def extract_texts():
    """Extraction de textes"""
    try:
        data = request.get_json()
        if not data or "file_content" not in data or "filepath" not in data:
            return jsonify({"success": False, "error": "Contenu de fichier et chemin requis"}), 400

        filepath = data["filepath"]

        # Utiliser l'extracteur
        extractor = TextExtractor(cache_size=1000)
        result = extractor.extract_texts_streaming(filepath, batch_size=100)

        # Convertir le générateur en liste pour la réponse
        results = list(result)

        return jsonify({"success": True, "results": results, "extracted_count": len(results)})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur extraction: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de l'extraction: {e!s}"}), 500


@API.route("/api/extraction/validate-file", methods=["POST"])
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


@API.route("/api/extraction/get-settings", methods=["GET"])
def get_extraction_settings():
    """Récupère les paramètres d'extraction"""
    try:
        # Charger les paramètres depuis la configuration
        settings = AppConfig.load_settings_from_disk()
        extraction_settings = settings.get("extraction", {})

        # Paramètres par défaut
        default_settings = {
            "detect_duplicates": True,
            "code_prefix": "code",
            "asterisk_prefix": "asterisk",
            "tilde_prefix": "tilde",
            "empty_prefix": "empty",
        }

        # Fusionner avec les paramètres par défaut
        final_settings = {**default_settings, **extraction_settings}

        return jsonify({"success": True, "settings": final_settings})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur récupération paramètres extraction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/extraction/set-settings", methods=["POST"])
def set_extraction_settings():
    """Met à jour les paramètres d'extraction"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Paramètres requis"}), 400

        # Charger les paramètres actuels
        current_settings = AppConfig.load_settings_from_disk()

        # Mettre à jour les paramètres d'extraction
        if "extraction" not in current_settings:
            current_settings["extraction"] = {}

        current_settings["extraction"].update(data)

        # Sauvegarder
        AppConfig.save_settings_to_disk(current_settings)

        return jsonify({"success": True, "message": "Paramètres d'extraction mis à jour"})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur mise à jour paramètres extraction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/extraction/open-file", methods=["POST"])
def open_extraction_file():
    """Ouvre un fichier dans l'éditeur externe configuré"""
    try:
        data = request.get_json()
        logger.info("🔍 open_extraction_file - Données reçues: %s", data)

        if not data or "filepath" not in data:
            logger.error("❌ open_extraction_file - Chemin de fichier manquant")
            return jsonify({"success": False, "error": "Chemin de fichier requis"}), 400

        filepath = data["filepath"]
        line_number = data.get("line_number", None)

        logger.info("🔍 open_extraction_file - Chemin: %s, Ligne: %s", filepath, line_number)

        # Convertir le chemin Windows en chemin Linux si nécessaire
        if filepath.startswith("B:\\"):
            # Essayer différentes conversions WSL
            possible_paths = [
                # Conversion standard WSL
                filepath.replace("B:\\", "/mnt/b/").replace("\\", "/"),
                # Conversion alternative
                filepath.replace("B:\\", "/mnt/c/").replace("\\", "/"),
                # Chemin direct Windows (pour certains environnements)
                filepath,
            ]

            logger.info("🔍 open_extraction_file - Tentative de conversion du chemin: %s", filepath)

            # Tester chaque chemin possible
            for test_path in possible_paths:
                if os.path.exists(test_path):
                    filepath = test_path
                    logger.info("✅ open_extraction_file - Chemin trouvé: %s", filepath)
                    break
            else:
                # Aucun chemin n'existe, utiliser le premier et laisser l'erreur se produire
                filepath = possible_paths[0]
                logger.warning(
                    "⚠️ open_extraction_file - Aucun chemin valide trouvé, utilisation: %s",
                    filepath,
                )

        # Vérifier que le fichier existe
        if not os.path.exists(filepath):
            logger.error("❌ open_extraction_file - Fichier introuvable: %s", filepath)
            return jsonify({"success": False, "error": f"Fichier introuvable: {filepath}"}), 404

        # Charger les paramètres pour récupérer le chemin de l'éditeur configuré
        settings = AppConfig.load_settings_from_disk()
        editor_path = settings.get("paths", {}).get("editor", "")
        logger.info("🔍 open_extraction_file - Chemin éditeur configuré: %s", editor_path)

        # Construire la commande selon l'éditeur configuré
        system = platform.system()
        cmd = None
        editor_name = "éditeur par défaut"

        if editor_path and os.path.exists(editor_path):
            # Utiliser l'éditeur configuré
            cmd = [editor_path, filepath]
            editor_name = os.path.basename(editor_path)
            logger.info(
                "✅ open_extraction_file - Utilisation de l'éditeur configuré: %s", editor_path
            )

            # Ajouter le numéro de ligne si l'éditeur le supporte
            if line_number:
                # Détecter le type d'éditeur par le nom de l'exécutable
                editor_basename = os.path.basename(editor_path).lower()
                if "code" in editor_basename:  # VS Code
                    cmd.extend(["--goto", f"{filepath}:{line_number}"])
                elif "subl" in editor_basename or "sublime" in editor_basename:  # Sublime Text
                    cmd.extend([f"{filepath}:{line_number}"])
                # Pour les autres éditeurs, le numéro de ligne sera ignoré
        else:
            # Utiliser l'éditeur par défaut du système
            logger.warning(
                "⚠️ open_extraction_file - Aucun éditeur configuré ou chemin invalide, \
                  utilisation de l'éditeur par défaut"
            )
            if system == "Windows":
                cmd = ["notepad", filepath]
            elif system == "Darwin":  # macOS
                cmd = ["open", "-t", filepath]
            else:  # Linux
                cmd = ["xdg-open", filepath]

        # Exécuter la commande
        try:
            subprocess.Popen(cmd, shell=False)
            message = f"Fichier ouvert avec {editor_name}"
            if line_number and editor_name not in ["code", "subl"]:
                message += f" (numéro de ligne {line_number} ignoré)"
            return jsonify({"success": True, "message": message})
        except FileNotFoundError:
            logger.warning(
                "⚠️ Éditeur %s non trouvé, tentative avec l'éditeur par défaut", editor_name
            )

            # Fallback vers l'éditeur par défaut du système
            try:
                if system == "Windows":
                    fallback_cmd = ["notepad", filepath]
                elif system == "Darwin":  # macOS
                    fallback_cmd = ["open", "-t", filepath]
                else:  # Linux
                    fallback_cmd = ["xdg-open", filepath]

                subprocess.Popen(fallback_cmd, shell=False)
                message = (
                    f"Fichier ouvert avec l'éditeur par défaut du système "
                    f"(éditeur {editor_name} non trouvé)"
                )
                if line_number:
                    message += f" (numéro de ligne {line_number} ignoré)"
                return jsonify({"success": True, "message": message})

            except (OSError, subprocess.SubprocessError, RuntimeError) as fallback_error:
                logger.error("❌ Échec du fallback: %s", fallback_error)
                return jsonify(
                    {
                        "success": False,
                        "error": (
                            f"Éditeur {editor_name} non trouvé et fallback échoué: {fallback_error}"
                        ),
                    }
                ), 400
        except (OSError, subprocess.SubprocessError, RuntimeError) as e:
            logger.error("❌ Erreur ouverture fichier: %s", e)
            return jsonify(
                {
                    "success": False,
                    "error": f"Erreur lors de l'ouverture du fichier: {e!s}",
                }
            ), 500

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur ouverture fichier: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE COHÉRENCE
# ============================================================================


# L'ancienne route /api/coherence/check a été supprimée
# Elle est remplacée par /api/coherence/check-svelte qui retourne du JSON structuré


@API.route("/api/coherence/check-svelte", methods=["POST"])
def check_coherence_svelte():
    """Vérification de cohérence pour l'interface Svelte"""
    try:
        data = request.get_json()
        if not data or "target_path" not in data:
            return jsonify({"success": False, "error": "Chemin cible requis"}), 400

        target_path = data["target_path"]

        # Utiliser le vérificateur
        checker = CoherenceChecker(max_workers=4, cache_size=500)

        # Lancer l'analyse et récupérer les détails
        result = checker.check_coherence_parallel(
            target_path,
            return_details=True,
        )

        # Extraire les données du résultat
        if isinstance(result, dict):
            all_issues = result.get("issues", [])
            stats = result.get("stats", {})
        else:
            all_issues = result
            stats = {}

        # Calculer les statistiques si pas déjà calculées
        if not stats:
            unique_files = {issue["file"] for issue in all_issues}
            stats = checker.calculate_statistics(all_issues, len(unique_files))

        # Grouper les problèmes par fichier
        issues_by_file = defaultdict(list)
        for issue in all_issues:
            issues_by_file[issue["file"]].append(issue)

        # Préparer la réponse structurée pour Svelte
        svelte_result = {
            "stats": {
                "total_issues": stats.get("total_issues", 0),
                "files_analyzed": stats.get("files_analyzed", 0),
                "issues_by_type": stats.get("issues_by_type", {}),
            },
            "issues_by_file": dict(issues_by_file),
            "target_path": target_path,
        }

        return jsonify({"success": True, "result": svelte_result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur vérification cohérence Svelte: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de la vérification: {e!s}"}), 500


@API.route("/api/coherence/options", methods=["GET"])
def get_coherence_options():
    """Récupère les options de cohérence"""
    try:
        checker = CoherenceChecker()
        options = checker.options
        return jsonify({"success": True, "options": options})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur récupération options: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/coherence/options", methods=["POST"])
def set_coherence_options():
    """Configure les options de cohérence"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Options requises"}), 400

        checker = CoherenceChecker()
        checker.options.update(data)

        return jsonify({"success": True, "message": "Options mises à jour"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur mise à jour options: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE RECONSTRUCTION
# ============================================================================


@API.route("/api/reconstruction/validate", methods=["POST"])
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


@API.route("/api/reconstruction/reconstruct", methods=["POST"])
def reconstruct_file():
    """Reconstruction d'un fichier"""
    try:
        data = request.get_json()
        if not data or "file_content" not in data or "filepath" not in data:
            return jsonify({"success": False, "error": "Contenu de fichier et chemin requis"}), 400

        file_content = data["file_content"]
        filepath = data["filepath"]
        save_mode = data.get("save_mode", "new_file")

        # Utiliser le reconstructeur
        reconstructor = FileReconstructor(cache_size=100)
        reconstructor.load_file_content(file_content, filepath)
        result = reconstructor.reconstruct_file(save_mode)

        return jsonify({"success": True, "result": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur reconstruction: %s", e)
        return jsonify({"success": False, "error": f"Erreur lors de la reconstruction: {e!s}"}), 500


# ============================================================================
# ROUTES DE PROJET
# ============================================================================


@API.route("/api/project/validate", methods=["POST"])
def validate_project():
    """Validation d'un projet Ren'Py"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        project_manager = ProjectManager()
        result = project_manager.validate_project(project_path)

        return jsonify({"success": True, "validation": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur validation projet: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/project/languages", methods=["POST"])
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


@API.route("/api/project/find-root", methods=["POST"])
def find_project_root():
    """Trouve la racine d'un projet Ren'Py à partir d'un sous-dossier"""
    try:
        data = request.get_json()
        if not data or "subdir_path" not in data:
            return jsonify({"success": False, "error": "Chemin de sous-dossier requis"}), 400

        subdir_path = data["subdir_path"]
        max_levels = data.get("max_levels", 10)

        project_manager = ProjectManager()
        root_path = project_manager.find_project_root(subdir_path, max_levels)

        if root_path:
            return jsonify({"success": True, "root_path": root_path})
        else:
            return jsonify({"success": False, "error": "Racine de projet non trouvée"})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur recherche racine projet: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/project/set-current", methods=["POST"])
def set_current_project():
    """Définit le projet courant"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        project_manager = ProjectManager()
        result = project_manager.set_current_project(project_path)

        return jsonify({"success": result})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur définition projet courant: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/project/summary", methods=["POST"])
def get_project_summary():
    """Obtient un résumé du projet"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        project_manager = ProjectManager()
        summary = project_manager.get_project_summary(project_path)

        return jsonify({"success": True, "summary": summary})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur résumé projet: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/project/files", methods=["POST"])
def get_project_files():
    """Obtient la liste des fichiers du projet"""
    try:
        data = request.get_json()
        if not data or "project_path" not in data:
            return jsonify({"success": False, "error": "Chemin de projet requis"}), 400

        project_path = data["project_path"]
        file_type = data.get("file_type", "all")
        language = data.get("language")
        project_manager = ProjectManager()
        files = project_manager.get_project_files(project_path, file_type, language)

        return jsonify({"success": True, "files": files})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur fichiers projet: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/project/load-file", methods=["POST"])
def load_project_file():
    """Charge le contenu d'un fichier de projet"""
    try:
        data = request.get_json()
        if not data or "filepath" not in data:
            return jsonify({"success": False, "error": "Chemin de fichier requis"}), 400

        filepath = data["filepath"]
        project_manager = ProjectManager()
        result = project_manager.load_file_content(filepath)

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur chargement fichier: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE CONFIGURATION
# ============================================================================


@API.route("/api/settings", methods=["GET"])
def get_settings():
    """Récupère les paramètres de l'application"""
    try:
        settings = AppConfig.load_settings_from_disk()
        return jsonify({"success": True, "settings": settings})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur récupération paramètres: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/settings", methods=["POST"])
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


@API.route("/api/updates/check", methods=["GET"])
def check_for_updates():
    """Vérifie les mises à jour disponibles"""
    try:
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER,
            AppConfig.GITHUB_REPO_NAME,
            AppConfig.APP_VERSION,
        )
        result = update_manager.check_for_updates()
        return jsonify(result)
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur vérification mises à jour: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/updates/download", methods=["POST"])
def download_update():
    """Télécharge une mise à jour"""
    try:
        data = request.get_json()
        if not data or "download_url" not in data:
            return jsonify({"success": False, "error": "URL de téléchargement requise"}), 400

        download_url = data["download_url"]
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER,
            AppConfig.GITHUB_REPO_NAME,
            AppConfig.APP_VERSION,
        )
        result = update_manager.download_update(download_url)

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur téléchargement: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES UTILITAIRES
# ============================================================================


def is_wsl_environment():
    """Détecte si on est dans un environnement WSL"""
    try:
        # Vérifier la présence de fichiers spécifiques à WSL
        return (
            os.path.exists("/proc/version")
            and "microsoft" in open("/proc/version", encoding="utf-8").read().lower()
        ) or os.environ.get("WSL_DISTRO_NAME") is not None
    except OSError:
        return False


def get_wsl_fallback_path(dialog_type, title, initialdir, filetypes):
    """Fallback pour WSL - utilise une interface en ligne de commande"""

    try:
        # Essayer d'utiliser zenity si disponible (interface graphique légère)
        if dialog_type == "folder":
            cmd = ["zenity", "--file-selection", "--directory", "--title", title]
        else:
            # Construire le filtre pour zenity
            file_filter = "|".join([f"*.{ext.replace('*.', '')}" for _, ext in filetypes])
            cmd = ["zenity", "--file-selection", "--title", title, "--file-filter", file_filter]

        if initialdir:
            cmd.extend(["--filename", initialdir])

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        pass

    # Si zenity n'est pas disponible, utiliser une interface texte simple
    print(f"\n=== {title} ===")
    print("Environnement WSL détecté - Interface texte")

    if dialog_type == "folder":
        print("Veuillez entrer le chemin du dossier:")
    else:
        print("Veuillez entrer le chemin du fichier:")
        print("Types acceptés:", ", ".join([f"{desc} ({ext})" for desc, ext in filetypes]))

    if initialdir:
        print(f"Dossier initial: {initialdir}")

    # En mode serveur, on ne peut pas utiliser input() directement
    # On retourne un chemin par défaut ou on demande au frontend de gérer
    return None


@API.route("/api/file-dialog/open", methods=["POST"])
def open_dialog():
    """Ouvre un dialogue de sélection de fichier ou dossier"""
    try:
        # Récupérer les paramètres de la requête
        data = request.get_json() or {}
        dialog_type = data.get("dialog_type", "file")
        title = data.get("title", "Sélectionner un fichier")
        initialdir = data.get("initialdir", "")
        filetypes = data.get(
            "filetypes", [("Fichiers Ren'Py", "*.rpy"), ("Tous les fichiers", "*.*")]
        )

        # Détecter l'environnement WSL
        if is_wsl_environment():
            logger.info("Environnement WSL détecté, utilisation du fallback")

            # Essayer zenity d'abord
            selected_path = get_wsl_fallback_path(dialog_type, title, initialdir, filetypes)

            if selected_path:
                return jsonify(
                    {
                        "success": True,
                        "path": selected_path,
                        "message": "Sélectionné: " + selected_path,
                    }
                )

            # Si zenity n'est pas disponible, retourner une erreur avec instructions
            return jsonify(
                {
                    "success": False,
                    "error": "Interface graphique non disponible en WSL",
                    "message": "Pour utiliser les dialogues de fichier en WSL, \
                      installez zenity: sudo apt install zenity",
                    "wsl_mode": True,
                    "suggested_path": initialdir or os.path.expanduser("~"),
                }
            )

        # Mode normal avec tkinter
        try:
            # Créer une fenêtre tkinter cachée
            root = tk.Tk()
            root.withdraw()  # Cacher la fenêtre principale

            selected_path = None

            if dialog_type == "folder":
                # Ouvrir le dialogue de dossier
                selected_path = filedialog.askdirectory(title=title, initialdir=initialdir)
            else:
                # Ouvrir le dialogue de fichier
                selected_path = filedialog.askopenfilename(
                    title=title,
                    initialdir=initialdir,
                    filetypes=filetypes,
                )

            # Fermer la fenêtre tkinter
            root.destroy()

            if selected_path:
                return jsonify(
                    {
                        "success": True,
                        "path": selected_path,
                        "message": "Sélectionné: " + selected_path,
                    }
                )
            else:
                return jsonify({"success": False, "message": "Aucune sélection"})

        except (OSError, RuntimeError) as tk_error:
            logger.warning("Erreur tkinter: %s", tk_error)
            # Fallback vers l'interface WSL
            selected_path = get_wsl_fallback_path(dialog_type, title, initialdir, filetypes)

            if selected_path:
                return jsonify(
                    {
                        "success": True,
                        "path": selected_path,
                        "message": "Sélectionné: " + selected_path,
                    }
                )
            else:
                return jsonify(
                    {
                        "success": False,
                        "error": "tkinter non disponible sur ce système",
                        "message": "Veuillez installer tkinter ou zenity \
                          pour utiliser les dialogues de fichier",
                    }
                )

    except ImportError:
        # Fallback si tkinter n'est pas disponible
        logger.warning("tkinter non disponible, utilisation du fallback")
        return jsonify(
            {
                "success": False,
                "error": "tkinter non disponible sur ce système",
                "message": "Veuillez installer tkinter ou utiliser un autre système",
            }
        )
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur dialogue fichier: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/file-dialog/save", methods=["POST"])
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


@API.route("/api/system/check-zenity", methods=["GET"])
def check_zenity():
    """Vérifie si zenity est disponible sur le système"""
    try:
        result = subprocess.run(
            ["zenity", "--version"], capture_output=True, text=True, timeout=5, check=False
        )
        if result.returncode == 0:
            return jsonify(
                {
                    "success": True,
                    "available": True,
                    "version": result.stdout.strip(),
                    "message": "zenity est disponible",
                }
            )
        else:
            return jsonify(
                {"success": True, "available": False, "message": "zenity n'est pas installé"}
            )
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return jsonify(
            {"success": True, "available": False, "message": "zenity n'est pas installé"}
        )
    except OSError as e:
        logger.error("Erreur vérification zenity: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/system/wsl-info", methods=["GET"])
def wsl_info():
    """Retourne des informations sur l'environnement WSL"""
    try:
        is_wsl = is_wsl_environment()
        info = {
            "is_wsl": is_wsl,
            "distro": os.environ.get("WSL_DISTRO_NAME", "Unknown"),
            "version": os.environ.get("WSL_VERSION", "Unknown"),
        }

        if is_wsl:
            # Vérifier zenity
            zenity_available = False
            try:
                result = subprocess.run(
                    ["zenity", "--version"], capture_output=True, text=True, timeout=5, check=False
                )
                zenity_available = result.returncode == 0
            except (OSError, subprocess.SubprocessError):
                pass

            info["zenity_available"] = zenity_available
            info["recommendations"] = [
                "Installer zenity pour les dialogues graphiques: sudo apt install zenity",
                "Ou utiliser les chemins manuels via les prompts",
                "Les chemins Windows sont accessibles via /mnt/c/, /mnt/d/, etc.",
            ]

        return jsonify({"success": True, "info": info})
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur info WSL: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTE RACINE
# ============================================================================


# ============================================================================
# ROUTES DE TRADUCTION
# ============================================================================


@API.route("/api/translator/health", methods=["GET"])
def translator_health():
    """Vérification de l'état du service de traduction"""
    try:
        health_status = translator_service.get_health_status()
        return jsonify(health_status)
    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur vérification traducteur: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/translator/run", methods=["POST"])
def translator_run():
    """Exécution de la traduction de fichiers"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Données requises"}), 400

        input_folder = data.get("inputFolder", "")
        recursive = data.get("recursive", True)
        source_lang = data.get("sourceLang", "auto")
        target_lang = data.get("targetLang", "fra_Latn")
        translation_scope = data.get("translationScope", "all")
        selected_file = data.get("selectedFile", None)

        logger.info("Traduction - scope: %s, fichier: %s", translation_scope, selected_file)

        result = translator_service.translate_files(
            input_folder=input_folder,
            recursive=recursive,
            source_lang=source_lang,
            target_lang=target_lang,
            translation_scope=translation_scope,
            selected_file=selected_file,
        )

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur traduction fichiers: %s", e)
        return jsonify(
            {"success": False, "error": f"Erreur: {e!s}", "stdout": "", "stderr": str(e)}
        ), 500


@API.route("/api/translator/translate", methods=["POST"])
def translate_text():
    """Traduction de texte"""
    try:
        data = request.get_json()
        if not data or "text" not in data:
            return jsonify({"success": False, "error": "Texte à traduire requis"}), 400

        text = data["text"]
        source_lang = data.get("source_language", "auto")
        target_lang = data.get("target_language", "fra_Latn")

        result = translator_service.translate_text(
            text=text, source_lang=source_lang, target_lang=target_lang
        )

        return jsonify(result)

    except OSError as e:
        logger.error("Erreur traduction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/translator/install", methods=["POST"])
def translator_install():
    """Installation des dépendances de traduction"""
    try:
        result = translator_service.install_dependencies()
        return jsonify(result)
    except OSError as e:
        logger.error("Erreur installation traducteur: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/translator/files", methods=["GET"])
def translator_files():
    """Récupération des fichiers de traduction disponibles"""
    try:
        # Récupérer le chemin du projet depuis les paramètres
        settings = AppConfig.load_settings_from_disk()
        project_path = settings.get("paths", {}).get("editor", "")

        result = translator_service.get_available_files(project_path)
        return jsonify(result)
    except OSError as e:
        logger.error("Erreur récupération fichiers traduction: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE BACKUP
# ============================================================================


@API.route("/api/backup/create", methods=["POST"])
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


@API.route("/api/backup/restore", methods=["POST"])
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


@API.route("/api/backup/list", methods=["GET"])
def list_backups():
    """Liste des sauvegardes disponibles"""
    try:
        # Récupérer les paramètres de filtrage
        game_filter = request.args.get("game")
        type_filter = request.args.get("type")

        # Utiliser le BackupManager pour lister les sauvegardes
        backup_manager = BackupManager()
        backups = backup_manager.list_all_backups(game_filter, type_filter)

        return jsonify({"success": True, "backups": backups})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur liste backups: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


# ============================================================================
# ROUTES DE FICHIERS ET DOSSIERS
# ============================================================================


@API.route("/api/file-dialog/save-path", methods=["POST"])
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


@API.route("/api/updates/install", methods=["POST"])
def install_update():
    """Installe une mise à jour"""
    try:
        # Note: install_update method needs executable_path parameter
        result = {"success": False, "error": "Fonctionnalité non implémentée"}

        return jsonify(result)

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur installation: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/updates/config", methods=["GET"])
def get_update_config():
    """Récupère la configuration des mises à jour"""
    try:
        update_manager = UpdateManager(
            AppConfig.GITHUB_REPO_OWNER,
            AppConfig.GITHUB_REPO_NAME,
            AppConfig.APP_VERSION,
        )
        config = update_manager.get_config()

        return jsonify({"success": True, "config": config})

    except (OSError, ValueError, TypeError) as e:
        logger.error("Erreur config updates: %s", e)
        return jsonify({"success": False, "error": f"Erreur: {e!s}"}), 500


@API.route("/api/updates/config", methods=["POST"])
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


@API.route("/api/updates/auto-check", methods=["GET"])
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


@API.route("/")
def index():
    """Route racine - sert l'interface Svelte"""
    static_folder = current_app.static_folder
    index_path = os.path.join(static_folder, "index.html")

    logger.info("🔍 Tentative de chargement de l'interface Svelte")
    logger.info("📁 Dossier statique: %s", static_folder)
    logger.info("📄 Chemin index.html: %s", index_path)
    logger.info("✅ Fichier existe: %s", os.path.exists(index_path))

    if not os.path.exists(index_path):
        logger.error("❌ Interface Svelte non trouvée: %s", index_path)
        return jsonify(
            {
                "error": "Interface Svelte non trouvée",
                "message": "Veuillez compiler l'application avec: pnpm run build",
                "static_folder": static_folder,
                "index_path": index_path,
            }
        ), 404

    logger.info("✅ Interface Svelte trouvée, envoi du fichier")
    return send_from_directory(static_folder, "index.html")


@API.route("/<path:filename>")
def serve_static(filename):
    """Sert les fichiers statiques de SvelteKit"""
    static_folder = current_app.static_folder
    file_path = os.path.join(static_folder, filename)

    logger.debug("📁 Demande de fichier statique: %s", filename)
    logger.debug("📄 Chemin complet: %s", file_path)
    logger.debug("✅ Fichier existe: %s", os.path.exists(file_path))

    if not os.path.exists(file_path):
        logger.warning("⚠️ Fichier statique non trouvé: %s", filename)
        return jsonify({"error": "Fichier non trouvé: " + filename}), 404

    return send_from_directory(static_folder, filename)


@API.route("/api")
def api_info():
    """Route d'information de l'API"""
    return jsonify(
        {
            "message": "RenExtract v2 API - Structure réorganisée",
            "version": "2.0",
            "status": "active",
            "endpoints": [
                "/api/health",
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
