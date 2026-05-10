#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

python3 -m venv .venv-linux
. .venv-linux/bin/activate
python -m pip install -r requirements.txt pyinstaller
python -m PyInstaller --onefile --name clipocr-cli clipocr.py

mkdir -p release/linux
cp dist/clipocr-cli release/linux/clipocr-cli
cp README.md release/linux/README.md
cp README.zh-CN.md release/linux/README.zh-CN.md
chmod +x release/linux/clipocr-cli

echo "Linux release created at $PROJECT_ROOT/release/linux"
