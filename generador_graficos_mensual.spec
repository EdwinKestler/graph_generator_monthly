# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['montly_graph.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets\\logo_insivumeh.png',   'assets'),
        ('assets\\waterco-logo.png',     'assets'),
        ('assets\\IUCN_logo.png',        'assets'),
        ('assets\\spinning-loading.gif', 'assets'),
    ],
    hiddenimports=[
        'data_processing',
        'graph_generation',
        'map_viewer',
        'download_database',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='generador_graficos_mensual',
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
    icon='assets\\logo_insivumeh.png',
)
