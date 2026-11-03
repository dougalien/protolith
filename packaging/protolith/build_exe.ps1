# Build dist\Protolith.exe on Windows.  Run from the Protolith folder:
#   powershell -ExecutionPolicy Bypass -File packaging\protolith\build_exe.ps1
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install numpy scipy pyinstaller
python -m PyInstaller --noconfirm --clean packaging\protolith\protolith.spec
Write-Host "Built dist\Protolith.exe"
