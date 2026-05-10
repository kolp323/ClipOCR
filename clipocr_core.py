from __future__ import annotations

import base64
import io
import json
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, Union

import requests
from PIL import Image, ImageGrab

if platform.system() == "Windows":
    import tkinter as tk
else:
    tk = None

DEFAULT_PROMPT = """You are an OCR and document layout assistant.
Read the screenshot image and return clean, ready-to-paste Markdown.

Rules:
- Output Markdown only. Do not explain your process.
- Preserve headings, lists, tables, code blocks, and math as accurately as possible.
- Convert tables to Markdown tables when possible.
- Put code into fenced code blocks.
- Remove OCR noise, meaningless line breaks, duplicated text, and UI clutter.
- If the image contains multiple sections, keep their order.
- If text is unclear, make the best conservative reconstruction.
"""


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
        raise ClipOCRError("Missing environment variables: " + ", ".join(missing))

    try:
        timeout = int(timeout_raw)
    except ValueError as exc:
        raise ClipOCRError("CLIPOCR_TIMEOUT must be an integer") from exc

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
        data = read_linux_clipboard_image()
        if data:
            return Image.open(io.BytesIO(data))

    raise ClipOCRError("No image found in clipboard")


def read_linux_clipboard_image() -> Optional[bytes]:
    if shutil.which("wl-paste"):
        result = subprocess.run(["wl-paste", "--type", "image/png"], capture_output=True)
        if result.returncode == 0 and result.stdout:
            return result.stdout

    if shutil.which("xclip"):
        result = subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png", "-o"], capture_output=True)
        if result.returncode == 0 and result.stdout:
            return result.stdout

    if shutil.which("xsel"):
        result = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True)
        if result.returncode == 0 and result.stdout:
            return result.stdout

    return None


def image_fingerprint(image: Image.Image) -> tuple[str, tuple[int, int]]:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    data = base64.b64encode(buffer.getvalue()).decode("ascii")
    return data[:96] + str(len(data)), image.size


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def chat_completions_url(api_base_url: str) -> str:
    base = api_base_url.rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    if base.endswith("/v1"):
        return base + "/chat/completions"
    return base + "/v1/chat/completions"


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

    try:
        response = requests.post(
            chat_completions_url(str(config["api_base_url"])),
            headers=headers,
            json=payload,
            timeout=int(config["timeout"]),
        )
    except requests.RequestException as exc:
        raise ClipOCRError(f"API request failed: {exc}") from exc

    if response.status_code >= 400:
        raise ClipOCRError(f"API returned HTTP {response.status_code}: {response.text[:500]}")

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

    if shutil.which("wl-copy"):
        subprocess.run(["wl-copy"], input=text.encode("utf-8"), check=True)
        return

    if shutil.which("xclip"):
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode("utf-8"), check=True)
        return

    if shutil.which("xsel"):
        subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode("utf-8"), check=True)
        return

    raise ClipOCRError("No clipboard writer available")


def recognize_clipboard_image(config: Dict[str, Union[str, int]]) -> str:
    image = read_clipboard_image()
    markdown = clean_markdown(call_vision_api(config, image_to_data_url(image)))
    if not markdown:
        raise ClipOCRError("OCR result is empty after Markdown cleanup")
    write_text_to_clipboard(markdown)
    return markdown
