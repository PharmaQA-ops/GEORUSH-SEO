
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from pathlib import Path

root = Path(SPECPATH)

hidden = [
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
    "webview",
]

hidden += collect_submodules("uvicorn")
hidden += collect_submodules("webview")

datas = [
    (str(root / "index.html"), "."),
    (str(root / "styles.css"), "."),
    (str(root / "app.js"), "."),
    (str(root / "api-config.js"), "."),
]

# Include project modules as data is unnecessary; PyInstaller discovers imports
# from main.py and georush_desktop.py. The frontend files are explicitly bundled.
a = Analysis(
    ["georush_desktop.py"],
    pathex=[str(root)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
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
    name="GEORUSH-SEO",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
)
