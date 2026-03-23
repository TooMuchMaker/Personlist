# -*- mode: python ; coding: utf-8 -*-
"""
TRAEWORK PyInstaller 打包配置
独立桌面应用 - 所有代码打包到单个EXE
"""

import sys
from pathlib import Path

block_cipher = None

project_root = Path(SPECPATH)

a = Analysis(
    ['traework/__main__.py'],
    pathex=[str(project_root)],
    binaries=[],
    datas=[
        ('traework', 'traework'),
    ],
    hiddenimports=[
        'flask',
        'flask.json',
        'flask.templating',
        'werkzeug',
        'werkzeug.routing',
        'werkzeug.serving',
        'werkzeug.middleware',
        'werkzeug.middleware.proxy_fix',
        'jinja2',
        'jinja2.ext',
        'requests',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'pystray',
        'pystray._win32',
        'webview',
        'webview.window',
        'webview.dom',
        'webview.event',
        'multiprocessing',
        'multiprocessing.spawn',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'pytest',
        'IPython',
        'notebook',
        'pystray._dbus',
        'pystray._gtk',
        'pystray._appindicator',
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
    name='TRAEWORK',
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
    icon=None,
)
