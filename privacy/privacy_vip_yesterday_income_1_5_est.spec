# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Users\\danie\\Desktop\\projects\\privacy_vip_yesterday_income_1_5_est.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\users\\danie\\desktop\\projects\\venv_projects\\Lib\\site-packages\\playwright_stealth\\js', 'playwright_stealth\\js')],
    hiddenimports=['playwright._impl', 'playwright._repo', 'playwright._api', 'playwright.sync_api', 'playwright.async_api', 'playwright.driver', 'playwright_stealth'],
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
    name='privacy_vip_yesterday_income_1_5_est',
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
