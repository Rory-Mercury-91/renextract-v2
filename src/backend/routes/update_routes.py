"""
Routes pour la gestion des mises à jour
"""
import os
import threading
import time

from flask import Blueprint, jsonify, request

# Blueprint pour les mises à jour
update_bp = Blueprint('updates', __name__)

# Variable globale pour le gestionnaire de mises à jour
update_manager = None


def init_update_manager(manager):
    """Initialise le gestionnaire de mises à jour"""
    global update_manager  # pylint: disable=global-statement
    update_manager = manager


@update_bp.route('/api/updates/check', methods=['GET'])
def check_for_updates():
    """Vérifie s'il y a des mises à jour disponibles"""
    try:
        result = update_manager.check_for_updates()
        return jsonify(result)
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la vérification: {str(e)}'
        }), 500


@update_bp.route('/api/updates/download', methods=['POST'])
def download_update():
    """Télécharge la mise à jour disponible"""
    try:
        data = request.get_json()
        if not data or 'download_url' not in data:
            return jsonify({
                'success': False,
                'error': 'URL de téléchargement requise'
            }), 400

        download_url = data['download_url']
        latest_version = data.get('latest_version')

        # Fonction de callback pour le progrès (optionnel)
        def progress_callback(progress, downloaded, total):
            # Ici on pourrait envoyer des événements WebSocket ou stocker le progrès
            print(
                f"Download progress: {progress:.1f}% ({downloaded}/{total} bytes)")

        result = update_manager.download_update(
            download_url, latest_version, progress_callback)
        return jsonify(result)

    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors du téléchargement: {str(e)}'
        }), 500


@update_bp.route('/api/updates/install', methods=['POST'])
def install_update():
    """Installe la mise à jour téléchargée"""
    try:
        data = request.get_json()
        if not data or 'executable_path' not in data:
            return jsonify({
                'success': False,
                'error': 'Chemin de l\'exécutable requis'
            }), 400

        executable_path = data['executable_path']
        result = update_manager.install_update(executable_path)
        return jsonify(result)

    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de l\'installation: {str(e)}'
        }), 500


@update_bp.route('/api/updates/config', methods=['GET'])
def get_update_config():
    """Récupère la configuration des mises à jour"""
    try:
        config = update_manager.get_config()
        return jsonify({
            'success': True,
            'config': config
        })
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la récupération de la config: {str(e)}'
        }), 500


@update_bp.route('/api/updates/config', methods=['POST'])
def update_update_config():
    """Met à jour la configuration des mises à jour"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'Configuration requise'
            }), 400

        update_manager.set_config(data)
        return jsonify({
            'success': True,
            'message': 'Configuration mise à jour avec succès',
            'config': update_manager.get_config()
        })

    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la mise à jour de la config: {str(e)}'
        }), 500


@update_bp.route('/api/updates/auto-check', methods=['GET'])
def should_auto_check():
    """Vérifie si on doit faire une vérification automatique"""
    try:
        should_check = update_manager.should_check_for_updates()
        return jsonify({
            'success': True,
            'should_check': should_check
        })
    except (OSError, ValueError, KeyError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la vérification auto: {str(e)}'
        }), 500


@update_bp.route('/api/app/exit', methods=['POST'])
def exit_app():
    """Ferme l'application proprement"""
    try:
        # Planifier la fermeture après avoir renvoyé la réponse
        def shutdown():
            # Attendre 2 secondes pour que la réponse soit envoyée et le script lancé
            time.sleep(2)
            # Forcer la fermeture  # pylint: disable=protected-access
            os._exit(0)

        # Lancer dans un thread séparé
        shutdown_thread = threading.Thread(target=shutdown)
        shutdown_thread.daemon = True
        shutdown_thread.start()

        return jsonify({
            'success': True,
            'message': 'L\'application va se fermer'
        })
    except (OSError, ValueError, RuntimeError) as e:
        return jsonify({
            'success': False,
            'error': f'Erreur lors de la fermeture: {str(e)}'
        }), 500
