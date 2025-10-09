# src/backend/optimized_reconstruction.py
# Version optimisée de la reconstruction avec cache et streaming

"""Module de reconstruction optimisé pour RenExtract v2."""

import glob
import hashlib
import json
import logging
import os
import re
import time
from collections import OrderedDict
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class OptimizedFileReconstructor:
    """Classe optimisée pour la reconstruction des fichiers traduits"""

    def __init__(self, cache_size: int = 100):
        """Initialise le reconstructeur optimisé"""
        self.cache_size = cache_size
        self._cache = {}
        self._file_hash_cache = {}

        # Préfixes par défaut
        self.code_prefix = "RENPY_CODE"
        self.asterisk_prefix = "RENPY_ASTERISK"
        self.tilde_prefix = "RENPY_TILDE"
        self.empty_prefix = "RENPY_EMPTY"

        # Initialiser les attributs principaux
        self.file_content = []
        self.original_path = ""

        # Initialiser les mappings
        self.mapping = OrderedDict()
        self.empty_mapping = OrderedDict()
        self.asterix_mapping = OrderedDict()
        self.tilde_mapping = OrderedDict()

        # Initialiser les listes de traduction
        self.translations = []
        self.duplicate_translations = []
        self.asterix_translations = []
        self.tilde_translations = []

        # Initialiser les données de reconstruction
        self.line_to_content_indices = {}
        self.original_lines = {}
        self.all_contents_linear = []
        self.suffixes = []
        self.content_prefixes = []
        self.content_suffixes = []
        self.asterix_metadata = {}
        self.tilde_metadata = {}
        self.translation_map = {}
        self.duplicate_originals_ordered = []

        # Données de reconstruction
        self._reset_reconstruction_data()

    def _reset_reconstruction_data(self):
        """Réinitialise toutes les données de reconstruction"""
        self.file_content = []
        self.original_path = ""

        self.mapping = OrderedDict()
        self.empty_mapping = OrderedDict()
        self.asterix_mapping = OrderedDict()
        self.tilde_mapping = OrderedDict()

        self.translations = []
        self.duplicate_translations = []
        self.asterix_translations = []
        self.tilde_translations = []

        self.line_to_content_indices = {}
        self.original_lines = {}
        self.all_contents_linear = []
        self.suffixes = []
        self.content_prefixes = []
        self.content_suffixes = []
        self.asterix_metadata = {}
        self.tilde_metadata = {}
        self.translation_map = {}

    @lru_cache(maxsize=1000)
    def _get_file_hash(self, filepath: str) -> str:
        """Calcule le hash d'un fichier pour le cache"""
        try:
            with open(filepath, "rb") as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except OSError:
            return ""

    def _is_cached(self, filepath: str) -> bool:
        """Vérifie si le fichier est en cache"""
        current_hash = self._get_file_hash(filepath)
        cached_hash = self._file_hash_cache.get(filepath)
        return current_hash == cached_hash and current_hash != ""

    def _update_cache(self, filepath: str, result: dict[str, Any]):
        """Met à jour le cache avec les résultats"""
        if len(self._cache) >= self.cache_size:
            # Supprimer le plus ancien
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[filepath] = result
        self._file_hash_cache[filepath] = self._get_file_hash(filepath)

    def _get_cached_result(self, filepath: str) -> dict[str, Any] | None:
        """Récupère le résultat depuis le cache"""
        if filepath in self._cache:
            return self._cache.get(filepath)
        return None

    def load_file_content_optimized(self, file_content: list[str], original_path: str):
        """Charge le fichier original et les données d'extraction de manière optimisée"""
        if not file_content or not isinstance(file_content, list):
            raise ValueError("Contenu de fichier invalide ou manquant")

        # Vérifier le cache d'abord
        cached_result = self._get_cached_result(original_path)
        if cached_result:
            logger.info("📋 Utilisation du cache pour %s", os.path.basename(original_path))
            self._load_from_cache(cached_result)
            return

        # Essayer de charger le fichier avec placeholders
        file_base = self._get_file_base_name(original_path)
        game_name = self._extract_game_name(os.path.dirname(original_path))
        reference_folder = os.path.join("01_Temporary", game_name, "fichiers_a_referencer")
        placeholders_path = os.path.join(reference_folder, f"{file_base}_with_placeholders.rpy")

        if os.path.exists(placeholders_path):
            logger.info("📂 Chargement fichier avec placeholders: %s", placeholders_path)
            with open(placeholders_path, encoding="utf-8") as f:
                self.file_content = f.readlines()
        else:
            logger.warning(
                "⚠️ Fichier with_placeholders.rpy non trouvé, utilisation du fichier original",
            )
            self.file_content = file_content[:]

        self.original_path = original_path

        # Charger les données de reconstruction
        self._load_data_for_reconstruction_optimized()

    def _load_from_cache(self, cached_data: dict[str, Any]):
        """Charge les données depuis le cache"""
        self.file_content = cached_data.get("file_content", [])
        self.original_path = cached_data.get("original_path", "")
        self.mapping = cached_data.get("mapping", OrderedDict())
        self.empty_mapping = cached_data.get("empty_mapping", OrderedDict())
        self.asterix_mapping = cached_data.get("asterix_mapping", OrderedDict())
        self.tilde_mapping = cached_data.get("tilde_mapping", OrderedDict())
        self.translations = cached_data.get("translations", [])
        self.duplicate_translations = cached_data.get("duplicate_translations", [])
        self.asterix_translations = cached_data.get("asterix_translations", [])
        self.tilde_translations = cached_data.get("tilde_translations", [])
        self.line_to_content_indices = cached_data.get("line_to_content_indices", {})
        self.original_lines = cached_data.get("original_lines", {})
        self.all_contents_linear = cached_data.get("all_contents_linear", [])
        self.suffixes = cached_data.get("suffixes", [])
        self.content_prefixes = cached_data.get("content_prefixes", [])
        self.content_suffixes = cached_data.get("content_suffixes", [])
        self.asterix_metadata = cached_data.get("asterix_metadata", {})
        self.tilde_metadata = cached_data.get("tilde_metadata", {})
        self.translation_map = cached_data.get("translation_map", {})

    def _load_data_for_reconstruction_optimized(self):
        """Charge les métadonnées JSON et les fichiers de traduction de manière optimisée"""
        try:
            file_base = self._get_file_base_name(self.original_path)
            game_name = self._extract_game_name(os.path.dirname(self.original_path))

            # Utiliser le bon nom de dossier
            reference_folder = os.path.join("01_Temporary", game_name, "fichiers_a_referencer")
            translate_folder = os.path.join("01_Temporary", game_name, "fichiers_a_traduire")

            logger.info("📂 Dossier référence: %s", reference_folder)
            logger.info("📂 Dossier traduction: %s", translate_folder)

            # Charger le fichier positions.json
            positions_file = os.path.join(reference_folder, f"{file_base}_positions.json")

            if not os.path.exists(positions_file):
                raise FileNotFoundError(f"Fichier positions.json introuvable: {positions_file}")

            with open(positions_file, encoding="utf-8") as f:
                data = json.load(f)

                # Charger les métadonnées
                self.line_to_content_indices = {
                    int(k): v for k, v in data["line_to_content_indices"].items()
                }
                self.original_lines = {int(k): v for k, v in data["original_lines"].items()}
                self.all_contents_linear = data["all_contents_linear"]
                self.suffixes = data["suffixes"]
                self.content_prefixes = data.get("content_prefixes", [])
                self.content_suffixes = data.get("content_suffixes", [])

                # Charger les mappings
                self.mapping = data.get("mapping", {})
                self.asterix_mapping = data.get("asterix_mapping", {})
                self.tilde_mapping = data.get("tilde_mapping", {})
                self.empty_mapping = data.get("empty_mapping", {})

                # Charger les métadonnées
                self.asterix_metadata = data.get("asterix_metadata", {})
                self.tilde_metadata = data.get("tilde_metadata", {})

                # Charger la liste ordonnée des doublons originaux
                self.duplicate_originals_ordered = data.get("duplicate_originals_ordered", [])

            # Charger les fichiers de traduction
            self._load_translation_files_optimized(translate_folder, file_base)

            # Construire le mapping de traduction
            self._build_translation_mapping_optimized()

            total_dialogue = len(self.translations)
            total_asterix = len(self.asterix_translations)
            total_tilde = len(self.tilde_translations)
            total_lines = total_dialogue + total_asterix + total_tilde

            logger.info(
                "📂 Chargement optimisé : %s lignes (dialogue:%s, astérisques:%s, tildes:%s)",
                total_lines,
                total_dialogue,
                total_asterix,
                total_tilde,
            )

            # Mettre en cache
            self._update_cache(self.original_path, self._get_cache_data())

        except Exception as e:
            logger.error("Erreur chargement données reconstruction: %s", e)
            raise

    def _get_cache_data(self) -> dict[str, Any]:
        """Retourne les données à mettre en cache"""
        return {
            "file_content": self.file_content,
            "original_path": self.original_path,
            "mapping": self.mapping,
            "empty_mapping": self.empty_mapping,
            "asterix_mapping": self.asterix_mapping,
            "tilde_mapping": self.tilde_mapping,
            "translations": self.translations,
            "duplicate_translations": self.duplicate_translations,
            "asterix_translations": self.asterix_translations,
            "tilde_translations": self.tilde_translations,
            "line_to_content_indices": self.line_to_content_indices,
            "original_lines": self.original_lines,
            "all_contents_linear": self.all_contents_linear,
            "suffixes": self.suffixes,
            "content_prefixes": self.content_prefixes,
            "content_suffixes": self.content_suffixes,
            "asterix_metadata": self.asterix_metadata,
            "tilde_metadata": self.tilde_metadata,
            "translation_map": self.translation_map,
        }

    def _load_translation_files_optimized(self, translate_folder: str, file_base: str):
        """Charge tous les fichiers de traduction de manière optimisée"""
        try:
            # Fichier dialogue principal
            dialogue_files = self._find_translation_files_optimized(
                translate_folder,
                f"{file_base}_dialogue.txt",
            )
            if dialogue_files:
                raw_translations = self._load_multi_files_optimized(dialogue_files)
                self.translations = [line.rstrip("\n\r") for line in raw_translations]

            # Fichier doublons (optionnel)
            doublons_files = self._find_translation_files_optimized(
                translate_folder,
                f"{file_base}_doublons.txt",
            )
            if doublons_files:
                raw_duplicates = self._load_multi_files_optimized(doublons_files)
                self.duplicate_translations = [line.rstrip("\n\r") for line in raw_duplicates]

            # Fichier astérisques/tildes combiné
            asterix_files = self._find_translation_files_optimized(
                translate_folder,
                f"{file_base}_asterix.txt",
            )
            if asterix_files:
                raw_asterix_lines = self._load_multi_files_optimized(asterix_files)
                all_lines = [line.rstrip("\n\r") for line in raw_asterix_lines]

                # Séparer astérisques et tildes
                asterix_count = len(self.asterix_mapping)
                tilde_count = len(self.tilde_mapping)

                if asterix_count > 0:
                    self.asterix_translations = all_lines[:asterix_count]
                if tilde_count > 0:
                    self.tilde_translations = all_lines[asterix_count : asterix_count + tilde_count]

        except Exception as e:
            logger.error("Erreur chargement fichiers traduction: %s", e)
            raise

    def _find_translation_files_optimized(self, folder: str, base_filename: str) -> list[str]:
        """Trouve tous les fichiers de traduction de manière optimisée"""
        try:
            name, ext = os.path.splitext(base_filename)

            # Fichier principal
            main_file = os.path.join(folder, base_filename)

            # Fichiers numérotés
            numbered_pattern = os.path.join(folder, f"{name}_*{ext}")
            numbered_files = glob.glob(numbered_pattern)

            all_files = []

            if os.path.exists(main_file):
                all_files.append(main_file)

            all_files.extend(numbered_files)

            if all_files:
                # Trier par numéro
                all_files.sort(key=lambda x: self._extract_file_number_optimized(x, base_filename))
                return all_files

            return []

        except (OSError, ValueError):
            return []

    def _extract_file_number_optimized(self, filepath: str, base_filename: str) -> int:
        """Extrait le numéro d'un fichier pour le tri de manière optimisée"""
        try:
            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(base_filename)

            if filename == base_filename:
                return 0  # Fichier principal

            # Extraire le numéro
            pattern = f"{name}_"
            if filename.startswith(pattern):
                number_part = filename[len(pattern) : -len(ext)]
                return int(number_part)

            return 999

        except (OSError, ValueError):
            return 999

    def _load_multi_files_optimized(self, files: list[str]) -> list[str]:
        """Charge et concatène plusieurs fichiers de manière optimisée"""
        all_lines = []

        for file_path in files:
            try:
                with open(file_path, encoding="utf-8") as f:
                    all_lines.extend(f.readlines())
            except (OSError, ValueError) as e:
                logger.error("Erreur lecture %s: %s", file_path, e)

        return all_lines

    def _build_translation_mapping_optimized(self):
        """Mappe les traductions de manière optimisée"""
        try:
            self.translation_map = {}

            # Utiliser la liste ordonnée des doublons si disponible
            if hasattr(self, "duplicate_originals_ordered") and self.duplicate_originals_ordered:
                logger.info("Utilisation de duplicate_originals_ordered sauvegardée")
                duplicate_originals = self.duplicate_originals_ordered

                # Calculer les uniques
                content_counts = OrderedDict()
                for content in self.all_contents_linear:
                    content_counts[content] = content_counts.get(content, 0) + 1
                unique_originals = [c for c, count in content_counts.items() if count == 1]
            else:
                # Fallback: ancienne méthode
                logger.warning(
                    "duplicate_originals_ordered non trouvée, utilisation de la méthode de calcul",
                )
                content_counts = OrderedDict()
                for content in self.all_contents_linear:
                    content_counts[content] = content_counts.get(content, 0) + 1

                duplicate_originals = [c for c, count in content_counts.items() if count > 1]
                unique_originals = [c for c, count in content_counts.items() if count == 1]

            # Mapper les doublons
            for i, original in enumerate(duplicate_originals):
                if i < len(self.duplicate_translations):
                    self.translation_map[original] = self.duplicate_translations[i]

            # Mapper les uniques
            for i, original in enumerate(unique_originals):
                if i < len(self.translations):
                    self.translation_map[original] = self.translations[i]

            logger.info("Mapping de traduction créé: %d entrées", len(self.translation_map))
            logger.info("  - Doublons: %d", len(duplicate_originals))
            logger.info("  - Uniques: %d", len(unique_originals))

        except (KeyError, IndexError, ValueError) as e:
            logger.error("Erreur construction mapping traduction: %s", e)
            self.translation_map = {}

    def reconstruct_file_optimized(self, save_mode: str = "new_file") -> dict[str, Any]:
        """Reconstruit le fichier traduit de manière optimisée"""
        start_time = time.time()

        try:
            # Le fichier self.file_content contient déjà les placeholders
            content = self.file_content.copy()

            # Remplacer seulement les placeholders de dialogue par les
            # traductions
            content = self._replace_dialogue_placeholders_optimized(content)

            # Remplacer les autres placeholders (codes, astérisques, tildes,
            # vides)
            content = self._replace_other_placeholders_optimized(content)

            # Ajouter marqueur de reconstruction
            content = self._add_reconstruction_marker_optimized(content)

            # Déterminer le chemin de sauvegarde
            if save_mode == "overwrite":
                save_path = self.original_path
            else:  # new_file
                save_path = self.original_path.replace(".rpy", "_translated.rpy")

            # Écrire le fichier
            with open(save_path, "w", encoding="utf-8", newline="") as f:
                f.writelines(content)

            reconstruction_time = time.time() - start_time
            logger.info("✅ Reconstruction optimisée réussie en %.2fs", reconstruction_time)

            return {
                "success": True,
                "save_path": save_path,
                "save_mode": save_mode,
                "reconstruction_time": reconstruction_time,
            }

        except Exception as e:
            logger.error("Erreur reconstruction: %s", e)
            return {"success": False, "error": str(e)}

    def _replace_dialogue_placeholders_optimized(self, content: list[str]) -> list[str]:
        """Remplace les placeholders de dialogue par les traductions de manière optimisée"""
        try:
            # Pour chaque ligne qui contient des dialogues traduits
            for position_idx, content_indices in self.line_to_content_indices.items():
                if position_idx >= len(content):
                    continue

                line = content[position_idx]

                # Vérifier si c'est une ligne de dialogue (contient des
                # guillemets)
                if '"' in line and line.strip().startswith('"'):
                    # Récupérer l'indentation
                    indent = ""
                    indent_match = re.match(r"^(\s*)", line)
                    if indent_match:
                        indent = indent_match.group(1)

                    # Construire le contenu traduit avec préfixes/suffixes
                    translated_content = ""
                    for i, content_idx in enumerate(content_indices):
                        # Utiliser le mapping pour obtenir la traduction
                        original_text = (
                            self.all_contents_linear[content_idx]
                            if content_idx < len(self.all_contents_linear)
                            else None
                        )

                        if original_text and original_text in self.translation_map:
                            translation = self.translation_map[original_text]
                            # Récupérer les préfixes et suffixes pour ce
                            # contenu
                            if position_idx < len(self.content_prefixes):
                                prefixes = self.content_prefixes[position_idx]
                                suffixes = self.content_suffixes[position_idx]

                                prefix = prefixes[i] if i < len(prefixes) else ""
                                suffix = suffixes[i] if i < len(suffixes) else ""

                                translated_content += prefix + translation + suffix
                            else:
                                translated_content += translation

                    # Ajouter le suffixe de ligne
                    line_suffix = ""
                    if position_idx < len(self.suffixes):
                        line_suffix = self.suffixes[position_idx]

                    # Construire la nouvelle ligne
                    new_line = indent + '"' + translated_content + '"' + line_suffix
                    if not new_line.endswith("\n"):
                        if line_suffix and not new_line.rstrip("\n").endswith(line_suffix.rstrip()):
                            # Ajouter le suffixe seulement s'il n'est pas déjà
                            # présent
                            if new_line.endswith("\n"):
                                new_line = new_line.rstrip("\n") + line_suffix + "\n"
                            else:
                                new_line += line_suffix

                    # S'assurer que la ligne se termine par un retour à la
                    # ligne si l'original en avait un
                    if line.endswith("\n") and not new_line.endswith("\n"):
                        new_line += "\n"

                    content[position_idx] = new_line

            logger.info("✅ %d lignes de dialogue reconstruites", len(self.line_to_content_indices))
            return content

        except Exception as e:
            logger.error("Erreur remplacement placeholders dialogue: %s", e)
            raise

    def _replace_other_placeholders_optimized(self, content: list[str]) -> list[str]:
        """Remplace les autres placeholders de manière optimisée"""
        try:
            content_str = "".join(content)

            # 1. Remplacer les codes/variables (inverser le mapping)
            for original, placeholder in self.mapping.items():
                content_str = content_str.replace(placeholder, original)

            # 2. Remplacer les astérisques avec métadonnées - ORDRE INVERSE
            asterix_items = []
            for placeholder in self.asterix_mapping.keys():
                if placeholder in self.asterix_metadata:
                    meta = self.asterix_metadata[placeholder]
                    placeholder_index = list(self.asterix_mapping.keys()).index(placeholder)
                    asterix_items.append((placeholder, meta, placeholder_index))

            # Trier par niveau décroissant
            asterix_items.sort(key=lambda x: x[1].get("pass_level", 1), reverse=True)

            for placeholder, meta, placeholder_index in asterix_items:
                if placeholder_index < len(self.asterix_translations):
                    translation = self.asterix_translations[placeholder_index].rstrip("\n")

                    # Reconstruire avec le bon nombre d'astérisques
                    prefix = "*" * meta["prefix_count"]
                    suffix = "*" * meta["suffix_count"]
                    reconstructed = f"{prefix}{translation}{suffix}"

                    content_str = content_str.replace(placeholder, reconstructed)

            # 3. Remplacer les tildes avec métadonnées - ORDRE INVERSE
            tilde_items = []
            for placeholder in self.tilde_mapping.keys():
                if placeholder in self.tilde_metadata:
                    meta = self.tilde_metadata[placeholder]
                    placeholder_index = list(self.tilde_mapping.keys()).index(placeholder)
                    tilde_items.append((placeholder, meta, placeholder_index))

            # Trier par niveau décroissant
            tilde_items.sort(key=lambda x: x[1].get("pass_level", 1), reverse=True)

            for placeholder, meta, placeholder_index in tilde_items:
                if placeholder_index < len(self.tilde_translations):
                    translation = self.tilde_translations[placeholder_index].rstrip("\n")

                    # Vérifier si c'est un orphelin ou un groupe structuré
                    if meta.get("orphan", False):
                        reconstructed = meta["full_text"]
                    else:
                        prefix = "~" * meta["prefix_count"]
                        suffix = "~" * meta["suffix_count"]
                        reconstructed = f"{prefix}{translation}{suffix}"

                    content_str = content_str.replace(placeholder, reconstructed)

            # 4. Remplacer les textes vides
            for placeholder in self.empty_mapping.keys():
                content_str = content_str.replace(placeholder, '""')

            # Reconvertir en liste de lignes
            return content_str.splitlines(keepends=True)

        except Exception as e:
            logger.error("Erreur remplacement autres placeholders: %s", e)
            raise

    def _add_reconstruction_marker_optimized(self, content: list[str]) -> list[str]:
        """Ajoute un marqueur de reconstruction à la fin du fichier de manière optimisée"""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        marker = (
            f"\n# Fichier reconstruit après traduction par RenExtract (optimisé) le {timestamp}\n"
        )

        if content and not content[-1].endswith("\n"):
            content[-1] += "\n"

        content.append(marker)
        return content

    @lru_cache(maxsize=1000)
    def _get_file_base_name(self, filepath: str) -> str:
        """Récupère le nom de base du fichier sans extension (avec cache)"""
        if not filepath:
            return "fichier_inconnu"
        filename = os.path.basename(filepath)
        base_name = os.path.splitext(filename)[0]
        return re.sub(r'[<>:"/\\|?*]', "_", base_name)

    @lru_cache(maxsize=1000)
    def _extract_game_name(self, project_path: str) -> str:
        """Extrait le nom du jeu depuis le chemin du projet (avec cache)"""
        try:
            game_name = os.path.basename(project_path.rstrip(os.sep))
            game_name = re.sub(r'[<>:"/\\|?*]', "_", game_name)
            return game_name
        except Exception:
            return "jeu_inconnu"

    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._file_hash_cache.clear()
        logger.info("🗑️ Cache de reconstruction vidé")

    def get_cache_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_hit_ratio": len(self._cache) / self.cache_size if self.cache_size > 0 else 0,
            "cached_files": list(self._cache.keys()),
        }


# Instance globale optimisée
optimized_reconstructor = OptimizedFileReconstructor(cache_size=100)
