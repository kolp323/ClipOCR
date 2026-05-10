# ClipOCR

ClipOCR is a lightweight Windows command-line tool that reads a screenshot image from the clipboard, sends it to a configurable vision model API, converts the OCR and layout result into clean Markdown, and copies the Markdown back to the clipboard.

It is designed for low-friction note taking, blog drafting, Markdown editors, Obsidian, Typora, and GitHub documents.

## Features

- Read image data directly from the Windows clipboard
- Call an OpenAI-compatible vision chat completions API
- Convert OCR and layout understanding results to Markdown
- Preserve headings, lists, tables, and code blocks when possible
- Copy the final Markdown back to the clipboard automatically
- Keep the implementation small and easy to extend

## Workflow

1. Take a screenshot and copy it to the clipboard.
2. Run `python clipocr.py`.
3. ClipOCR sends the image to the configured vision model.
4. The model returns clean Markdown.
5. ClipOCR writes the Markdown back to the clipboard.
6. Paste the result into your editor.

## Installation

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

## Configuration

Edit `.env`:

```env
CLIPOCR_API_BASE_URL=https://api.openai.com/v1
CLIPOCR_API_KEY=your_api_key_here
CLIPOCR_MODEL=gpt-4o-mini
CLIPOCR_TIMEOUT=60
```

Configuration fields:

- `CLIPOCR_API_BASE_URL`: API base URL. OpenAI-compatible `/v1` endpoints are expected.
- `CLIPOCR_API_KEY`: API key used as a Bearer token.
- `CLIPOCR_MODEL`: Vision-capable model name.
- `CLIPOCR_TIMEOUT`: Request timeout in seconds.

## Usage

Copy a screenshot to the clipboard, then run:

```powershell
python clipocr.py
```

Also print the Markdown result to the terminal:

```powershell
python clipocr.py --print
```

## Build

Create a Windows executable:

```powershell
.\build-windows.ps1
```

The release files are written to `release\windows`.

Create a Linux executable on Linux or WSL with `python3-venv` installed:

```bash
bash build-linux.sh
```

The release files are written to `release/linux`.

Linux clipboard support requires one of these tools:

- `wl-paste` and `wl-copy` for Wayland
- `xclip` for X11
- `xsel` as a fallback

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
| GUI | TBD | Later |
```

## Known Limitations

- Windows desktop clipboard is the primary target.
- OCR quality depends on the selected vision model.
- The API must support image input in OpenAI-compatible chat completions format.
- The tool processes one clipboard image at a time.
- There is no GUI, hotkey listener, or tray mode in the MVP.

## Roadmap

- Add optional image file input
- Add a `--no-copy` mode
- Add saved debug output for failed OCR attempts
- Add a simple tray or hotkey launcher
