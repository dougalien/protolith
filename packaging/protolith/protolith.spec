# PyInstaller recipe for Protolith.exe: one file holding Python, numpy, scipy, the shell and every module
# (Magma, Reaction) with their windows and data tables, including Reaction's OBIGT and EQ3/6 ion-size data
# (src/reaction/data/reference, see its NOTICE.md).
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
           (str(SRC / "reaction" / "data" / "reference"), "reaction/data/reference"),
           (str(SRC / "reaction" / "app" / "static"), "reaction/app/static"),
           (str(SRC / "protolith" / "app" / "static"), "protolith/app/static"),
           (str(SRC / "protolith" / "core" / "data" / "*.tsv"), "protolith/core/data")],
    # the modules' servers are imported when the shell starts them
    hiddenimports=["magma.app.server", "reaction.app.server", "protolith.reaction_link", "protolith.magma_link"],
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
