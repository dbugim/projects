# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['p_sch_now_privacy_1_2_est.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\danie\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\playwright_stealth\\js', 'playwright_stealth\\js')],
    hiddenimports=[],
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
    name='p_sch_now_privacy_1_2_est',
    debug=False,
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
)
