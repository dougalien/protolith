# Build dist\Magma.exe, dist\Reaction.exe and dist\Kafka.exe on Windows.  Run from the Protolith folder:
#   powershell -ExecutionPolicy Bypass -File packaging\build_all.ps1
$ErrorActionPreference = "Stop"
python -m pip install --upgrade pip
python -m pip install numpy scipy pyinstaller
foreach ($app in "magma", "reaction", "kafka") {
    python -m PyInstaller --noconfirm --clean "packaging\$app\$app.spec"
    if ($LASTEXITCODE -ne 0) { throw "the $app build failed" }
}
Write-Host "Built dist\Magma.exe, dist\Reaction.exe and dist\Kafka.exe"
