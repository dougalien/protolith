# PyInstaller recipe for Protolith.exe: one file holding Python, numpy, scipy, the shell and every module
# (Magma, Reaction, Metamorphism) with their windows and data tables.  Reaction's thermodynamic databases are not inside
# it; as for Reaction.exe they stay in %LOCALAPPDATA%\Reaction\external (scripts\fetch_references.ps1).
# Build from the repository root with packaging\protolith\build_exe.ps1.
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent
SRC = ROOT / "src"
HERE = ROOT / "packaging" / "protolith"

a = Analysis(
    [str(HERE / "protolith_exe.py")],
    pathex=[str(SRC)],
    datas=[(str(SRC / "magma" / "data" / "*.tsv"), "magma/data"),
           (str(SRC / "magma" / "app" / "static"), "magma/app/static"),
           (str(SRC / "reaction" / "data" / "*.tsv"), "reaction/data"),
           (str(SRC / "reaction" / "app" / "static"), "reaction/app/static"),
           (str(SRC / "metamorphism" / "app" / "static"), "metamorphism/app/static"),
           (str(SRC / "protolith" / "app" / "static"), "protolith/app/static"),
           (str(SRC / "protolith" / "core" / "data" / "*.tsv"), "protolith/core/data")],
    # the modules' servers are imported when the shell starts them
    hiddenimports=["magma.app.server", "reaction.app.server", "metamorphism.app.server", "protolith.reaction_link",
                   "protolith.magma_link", "protolith.metamorphism_link"],
    excludes=["matplotlib", "pandas", "tkinter", "pytest", "IPython"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="Protolith",
    console=True,          # the window shows where the app runs; closing it stops every module
    upx=False,
    icon=str(HERE / "protolith.ico"),                 # the P in the Dougalien Systems style (icon/make_icons.py)
    version=str(HERE / "version_info.txt"),           # company and product in Properties > Details
)
