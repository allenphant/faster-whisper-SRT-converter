# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\raging\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\customtkinter', 'customtkinter'), ('C:\\Users\\raging\\AppData\\Local\\Programs\\Python\\Python313\\Lib\\site-packages\\faster_whisper\\assets', 'faster_whisper/assets'), ('faster_whisper_srt.py', '.')],
    hiddenimports=['faster_whisper', 'ctranslate2', 'sklearn.utils._typedefs', 'sklearn.neighbors._partition_nodes'],
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
    [],
    exclude_binaries=True,
    name='FasterWhisperSRT',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FasterWhisperSRT',
)
