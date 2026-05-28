# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Cis-GS
Supports: Windows (.exe), Linux (binary), macOS (.app)

Run with:  pyinstaller --clean --noconfirm Cis-GS.spec
"""

import sys
from pathlib import Path

block_cipher = None
app_name     = 'Cis-GS'
main_script  = 'app_v4_open.py'

# ── Icon path (platform-aware) ─────────────────────────────────────────────
if sys.platform == 'win32':
    # Prefer the custom app icon; fall back to assets/favicon.ico
    for _ico in ['image.ico', 'assets/favicon.ico']:
        if Path(_ico).exists():
            icon_arg = _ico
            break
    else:
        icon_arg = None
elif sys.platform == 'darwin':
    icon_file = 'assets/favicon.icns'
    icon_arg  = icon_file if Path(icon_file).exists() else None
else:
    icon_arg  = None

# ── Data files ────────────────────────────────────────────────────────────
datas = [('assets', 'assets')]

# Always bundle the banner and custom icon so the app can find them at runtime
for _extra_data in [('banner.png', '.'), ('image.png', '.'), ('image.ico', '.')]:
    if Path(_extra_data[0]).exists():
        datas.append(_extra_data)

for extra in ['chromosome_utils.py', 'planttfdb_importer.py',
              'animaltfdb_importer.py']:
    if Path(extra).exists():
        datas.append((extra, '.'))

# ── Hidden imports ─────────────────────────────────────────────────────────
hiddenimports = [
    'PyQt5.QtPrintSupport',
    'PyQt5.QtSvg',
    'scipy.spatial.transform._rotation_groups',
    'scipy.special.cython_special',
    'scipy.special._ufuncs_cxx',
    'sklearn.utils._typedefs',
    'sklearn.neighbors._partition_nodes',
    'sklearn.utils._heap',
    'sklearn.utils._sorting',
    'sklearn.utils._vector_sentinel',
    'logomaker',
    'Bio.Seq',
    'Bio.SeqIO',
    'Bio.Entrez',
    'Bio.SeqRecord',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.backends.backend_agg',
    'pandas._libs.tslibs.timedeltas',
    'pandas._libs.tslibs.np_datetime',
    'pandas._libs.tslibs.nattype',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
    'PIL.ImageFont',
    'PIL.ImageQt',
    'networkx',
    'community',
    'igraph',
    'igraph._igraph',
    'charset_normalizer',
    'chromosome_utils',
    'planttfdb_importer',
    'animaltfdb_importer',
    # cis_gs subpackage modules (lazy-imported by the GUI / CLI)
    'cis_gs',
    'cis_gs.cli',
    'cis_gs.cli_enrichment',
    'cis_gs.cli_interactive',
    'cis_gs.enrichment',
    'cis_gs.enrichment.core',
    'cis_gs.enrichment.kegg',
    'cis_gs.enrichment.idmap',
    'cis_gs.enrichment.plots',
    'json',
    'urllib.request',
    'urllib.parse',
    'urllib.error',
    'ftplib',
    'gzip',
    'zipfile',
    'tempfile',
    'shutil',
    're',
]

# ── Analysis ───────────────────────────────────────────────────────────────
a = Analysis(
    [main_script],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'PyQt5.QtWebEngine',
        'PyQt5.QtWebEngineWidgets',
        'PyQt5.Qt3D',
        'PyQt5.QtBluetooth',
        'PyQt5.QtNfc',
        'PyQt5.QtPositioning',
        'PyQt5.QtLocation',
        'PyQt5.QtQuick',
        'PyQt5.QtQuickWidgets',
        'PyQt5.QtRemoteObjects',
        'PyQt5.QtSensors',
        'PyQt5.QtSerialPort',
        'PyQt5.QtTextToSpeech',
        'PyQt5.QtVirtualKeyboard',
        'matplotlib.tests',
        'pandas.tests',
        'numpy.tests',
        'scipy.tests',
        'sklearn.tests',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'docutils',
        'sphinx',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_arg,
)

if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name=app_name + '.app',
        icon=icon_arg,
        bundle_identifier='com.plantsignalinglab.cis-gs',
        info_plist={
            'CFBundleShortVersionString': '1.2.0',
            'CFBundleDisplayName': 'Cis-GS',
            'NSHighResolutionCapable': True,
        },
    )
