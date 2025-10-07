# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path

# Chemin vers le dossier dist
dist_path = Path('dist')

# Collecter tous les fichiers statiques pour les intégrer dans l'exécutable
datas = []
if dist_path.exists():
    for file_path in dist_path.rglob('*'):
        if file_path.is_file():
            # Calculer le chemin relatif pour l'inclusion
            rel_path = file_path.relative_to(dist_path)
            # Inclure tous les fichiers statiques dans l'exécutable
            datas.append((str(file_path), str(rel_path.parent) if rel_path.parent != Path('.') else '.'))

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'flask',
        'flask_cors',
        'webview',
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
    name='app-temp',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='favicon.ico',
    onefile=True,
    exclude_binaries=False,
)
