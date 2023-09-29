# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['dataset_modified_multythread.py'],
    pathex=[],
    binaries=[],
    datas=[('images\\logo_insivumeh.png', 'images\\logo_insivumeh.png'), ('images\\waterco-logo.png', 'images\\waterco-logo.png'), ('images\\IUCN_logo.png', 'images\\IUCN_logo.png')],
    hiddenimports=[],
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
)
