# src/backend/core/coherence.py
# Version optimisée de la vérification de cohérence avec cache et
# parallélisation

"""Module de vérification de cohérence optimisé pour RenExtract v2."""

import glob
import hashlib
import logging
import os
import re
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from functools import lru_cache
from typing import Any

from src.backend.api.coherence_html import generate_modern_html_report

logger = logging.getLogger(__name__)


class OptimizedCoherenceChecker:
    """Vérificateur de cohérence optimisé avec cache et parallélisation"""

    def __init__(self, max_workers: int = 4, cache_size: int = 500):
        """Initialise le vérificateur optimisé"""
        self.max_workers = max_workers
        self.cache_size = cache_size
        self._cache = {}
        self._file_hash_cache = {}

        # Options de vérification
        self.options = {
            "check_variables": True,
            "check_tags": True,
            "check_untranslated": True,
            "check_ellipsis": True,
            "check_escape_sequences": True,
            "check_percentages": True,
            "check_quotations": True,
            "check_parentheses": True,
            "check_syntax": True,
            "check_deepl_ellipsis": True,
            "check_isolated_percent": True,
            "check_french_quotes": True,
            "check_double_dash_ellipsis": True,
            "check_special_codes": False,
            "check_line_structure": True,
            "custom_exclusions": ["OK", "Menu", "Continue", "Yes", "No", "Level"],
        }

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

    def _update_cache(self, filepath: str, result: list[dict[str, Any]]):
        """Met à jour le cache avec les résultats"""
        if len(self._cache) >= self.cache_size:
            # Supprimer le plus ancien
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]

        self._cache[filepath] = result
        self._file_hash_cache[filepath] = self._get_file_hash(filepath)

    def _get_cached_result(self, filepath: str) -> list[dict[str, Any]] | None:
        """Récupère le résultat depuis le cache"""
        if filepath in self._cache:
            return self._cache.get(filepath, [])
        return None

    def check_coherence_parallel(
        self,
        target_path: str,
        return_details: bool = False,
        selection_info: dict | None = None,
    ) -> Any:
        """Vérification de cohérence avec parallélisation"""
        start_time = time.time()

        try:
            logger.info("🔍 Début vérification cohérence optimisée: %s", target_path)

            # 1. Déterminer les fichiers à analyser
            if os.path.isfile(target_path):
                files_to_check = [target_path]
            else:
                files_to_check = self._find_translation_files_optimized(target_path)

            logger.info("📂 %d fichier(s) à analyser", len(files_to_check))

            # 2. Analyser les fichiers en parallèle
            all_issues = []

            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Soumettre les tâches
                future_to_file = {
                    executor.submit(self._check_file_coherence_optimized, file_path): file_path
                    for file_path in files_to_check
                }

                # Collecter les résultats
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        issues = future.result()
                        all_issues.extend(issues)
                        logger.debug(
                            "✅ %s: %d problème(s)",
                            os.path.basename(file_path),
                            len(issues),
                        )
                    except (OSError, ValueError, TypeError) as e:
                        logger.error("❌ Erreur analyse %s: %s", file_path, e)

            # 3. Calculer les statistiques
            stats = self._calculate_statistics_optimized(all_issues, len(files_to_check))

            # 4. Générer le rapport
            rapport_path = self._generate_coherence_report_optimized(
                all_issues,
                target_path,
                selection_info,
                stats,
            )

            analysis_time = time.time() - start_time
            logger.info(
                "✅ Vérification terminée en %.2fs - %d problème(s)",
                analysis_time,
                stats["total_issues"],
            )

            # 5. Retourner les résultats
            if return_details:
                return {
                    "rapport_path": rapport_path,
                    "stats": stats,
                    "issues": all_issues,
                    "analysis_time": analysis_time,
                }
            return rapport_path

        except Exception as e:
            logger.error("Erreur vérification cohérence: %s", e)
            raise

    def _find_translation_files_optimized(self, target_path: str) -> list[str]:
        """Trouve les fichiers de traduction de manière optimisée"""
        try:
            if not os.path.exists(target_path):
                return []

            # Recherche optimisée avec glob
            pattern = os.path.join(target_path, "**", "*.rpy")
            files = glob.glob(pattern, recursive=True)

            # Filtrer selon les exclusions
            excluded_files = self.options.get("custom_exclusions", [])
            filtered_files = []

            for file_path in files:
                filename = os.path.basename(file_path)
                should_exclude = False

                for exclusion in excluded_files:
                    if exclusion.lower() in filename.lower():
                        should_exclude = True
                        break

                if not should_exclude:
                    filtered_files.append(file_path)

            return sorted(filtered_files)

        except (OSError, ValueError) as e:
            logger.error("Erreur recherche fichiers: %s", e)
            return []

    def _check_file_coherence_optimized(self, file_path: str) -> list[dict[str, Any]]:
        """Analyse la cohérence d'un fichier de manière optimisée"""
        try:
            # Vérifier le cache d'abord
            cached_result = self._get_cached_result(file_path)
            if cached_result:
                logger.debug("📋 Utilisation du cache pour %s", os.path.basename(file_path))
                return cached_result

            issues = []

            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            old_line = None

            # Traitement optimisé ligne par ligne
            for i, line in enumerate(lines, 1):
                stripped = line.strip()

                # Ignorer les commentaires de fichier
                if stripped.startswith("# ") and not stripped.startswith('# "'):
                    continue

                # Détecter les lignes OLD
                if self._is_old_line_optimized(stripped):
                    if not self._is_voice_line_optimized(stripped):
                        # Extraire le texte entre # " et "
                        old_line = stripped[3:-1]
                    continue

                # Détecter les lignes NEW
                if self._is_new_line_optimized(stripped):
                    if not self._is_voice_line_optimized(stripped):
                        new_line = stripped[1:-1] if stripped.endswith('"') else stripped[1:]

                        if old_line:
                            # Vérifier la cohérence OLD/NEW
                            line_issues = self._check_line_coherence_optimized(
                                old_line,
                                new_line,
                                file_path,
                                i,
                            )
                            issues.extend(line_issues)

                            # Reset pour la prochaine paire
                            old_line = None

            # Mettre en cache
            self._update_cache(file_path, issues)

            logger.debug("Fichier %s: %d problème(s)", os.path.basename(file_path), len(issues))
            return issues

        except (OSError, ValueError) as e:
            logger.error("Erreur analyse fichier %s: %s", file_path, e)
            return []

    @lru_cache(maxsize=1000)
    def _is_old_line_optimized(self, line: str) -> bool:
        """Vérifie si une ligne est une ligne OLD (avec cache)"""
        return line.startswith('# "') and line.endswith('"')

    @lru_cache(maxsize=1000)
    def _is_new_line_optimized(self, line: str) -> bool:
        """Vérifie si une ligne est une ligne NEW (avec cache)"""
        if line.startswith("# "):
            return False

        return '"' in line and not line.startswith("#")

    @lru_cache(maxsize=1000)
    def _is_voice_line_optimized(self, line: str) -> bool:
        """Vérifie si une ligne contient une instruction voice (avec cache)"""
        return "voice " in line and '"' in line

    def _check_line_coherence_optimized(
        self,
        old_line: str,
        new_line: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie la cohérence entre une ligne OLD et NEW de manière optimisée"""
        issues = []

        try:
            old_text = old_line.strip()
            new_text = new_line.strip()

            if not old_text or not new_text:
                return issues

            # Vérifications optimisées selon les options
            if self.options.get("check_untranslated", True):
                if self._is_untranslated_line_optimized(old_text, new_text):
                    issues.append(
                        {
                            "file": file_path,
                            "line_number": line_number,
                            "type": "untranslated",
                            "message": "Ligne potentiellement non traduite (contenu identique)",
                            "old_content": old_text,
                            "new_content": new_text,
                        },
                    )
                    return issues  # Pas besoin de vérifier le reste si non traduit

            # Vérifications parallèles
            check_functions = []

            if self.options.get("check_variables", True):
                check_functions.append(("variables", self._check_variables_optimized))

            if self.options.get("check_tags", True):
                check_functions.append(("tags", self._check_tags_optimized))

            if self.options.get("check_escape_sequences", True):
                check_functions.append(("escape_sequences", self._check_escape_sequences_optimized))

            if self.options.get("check_percentages", True):
                check_functions.append(("percentages", self._check_percentages_optimized))

            if self.options.get("check_parentheses", True):
                check_functions.append(("parentheses", self._check_parentheses_optimized))

            if self.options.get("check_deepl_ellipsis", True):
                check_functions.append(("deepl_ellipsis", self._check_deepl_ellipsis_optimized))

            if self.options.get("check_isolated_percent", True):
                check_functions.append(("isolated_percent", self._check_isolated_percent_optimized))

            if self.options.get("check_french_quotes", True):
                check_functions.append(("french_quotes", self._check_french_quotes_optimized))

            if self.options.get("check_double_dash_ellipsis", True):
                check_functions.append(
                    ("double_dash_ellipsis", self._check_double_dash_ellipsis_optimized),
                )

            # Exécuter les vérifications
            for check_name, check_func in check_functions:
                try:
                    check_issues = check_func(old_text, new_text, file_path, line_number)
                    issues.extend(check_issues)
                except (OSError, ValueError) as e:
                    logger.error("Erreur vérification %s: %s", check_name, e)

        except (OSError, ValueError) as e:
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "analysis_error",
                    "message": f"Erreur d'analyse: {e!s}",
                    "old_content": old_line,
                    "new_content": new_line,
                },
            )

        return issues

    @lru_cache(maxsize=1000)
    def _is_untranslated_line_optimized(self, old_text: str, new_text: str) -> bool:
        """Vérifie si une ligne est probablement non traduite (avec cache)"""
        if old_text.strip() != new_text.strip():
            return False

        text = old_text.strip()

        # Auto-exclusions optimisées
        if self._is_auto_excluded_optimized(text):
            return False

        # Exclusions personnalisées
        custom_exclusions = self.options.get("custom_exclusions", [])
        if text in custom_exclusions:
            return False

        # Si le texte est court et contient peu de mots, probablement OK
        if len(text) <= 3 or len(text.split()) <= 1:
            return False

        return True

    @lru_cache(maxsize=1000)
    def _is_auto_excluded_optimized(self, text: str) -> bool:
        """Vérifie les auto-exclusions par défaut (avec cache)"""
        # Ellipsis
        if self.options.get("check_ellipsis", True) and text in ["...", "…", "....", "....."]:
            return True

        # Variables seules
        if re.match(r"^\[[^\]]+\]", text):
            return True

        # Balises seules
        if re.match(r"^\{[^}]*\}", text):
            return True

        # Texte vide ou espaces
        if not text or text.isspace():
            return True

        # Ponctuations expressives
        if re.match(r"^[!?…\.]+", text):
            return True

        # Onomatopées courtes
        if len(text) <= 3 and re.match(r"^[A-Za-z]+[!?]*", text):
            return True

        return False

    def _check_variables_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie la cohérence des variables [] de manière optimisée"""
        issues = []

        try:
            old_vars = re.findall(r"\[[^\]]*\]", old_text)
            new_vars = re.findall(r"\[[^\]]*\]", new_text)

            # Normaliser les variables
            old_vars_norm = [self._normalize_variable_optimized(var) for var in old_vars]
            new_vars_norm = [self._normalize_variable_optimized(var) for var in new_vars]

            if sorted(old_vars_norm) != sorted(new_vars_norm):
                issues.append(
                    {
                        "file": file_path,
                        "line_number": line_number,
                        "type": "variable_mismatch",
                        "message": f"Variables incohérentes => Attendu: {old_vars}, "
                        f"Présent: {new_vars}",
                        "old_content": old_text,
                        "new_content": new_text,
                    },
                )

        except (OSError, ValueError):
            pass

        return issues

    @lru_cache(maxsize=1000)
    def _normalize_variable_optimized(self, variable: str) -> str:
        """Normalise une variable en enlevant les fonctions de traduction (avec cache)"""
        return re.sub(r"![tulc]", "", variable)

    def _check_tags_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie que les balises {xxx} sont équilibrées de manière optimisée"""
        issues = []

        # Vérifier l'équilibre des accolades
        new_open = new_text.count("{")
        new_close = new_text.count("}")

        if new_open != new_close:
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "tags_unbalanced",
                    "severity": "error",
                    "message": f"Balises déséquilibrées: {new_open} {{ mais {new_close} }}",
                    "old_line": old_text,
                    "new_line": new_text,
                },
            )

        return issues

    def _check_escape_sequences_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie la cohérence des séquences d'échappement de manière optimisée"""
        issues = []

        escape_sequences = [r"\\n", r"\\t", r"\\r", r"\\\\"]

        for seq in escape_sequences:
            old_count = old_text.count(seq)
            new_count = new_text.count(seq)

            if old_count != new_count:
                seq_name = seq.replace("\\\\", "\\")
                issues.append(
                    {
                        "file": file_path,
                        "line_number": line_number,
                        "type": f"escape_sequence_{seq_name}",
                        "severity": "warning",
                        "message": f"Séquence {seq_name} incohérente: {old_count} → {new_count}",
                        "old_line": old_text,
                        "new_line": new_text,
                    },
                )

        return issues

    def _check_percentages_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie la cohérence des variables de formatage de manière optimisée"""
        issues = []

        # Pattern pour %s, %d, %f, etc.
        pattern = r"%[sdfioxXeEgGcr]"

        old_formats = re.findall(pattern, old_text)
        new_formats = re.findall(pattern, new_text)

        if len(old_formats) != len(new_formats):
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "format_variables",
                    "severity": "error",
                    "message": f"Variables de formatage incohérentes: {len(old_formats)} → {
                        len(new_formats)
                    }",
                    "old_line": old_text,
                    "new_line": new_text,
                },
            )

        return issues

    def _check_parentheses_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Vérifie l'équilibre des parenthèses de manière optimisée"""
        issues = []

        # Paires à vérifier
        pairs = [("(", ")", "parenthèses"), ("[", "]", "crochets"), ("{", "}", "accolades")]

        for open_char, close_char, name in pairs:
            open_count = new_text.count(open_char)
            close_count = new_text.count(close_char)

            if open_count != close_count:
                issues.append(
                    {
                        "file": file_path,
                        "line_number": line_number,
                        "type": f"{name}_unbalanced",
                        "severity": "error",
                        "message": f"{name.capitalize()} déséquilibrées: {open_count} ouvertures, "
                        f"{close_count} fermetures",
                        "old_line": old_text,
                        "new_line": new_text,
                    },
                )

        return issues

    def _check_deepl_ellipsis_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Détecte les ellipses DeepL de manière optimisée"""
        issues = []

        if "[...]" in new_text or "[…]" in new_text:
            count = new_text.count("[...]") + new_text.count("[…]")
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "deepl_ellipsis",
                    "severity": "warning",
                    "message": f"Ellipse DeepL détectée ({count}x) - devrait être '...'",
                    "old_line": old_text,
                    "new_line": new_text,
                },
            )

        return issues

    def _check_isolated_percent_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Détecte les % isolés de manière optimisée"""
        issues = []

        # Pattern pour % isolé
        pattern = r"(?<!%)%(?!%|[sdfioxXeEgGcr]|\([^)]+\))"

        matches = re.findall(pattern, new_text)

        if matches:
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "isolated_percent",
                    "severity": "error",
                    "message": f"Pourcentage isolé détecté ({len(matches)}x) - devrait être '%%'",
                    "old_line": old_text,
                    "new_line": new_text,
                },
            )

        return issues

    def _check_french_quotes_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Détecte les guillemets français de manière optimisée"""
        issues = []

        # Détecter « et »
        if "«" in new_text or "»" in new_text:
            count = new_text.count("«") + new_text.count("»")
            issues.append(
                {
                    "file": file_path,
                    "line_number": line_number,
                    "type": "french_quotes",
                    "severity": "warning",
                    "message": f'Guillemets français détectés ({count}x) - devraient être \\"',
                    "old_line": old_text,
                    "new_line": new_text,
                },
            )

        return issues

    def _check_double_dash_ellipsis_optimized(
        self,
        old_text: str,
        new_text: str,
        file_path: str,
        line_number: int,
    ) -> list[dict[str, Any]]:
        """Détecte les doubles tirets -- de manière optimisée"""
        issues = []

        # Détecter -- (mais pas --- ou plus)
        if "--" in new_text and "---" not in new_text:
            count = new_text.count("--") - new_text.count("---")

            if count > 0:
                issues.append(
                    {
                        "file": file_path,
                        "line_number": line_number,
                        "type": "double_dash_ellipsis",
                        "severity": "info",
                        "message": f"Ellipse (-- → ...) détectée ({count}x) - "
                        f"recommandation : utiliser '...' pour cohérence",
                        "old_line": old_text,
                        "new_line": new_text,
                    },
                )

        return issues

    def _calculate_statistics_optimized(
        self,
        all_issues: list[dict[str, Any]],
        files_analyzed: int,
    ) -> dict[str, Any]:
        """Calcule les statistiques des problèmes détectés de manière optimisée"""
        stats = {
            "files_analyzed": files_analyzed,
            "total_issues": len(all_issues),
            "issues_by_type": defaultdict(int),
            "issues_by_severity": defaultdict(int),
        }

        for issue in all_issues:
            issue_type = issue["type"]
            severity = issue.get("severity", "unknown")

            stats["issues_by_type"][issue_type] += 1
            stats["issues_by_severity"][severity] += 1

        # Convertir les defaultdict en dicts normaux
        stats["issues_by_type"] = dict(stats["issues_by_type"])
        stats["issues_by_severity"] = dict(stats["issues_by_severity"])

        return stats

    def _generate_coherence_report_optimized(
        self,
        all_issues: list[dict[str, Any]],
        target_path: str,
        selection_info: dict | None,
        stats: dict[str, Any],
    ) -> str:
        """Génère un rapport HTML de manière optimisée"""
        try:
            # Créer le dossier de rapports
            if selection_info and "project_path" in selection_info:
                project_path = selection_info["project_path"]
                project_name = os.path.basename(project_path)
                rapport_folder = os.path.join("02_Reports", project_name, "coherence")
            else:
                rapport_folder = "02_Reports"

            os.makedirs(rapport_folder, exist_ok=True)

            # Générer le nom du fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if selection_info:
                project_name = os.path.basename(selection_info.get("project_path", "")) or "unknown"
                rapport_name = f"{project_name}_coherence_optimized_{timestamp}.html"
            else:
                rapport_name = f"coherence_optimized_{timestamp}.html"

            rapport_path = os.path.join(rapport_folder, rapport_name)

            # Grouper les problèmes par fichier
            issues_by_file = defaultdict(list)
            for issue in all_issues:
                file_path = issue["file"]
                issues_by_file[file_path].append(issue)

            # Générer le HTML avec le design moderne
            html_content = generate_modern_html_report(
                issues_by_file,
                target_path,
                selection_info,
                stats,
            )

            # Sauvegarder
            with open(rapport_path, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info("📊 Rapport de cohérence optimisé généré: %s", rapport_path)
            return rapport_path

        except Exception as e:
            logger.error("Erreur génération rapport: %s", e)
            raise

    def clear_cache(self):
        """Vide le cache"""
        self._cache.clear()
        self._file_hash_cache.clear()
        logger.info("🗑️ Cache de cohérence vidé")

    def get_cache_stats(self) -> dict[str, Any]:
        """Retourne les statistiques du cache"""
        return {
            "cache_size": len(self._cache),
            "max_cache_size": self.cache_size,
            "cache_hit_ratio": len(self._cache) / self.cache_size if self.cache_size > 0 else 0,
            "cached_files": list(self._cache.keys()),
        }


# Instance globale optimisée
optimized_coherence_checker = OptimizedCoherenceChecker(max_workers=4, cache_size=500)
