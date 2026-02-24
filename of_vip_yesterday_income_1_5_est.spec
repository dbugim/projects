# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\playwright_stealth', 'playwright_stealth'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\yfinance', 'yfinance'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\bs4', 'bs4'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\soupsieve', 'soupsieve'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\frozendict', 'frozendict'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\peewee.py', '.'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\websockets', 'websockets'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\google', 'google'), ('C:\\Users\\danie\\Desktop\\projects\\venv_projects\\Lib\\site-packages\\multitasking', 'multitasking')]
binaries = []
hiddenimports = ['playwright_stealth', 'yfinance', 'pandas', 'numpy', 'requests', 'lxml', 'html5lib', 'bs4', 'pytz', 'dateutil', 'collections.abc', 'curl_cffi', 'html', 'html.parser', 'frozendict', 'peewee', 'websockets', 'google.protobuf', 'multitasking']
tmp_ret = collect_all('lxml')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['C:\\Users\\danie\\Desktop\\projects\\of_vip_yesterday_income_1_5_est.py'],
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
    name='of_vip_yesterday_income_1_5_est',
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
