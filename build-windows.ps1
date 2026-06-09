$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}

& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") pyinstaller
Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller --onefile --windowed --name clipocr .\clipocr_app.py
    & $Python -m PyInstaller --onefile --name clipocr-cli .\clipocr.py
}
finally {
    Pop-Location
}

$ReleaseDir = Join-Path $ProjectRoot "release\windows"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
Copy-Item (Join-Path $ProjectRoot "dist\clipocr.exe") (Join-Path $ReleaseDir "clipocr.exe") -Force
Copy-Item (Join-Path $ProjectRoot "dist\clipocr-cli.exe") (Join-Path $ReleaseDir "clipocr-cli.exe") -Force
Copy-Item (Join-Path $ProjectRoot "README.md") (Join-Path $ReleaseDir "README.md") -Force
Copy-Item (Join-Path $ProjectRoot "README.en.md") (Join-Path $ReleaseDir "README.en.md") -Force

Write-Host "Windows release created at $ReleaseDir"
