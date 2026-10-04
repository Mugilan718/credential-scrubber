# -*- mode: python ; coding: utf-8 -*-

# Paths are anchored to SPECPATH (PyInstaller's built-in: the absolute
# directory containing this .spec file) rather than the current working
# directory, so `pyinstaller CredentialScrubber.spec` builds correctly
# regardless of where it's invoked from.
import os

a = Analysis(
    [os.path.join(SPECPATH, 'app.py')],
    pathex=[],
    binaries=[],
    datas=[
        (os.path.join(SPECPATH, 'rules_default.yaml'), '.'),
        (os.path.join(SPECPATH, 'templates'), 'templates'),
        (os.path.join(SPECPATH, 'static'), 'static'),
    ],
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
    name='CredentialScrubber',
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
