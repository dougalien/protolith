# Build dist\Reaction.exe on Windows.  Run from the Protolith folder:
#   powershell -ExecutionPolicy Bypass -File packaging\reaction\build_exe.ps1
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install numpy scipy pyinstaller
python -m PyInstaller --noconfirm --clean packaging\reaction\reaction.spec
Write-Host "Built dist\Reaction.exe"
