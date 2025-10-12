#!/usr/bin/env python3
"""Service de traduction intégré pour RenExtract"""

import importlib.util
import logging
import subprocess
import sys
import time
from pathlib import Path

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

# Imports conditionnels pour les dépendances optionnelles
try:
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

logger = logging.getLogger(__name__)


class TranslatorService:
    """Service de traduction utilisant des modèles NLLB intégrés"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent.parent.parent
        self.translator_dir = self.base_dir / "translator"
        self.models_dir = self.translator_dir / "models"
        self.scripts_dir = self.translator_dir / "scripts"

        # Configuration par défaut
        self.default_model = "virusf/nllb-renpy-rory-v4"
        self.supported_languages = {
            "auto": "Détection automatique",
            "eng_Latn": "Anglais",
            "fra_Latn": "Français",
            "spa_Latn": "Espagnol",
            "deu_Latn": "Allemand",
            "ita_Latn": "Italien",
            "por_Latn": "Portugais",
            "rus_Cyrl": "Russe",
            "jpn_Jpan": "Japonais",
            "kor_Hang": "Coréen",
            "zho_Hans": "Chinois simplifié",
        }

    def is_available(self) -> bool:
        """Vérifie si le service de traduction est disponible"""
        try:
            # Vérifier si les dépendances sont installées
            torch_spec = importlib.util.find_spec("torch")
            transformers_spec = importlib.util.find_spec("transformers")

            if not torch_spec or not transformers_spec:
                logger.warning("Dépendances de traduction non installées")
                return False

            # Vérifier si le modèle est disponible
            return self._check_model_availability()
        except (OSError, ImportError, RuntimeError) as e:
            logger.warning("Erreur lors de la vérification des dépendances: %s", e)
            return False

    def _check_model_availability(self) -> bool:
        """Vérifie si le modèle de traduction est disponible"""
        try:
            model_name = self.default_model
            AutoTokenizer.from_pretrained(model_name)
            AutoModelForSeq2SeqLM.from_pretrained(model_name)

            logger.info("Modèle de traduction %s disponible", model_name)
            return True
        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.warning("Modèle de traduction non disponible: %s", e)
            return False

    def get_health_status(self) -> dict:
        """Retourne le statut de santé du service de traduction"""
        try:
            available = self.is_available()

            if available:
                # Essayer de récupérer des informations sur le modèle
                try:
                    AutoTokenizer.from_pretrained(self.default_model)
                    model_info = {
                        "success": True,
                        "exists": True,
                        "model": self.default_model,
                        "languages": list(self.supported_languages.keys()),
                        "gitHead": None,  # Pas de git pour les modèles HuggingFace
                    }
                except (OSError, ImportError, RuntimeError, ValueError) as e:
                    model_info = {
                        "success": True,
                        "exists": True,
                        "model": self.default_model,
                        "error": f"Erreur lors de la récupération des infos: {e}",
                    }
            else:
                model_info = {
                    "success": False,
                    "exists": False,
                    "error": "Service de traduction non disponible",
                }

            return model_info

        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.error("Erreur lors de la vérification du statut: %s", e)
            return {
                "success": False,
                "exists": False,
                "error": f"Erreur: {e}",
            }

    def translate_text(
        self, text: str, source_lang: str = "auto", target_lang: str = "fra_Latn"
    ) -> dict:
        """Traduit un texte"""
        try:
            if not self.is_available():
                return {"success": False, "error": "Service de traduction non disponible"}

            # Charger le modèle
            model_name = self.default_model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            # Préparer le texte pour la traduction
            if source_lang == "auto":
                # Pour la détection automatique, on assume que c'est de l'anglais
                source_lang = "eng_Latn"

            # Créer le prompt pour NLLB
            prompt = f"{source_lang} {target_lang} {text}"

            # Tokeniser et traduire
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

            with torch.no_grad():
                outputs = model.generate(
                    **inputs, max_new_tokens=128, num_beams=4, early_stopping=True, do_sample=False
                )

            # Décoder la traduction
            translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "source_language": source_lang,
                "target_language": target_lang,
                "model": model_name,
            }

        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.error("Erreur lors de la traduction: %s", e)
            return {"success": False, "error": f"Erreur de traduction: {e}", "original_text": text}

    def translate_files(
        self,
        input_folder: str,
        recursive: bool = True,
        source_lang: str = "auto",
        target_lang: str = "fra_Latn",
        translation_scope: str = "all",
        selected_file: str | None = None,
        progress_callback=None,
    ) -> dict:
        """Traduit des fichiers dans un dossier"""
        try:
            if not self.is_available():
                return {"success": False, "error": "Service de traduction non disponible"}

            input_path = Path(input_folder)
            if not input_path.exists():
                return {"success": False, "error": f"Dossier d'entrée non trouvé: {input_folder}"}

            # Charger le modèle de traduction
            model_name = self.default_model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            files_processed = 0
            files_translated = 0
            stdout_messages = []
            stderr_messages = []

            # Parcourir les fichiers .rpy
            logger.info("Scope: %s, fichier sélectionné: %s", translation_scope, selected_file)

            if translation_scope == "specific" and selected_file:
                # Traiter seulement le fichier spécifique
                specific_file = input_path / selected_file
                logger.info("Fichier spécifique: %s", specific_file)
                if specific_file.exists():
                    rpy_files = [specific_file]
                    logger.info("Fichier spécifique trouvé, traitement d'un seul fichier")
                else:
                    logger.error("Fichier spécifique non trouvé: %s", specific_file)
                    return {
                        "success": False,
                        "error": f"Fichier spécifique non trouvé: {selected_file}",
                    }
            else:
                # Traiter tous les fichiers du dossier
                pattern = "**/*.rpy" if recursive else "*.rpy"
                rpy_files = list(input_path.glob(pattern))
                logger.info("Mode tous les fichiers, %d fichiers trouvés", len(rpy_files))

            if not rpy_files:
                return {
                    "success": True,
                    "message": f"Aucun fichier .rpy trouvé dans {input_path}",
                    "input_folder": str(input_path),
                    "files_processed": 0,
                    "files_translated": 0,
                    "stdout": "Aucun fichier à traduire",
                    "stderr": "",
                }

            stdout_messages.append(f"Traitement de {len(rpy_files)} fichiers...")
            logger.info("Début de la traduction de %d fichiers", len(rpy_files))

            if progress_callback:
                progress_callback(f"Traitement de {len(rpy_files)} fichiers...", 0)

            for i, rpy_file in enumerate(rpy_files):
                try:
                    files_processed += 1
                    progress = int((i / len(rpy_files)) * 100)
                    stdout_messages.append(f"Traitement de {rpy_file.name}...")
                    logger.info("Traitement du fichier: %s", rpy_file.name)

                    if progress_callback:
                        progress_callback(f"Traitement de {rpy_file.name}...", progress)

                    # Lire le fichier
                    with open(rpy_file, encoding="utf-8") as f:
                        content = f.read()

                    logger.info("Fichier %s lu, taille: %d caractères", rpy_file.name, len(content))

                    # Extraire les chaînes de dialogue (lignes qui commencent par des guillemets)
                    lines = content.split("\n")
                    translated_lines = []
                    trans_made = 0

                    for line in lines:
                        stripped = line.strip()
                        # Détecter les lignes de dialogue (commencent par des guillemets)
                        if stripped.startswith('"') and stripped.endswith('"'):
                            # Extraire le texte entre guillemets
                            text = stripped[1:-1]  # Enlever les guillemets

                            if text.strip():  # Si le texte n'est pas vide
                                # Traduire le texte
                                if source_lang == "auto":
                                    source_lang = "eng_Latn"  # Assume anglais par défaut

                                prompt = f"{source_lang} {target_lang} {text}"
                                inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

                                with torch.no_grad():
                                    outputs = model.generate(
                                        **inputs,
                                        max_new_tokens=128,
                                        num_beams=4,
                                        early_stopping=True,
                                        do_sample=False,
                                    )

                                translated_text = tokenizer.decode(
                                    outputs[0], skip_special_tokens=True
                                )
                                translated_lines.append(f'    "{translated_text}"')
                                trans_made += 1
                            else:
                                translated_lines.append(line)
                        else:
                            translated_lines.append(line)

                    # Créer le fichier de sortie
                    output_file = rpy_file.parent / f"{rpy_file.stem}_translated.rpy"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(translated_lines))

                    files_translated += 1
                    stdout_messages.append(
                        f"  ✓ {rpy_file.name} → {output_file.name} ({trans_made} traductions)"
                    )

                except (OSError, ImportError, RuntimeError, ValueError) as e:
                    stderr_messages.append(f"Erreur lors du traitement de {rpy_file.name}: {e}")
                    continue

            return {
                "success": True,
                "message": f"Traduction terminée: {files_translated}/{files_processed} "
                f"fichiers traités",
                "input_folder": str(input_path),
                "files_processed": files_processed,
                "files_translated": files_translated,
                "stdout": "\n".join(stdout_messages),
                "stderr": "\n".join(stderr_messages),
            }

        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.error("Erreur lors de la traduction des fichiers: %s", e)
            return {"success": False, "error": f"Erreur: {e}", "stdout": "", "stderr": str(e)}

    def translate_files_with_progress(
        self,
        input_folder: str,
        recursive: bool = True,
        source_lang: str = "auto",
        target_lang: str = "fra_Latn",
        translation_scope: str = "all",
        selected_file: str | None = None,
        progress_callback=None,
    ) -> dict:
        """Traduit des fichiers avec progression détaillée"""
        try:
            if not self.is_available():
                return {"success": False, "error": "Service de traduction non disponible"}

            input_path = Path(input_folder)
            if not input_path.exists():
                return {"success": False, "error": f"Dossier d'entrée non trouvé: {input_folder}"}

            # Charger le modèle de traduction
            model_name = self.default_model
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

            files_processed = 0
            files_translated = 0
            stdout_messages = []
            stderr_messages = []

            # Parcourir les fichiers .rpy
            logger.info("Scope: %s, fichier sélectionné: %s", translation_scope, selected_file)

            if translation_scope == "specific" and selected_file:
                # Traiter seulement le fichier spécifique
                specific_file = input_path / selected_file
                logger.info("Fichier spécifique: %s", specific_file)
                if specific_file.exists():
                    rpy_files = [specific_file]
                    logger.info("Fichier spécifique trouvé, traitement d'un seul fichier")
                else:
                    logger.error("Fichier spécifique non trouvé: %s", specific_file)
                    return {
                        "success": False,
                        "error": f"Fichier spécifique non trouvé: {selected_file}",
                    }
            else:
                # Traiter tous les fichiers du dossier
                pattern = "**/*.rpy" if recursive else "*.rpy"
                rpy_files = list(input_path.glob(pattern))
                logger.info("Mode tous les fichiers, %d fichiers trouvés", len(rpy_files))

            if not rpy_files:
                return {
                    "success": True,
                    "message": f"Aucun fichier .rpy trouvé dans {input_path}",
                    "input_folder": str(input_path),
                    "files_processed": 0,
                    "files_translated": 0,
                    "stdout": "Aucun fichier à traduire",
                    "stderr": "",
                }

            stdout_messages.append(f"Traitement de {len(rpy_files)} fichiers...")
            logger.info("Début de la traduction de %d fichiers", len(rpy_files))

            if progress_callback:
                progress_callback(f"Traitement de {len(rpy_files)} fichiers...", 0, 0, 0, 0, 0.0)

            # Variables pour le timing
            start_time = time.time()
            total_translations = 0

            for i, rpy_file in enumerate(rpy_files):
                try:
                    files_processed += 1
                    file_progress = int((i / len(rpy_files)) * 100)
                    stdout_messages.append(f"Traitement de {rpy_file.name}...")
                    logger.info("Traitement du fichier: %s", rpy_file.name)

                    if progress_callback:
                        progress_callback(
                            f"Traitement de {rpy_file.name}...", file_progress, 0, 0, 0, 0.0
                        )

                    # Lire le fichier
                    with open(rpy_file, encoding="utf-8") as f:
                        content = f.read()

                    logger.info("Fichier %s lu, taille: %d caractères", rpy_file.name, len(content))

                    # Extraire les chaînes de dialogue (lignes qui commencent par des guillemets)
                    lines = content.split("\n")
                    translated_lines = []
                    translations_made = 0
                    total_lines = 0

                    # Compter d'abord le nombre total de lignes de dialogue
                    for line in lines:
                        stripped = line.strip()
                        if (
                            stripped.startswith('"')
                            and stripped.endswith('"')
                            and stripped[1:-1].strip()
                        ):
                            total_lines += 1

                    if progress_callback:
                        progress_callback(
                            f"Traduction de {rpy_file.name}...",
                            file_progress,
                            0,
                            total_lines,
                            total_lines,
                            0.0,
                        )

                    for line in enumerate(lines):
                        stripped = line.strip()
                        # Détecter les lignes de dialogue (commencent par des guillemets)
                        if stripped.startswith('"') and stripped.endswith('"'):
                            # Extraire le texte entre guillemets
                            text = stripped[1:-1]  # Enlever les guillemets

                            if text.strip():  # Si le texte n'est pas vide
                                # Traduire le texte
                                if source_lang == "auto":
                                    source_lang = "eng_Latn"  # Assume anglais par défaut

                                prompt = f"{source_lang} {target_lang} {text}"
                                inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

                                with torch.no_grad():
                                    outputs = model.generate(
                                        **inputs,
                                        max_new_tokens=128,
                                        num_beams=4,
                                        early_stopping=True,
                                        do_sample=False,
                                    )

                                translated_text = tokenizer.decode(
                                    outputs[0], skip_special_tokens=True
                                )
                                translated_lines.append(f'    "{translated_text}"')
                                translations_made += 1
                                total_translations += 1

                                # Mettre à jour la progression
                                remaining_lines = total_lines - translations_made
                                current_time = time.time()
                                elapsed_time = current_time - start_time
                                lines_per_second = (
                                    total_translations / elapsed_time if elapsed_time > 0 else 0.0
                                )

                                if progress_callback:
                                    progress_callback(
                                        f"Traduction ligne {translations_made}/{total_lines}",
                                        file_progress,
                                        +int(
                                            (translations_made / total_lines)
                                            * (100 / len(rpy_files))
                                        ),
                                        translations_made,
                                        total_lines,
                                        remaining_lines,
                                        lines_per_second,
                                    )
                            else:
                                translated_lines.append(line)
                        else:
                            translated_lines.append(line)

                    # Créer le fichier de sortie
                    output_file = rpy_file.parent / f"{rpy_file.stem}_translated.rpy"
                    with open(output_file, "w", encoding="utf-8") as f:
                        f.write("\n".join(translated_lines))

                    files_translated += 1
                    stdout_messages.append(
                        f"  ✓ {rpy_file.name} → {output_file.name} "
                        f"({translations_made} traductions)"
                    )

                except (OSError, ImportError, RuntimeError, ValueError) as e:
                    stderr_messages.append(f"Erreur lors du traitement de {rpy_file.name}: {e}")
                    continue

            return {
                "success": True,
                "message": f"Traduction terminée: {files_translated}/{files_processed} "
                f"fichiers traités",
                "input_folder": str(input_path),
                "files_processed": files_processed,
                "files_translated": files_translated,
                "stdout": "\n".join(stdout_messages),
                "stderr": "\n".join(stderr_messages),
            }

        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.error("Erreur lors de la traduction des fichiers: %s", e)
            return {"success": False, "error": f"Erreur: {e}", "stdout": "", "stderr": str(e)}

    def get_available_files(self, project_path: str | None = None) -> dict:
        """Récupère les fichiers de traduction disponibles"""
        try:
            # Utiliser le chemin du projet si fourni, sinon le base_dir
            if project_path:
                project_dir = Path(project_path)
            else:
                project_dir = self.base_dir

            # Scanner les dossiers tl/ pour trouver les fichiers de traduction
            tl_dir = project_dir / "tl"

            if not tl_dir.exists():
                return {
                    "success": True,
                    "files": [],
                    "languages": [],
                    "message": f"Aucun dossier de traduction trouvé dans {tl_dir}",
                }

            files = []
            languages = set()

            # Parcourir les dossiers de langues
            for lang_dir in tl_dir.iterdir():
                if lang_dir.is_dir():
                    languages.add(lang_dir.name)

                    # Parcourir les fichiers .rpy dans chaque dossier de langue
                    for rpy_file in lang_dir.glob("*.rpy"):
                        relative_path = rpy_file.relative_to(project_dir)
                        files.append(str(relative_path))

            return {
                "success": True,
                "files": sorted(files),
                "languages": sorted(languages),
                "message": f"Trouvé {len(files)} fichiers dans {len(languages)} langues",
            }

        except (OSError, ImportError, RuntimeError, ValueError) as e:
            logger.error("Erreur lors de la récupération des fichiers: %s", e)
            return {"success": False, "error": f"Erreur: {e}", "files": [], "languages": []}

    def install_dependencies(self) -> dict:
        """Installe les dépendances nécessaires pour la traduction"""
        try:
            # Liste des packages nécessaires
            packages = ["torch", "transformers", "sentencepiece", "protobuf"]

            # Installer les packages
            for package in packages:
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", package],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    logger.info("Package %s installé avec succès", package)
                except subprocess.CalledProcessError as e:
                    logger.warning("Erreur lors de l'installation de %s: %s", package, e)

            return {
                "success": True,
                "message": "Dépendances installées avec succès",
                "packages": packages,
            }

        except (OSError, subprocess.SubprocessError, RuntimeError) as e:
            logger.error("Erreur lors de l'installation des dépendances: %s", e)
            return {"success": False, "error": f"Erreur: {e}"}


# Instance globale du service
translator_service = TranslatorService()
