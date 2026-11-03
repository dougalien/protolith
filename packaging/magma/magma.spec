# PyInstaller recipe for Magma.exe: one file holding Python, numpy, scipy, the app, its data tables and the
# Holland & Powell core it computes with.  No Reaction, no Protolith.
# Build from the Protolith folder with packaging\magma\build_exe.ps1.
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent
SRC = ROOT / "src"
HERE = ROOT / "packaging" / "magma"

a = Analysis(
    [str(HERE / "magma_exe.py")],
    pathex=[str(SRC)],
    datas=[(str(SRC / "magma" / "data" / "*.tsv"), "magma/data"),
           (str(SRC / "magma" / "app" / "static"), "magma/app/static"),
           (str(SRC / "protolith" / "core" / "data" / "*.tsv"), "protolith/core/data")],
    hiddenimports=["magma.app.server", "protolith.magma_link", "protolith.sample"],
    excludes=["reaction", "metamorphism", "matplotlib", "pandas", "tkinter", "pytest", "IPython"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="Magma",
    console=True,          # the window shows where the app runs; closing it stops the app
    upx=False,
    icon=str(HERE / "magma.ico"),
    version=str(HERE / "version_info.txt"),
)
