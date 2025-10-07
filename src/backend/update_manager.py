#!/usr/bin/env python3
"""
Gestionnaire de mise à jour automatique pour l'application
"""
import json
import os
import platform
import shutil
import sys
import tempfile
import time
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Optional
import requests


class UpdateManager:
    """Gestionnaire de mise à jour automatique"""

    def __init__(self, repo_owner: str, repo_name: str, current_version: str):
        """
        Initialise le gestionnaire de mise à jour

        Args:
            repo_owner: Propriétaire du dépôt GitHub (ex: "votre-username")
            repo_name: Nom du dépôt GitHub (ex: "renextract-v2")
            current_version: Version actuelle de l'application
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.current_version = current_version
        self.github_api_base = "https://api.github.com"
        self.releases_url = f"{self.github_api_base}/repos/{repo_owner}/{repo_name}/releases"
        self.latest_release_url = f"{self.releases_url}/latest"

        # Déterminer l'OS actuel
        self.current_os = self._get_current_os()

        # Configuration des mises à jour
        self._update_config = {
            'auto_check': True,
            'auto_download': False,
            'auto_install': False,
            'check_interval_hours': 24,
            'last_check': None
        }

        # Charger la configuration depuis le disque
        self._load_config()

    def _get_current_os(self) -> str:
        """Détermine l'OS actuel pour télécharger le bon exécutable"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "unknown"

    def _load_config(self):
        """Charge la configuration des mises à jour depuis le disque"""
        config_path = Path("04_Configs/update_config.json")
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    saved_config = json.load(f)
                    self._update_config.update(saved_config)
        except (OSError, json.JSONDecodeError) as e:
            print(f"DEBUG: Failed to load update config: {e}")

    def _save_config(self):
        """Sauvegarde la configuration des mises à jour sur le disque"""
        config_path = Path("04_Configs/update_config.json")
        try:
            config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self._update_config, f, ensure_ascii=False, indent=2)
        except (OSError, TypeError) as e:
            print(f"DEBUG: Failed to save update config: {e}")

    def _get_asset_name_for_os(self, assets: list) -> Optional[str]:
        """Trouve le nom de l'asset correspondant à l'OS actuel"""
        os_patterns = {
            "windows": [".exe", "windows"],
            "macos": ["macos", "darwin"],
            "linux": ["linux", "ubuntu"]
        }

        patterns = os_patterns.get(self.current_os, [])

        for asset in assets:
            asset_name = asset.get('name', '').lower()
            for pattern in patterns:
                if pattern in asset_name:
                    return asset['name']

        # Fallback: prendre le premier asset si aucun ne correspond
        if assets:
            return assets[0]['name']

        return None

    def check_for_updates(self) -> Dict:
        """
        Vérifie s'il y a des mises à jour disponibles

        Returns:
            Dict contenant les informations sur les mises à jour
        """
        try:
            print(
                f"DEBUG: Checking for updates from {self.latest_release_url}")

            # Faire la requête à l'API GitHub
            response = requests.get(self.latest_release_url, timeout=10)
            response.raise_for_status()

            release_data = response.json()
            latest_version = release_data.get('tag_name', '').lstrip('v')
            latest_version_name = release_data.get('name', '')
            release_notes = release_data.get('body', '')
            published_at = release_data.get('published_at', '')
            assets = release_data.get('assets', [])

            # Trouver l'asset correspondant à notre OS
            asset_name = self._get_asset_name_for_os(assets)
            download_url = None
            download_size = 0

            if asset_name:
                for asset in assets:
                    if asset['name'] == asset_name:
                        download_url = asset['browser_download_url']
                        download_size = asset.get('size', 0)
                        break

            # Comparer les versions
            is_newer = self._compare_versions(
                latest_version, self.current_version)

            # Mettre à jour la dernière vérification
            self._update_config['last_check'] = time.time()
            self._save_config()

            result = {
                'success': True,
                'has_update': is_newer,
                'current_version': self.current_version,
                'latest_version': latest_version,
                'latest_version_name': latest_version_name,
                'release_notes': release_notes,
                'published_at': published_at,
                'download_url': download_url,
                'download_size': download_size,
                'asset_name': asset_name,
                'current_os': self.current_os
            }

            print(f"DEBUG: Update check result: {result}")
            return result

        except requests.RequestException as e:
            print(f"DEBUG: Failed to check for updates: {e}")
            return {
                'success': False,
                'error': f'Erreur de connexion: {str(e)}'
            }
        except (KeyError, ValueError) as e:
            print(f"DEBUG: Failed to parse update data: {e}")
            return {
                'success': False,
                'error': f'Erreur de parsing: {str(e)}'
            }

    def _compare_versions(self, version1: str, version2: str) -> bool:
        """
        Compare deux versions et retourne True si version1 > version2

        Args:
            version1: Version à comparer (ex: "2.1.0")
            version2: Version de référence (ex: "2.0.0")

        Returns:
            True si version1 est plus récente que version2
        """
        try:
            # Nettoyer les versions (enlever les préfixes 'v' et autres)
            v1_clean = version1.lstrip('v').split('-')[0]
            v2_clean = version2.lstrip('v').split('-')[0]

            # Séparer en composants numériques
            v1_parts = [int(x) for x in v1_clean.split('.')]
            v2_parts = [int(x) for x in v2_clean.split('.')]

            # Normaliser la longueur
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))

            # Comparer
            return v1_parts > v2_parts

        except (ValueError, AttributeError):
            # En cas d'erreur, considérer que c'est plus récent
            return True

    def download_update(self, download_url: str, progress_callback=None) -> Dict:
        """
        Télécharge la mise à jour

        Args:
            download_url: URL de téléchargement
            progress_callback: Fonction de callback pour le progrès (optionnel)

        Returns:
            Dict contenant le résultat du téléchargement
        """
        try:
            print(f"DEBUG: Downloading update from {download_url}")

            # Créer un dossier temporaire
            temp_dir = tempfile.mkdtemp(prefix="update_")
            download_path = os.path.join(temp_dir, "update.zip")

            # Télécharger avec une barre de progression
            def download_progress(block_num, block_size, total_size):
                if progress_callback and total_size > 0:
                    downloaded = block_num * block_size
                    progress = min(100, (downloaded / total_size) * 100)
                    progress_callback(progress, downloaded, total_size)

            urllib.request.urlretrieve(
                download_url, download_path, download_progress)

            # Vérifier que le fichier a été téléchargé
            if not os.path.exists(download_path):
                return {
                    'success': False,
                    'error': 'Le fichier de mise à jour n\'a pas été téléchargé'
                }

            # Extraire l'archive
            extract_path = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_path, exist_ok=True)

            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            return {
                'success': True,
                'temp_dir': temp_dir,
                'extract_path': extract_path,
                'download_path': download_path
            }

        except (OSError, urllib.error.URLError, zipfile.BadZipFile) as e:
            print(f"DEBUG: Failed to download update: {e}")
            return {
                'success': False,
                'error': f'Erreur de téléchargement: {str(e)}'
            }

    def install_update(self, extract_path: str) -> Dict:
        """
        Installe la mise à jour

        Args:
            extract_path: Chemin vers le dossier extrait

        Returns:
            Dict contenant le résultat de l'installation
        """
        try:
            print(f"DEBUG: Installing update from {extract_path}")

            # Trouver l'exécutable dans le dossier extrait
            exe_files = []
            for root, _, files in os.walk(extract_path):
                for file in files:
                    if self.current_os == "windows" and file.endswith('.exe'):
                        exe_files.append(os.path.join(root, file))
                    elif self.current_os != "windows" and not file.endswith('.exe'):
                        # Vérifier si c'est un exécutable
                        file_path = os.path.join(root, file)
                        if os.access(file_path, os.X_OK):
                            exe_files.append(file_path)

            if not exe_files:
                return {
                    'success': False,
                    'error': 'Aucun exécutable trouvé dans la mise à jour'
                }

            # Prendre le premier exécutable trouvé
            new_exe_path = exe_files[0]

            # Déterminer le chemin de destination
            if getattr(sys, 'frozen', False):
                # Mode exécutable
                current_exe = sys.executable
                backup_exe = current_exe + ".backup"
            else:
                # Mode développement
                current_exe = os.path.join(
                    os.path.dirname(__file__), "..", "..", "app.py")
                backup_exe = current_exe + ".backup"

            # Créer une sauvegarde de l'exécutable actuel
            if os.path.exists(current_exe):
                shutil.copy2(current_exe, backup_exe)

            # Copier le nouvel exécutable
            shutil.copy2(new_exe_path, current_exe)

            # Rendre l'exécutable exécutable sur Unix
            if self.current_os != "windows":
                os.chmod(current_exe, 0o755)

            return {
                'success': True,
                'message': 'Mise à jour installée avec succès. Redémarrez l\'application.'
            }

        except (OSError, shutil.Error) as e:
            print(f"DEBUG: Failed to install update: {e}")
            return {
                'success': False,
                'error': f'Erreur d\'installation: {str(e)}'
            }

    def should_check_for_updates(self) -> bool:
        """Vérifie si on doit vérifier les mises à jour selon la configuration"""
        if not self._update_config.get('auto_check', True):
            return False

        last_check = self._update_config.get('last_check')
        if not last_check:
            return True

        check_interval = self._update_config.get(
            'check_interval_hours', 24) * 3600  # Convertir en secondes
        return time.time() - last_check > check_interval

    def set_config(self, new_config: Dict):
        """Met à jour la configuration des mises à jour"""
        self._update_config.update(new_config)
        self._save_config()

    def get_config(self) -> Dict:
        """Retourne la configuration actuelle"""
        return self._update_config.copy()
