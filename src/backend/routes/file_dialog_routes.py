"""
Routes pour les dialogues de fichiers et dossiers
"""
import tkinter as tk
from tkinter import filedialog
from typing import Callable, List, Optional, Tuple

from flask import Blueprint, jsonify, request

from src.backend.utils import is_wsl_environment

# Blueprint pour les dialogues de fichiers
file_dialog_bp = Blueprint('file_dialog', __name__)


def wsl_mode_response(endpoint_hint: str):
    """Réponse standardisée pour indiquer le mode WSL et l'endpoint à utiliser en POST."""
    return jsonify({
        'success': False,
        'error': 'WSL_MODE',
        'message': (
            f"En mode WSL, utilisez POST {endpoint_hint} avec le chemin en paramètre"
        )
    }), 400


def open_dialog_hybrid(  # pylint: disable=too-many-arguments
    dialog_type: str,
    *,
    title: Optional[str] = None,
    initialdir: Optional[str] = None,
    filetypes: Optional[List[Tuple[str, str]]] = None,
    initialfile: Optional[str] = None,
    defaultextension: Optional[str] = None,
    must_exist: bool = True,
    validate: Optional[Callable[[str], bool]] = None,
) -> str:
    """Ouvre un dialogue (fichier ou dossier) avec tkinter, sinon fallback web.

    - dialog_type: 'file' ou 'folder'
    - title: titre de la fenêtre
    - initialdir: répertoire initial
    - filetypes: liste de filtres (uniquement pour 'file')
    - must_exist: contraint la sélection à des chemins existants
    - validate: fonction de validation supplémentaire; si False, retourne ""
    """
    try:
        root = tk.Tk()
        root.withdraw()  # Cacher la fenêtre principale

        path: str
        if dialog_type == 'folder':
            path = filedialog.askdirectory(
                title=title,
                initialdir=initialdir,
                mustexist=must_exist,
            ) or ""
        elif dialog_type == 'file':
            path = filedialog.askopenfilename(
                title=title,
                initialdir=initialdir,
                filetypes=filetypes,
            ) or ""
        else:  # 'save'
            path = filedialog.asksaveasfilename(
                title=title,
                initialfile=initialfile,
                defaultextension=defaultextension,
                filetypes=filetypes,
            ) or ""

        root.destroy()

        if not path:
            return ""
        if validate is not None and not validate(path):
            return ""
        return path
    except (tk.TclError, OSError) as e:
        print(f"Tkinter dialog failed: {e}")
        return ""


@file_dialog_bp.route('/api/file-dialog/save', methods=['POST'])
def get_save_dialog():
    """Open Windows save file dialog (asksaveasfilename equivalent)."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Données requises'
            }), 400

        # Paramètres du dialogue de sauvegarde
        title = data.get('title', 'Enregistrer sous...')
        initialfile = data.get('initialfile', '')
        defaultextension = data.get('defaultextension', '')
        filetypes = data.get('filetypes', [("Tous les fichiers", "*.*")])

        print(
            f"DEBUG: Save dialog params - title: {title}, initialfile: {initialfile}, "
            f"defaultextension: {defaultextension}")

        if is_wsl_environment():
            # En WSL, retourner une erreur indiquant qu'il faut utiliser
            # l'endpoint POST avec le chemin
            return jsonify({
                'success': False,
                'error': 'WSL_MODE',
                'message': ('En mode WSL, le dialogue de sauvegarde n\'est pas '
                            'disponible. Utilisez POST /api/file-dialog/save avec '
                            'le chemin en paramètre')
            }), 400

        # En mode normal, utiliser le dialogue natif
        file_path = open_dialog_hybrid(
            dialog_type='save',
            title=title,
            initialfile=initialfile,
            defaultextension=defaultextension,
            filetypes=filetypes
        )

        print(f"DEBUG: Save dialog returned: '{file_path}'")

        return jsonify({
            'success': True,
            'path': file_path
        })

    except (OSError, ValueError, KeyError) as e:
        print(f"DEBUG: Save dialog error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@file_dialog_bp.route('/api/file-dialog/save-path', methods=['POST'])
def set_save_path():
    """Set save file path manually (for WSL mode)."""
    try:
        data = request.get_json()
        if not data or 'path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin requis'
            }), 400

        file_path = data['path']
        print(f"DEBUG: Manual save path set: '{file_path}'")

        return jsonify({
            'success': True,
            'path': file_path
        })
    except (ValueError, KeyError) as e:
        print(f"DEBUG: Manual save path error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@file_dialog_bp.route('/api/file-dialog/open', methods=['POST'])
def open_dialog_unified():
    """Endpoint unifié pour ouvrir un fichier ou un dossier.

    Body JSON attendu:
    {
      "type": "file" | "folder",
      "path"?: string  # utilisé en WSL quand le dialogue natif n'est pas disponible
    }
    """
    try:
        data = request.get_json() or {}
        # Accepter 'type' et 'dialog_type' (alias)
        dialog_type = data.get('type') or data.get('dialog_type')
        manual_path = data.get('path')
        title = data.get('title')
        initialdir = data.get('initialdir')
        filetypes = data.get('filetypes')
        initialfile = data.get('initialfile')
        defaultextension = data.get('defaultextension')
        must_exist = data.get('must_exist')
        validate = data.get('validate')

        if dialog_type not in {'file', 'folder', 'save'}:
            return jsonify({
                'success': False,
                'error': 'TYPE_INVALID',
                'message': "Le champ 'type'/'dialog_type' doit valoir 'file', 'folder' ou 'save'"
            }), 400

        # WSL: accepter un path fourni, sinon demander au client de le fournir
        if is_wsl_environment():
            if isinstance(manual_path, str) and manual_path.strip():
                return jsonify({'success': True, 'path': manual_path})
            return wsl_mode_response('/api/file-dialog/open')

        # Mode normal: ouvrir le dialogue natif selon le type
        path = open_dialog_hybrid(
            dialog_type=dialog_type,
            title=title,
            initialdir=initialdir,
            filetypes=filetypes,
            initialfile=initialfile,
            defaultextension=defaultextension,
            must_exist=must_exist,
            validate=validate,
        )

        return jsonify({'success': True, 'path': path})
    except (OSError, ValueError, KeyError) as e:
        return jsonify({'success': False, 'error': str(e)}), 500
