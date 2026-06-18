# ClipOCR

ClipOCR turns screenshots into clean, editable Markdown with a lightweight tray app and CLI. It watches the clipboard for images, sends the selected screenshot to an OpenAI-compatible vision chat completions API, cleans the OCR/layout result, and copies Markdown back to the clipboard.

It is designed for note taking, blog drafting, academic reading, documentation work, Obsidian, Typora, GitHub issues, and any workflow where screenshot text needs to become structured Markdown quickly.

[中文说明](README.md)

## Product Overview

ClipOCR focuses on one fast loop:

1. Copy a screenshot.
2. Let ClipOCR recognize the text and layout.
3. Paste ready-to-edit Markdown into your editor.

The Windows tray app is the primary experience. It can monitor the clipboard continuously, process the current clipboard image on demand, and show status through the window and tray icon. A CLI is included for scripts and terminal workflows.

## Key Features

- Windows tray app with visible status indicators.
- Clipboard monitoring for new screenshots.
- Optional confirmation before monitored images are sent to the OCR API.
- Manual one-shot recognition for the current clipboard image.
- Global hotkey: `Ctrl+Alt+O` toggles monitoring.
- OpenAI-compatible vision chat completions API configuration.
- Markdown cleanup for headings, lists, tables, code blocks, math, and spacing.
- Large screenshot downscaling and compression before upload.
- Automatic clipboard write-back after recognition.
- Local rotating logs for troubleshooting.
- CLI mode for single-run OCR.

## How It Works

ClipOCR reads an image from the clipboard, normalizes it for API upload, and sends it with an OCR/layout prompt to the configured vision model. The model response is cleaned into Markdown and written back to the clipboard.

For monitored screenshots, `confirm_auto_send` is enabled by default. The app asks before uploading a detected image so private screenshots are not sent without a final confirmation. Manual recognition sends the current clipboard image immediately.

## Status Indicators

| Color | Status | Meaning |
| --- | --- | --- |
| Gray | Closed | Clipboard monitoring is off |
| Blue | Waiting | Monitoring is on and waiting for a screenshot |
| Orange | Recognizing | A screenshot is being processed |
| Green | Completed | Markdown was copied back to the clipboard |
| Red | Error | Configuration, API, or clipboard operation failed |

## Download and Run

1. Download the latest Windows zip from the GitHub Releases page.
2. Extract the zip to a local folder.
3. Run `clipocr.exe`.
4. Fill API Base URL, API Key, Model, and Timeout in the window.
5. The settings are saved to `config.json` and loaded on the next launch.

The Windows release contains:

- `clipocr.exe`: tray app
- `clipocr-cli.exe`: command-line app
- `README.md`: Chinese documentation
- `README.en.md`: English documentation

## Configuration

ClipOCR uses one local configuration file: `config.json`. You usually do not need to edit it manually because the tray app saves settings automatically.

Example:

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here",
  "model": "gpt-4o-mini",
  "timeout": 60,
  "start_on_launch": false,
  "confirm_auto_send": true
}
```

| Field | Required | Description |
| --- | --- | --- |
| `api_base_url` | Yes | API base URL. OpenAI-compatible `/v1` endpoints are expected. |
| `api_key` | Yes | API key used as a Bearer token. |
| `model` | Yes | Vision-capable model name. |
| `timeout` | No | Request timeout in seconds. Defaults to `60`; valid range is `5` to `600`. |
| `start_on_launch` | No | Whether monitoring starts automatically when the tray app opens. |
| `confirm_auto_send` | No | Whether monitored clipboard images require confirmation before API upload. Defaults to `true`. |

`config.json` is local-only and should not be committed. API keys are stored locally in this file; use a dedicated key when possible.

## Tray App Usage

Run:

```powershell
.\clipocr.exe
```

Controls:

- `Start listening`: watch for new clipboard screenshots.
- `Stop listening`: pause clipboard monitoring.
- `Recognize current clipboard`: process the current clipboard image once.
- Tray menu: open the app, toggle monitoring, run one-shot recognition, or quit.
- `Ctrl+Alt+O`: toggle monitoring.

Typical workflow:

1. Start ClipOCR.
2. Fill and save API settings.
3. Start monitoring or choose one-shot recognition.
4. Copy a screenshot to the clipboard.
5. Confirm API upload if prompted.
6. Wait until the tray icon turns green.
7. Paste the generated Markdown into your editor.

## CLI Usage

The CLI reads the same `config.json` file as the tray app.

```powershell
.\clipocr-cli.exe
.\clipocr-cli.exe --print
```

When running from source:

```powershell
python clipocr.py --print
```

## Install From Source

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python clipocr_app.py
```

Run tests:

```powershell
pip install -r requirements-dev.txt
python -m pytest
python -m py_compile clipocr_core.py clipocr_app.py clipocr.py
```

## Build From Source

Create Windows release files:

```powershell
.\build-windows.ps1
```

The release files are written to `release\windows`.

Create a Linux CLI executable on Linux or WSL with `python3-venv` installed:

```bash
bash build-linux.sh
```

Linux clipboard support requires one of these tools:

- `wl-paste` and `wl-copy` for Wayland
- `xclip` for X11
- `xsel` as a fallback

## Local Files and Logs

ClipOCR may create these local files next to the app:

- `config.json`: app settings and API configuration.
- `logs/clipocr.log`: local log file, rotated at about 1 MB with one `.log.1` backup.

These files are ignored by Git.

## Output Example

```markdown
# Meeting Notes

## Action Items

- Update the project README
- Verify the OCR workflow on Windows
- Publish the demo blog post

| Item | Owner | Status |
| --- | --- | --- |
| CLI MVP | Alice | Done |
| GUI | Later | Planned |
```

## Troubleshooting

### `Config file not found`

Run `clipocr.exe`, fill the settings in the window, and let it create `config.json`.

### Missing config fields

Fill API Base URL, API Key, and Model in the app window, or create `config.json` manually.

### The tray icon stays blue

ClipOCR is waiting for an image in the clipboard. Copy a screenshot instead of plain text.

### Recognition fails

Check that the API key is valid, the model supports image input, the Base URL is OpenAI-compatible, and the network is available. ClipOCR downsizes large images and falls back to JPEG compression, but extremely large or complex screenshots may still need cropping.

### The app asks before sending images

This is controlled by `confirm_auto_send`. It is enabled by default for monitored clipboard images. Manual one-shot recognition still sends the current clipboard image immediately.

### Hotkey does not work

`Ctrl+Alt+O` may already be used by another app. Use the app window or tray menu instead.

## Current Limitations

- Windows is the primary target for the tray app.
- Linux support is CLI-oriented and depends on system clipboard tools.
- The API must support image input in OpenAI-compatible chat completions format.
- OCR quality depends on the selected vision model and screenshot quality.
- The app processes one screenshot at a time.
- No OCR history database is included.
- API keys are stored locally in `config.json`.

## Roadmap

- Configurable hotkeys.
- Optional image file input.
- `--no-copy` CLI mode.
- Saved debug image for failed OCR attempts.
- OCR history export.
- Markdown cleanup presets.
