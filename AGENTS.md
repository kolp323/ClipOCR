# Repository Guidelines

## Project Structure & Module Organization

ClipOCR is a small Python application with root-level modules:

- `clipocr_app.py`: Windows tray GUI, settings, hotkey, and clipboard monitoring.
- `clipocr.py`: CLI entry point for one-shot OCR.
- `clipocr_core.py`: shared OCR, API, clipboard, logging, and Markdown cleanup logic.
- `requirements.txt`: runtime Python dependencies.
- `build-windows.ps1` and `build-linux.sh`: platform packaging scripts.
- `docs/`: article drafts and images for external documentation.

Generated or local-only paths such as `.venv/`, `build/`, `dist/`, `release/`, `logs/`, `.env`, and `config.json` should not be committed.

## Build, Test, and Development Commands

Use PowerShell on Windows unless a command is explicitly Linux-only.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python clipocr_app.py
```

Creates a local environment, installs dependencies, and starts the tray app from source.

```powershell
python clipocr.py --print
```

Runs the CLI against the current clipboard image and prints Markdown output.

```powershell
.\build-windows.ps1
```

Builds `clipocr.exe` and `clipocr-cli.exe` with PyInstaller into `release\windows`.

```bash
bash build-linux.sh
```

Builds the Linux CLI executable. Linux clipboard support depends on `wl-paste`/`wl-copy`, `xclip`, or `xsel`.

## Coding Style & Naming Conventions

Follow idiomatic Python 3 with 4-space indentation. Use `snake_case` for functions, variables, and module-level helpers; use `PascalCase` for classes. Keep UI logic in `clipocr_app.py`, shared behavior in `clipocr_core.py`, and CLI-only behavior in `clipocr.py`. Prefer small, targeted changes over broad refactors.

## Testing Guidelines

No automated test suite is currently present. For changes to OCR or Markdown cleanup, add focused tests under a future `tests/` directory using `pytest`, with files named `test_*.py`. Until tests exist, verify manually with:

```powershell
python clipocr.py --print
python clipocr_app.py
```

Check clipboard read/write behavior, config loading, and error messages when relevant.

## Commit & Pull Request Guidelines

Recent commits use short, imperative messages such as `Fix tray app clipboard write-back` and `Remove generated release artifacts from source`. Keep commit subjects concise and behavior-focused.

Pull requests should include a brief summary, validation steps, linked issue when available, and screenshots or screen recordings for GUI changes. Do not include generated build artifacts unless the change explicitly updates release packaging.

## Security & Configuration Tips

Keep API keys and local settings in `config.json` or `.env` only. Never commit secrets, logs, packaged binaries, or generated release directories.
