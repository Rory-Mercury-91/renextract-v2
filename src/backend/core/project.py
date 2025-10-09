#!/usr/bin/env python3
"""Gestionnaire de projets Ren'Py
Gère la validation, le scan et le chargement des projets et fichiers
"""

import os
from pathlib import Path


class ProjectManager:
    """Gestionnaire principal pour les projets Ren'Py"""

    def __init__(self):
        """Initialise le gestionnaire de projet"""
        self.current_project_path: str | None = None
        self.current_mode: str = "project"  # "project" ou "single_file"
        self.current_language: str | None = None
        self.current_file: str | None = None
        self.file_content: list[str] = []
        self.available_languages: list[dict] = []
        self.available_files: list[dict] = []

    def validate_project(self, project_path: str) -> dict[str, any]:
        """Valide qu'un chemin est un projet Ren'Py valide

        Args:
            project_path: Chemin vers le projet à valider

        Returns:
            Dict avec 'valid' (bool) et 'message' (str)

        """
        try:
            if not project_path or not os.path.exists(project_path):
                return {"valid": False, "message": "Le chemin n'existe pas"}

            if not os.path.isdir(project_path):
                return {"valid": False, "message": "Le chemin n'est pas un dossier"}

            # Vérifier la présence d'un dossier game/
            game_dir = os.path.join(project_path, "game")
            has_game_folder = os.path.isdir(game_dir)

            # Chercher des fichiers .exe (indicateur Ren'Py)
            has_exe = any(
                f.endswith(".exe")
                for f in os.listdir(project_path)
                if os.path.isfile(os.path.join(project_path, f))
            )

            # Chercher des fichiers .rpy ou .rpyc
            has_rpy_files = False
            if has_game_folder:
                for root, _dirs, files in os.walk(game_dir):
                    if any(f.endswith((".rpy", ".rpyc", ".rpa")) for f in files):
                        has_rpy_files = True
                        break
                    # Limiter la recherche à 2 niveaux
                    if root.count(os.sep) - game_dir.count(os.sep) >= 2:
                        break

            is_valid = has_game_folder or has_exe or has_rpy_files

            return {
                "valid": is_valid,
                "message": "Projet Ren'Py valide" if is_valid else "Pas un projet Ren'Py valide",
            }

        except Exception as e:
            return {"valid": False, "message": f"Erreur lors de la validation: {e!s}"}

    def find_project_root(self, subdir_path: str, max_levels: int = 10) -> str | None:
        """Remonte dans l'arborescence pour trouver la racine du projet Ren'Py

        Args:
            subdir_path: Chemin d'un sous-dossier
            max_levels: Nombre maximum de niveaux à remonter

        Returns:
            Chemin de la racine du projet ou None

        """
        try:
            current_path = Path(subdir_path).resolve()

            for _ in range(max_levels):
                # Vérifier si le chemin actuel est un projet valide
                validation = self.validate_project(str(current_path))
                if validation["valid"]:
                    return str(current_path)

                # Remonter d'un niveau
                parent = current_path.parent
                if parent == current_path:  # On est à la racine du système
                    break
                current_path = parent

            return None

        except Exception:
            return None

    def scan_languages(self, project_path: str) -> list[dict[str, any]]:
        """Scanne les langues disponibles dans game/tl/

        Args:
            project_path: Chemin vers le projet

        Returns:
            Liste de dicts avec 'name', 'file_count', 'path'

        """
        languages = []

        try:
            if not project_path or not os.path.exists(project_path):
                return languages

            tl_path = os.path.join(project_path, "game", "tl")
            if not os.path.exists(tl_path):
                return languages

            # Parcourir les sous-dossiers de tl/
            for item in os.listdir(tl_path):
                item_path = os.path.join(tl_path, item)

                # Ignorer les fichiers et dossiers spéciaux
                if not os.path.isdir(item_path) or item.startswith(".") or item.lower() == "none":
                    continue

                # Compter les fichiers .rpy
                rpy_files = []
                try:
                    for root, _dirs, files in os.walk(item_path):
                        for file in files:
                            if file.lower().endswith(".rpy"):
                                rpy_files.append(os.path.join(root, file))
                except Exception:
                    continue

                if rpy_files:
                    languages.append(
                        {"name": item, "file_count": len(rpy_files), "path": item_path},
                    )

            # Trier avec french en premier
            languages.sort(
                key=lambda x: (0 if x["name"].lower() == "french" else 1, x["name"].lower()),
            )

            return languages

        except Exception:
            return languages

    def scan_language_files(
        self, project_path: str, language: str, exclusions: list[str] | None = None,
    ) -> list[dict[str, any]]:
        """Scanne les fichiers .rpy d'une langue spécifique

        Args:
            project_path: Chemin vers le projet
            language: Nom de la langue (ex: 'french')
            exclusions: Liste de patterns à exclure

        Returns:
            Liste de dicts avec 'name', 'path', 'size', 'relative_path'

        """
        files = []

        try:
            if not project_path or not language:
                return files

            if exclusions is None:
                exclusions = []

            language_path = os.path.join(project_path, "game", "tl", language)
            if not os.path.exists(language_path):
                return files

            # Fichiers système à toujours exclure
            system_files = ["99_z_langselect.rpy", "99_z_console.rpy"]

            # Chercher tous les fichiers .rpy
            rpy_files = []
            try:
                for root, _dirs, files_in_dir in os.walk(language_path):
                    for file in files_in_dir:
                        if file.lower().endswith(".rpy"):
                            rpy_files.append(os.path.join(root, file))
            except Exception:
                return files

            for file_path in rpy_files:
                file_name = os.path.basename(file_path)

                # Vérifier les exclusions
                should_exclude = False

                # Exclusions utilisateur
                for exclusion in exclusions:
                    exclusion_clean = exclusion.strip().lower()
                    if exclusion_clean and exclusion_clean in file_name.lower():
                        should_exclude = True
                        break

                # Fichiers système
                if file_name.lower() in [f.lower() for f in system_files]:
                    should_exclude = True

                if not should_exclude:
                    try:
                        file_size = os.path.getsize(file_path)
                        files.append(
                            {
                                "name": file_name,
                                "path": file_path,
                                "size": file_size,
                                "relative_path": os.path.relpath(file_path, language_path),
                            },
                        )
                    except OSError:
                        continue

            # Trier par nom
            files.sort(key=lambda x: x["name"].lower())

            return files

        except Exception:
            return files

    def load_file_content(self, filepath: str) -> dict[str, any]:
        """Charge le contenu d'un fichier avec encodage UTF-8

        Args:
            filepath: Chemin vers le fichier

        Returns:
            Dict avec 'success', 'content' (liste de lignes), 'line_count', 'error'

        """
        try:
            if not filepath or not os.path.exists(filepath):
                return {
                    "success": False,
                    "error": "Fichier introuvable",
                    "content": [],
                    "line_count": 0,
                }

            with open(filepath, encoding="utf-8") as f:
                content = f.readlines()

            # Stocker dans l'état interne
            self.file_content = content
            self.current_file = filepath

            return {
                "success": True,
                "content": content,
                "line_count": len(content),
                "filepath": filepath,
            }

        except UnicodeDecodeError:
            return {
                "success": False,
                "error": "Erreur d'encodage (le fichier n'est pas en UTF-8)",
                "content": [],
                "line_count": 0,
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur lors du chargement: {e!s}",
                "content": [],
                "line_count": 0,
            }

    def get_project_summary(self, project_path: str) -> dict[str, any]:
        """Génère un résumé d'informations sur le projet

        Args:
            project_path: Chemin vers le projet

        Returns:
            Dict avec infos du projet

        """
        try:
            if not project_path or not os.path.exists(project_path):
                return {
                    "project_name": "Aucun projet",
                    "rpa_count": 0,
                    "rpy_count": 0,
                    "languages": [],
                    "summary": "Aucun projet sélectionné",
                }

            project_name = os.path.basename(project_path)
            game_dir = os.path.join(project_path, "game")

            if not os.path.isdir(game_dir):
                return {
                    "project_name": project_name,
                    "rpa_count": 0,
                    "rpy_count": 0,
                    "languages": [],
                    "summary": f"Projet: {project_name} (pas de dossier game/)",
                }

            # Compter les fichiers
            rpa_count = 0
            rpy_count = 0

            for f in os.listdir(game_dir):
                if f.endswith(".rpa"):
                    rpa_count += 1
                elif f.endswith(".rpy"):
                    rpy_count += 1

            # Obtenir les langues
            languages = self.scan_languages(project_path)

            # Construire le résumé
            info_parts = [f"Projet: {project_name}"]

            if rpa_count > 0:
                info_parts.append(f"{rpa_count} RPA")
            if rpy_count > 0:
                info_parts.append(f"{rpy_count} RPY")
            if languages:
                lang_names = [lang["name"] for lang in languages[:3]]
                info_parts.append(f"Traductions: {', '.join(lang_names)}")
                if len(languages) > 3:
                    info_parts.append("...")

            summary = " • ".join(info_parts)

            return {
                "project_name": project_name,
                "rpa_count": rpa_count,
                "rpy_count": rpy_count,
                "languages": languages,
                "summary": summary,
            }

        except Exception as e:
            return {
                "project_name": os.path.basename(project_path) if project_path else "Unknown",
                "rpa_count": 0,
                "rpy_count": 0,
                "languages": [],
                "summary": f"Erreur: {e!s}",
            }

    def set_current_project(self, project_path: str, mode: str = "project") -> dict[str, any]:
        """Définit le projet actuel et initialise l'état

        Args:
            project_path: Chemin vers le projet
            mode: Mode de fonctionnement ("project" ou "single_file")

        Returns:
            Dict avec le statut

        """
        self.current_project_path = project_path
        self.current_mode = mode
        self.current_language = None
        self.current_file = None
        self.file_content = []
        self.available_languages = []
        self.available_files = []

        return {"success": True, "project_path": project_path, "mode": mode}

    def get_state(self) -> dict[str, any]:
        """Retourne l'état actuel du gestionnaire

        Returns:
            Dict avec l'état complet

        """
        return {
            "mode": self.current_mode,
            "project_path": self.current_project_path,
            "language": self.current_language,
            "current_file": self.current_file,
            "file_content": self.file_content,
            "available_languages": self.available_languages,
            "available_files": self.available_files,
        }


# Instance globale
project_manager = ProjectManager()
