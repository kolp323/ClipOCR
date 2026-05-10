$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $Python)) {
    python -m venv (Join-Path $ProjectRoot ".venv")
}

& $Python -m pip install -r (Join-Path $ProjectRoot "requirements.txt") pyinstaller
Push-Location $ProjectRoot
try {
    & $Python -m PyInstaller --onefile --name clipocr .\clipocr.py
}
finally {
    Pop-Location
}

$ReleaseDir = Join-Path $ProjectRoot "release\windows"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
Copy-Item (Join-Path $ProjectRoot "dist\clipocr.exe") (Join-Path $ReleaseDir "clipocr.exe") -Force
Copy-Item (Join-Path $ProjectRoot ".env.example") (Join-Path $ReleaseDir ".env.example") -Force
Copy-Item (Join-Path $ProjectRoot "README.md") (Join-Path $ReleaseDir "README.md") -Force

Write-Host "Windows release created at $ReleaseDir"
