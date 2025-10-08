"""
Utilitaires communs pour l'application
"""
import os


def is_wsl_environment() -> bool:
    """Détecte si l'application tourne sous WSL."""
    try:
        if hasattr(os, 'uname'):
            if 'microsoft' in os.uname().release.lower():
                return True
        if 'WSL_DISTRO_NAME' in os.environ or 'WSLENV' in os.environ:
            return True
    except (AttributeError, OSError):
        return False
    return False
