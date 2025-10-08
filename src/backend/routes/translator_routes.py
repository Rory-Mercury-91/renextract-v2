"""
Routes pour l'intégration TranslationToolsIA
"""
import os
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError

from flask import Blueprint, jsonify, request

# Blueprint pour le traducteur
translator_bp = Blueprint('translator', __name__)


@translator_bp.route('/api/translator/health', methods=['GET'])
def translator_health():
    """Vérifie la présence du dépôt TranslationToolsIA et retourne des infos basiques."""
    try:
        repo_path = Path('external/TranslationToolsIA')
        exists = repo_path.exists()
        head = None
        if exists:
            try:
                # Lire le commit courant si git est présent
                result = subprocess.run(
                    ['git', '-C', str(repo_path), 'rev-parse',
                     '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                head = result.stdout.strip()
            except (CalledProcessError, FileNotFoundError):
                head = None

        return jsonify({
            'success': True,
            'exists': exists,
            'gitHead': head
        })
    except (OSError, ValueError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@translator_bp.route('/api/translator/run', methods=['POST'])
def translator_run():
    """Lance la traduction via TranslationToolsIA pour un dossier Ren'Py."""
    try:
        data = request.get_json() or {}
        input_folder = data.get('inputFolder')
        recursive = bool(data.get('recursive', True))
        model_path = data.get('modelPath', 'virusf/nllb-renpy-rory-v4')
        source_lang = data.get('sourceLang', 'auto')
        target_lang = data.get('targetLang', 'fra_Latn')

        if not input_folder or not os.path.isdir(input_folder):
            return jsonify(
                {'success': False, 'error': 'Dossier source invalide'}), 400

        repo_path = Path('external/TranslationToolsIA')
        if not repo_path.exists():
            return jsonify({
                'success': False,
                'error': (
                    'TranslationToolsIA non installé. '
                    'Exécutez pnpm run ttia:clone'
                )
            }), 400

        candidate_scripts = [
            repo_path / 'script' / 'traducteur_renpy_jeu_complet.py',
            repo_path / 'script' / 'traducteur_renpy.py',
        ]
        script_path = None
        for c in candidate_scripts:
            if c.exists():
                script_path = c
                break
        if script_path is None:
            return jsonify({
                'success': False,
                'error': 'Script de traduction introuvable dans TranslationToolsIA'
            }), 500

        cmd = [
            sys.executable,
            str(script_path),
            '--input-folder', input_folder,
            '--recursive', str(int(recursive)),
            '--model', model_path,
            '--source', source_lang,
            '--target', target_lang
        ]

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        success = proc.returncode == 0
        return jsonify({
            'success': success,
            'returncode': proc.returncode,
            'stdout': proc.stdout[-5000:],
            'stderr': proc.stderr[-5000:],
        }), (200 if success else 500)
    except (OSError, ValueError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500
