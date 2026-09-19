
# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

root = Path(SPECPATH)

project_modules = [
    "main", "crawler", "score", "gsc", "keywords", "competitor",
    "content", "analytics", "ai", "config", "database", "health",
    "seo_service", "ollama_agent", "multi_research", "radar"
]

hidden = []
for mod in project_modules:
    hidden += collect_submodules(mod) if mod in ["main"] else [mod]
hidden += collect_submodules("uvicorn")
hidden += collect_submodules("webview")

datas = [
    (str(root / "index.html"), "."),
    (str(root / "styles.css"), "."),
    (str(root / "app.js"), "."),
    (str(root / "api-config.js"), "."),
]

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
