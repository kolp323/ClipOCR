# Development Log

## 2026-06-07 Usability, Robustness, and Security Hardening

### Scope

This update improves ClipOCR's behavior around unsafe inputs, error handling, long-running tray usage, and release traceability. API keys are still stored in `config.json` by design for this iteration.

### Security Improvements

- Replaced raw API error body logging with sanitized summaries containing HTTP status, provider error type, code, and a short redacted message.
- Added redaction for common credential markers such as API keys, bearer tokens, authorization values, and `sk-...` style secrets before errors reach the GUI or log file.
- Added an opt-in confirmation prompt before automatically sending newly detected clipboard images while monitoring is enabled. Manual recognition remains one click.

### Robustness Improvements

- Added API Base URL validation for `http` and `https` URLs.
- Enforced timeout bounds between 5 and 600 seconds in shared config validation.
- Made GUI config loading tolerate invalid saved timeout values and fall back to the default instead of failing during startup.
- Added image normalization before upload: very large images are downscaled, PNG output is optimized, and oversized payloads fall back to JPEG compression.
- Added a hard failure when an image remains too large after compression, prompting the user to crop or resize.
- Added timeouts around Linux clipboard helper commands to avoid hangs when desktop clipboard tools misbehave.
- Wrapped Linux clipboard writer subprocess failures in `ClipOCRError` for clearer CLI and GUI messages.
- Explicitly unregisters the Windows global hotkey when the application exits.
- Recognition failures during monitoring now return the tray status to waiting after a short error display.
- Automatic monitoring now sends the exact image captured during clipboard detection instead of re-reading the clipboard after user confirmation.
- The monitoring confirmation prompt pauses polling while open to prevent duplicate prompts and nested recognition attempts.
- Application shutdown now stops status timers and waits briefly for an active recognition worker before exit.
- Tray Quit now defers application shutdown while OCR is running, disables new recognition controls, and exits automatically after the worker finishes.
- Clipboard image fingerprinting now uses a small thumbnail hash instead of full PNG/base64 encoding, reducing memory and CPU cost for very large screenshots.
- JPEG fallback now tries multiple quality levels and limited downscaling before rejecting an oversized image.

### Usability Improvements

- Updated configuration error messages to refer to required config fields instead of legacy environment variables.
- Added log rotation for `logs/clipocr.log` at approximately 1 MB, keeping one `.log.1` backup.
- Added a persistent `confirm_auto_send` configuration flag so users can choose whether automatic monitoring requires confirmation before remote API submission.
- Updated `README.md` with the confirmation setting, timeout range, test commands, log rotation behavior, and large image handling notes.
- Added `requirements-dev.txt` so test dependencies are installed with a documented command.

### Tests Added

- Added `tests/test_clipocr_core.py` for Markdown cleanup, chat completions URL construction, config validation, API error sanitization, image fingerprinting, JPEG fallback behavior, oversized image rejection, and direct image OCR.

### Manual Validation Checklist

- Run `python -m pytest`.
- Run `python -m py_compile clipocr_core.py clipocr_app.py clipocr.py`.
- Start the GUI with `python clipocr_app.py` and verify saved bad timeout values recover to the default.
- With monitoring enabled, copy an image and confirm that the send prompt appears when `confirm_auto_send` is enabled.
- Trigger API `401`, `429`, or `500` responses and confirm logs do not contain raw provider response bodies or credentials.
