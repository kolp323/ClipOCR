# ClipOCR

ClipOCR is a lightweight Windows tray app and CLI tool that watches the clipboard for screenshots, sends the image to a configurable vision model API, converts the OCR and layout result into clean Markdown, and copies the Markdown back to the clipboard.

It is built for low-friction note taking, blog drafting, academic reading, Obsidian, Typora, GitHub documents, and any workflow where screenshots need to become editable Markdown quickly.

[中文说明](README.zh-CN.md)

## Features

- Windows tray app with visible status indicators
- Start or stop clipboard monitoring from the app window, tray menu, or hotkey
- Global hotkey: `Ctrl+Alt+O` toggles monitoring
- Manual one-shot recognition for the current clipboard image
- Configurable OpenAI-compatible vision chat completions API
- Automatic OCR and layout understanding into Markdown
- Markdown cleanup for headings, lists, tables, code blocks, and spacing
- Automatic clipboard write-back after recognition
- In-app logs and local log file output
- CLI mode for scripts or quick terminal usage

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
5. The settings are saved automatically to `config.json` and loaded on the next launch.

The release zip contains:

- `clipocr.exe`: tray app
- `clipocr-cli.exe`: command-line app
- `README.md`: English documentation
- `README.zh-CN.md`: Chinese documentation

## Configuration

The app uses one local configuration file: `config.json`.

You normally do not need to edit this file manually. Fill the fields in the app window and ClipOCR saves them automatically.

Manual `config.json` example:

```json
{
  "api_base_url": "https://api.openai.com/v1",
  "api_key": "your_api_key_here",
  "model": "gpt-4o-mini",
  "timeout": 60,
  "start_on_launch": false
}
```

Configuration fields:

| Field | Required | Description |
| --- | --- | --- |
| `api_base_url` | Yes | API base URL. OpenAI-compatible `/v1` endpoints are expected. |
| `api_key` | Yes | API key used as a Bearer token. |
| `model` | Yes | Vision-capable model name. |
| `timeout` | No | Request timeout in seconds. Defaults to `60`. |
| `start_on_launch` | No | Whether monitoring starts automatically when the tray app opens. |

`config.json` is local-only and should not be committed.

## Tray App Usage

Run:

```powershell
.\clipocr.exe
```

Then use one of these controls:

- Click `Start listening` to watch for new clipboard screenshots.
- Click `Stop listening` to pause monitoring.
- Click `Recognize current clipboard` to process the current clipboard image once.
- Use the tray menu for the same actions.
- Press `Ctrl+Alt+O` to toggle monitoring.
- Close the window to keep ClipOCR running in the tray.
- Use `Quit` from the tray menu to fully exit.

Typical workflow:

1. Start ClipOCR.
2. Fill and save API settings in the window.
3. Start monitoring.
4. Copy a screenshot to the clipboard.
5. Wait until the tray icon turns green.
6. Paste the generated Markdown into your editor.

## CLI Usage

The CLI reads the same `config.json` file as the tray app.

Run the CLI once:

```powershell
.\clipocr-cli.exe
```

Also print the Markdown result to the terminal:

```powershell
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

## Build From Source

Create Windows release files:

```powershell
.\build-windows.ps1
```

The release files are written to `release\windows`:

- `clipocr.exe`: tray app
- `clipocr-cli.exe`: command-line app
- `README.md`
- `README.zh-CN.md`

Create a Linux CLI executable on Linux or WSL with `python3-venv` installed:

```bash
bash build-linux.sh
```

Linux clipboard support requires one of these tools:

- `wl-paste` and `wl-copy` for Wayland
- `xclip` for X11
- `xsel` as a fallback

## Logs and Local Files

ClipOCR may create these local files next to the app:

- `config.json`: app settings and API configuration
- `logs/clipocr.log`: local log file

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

Run `clipocr.exe`, fill the settings in the window, and let it create `config.json` automatically.

### `Missing environment variables` or missing config fields

Older versions used `.env`. New versions use `config.json`. Fill the settings in the app window or create `config.json` manually.

### The tray icon stays blue

ClipOCR is waiting for an image in the clipboard. Copy a screenshot, not plain text.

### Recognition fails

Check these items:

- API key is valid.
- Model supports image input.
- Base URL is OpenAI-compatible.
- Network connection is available.
- The screenshot is not too large for the selected model.

### Hotkey does not work

`Ctrl+Alt+O` may already be used by another app. Use the app window or tray menu instead.

## Known Limitations

- Windows is the primary target for the tray app.
- Linux support is CLI-oriented and depends on system clipboard tools.
- The API must support image input in OpenAI-compatible chat completions format.
- OCR quality depends on the selected vision model and screenshot quality.
- The app processes one screenshot at a time.
- No OCR history database is included.
- API keys are stored locally in `config.json`; use a dedicated key when possible.

## Roadmap

- Configurable hotkeys
- Optional image file input
- `--no-copy` CLI mode
- Saved debug image for failed OCR attempts
- OCR history export
- Better Markdown cleanup presets
