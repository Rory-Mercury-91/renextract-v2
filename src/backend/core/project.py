#!/usr/bin/env python3
"""Gestionnaire de projets Ren'Py
Gère la validation, le scan et le chargement des projets et fichiers
"""

import os
from pathlib import Path
from typing import Optional


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

    def _normalize_path(self, path: str) -> str:
        """Normalise un chemin pour qu'il soit accessible sur le système actuel

        Args:
            path: Chemin à normaliser

        Returns:
            Chemin normalisé
        """
        if not path:
            return path

        # Convertir les chemins WSL Windows vers Linux
        if path.startswith("\\\\wsl.localhost\\"):
            # \\wsl.localhost\Arch\home\rory\projets\... -> /home/rory/projets/...
            path = path.replace("\\\\wsl.localhost\\Arch\\", "/")
            path = path.replace("\\", "/")

        # Convertir les chemins Windows vers format Unix
        if "\\" in path and not path.startswith("/"):
            path = path.replace("\\", "/")

        # Convertir les chemins Windows spécifiques (C:, D:, B:, etc.)
        if len(path) >= 2 and path[1] == ":" and path[0].isalpha():
            # C:\path\to\project -> /mnt/c/path/to/project
            # B:/path/to/project -> /mnt/b/path/to/project
            drive_letter = path[0].lower()
            path = "/mnt/" + drive_letter + path[2:].replace("\\", "/")

        return path

    def validate_project(self, project_path: str) -> dict[str, any]:
        """Valide qu'un chemin est un projet Ren'Py valide

        Args:
            project_path: Chemin vers le projet à valider

        Returns:
            Dict avec 'valid' (bool) et 'message' (str)

        """
        try:
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(project_path)

            if not normalized_path or not os.path.exists(normalized_path):
                return {"valid": False, "message": "Le chemin n'existe pas"}

            if not os.path.isdir(normalized_path):
                return {"valid": False, "message": "Le chemin n'est pas un dossier"}

            # Vérifier la présence d'un dossier game/
            game_dir = os.path.join(normalized_path, "game")
            has_game_folder = os.path.isdir(game_dir)

            # Chercher des fichiers .exe (indicateur Ren'Py)
            has_exe = any(
                f.endswith(".exe")
                for f in os.listdir(normalized_path)
                if os.path.isfile(os.path.join(normalized_path, f))
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

        except (OSError, ValueError, TypeError) as e:
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
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(subdir_path)
            current_path = Path(normalized_path).resolve()

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

        except (OSError, ValueError, TypeError):
            return None

    def scan_languages(self, project_path: str) -> list[dict[str, any]]:
        """Scanne les langues disponibles dans game/tl/

        Args:
            project_path: Chemin vers le projet

        Returns:
            Liste de dicts avec 'name', 'file_count', 'path'

        """
        # Normaliser le chemin pour Windows/WSL
        normalized_path = self._normalize_path(project_path)
        languages = []

        try:
            if not normalized_path or not os.path.exists(normalized_path):
                return languages

            tl_path = os.path.join(normalized_path, "game", "tl")
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
                except (OSError, ValueError, TypeError):
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

        except (OSError, ValueError, TypeError):
            return languages

    def scan_language_files(
        self,
        project_path: str,
        language: str,
        exclusions: list[str] | None = None,
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
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(project_path)

            if not normalized_path or not language:
                return files

            if exclusions is None:
                exclusions = []

            language_path = os.path.join(normalized_path, "game", "tl", language)
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
            except (OSError, ValueError, TypeError):
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

        except (OSError, ValueError, TypeError):
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
        except (OSError, ValueError, TypeError) as e:
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
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(project_path)

            if not normalized_path or not os.path.exists(normalized_path):
                return {
                    "project_name": "Aucun projet",
                    "rpa_count": 0,
                    "rpy_count": 0,
                    "languages": [],
                    "summary": "Aucun projet sélectionné",
                }

            project_name = os.path.basename(normalized_path)
            game_dir = os.path.join(normalized_path, "game")

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
            languages = self.scan_languages(normalized_path)

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

        except (OSError, ValueError, TypeError) as e:
            return {
                "project_name": os.path.basename(normalized_path) if normalized_path else "Unknown",
                "rpa_count": 0,
                "rpy_count": 0,
                "languages": [],
                "summary": f"Erreur: {e!s}",
            }

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

    def get_project_files(
        self, project_path: str, file_type: str = "all", language: Optional[str] = None
    ) -> list[dict[str, any]]:
        """Obtient la liste des fichiers du projet selon le type demandé

        Args:
            project_path: Chemin vers le projet
            file_type: Type de fichiers ("all", "rpy", "rpa", "languages")
            language: Langue spécifique pour filtrer les fichiers de traduction

        Returns:
            Liste de dicts avec les informations des fichiers

        """
        try:
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(project_path)

            if not normalized_path or not os.path.exists(normalized_path):
                return []

            files = []

            if file_type in ["all", "rpy"]:
                # Fichiers .rpy dans game/
                game_dir = os.path.join(normalized_path, "game")
                if os.path.exists(game_dir):
                    for root, _dirs, filenames in os.walk(game_dir):
                        for filename in filenames:
                            if filename.endswith(".rpy"):
                                file_path = os.path.join(root, filename)
                                try:
                                    file_size = os.path.getsize(file_path)
                                    files.append(
                                        {
                                            "name": filename,
                                            "path": file_path,
                                            "size": file_size,
                                            "type": "rpy",
                                            "relative_path": os.path.relpath(
                                                file_path, normalized_path
                                            ),
                                        }
                                    )
                                except OSError:
                                    continue

            if file_type in ["all", "rpa"]:
                # Fichiers .rpa dans game/
                game_dir = os.path.join(normalized_path, "game")
                if os.path.exists(game_dir):
                    for filename in os.listdir(game_dir):
                        if filename.endswith(".rpa"):
                            file_path = os.path.join(game_dir, filename)
                            try:
                                file_size = os.path.getsize(file_path)
                                files.append(
                                    {
                                        "name": filename,
                                        "path": file_path,
                                        "size": file_size,
                                        "type": "rpa",
                                        "relative_path": os.path.relpath(
                                            file_path, normalized_path
                                        ),
                                    }
                                )
                            except OSError:
                                continue

            if file_type in ["all", "languages"]:
                # Fichiers de traduction
                if language:
                    # Seulement la langue spécifiée
                    lang_files = self.scan_language_files(normalized_path, language)
                    for file_info in lang_files:
                        file_info["type"] = "translation"
                        file_info["language"] = language
                        files.append(file_info)
                else:
                    # Toutes les langues
                    languages = self.scan_languages(normalized_path)
                    for lang in languages:
                        lang_files = self.scan_language_files(normalized_path, lang["name"])
                        for file_info in lang_files:
                            file_info["type"] = "translation"
                            file_info["language"] = lang["name"]
                            files.append(file_info)

            # Trier par nom
            files.sort(key=lambda x: x["name"].lower())

            return files

        except (OSError, ValueError, TypeError):
            return []

    def set_current_project(self, project_path: str) -> bool:
        """Définit le projet courant (version simplifiée pour l'API)

        Args:
            project_path: Chemin vers le projet

        Returns:
            True si succès, False sinon

        """
        try:
            # Normaliser le chemin pour Windows/WSL
            normalized_path = self._normalize_path(project_path)

            if not normalized_path or not os.path.exists(normalized_path):
                return False

            # Valider que c'est un projet Ren'Py
            validation = self.validate_project(normalized_path)
            if not validation["valid"]:
                return False

            # Définir le projet courant
            self.current_project_path = normalized_path
            self.current_mode = "project"
            self.current_language = None
            self.current_file = None
            self.file_content = []
            self.available_languages = self.scan_languages(normalized_path)
            self.available_files = []

            return True

        except (OSError, ValueError, TypeError):
            return False


# Instance globale
project_manager = ProjectManager()
