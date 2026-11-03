# PyInstaller recipe for Kafka.exe, the Metamorphism module on its own: one file holding Python, numpy,
# scipy, the module's windows and the Holland & Powell core with its data tables.  No Magma, no Reaction.
# Build from the repository root with packaging\kafka\build_exe.ps1.
from pathlib import Path

ROOT = Path(SPECPATH).parent.parent
SRC = ROOT / "src"
HERE = ROOT / "packaging" / "kafka"

a = Analysis(
    [str(HERE / "kafka_exe.py")],
    pathex=[str(SRC)],
    datas=[(str(SRC / "metamorphism" / "app" / "static"), "metamorphism/app/static"),
           (str(SRC / "protolith" / "core" / "data" / "*.tsv"), "protolith/core/data")],
    hiddenimports=["metamorphism.app.server", "protolith.metamorphism_link", "protolith.sample"],
    excludes=["magma", "reaction", "matplotlib", "pandas", "tkinter", "pytest", "IPython"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas,
    name="Kafka",
    console=True,          # the window shows where the app runs; closing it stops the app
    upx=False,
    icon=str(HERE / "kafka.ico"),                     # the K in the Dougalien Systems style (protolith/icon/make_icons.py)
    version=str(HERE / "version_info.txt"),           # company and product in Properties > Details
)
