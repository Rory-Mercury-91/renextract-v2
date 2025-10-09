# src/backend/__init__.py
"""Backend RenExtract v2 - Structure réorganisée

Modules principaux :
- core: Logique métier (extraction, cohérence, reconstruction, projet)
- services: Services utilitaires (config, backup, update, utils)
- api: API et routes consolidées
"""

__version__ = "2.0.0"
__author__ = "RenExtract Team"

# Contrôle des imports publics
__all__ = ["api", "core", "services"]
