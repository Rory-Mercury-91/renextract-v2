# src/backend/optimized_extraction.py
# Version optimisée de l'extraction avec cache et streaming

import hashlib
import logging
import os
import re
import time
from collections import OrderedDict, defaultdict
from collections.abc import Generator
from functools import lru_cache
from typing import Any

logger = logging.getLogger(__name__)


class OptimizedTextExtractor:
    """Version optimisée de l'extracteur avec cache et streaming"""

    def __init__(self, cache_size: int = 1000):
        """Initialise l'extracteur optimisé"""
        self.cache_size = cache_size
        self._cache = {}
        self._file_hash_cache = {}
        self._generators = {
            "code": PlaceholderGenerator("RENPY_CODE_001"),
            "asterisk": PlaceholderGenerator("RENPY_ASTERISK_001"),
            "tilde": PlaceholderGenerator("RENPY_TILDE_001"),
        }
        self.empty_prefix = "RENPY_EMPTY"
        self._counters = {"extracted": 0, "asterix": 0, "tilde": 0, "empty": 0}
        self._reset_data()

    def _reset_data(self):
        """Réinitialise les données d'extraction"""
        self._mappings = {
            "main": OrderedDict(),
            "empty": OrderedDict(),
            "asterix": OrderedDict(),
            "tilde": OrderedDict(),
        }
        self._texts = {"extracted": [], "asterix": [], "tilde": [], "empty": []}
        self.duplicate_manager = DuplicateManager()

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

    def extract_texts_streaming(
        self, filepath: str, batch_size: int = 1000,
    ) -> Generator[dict[str, Any], None, None]:
        """Extraction avec streaming pour les gros fichiers"""
        try:
            # Vérifier le cache d'abord
            cached_result = self._get_cached_result(filepath)
            if cached_result:
                logger.info("📋 Utilisation du cache pour %s", os.path.basename(filepath))
                yield cached_result
                return

            start_time = time.time()
            logger.info("📤 Début extraction streaming: %s", os.path.basename(filepath))

            # Réinitialiser les données
            self._reset_data()

            # Lire le fichier par lots
            with open(filepath, encoding="utf-8") as f:
                batch = []
                line_count = 0

                for line in f:
                    batch.append(line)
                    line_count += 1

                    if len(batch) >= batch_size:
                        # Traiter le lot
                        yield from self._process_batch(batch, line_count - len(batch))
                        batch = []

                # Traiter le dernier lot
                if batch:
                    yield from self._process_batch(batch, line_count - len(batch))

            # Finaliser l'extraction
            result = self._finalize_extraction(filepath, start_time)

            # Mettre en cache
            self._update_cache(filepath, result)

            yield result

        except (OSError, ValueError) as e:
            logger.error("Erreur extraction streaming: %s", e)
            yield {"success": False, "error": str(e)}

    def _process_batch(
        self, batch: list[str], start_line: int,
    ) -> Generator[dict[str, Any], None, None]:
        """Traite un lot de lignes"""
        try:
            for i, line in enumerate(batch):
                line_num = start_line + i

                # Traitement optimisé de la ligne
                if self._should_process_line(line.strip()):
                    if self._is_dialogue_line(line.strip()):
                        # Extraction optimisée des dialogues
                        dialogue_result = self._extract_dialogue_optimized(line, line_num)
                        if dialogue_result:
                            yield dialogue_result

                    # Extraction optimisée des astérisques
                    asterisk_result = self._extract_asterisks_optimized(line, line_num)
                    if asterisk_result:
                        yield asterisk_result

                    # Extraction optimisée des tildes
                    tilde_result = self._extract_tildes_optimized(line, line_num)
                    if tilde_result:
                        yield tilde_result

        except (OSError, ValueError) as e:
            logger.error("Erreur traitement lot: %s", e)

    @lru_cache(maxsize=500)
    def _should_process_line(self, line: str) -> bool:
        """Vérifie si une ligne doit être traitée (avec cache)"""
        if not line or line.startswith("#"):
            return False

        # Patterns optimisés
        patterns = [
            r'^\s*"[^"]*"\s*$',  # Ligne de dialogue simple
            r"^\s*\*[^*]*\*",  # Astérisques
            r"^\s*~[^~]*~",  # Tildes
        ]

        return any(re.match(pattern, line) for pattern in patterns)

    @lru_cache(maxsize=500)
    def _is_dialogue_line(self, line: str) -> bool:
        """Vérifie si une ligne est un dialogue (avec cache)"""
        return bool(re.match(r'^\s*"[^"]*"\s*$', line))

    def _extract_dialogue_optimized(self, line: str, line_num: int) -> dict[str, Any] | None:
        """Extraction optimisée des dialogues"""
        try:
            # Pattern optimisé pour extraire le contenu entre guillemets
            match = re.search(r'"([^"]*)"', line)
            if match:
                content = match.group(1)

                # Vérifier les doublons de manière optimisée
                if self.duplicate_manager.check_and_add(content):
                    return {
                        "type": "duplicate",
                        "content": content,
                        "line": line_num,
                        "original_line": line.strip(),
                    }
                return {
                    "type": "unique",
                    "content": content,
                    "line": line_num,
                    "original_line": line.strip(),
                }
        except (OSError, ValueError) as e:
            logger.error("Erreur extraction dialogue: %s", e)

        return None

    def _extract_asterisks_optimized(self, line: str, line_num: int) -> dict[str, Any] | None:
        """Extraction optimisée des astérisques"""
        try:
            # Pattern optimisé pour les astérisques
            asterisk_pattern = r"\*+([^*]+)\*+"
            matches = re.findall(asterisk_pattern, line)

            if matches:
                for match in matches:
                    content = match.strip()
                    if content:
                        return {
                            "type": "asterisk",
                            "content": content,
                            "line": line_num,
                            "original_line": line.strip(),
                        }
        except (OSError, ValueError) as e:
            logger.error("Erreur extraction astérisques: %s", e)

        return None

    def _extract_tildes_optimized(self, line: str, line_num: int) -> dict[str, Any] | None:
        """Extraction optimisée des tildes"""
        try:
            # Pattern optimisé pour les tildes
            tilde_pattern = r"~+([^~]+)~+"
            matches = re.findall(tilde_pattern, line)

            if matches:
                for match in matches:
                    content = match.strip()
                    if content:
                        return {
                            "type": "tilde",
                            "content": content,
                            "line": line_num,
                            "original_line": line.strip(),
                        }
        except (OSError, ValueError) as e:
            logger.error("Erreur extraction tildes: %s", e)

        return None

    def _finalize_extraction(self, filepath: str, start_time: float) -> dict[str, Any]:
        """Finalise l'extraction et retourne les résultats"""
        extraction_time = time.time() - start_time

        # Compter les résultats
        self._counters["extracted"] = len(self._texts["extracted"])
        self._counters["asterix"] = len(self._texts["asterix"])
        self._counters["tilde"] = len(self._texts["tilde"])
        self._counters["empty"] = len(self._texts["empty"])

        logger.info("✅ Extraction terminée en %.2fs", extraction_time)
        logger.info("  - Dialogues: %d", self._counters["extracted"])
        logger.info("  - Astérisques: %d", self._counters["asterix"])
        logger.info("  - Tildes: %d", self._counters["tilde"])
        logger.info("  - Vides: %d", self._counters["empty"])

        return {
            "success": True,
            "filepath": filepath,
            "extraction_time": extraction_time,
            "extracted_count": self._counters["extracted"],
            "asterix_count": self._counters["asterix"],
            "tilde_count": self._counters["tilde"],
            "empty_count": self._counters["empty"],
            "duplicate_count": len(self.duplicate_manager.duplicate_texts_for_translation),
            "extracted_texts": self._texts["extracted"],
            "asterix_texts": self._texts["asterix"],
            "tilde_texts": self._texts["tilde"],
            "empty_texts": self._texts["empty"],
            "duplicate_texts": self.duplicate_manager.duplicate_texts_for_translation,
        }

    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._file_hash_cache.clear()
        logger.info("🗑️ Cache vidé")

    def get_cache_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_hit_ratio": len(self._cache) / self.cache_size if self.cache_size > 0 else 0,
            "cached_files": list(self._cache.keys()),
        }


class PlaceholderGenerator:
    """Générateur de placeholders optimisé"""

    def __init__(self, pattern: str):
        self.pattern = pattern
        self.counter = 0
        self._parse_pattern()

    def _parse_pattern(self):
        """Parse le pattern pour extraire le préfixe et le numéro"""
        match = re.match(r"([A-Z_]+)(\d+)", self.pattern)
        if match:
            self.prefix = match.group(1)
            self.start_number = int(match.group(2))
            self.counter = self.start_number - 1
        else:
            self.prefix = self.pattern
            self.start_number = 1
            self.counter = 0

    def next_placeholder(self) -> str:
        """Génère le prochain placeholder"""
        self.counter += 1
        return f"{self.prefix}_{self.counter:03d}"


class DuplicateManager:
    """Gestionnaire de doublons optimisé"""

    def __init__(self):
        self.seen_texts = set()
        self.duplicate_texts_for_translation = []
        self._text_counts = defaultdict(int)

    def check_and_add(self, text: str) -> bool:
        """Vérifie et ajoute un texte, retourne True si c'est un doublon"""
        if text in self.seen_texts:
            self._text_counts[text] += 1
            if self._text_counts[text] == 2:  # Premier doublon
                self.duplicate_texts_for_translation.append(text)
            return True
        self.seen_texts.add(text)
        self._text_counts[text] = 1
        return False

    def get_duplicate_stats(self) -> dict[str, Any]:
        """Retourne les statistiques des doublons"""
        return {
            "total_unique": len(self.seen_texts),
            "total_duplicates": len(self.duplicate_texts_for_translation),
            "duplicate_ratio": len(self.duplicate_texts_for_translation) / len(self.seen_texts)
            if self.seen_texts
            else 0,
        }


# Instance globale optimisée
optimized_extractor = OptimizedTextExtractor(cache_size=1000)
