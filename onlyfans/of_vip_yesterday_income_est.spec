# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\danie\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\playwright_stealth', 'playwright_stealth'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\yfinance', 'yfinance')]
binaries = []
hiddenimports = ['playwright_stealth', 'yfinance', 'pandas', 'numpy', 'requests', 'lxml', 'html5lib', 'bs4', 'pytz', 'dateutil', 'collections.abc', 'curl_cffi']
datas += collect_data_files('yfinance')
binaries += collect_dynamic_libs('yfinance')
hiddenimports += collect_submodules('yfinance')
tmp_ret = collect_all('yfinance')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\danie\\Desktop\\projects\\onlyfans\\of_vip_yesterday_income_est.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    name='of_vip_yesterday_income_est',
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
