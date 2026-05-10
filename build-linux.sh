#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

python3 -m venv .venv-linux
. .venv-linux/bin/activate
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --name clipocr clipocr.py

mkdir -p release/linux
cp dist/clipocr release/linux/clipocr
cp .env.example release/linux/.env.example
cp README.md release/linux/README.md
chmod +x release/linux/clipocr

echo "Linux release created at $PROJECT_ROOT/release/linux"
