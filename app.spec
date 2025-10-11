# -*- mode: python ; coding: utf-8 -*-

import os
import json
import platform
from pathlib import Path

# Récupérer automatiquement la version et la distribution
def get_version():
    """Récupère la version depuis package.json"""
    try:
        with open('package.json', 'r') as f:
            data = json.load(f)
            return data.get('version', '2.0.0')
    except:
        return '2.0.0'

def get_distribution():
    """Détecte automatiquement la distribution"""
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'darwin':
        return 'macos'
    elif system == 'linux':
        return 'linux'
    else:
        return 'unknown'

# Générer le nom automatiquement
version = get_version()
distribution = get_distribution()
app_name = f'renextract-{distribution}-v{version}'

# Chemin vers le dossier dist
dist_path = Path('dist')

# Collecter tous les fichiers statiques pour les intégrer dans l'exécutable
datas = []
if dist_path.exists():
    for file_path in dist_path.rglob('*'):
        if file_path.is_file():
            # Calculer le chemin relatif pour l'inclusion
            rel_path = file_path.relative_to(dist_path)
            # Inclure tous les fichiers statiques dans l'exécutable avec la structure dist/
            datas.append((str(file_path), f"dist/{rel_path.parent}" if rel_path.parent != Path('.') else "dist"))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'flask_cors',
        'webview',
        'webview.platforms.gtk',
        'webview.platforms.qt',
        'webview.platforms.cocoa',
        'webview.platforms.winforms',
        'dotenv',
        'threading',
        'json',
        'time'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=app_name,
    debug=True,
    bootloader_ignore_signals=False,
    strip=True,   # Stripper les symboles pour réduire la taille
    upx=False,    # Désactiver UPX qui peut causer des faux positifs
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='public/favicon.ico',
    manifest='app.manifest',
    onefile=True,
    exclude_binaries=False,
)
