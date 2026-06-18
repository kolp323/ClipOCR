from __future__ import annotations

import base64
import hashlib
import io
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional, Union
from urllib.parse import urlparse

import requests
from PIL import Image, ImageGrab

if platform.system() == "Windows":
    import tkinter as tk
else:
    tk = None

DEFAULT_PROMPT = r"""You are an OCR and document layout assistant.
Read the screenshot image and return clean, ready-to-paste Markdown.

Rules:
- Output Markdown only. Do not explain your process.
- Preserve headings, lists, tables, code blocks, and math as accurately as possible.
- Convert tables to Markdown tables when possible.
- Put code into fenced code blocks.
- Write math as valid LaTeX: use `$...$` for inline math and `$$...$$` for standalone formulas.
- For multi-line formulas, keep them inside one display math block and use LaTeX environments such as `aligned`, `align*`, `cases`, or `matrix` when appropriate; use `\\` for line breaks and `&` to align relation signs or columns.
- Do not insert Markdown bullets, blank lines, or manual spacing commands inside a formula block unless they are part of the LaTeX structure.
- Pay special attention to subscripts and superscripts. Use `_` and `^` exactly where shown, and wrap multi-character parts in braces, for example `x_i`, `x_{ij}`, `a_{n+1}`, and `e^{i\theta}`.
- Before finalizing, self-check every formula for valid LaTeX syntax, balanced braces, correct line breaks/alignment, and missing subscript underscores.
- Remove OCR noise, meaningless line breaks, duplicated text, and UI clutter.
- If the image contains multiple sections, keep their order.
- If text is unclear, make the best conservative reconstruction.
"""

MAX_IMAGE_PIXELS = 8_000_000
MAX_IMAGE_DATA_BYTES = 6_000_000
MIN_IMAGE_DIMENSION = 900
CLIPBOARD_COMMAND_TIMEOUT = 5


class ClipOCRError(Exception):
    pass


def app_dir() -> Path:
    return Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent


def default_config_path() -> Path:
    return app_dir() / "config.json"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Union[str, int]]:
    path = config_path or default_config_path()
    if not path.exists():
        raise ClipOCRError(f"Config file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ClipOCRError(f"Failed to load config file: {path}") from exc

    return validate_config(
        str(data.get("api_base_url", "")).strip(),
        str(data.get("api_key", "")).strip(),
        str(data.get("model", "")).strip(),
        str(data.get("timeout", 60)).strip(),
    )


def validate_config(api_base_url: str, api_key: str, model: str, timeout_raw: str) -> Dict[str, Union[str, int]]:
    missing = [
        name
        for name, value in (
            ("api_base_url", api_base_url),
            ("api_key", api_key),
            ("model", model),
        )
        if not value
    ]
    if missing:
        raise ClipOCRError("Missing required config fields: " + ", ".join(missing))

    parsed_url = urlparse(api_base_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        raise ClipOCRError("API Base URL must be a valid http or https URL")

    try:
        timeout = int(timeout_raw)
    except ValueError as exc:
        raise ClipOCRError("Timeout must be an integer") from exc
    if timeout < 5 or timeout > 600:
        raise ClipOCRError("Timeout must be between 5 and 600 seconds")

    return {
        "api_base_url": api_base_url,
        "api_key": api_key,
        "model": model,
        "timeout": timeout,
    }


def read_clipboard_image() -> Image.Image:
    if platform.system() == "Windows":
        data = ImageGrab.grabclipboard()

        if isinstance(data, Image.Image):
            return data

        if isinstance(data, list):
            for item in data:
                path = Path(item)
                if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp"}:
                    return Image.open(path)
    else:
        try:
            data = read_linux_clipboard_image()
            if data:
                return Image.open(io.BytesIO(data))
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ClipOCRError(f"Clipboard read failed: {exc}") from exc

    raise ClipOCRError("No image found in clipboard")


def read_linux_clipboard_image() -> Optional[bytes]:
    if shutil.which("wl-paste"):
        result = subprocess.run(
            ["wl-paste", "--type", "image/png"],
            capture_output=True,
            timeout=CLIPBOARD_COMMAND_TIMEOUT,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout

    if shutil.which("xclip"):
        result = subprocess.run(
            ["xclip", "-selection", "clipboard", "-t", "image/png", "-o"],
            capture_output=True,
            timeout=CLIPBOARD_COMMAND_TIMEOUT,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout

    if shutil.which("xsel"):
        result = subprocess.run(
            ["xsel", "--clipboard", "--output"],
            capture_output=True,
            timeout=CLIPBOARD_COMMAND_TIMEOUT,
        )
        if result.returncode == 0 and result.stdout:
            return result.stdout

    return None


def normalize_image_for_api(image: Image.Image) -> Image.Image:
    width, height = image.size
    pixels = width * height
    if pixels <= MAX_IMAGE_PIXELS:
        return image

    scale = (MAX_IMAGE_PIXELS / pixels) ** 0.5
    new_size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(new_size, Image.Resampling.LANCZOS)


def image_fingerprint(image: Image.Image) -> tuple[str, tuple[int, int]]:
    thumbnail = image.convert("RGB")
    thumbnail.thumbnail((96, 96), Image.Resampling.BILINEAR)
    digest = hashlib.sha256(thumbnail.tobytes()).hexdigest()
    return f"{image.mode}:{digest}", image.size


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    normalized = normalize_image_for_api(image).convert("RGB")
    normalized.save(buffer, format="PNG", optimize=True)
    raw = buffer.getvalue()
    if len(raw) > MAX_IMAGE_DATA_BYTES:
        raw = encode_jpeg_with_size_limit(normalized)
        mime_type = "image/jpeg"
    else:
        mime_type = "image/png"

    encoded = base64.b64encode(raw).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def encode_jpeg_with_size_limit(image: Image.Image) -> bytes:
    current = image
    for _ in range(4):
        for quality in (88, 78, 68, 58):
            buffer = io.BytesIO()
            current.save(buffer, format="JPEG", quality=quality, optimize=True)
            raw = buffer.getvalue()
            if len(raw) <= MAX_IMAGE_DATA_BYTES:
                return raw

        width, height = current.size
        if min(width, height) <= MIN_IMAGE_DIMENSION:
            break
        scale = max(MIN_IMAGE_DIMENSION / min(width, height), 0.75)
        next_size = (max(1, int(width * scale)), max(1, int(height * scale)))
        if next_size == current.size:
            break
        current = current.resize(next_size, Image.Resampling.LANCZOS)

    raise ClipOCRError("Clipboard image is too large after compression; crop or resize it and try again")


def chat_completions_url(api_base_url: str) -> str:
    base = api_base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


def safe_api_error_message(response: requests.Response) -> str:
    detail = ""
    try:
        data = response.json()
    except ValueError:
        data = None

    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            message = str(error.get("message", "")).strip()
            code = str(error.get("code", "")).strip()
            err_type = str(error.get("type", "")).strip()
            parts = [part for part in (err_type, code, redact_sensitive_text(message[:180])) if part]
            detail = " - " + " | ".join(parts) if parts else ""

    return f"API returned HTTP {response.status_code}{detail}"


def redact_sensitive_text(text: str) -> str:
    text = re.sub(r"(?i)(api[_ -]?key|token|authorization|bearer)\s*[:=]?\s*\S+", r"\1 [redacted]", text)
    text = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}\b", "sk-[redacted]", text)
    return text


def call_vision_api(config: Dict[str, Union[str, int]], data_url: str) -> str:
    payload = {
        "model": config["model"],
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": DEFAULT_PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "temperature": 0,
    }
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }

    last_exception: Optional[requests.RequestException] = None
    for attempt in range(3):
        try:
            response = requests.post(
                chat_completions_url(str(config["api_base_url"])),
                headers=headers,
                json=payload,
                timeout=int(config["timeout"]),
            )
            break
        except requests.RequestException as exc:
            last_exception = exc
            if attempt == 2 or not isinstance(
                exc,
                (requests.ConnectionError, requests.Timeout, requests.exceptions.SSLError),
            ):
                raise ClipOCRError(f"API request failed: {exc}") from exc
            time.sleep(0.5 * (attempt + 1))
    else:
        raise ClipOCRError(f"API request failed: {last_exception}")

    if response.status_code >= 400:
        raise ClipOCRError(safe_api_error_message(response))

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ClipOCRError("API response did not contain message content") from exc

    if isinstance(content, list):
        content = "\n".join(part.get("text", "") for part in content if isinstance(part, dict))

    text = str(content).strip()
    if not text:
        raise ClipOCRError("API returned empty OCR result")

    return text


def clean_markdown(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```(?:markdown|md)?\s*\n", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\n```\s*$", "", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def write_text_to_clipboard(text: str) -> None:
    if platform.system() == "Windows":
        if tk is None:
            raise ClipOCRError("tkinter is unavailable on this system")
        root = tk.Tk()
        root.withdraw()
        try:
            root.clipboard_clear()
            root.clipboard_append(text)
            root.update()
        finally:
            root.destroy()
        return

    try:
        if shutil.which("wl-copy"):
            subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True, timeout=CLIPBOARD_COMMAND_TIMEOUT)
            return

        if shutil.which("xclip"):
            subprocess.run(
                ["xclip", "-selection", "clipboard"],
                input=text.encode("utf-8"),
                check=True,
                timeout=CLIPBOARD_COMMAND_TIMEOUT,
            )
            return

        if shutil.which("xsel"):
            subprocess.run(
                ["xsel", "--clipboard", "--input"],
                input=text.encode("utf-8"),
                check=True,
                timeout=CLIPBOARD_COMMAND_TIMEOUT,
            )
            return
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise ClipOCRError(f"Clipboard write failed: {exc}") from exc

    raise ClipOCRError("No clipboard writer available")


def ocr_image(image: Image.Image, config: Dict[str, Union[str, int]]) -> str:
    markdown = clean_markdown(call_vision_api(config, image_to_data_url(image)))
    if not markdown:
        raise ClipOCRError("OCR result is empty after Markdown cleanup")
    return markdown


def ocr_clipboard_image(config: Dict[str, Union[str, int]]) -> str:
    return ocr_image(read_clipboard_image(), config)


def recognize_clipboard_image(config: Dict[str, Union[str, int]]) -> str:
    markdown = ocr_clipboard_image(config)
    write_text_to_clipboard(markdown)
    return markdown
