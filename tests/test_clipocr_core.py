import pytest
import requests
from PIL import Image

from clipocr_core import (
    ClipOCRError,
    chat_completions_url,
    clean_markdown,
    image_fingerprint,
    image_to_data_url,
    ocr_image,
    safe_api_error_message,
    validate_config,
)


def test_clean_markdown_removes_outer_fence_and_extra_blank_lines():
    text = "```markdown\n# Title\n\n\nBody  \n```"

    assert clean_markdown(text) == "# Title\n\nBody"


@pytest.mark.parametrize(
    ("base_url", "expected"),
    [
        ("https://api.example.com", "https://api.example.com/v1/chat/completions"),
        ("https://api.example.com/v1", "https://api.example.com/v1/chat/completions"),
        ("https://api.example.com/v1/chat/completions", "https://api.example.com/v1/chat/completions"),
    ],
)
def test_chat_completions_url(base_url, expected):
    assert chat_completions_url(base_url) == expected


def test_validate_config_rejects_invalid_url():
    with pytest.raises(ClipOCRError, match="valid http or https URL"):
        validate_config("file:///tmp/service", "key", "model", "60")


def test_validate_config_rejects_timeout_out_of_range():
    with pytest.raises(ClipOCRError, match="between 5 and 600"):
        validate_config("https://api.example.com/v1", "key", "model", "1")


def test_safe_api_error_message_uses_short_json_error_without_raw_body():
    response = requests.Response()
    response.status_code = 401
    response._content = (
        b'{"error":{"type":"auth_error","code":"invalid_key",'
        b'"message":"The provided API key is invalid. secret-token-1234567890"}}'
    )

    message = safe_api_error_message(response)

    assert message.startswith("API returned HTTP 401")
    assert "auth_error" in message
    assert "invalid_key" in message
    assert "secret-token-1234567890" not in message
    assert "[redacted]" in message
    assert '{"error"' not in message


def test_image_to_data_url_downscales_large_image(monkeypatch):
    import clipocr_core

    monkeypatch.setattr(clipocr_core, "MAX_IMAGE_PIXELS", 100)
    image = Image.new("RGB", (100, 100), "white")

    data_url = image_to_data_url(image)

    assert data_url.startswith("data:image/")


def test_image_fingerprint_uses_size_and_content():
    image_a = Image.new("RGB", (120, 120), "white")
    image_b = Image.new("RGB", (120, 120), "black")
    image_c = Image.new("RGB", (121, 120), "white")

    assert image_fingerprint(image_a) != image_fingerprint(image_b)
    assert image_fingerprint(image_a) != image_fingerprint(image_c)


def test_image_to_data_url_falls_back_to_jpeg(monkeypatch):
    import clipocr_core

    original_limit = clipocr_core.MAX_IMAGE_DATA_BYTES
    monkeypatch.setattr(clipocr_core, "MAX_IMAGE_DATA_BYTES", 2)

    def fake_encoder(image):
        return b"ok"

    monkeypatch.setattr(clipocr_core, "encode_jpeg_with_size_limit", fake_encoder)
    image = Image.new("RGB", (20, 20), "white")

    data_url = image_to_data_url(image)

    assert original_limit > 2
    assert data_url.startswith("data:image/jpeg;base64,")


def test_encode_jpeg_with_size_limit_raises_when_still_too_large(monkeypatch):
    import clipocr_core

    monkeypatch.setattr(clipocr_core, "MAX_IMAGE_DATA_BYTES", 1)
    monkeypatch.setattr(clipocr_core, "MIN_IMAGE_DIMENSION", 10_000)
    image = Image.new("RGB", (20, 20), "white")

    with pytest.raises(ClipOCRError, match="too large"):
        clipocr_core.encode_jpeg_with_size_limit(image)


def test_ocr_image_uses_provided_image(monkeypatch):
    import clipocr_core

    seen = {}

    def fake_call_vision_api(config, data_url):
        seen["data_url"] = data_url
        return "# Result"

    monkeypatch.setattr(clipocr_core, "call_vision_api", fake_call_vision_api)
    image = Image.new("RGB", (10, 10), "white")

    assert ocr_image(image, {"api_base_url": "https://api.example.com/v1", "api_key": "key", "model": "m", "timeout": 60}) == "# Result"
    assert seen["data_url"].startswith("data:image/")
