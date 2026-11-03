# Build dist\Kafka.exe on Windows.  Run from the Protolith folder:
#   powershell -ExecutionPolicy Bypass -File packaging\kafka\build_exe.ps1
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install numpy scipy pyinstaller
python -m PyInstaller --noconfirm --clean packaging\kafka\kafka.spec
Write-Host "Built dist\Kafka.exe"
