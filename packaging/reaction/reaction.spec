# PyInstaller recipe for Reaction.exe: one file holding Python, numpy, scipy, the app and its data tables.
# OBIGT only: the Holland & Powell core, Magma and Kafka are left out.  The OBIGT databases are not inside;
# they stay in %LOCALAPPDATA%\Reaction\external (scripts\fetch_references.ps1), as before.
# Build from the Protolith folder with packaging\reaction\build_exe.ps1.
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent
SRC = ROOT / "src"
HERE = ROOT / "packaging" / "reaction"

a = Analysis(
    [str(HERE / "reaction_exe.py")],
    pathex=[str(SRC)],
    datas=[(str(SRC / "reaction" / "data" / "*.tsv"), "reaction/data"),
           (str(SRC / "reaction" / "app" / "static"), "reaction/app/static")],
    hiddenimports=["protolith.reaction_link", "protolith.sample"],
    excludes=["protolith.core", "magma", "metamorphism", "matplotlib", "pandas", "tkinter", "pytest", "IPython"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="Reaction",
    console=True,          # the window shows where the app runs; closing it stops the app
    upx=False,
    icon=str(HERE / "reaction.ico"),
    version=str(HERE / "version_info.txt"),
)
