"""
Routes pour la gestion des sauvegardes
"""
import os
import shutil
from pathlib import Path

from flask import Blueprint, jsonify, request

# Blueprint pour les sauvegardes
backup_bp = Blueprint('backups', __name__)

# Variable globale pour le gestionnaire de sauvegardes
backup_manager = None


def init_backup_manager(manager):
    """Initialise le gestionnaire de sauvegardes"""
    global backup_manager  # pylint: disable=global-statement
    backup_manager = manager


@backup_bp.route('/api/backups', methods=['GET'])
def get_backups():
    """Liste toutes les sauvegardes avec filtres optionnels"""
    try:
        game_filter = request.args.get('game')
        type_filter = request.args.get('type')

        backups = backup_manager.list_all_backups(
            game_filter=game_filter,
            type_filter=type_filter
        )

        return jsonify({
            'success': True,
            'backups': backups
        })
    except (OSError, ValueError, KeyError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@backup_bp.route('/api/backups/<backup_id>/restore', methods=['POST'])
def restore_backup(backup_id):
    """Restaure une sauvegarde"""
    try:
        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]
        target_path = backup.get('source_path')

        if not target_path or not os.path.exists(os.path.dirname(target_path)):
            return jsonify({
                'success': False,
                'error': 'Chemin de destination invalide'
            }), 400

        # Copier le fichier
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy2(backup['backup_path'], target_path)

        # Supprimer la sauvegarde après restauration
        os.remove(backup['backup_path'])
        del backup_manager.metadata[backup_id]
        backup_manager.save_metadata()

        return jsonify({
            'success': True,
            'message': 'Sauvegarde restaurée avec succès'
        })

    except (OSError, KeyError, FileNotFoundError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@backup_bp.route('/api/backups/<backup_id>/restore-to', methods=['POST'])
def restore_backup_to(backup_id):
    """Restaure une sauvegarde vers un chemin spécifique"""
    try:
        data = request.get_json()
        print(f"DEBUG: restore_backup_to called with backup_id: {backup_id}")
        print(f"DEBUG: request data: {data}")

        if not data or 'target_path' not in data:
            print("DEBUG: Missing target_path in request data")
            return jsonify({
                'success': False,
                'error': 'Chemin de destination requis'
            }), 400

        target_path = data['target_path']
        print(f"DEBUG: Target path: {target_path}")

        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            print(f"DEBUG: Backup {backup_id} not found in metadata")
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]
        print(f"DEBUG: Backup found: {backup}")

        # Vérifier que le répertoire de destination existe
        target_path_obj = Path(target_path)
        target_dir = target_path_obj.parent
        print(f"DEBUG: Target directory: {target_dir}")
        print(f"DEBUG: Target directory exists: {target_dir.exists()}")

        if not target_dir.exists():
            print(f"DEBUG: Target directory does not exist: {target_dir}")
            # Créer le répertoire s'il n'existe pas
            try:
                target_dir.mkdir(parents=True, exist_ok=True)
                print(f"DEBUG: Created target directory: {target_dir}")
            except (OSError, PermissionError) as e:
                print(f"DEBUG: Failed to create target directory: {e}")
                return jsonify({
                    'success': False,
                    'error': f'Impossible de créer le répertoire de destination: {target_dir}'
                }), 400

        # Copier le fichier vers la destination
        print(f"DEBUG: Copying from {backup['backup_path']} to {target_path}")
        shutil.copy2(backup['backup_path'], target_path)

        print("DEBUG: Restore successful")
        return jsonify({
            'success': True,
            'message': f'Fichier restauré vers {target_path}'
        })

    except (OSError, KeyError, FileNotFoundError, ValueError) as e:
        print(f"DEBUG: Exception in restore_backup_to: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@backup_bp.route('/api/backups/<backup_id>', methods=['DELETE'])
def delete_backup(backup_id):
    """Supprime une sauvegarde"""
    try:
        # Trouver le backup dans les métadonnées
        if backup_id not in backup_manager.metadata:
            return jsonify({
                'success': False,
                'error': 'Sauvegarde introuvable'
            }), 404

        backup = backup_manager.metadata[backup_id]

        # Supprimer le fichier
        if os.path.exists(backup['backup_path']):
            os.remove(backup['backup_path'])

        # Supprimer des métadonnées
        del backup_manager.metadata[backup_id]
        backup_manager.save_metadata()

        # Nettoyer les dossiers vides
        backup_manager.cleanup_empty_folders()

        return jsonify({
            'success': True,
            'message': 'Sauvegarde supprimée avec succès'
        })

    except (OSError, KeyError, FileNotFoundError) as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
