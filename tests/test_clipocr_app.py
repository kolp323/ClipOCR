from PIL import Image
import pytest

pytest.importorskip("PySide6")

from clipocr_app import OcrWorker


def test_ocr_worker_uses_provided_image(monkeypatch):
    calls = []

    def fake_ocr_image(image, config):
        calls.append(("image", image, config))
        return "from image"

    def fake_ocr_clipboard_image(config):
        calls.append(("clipboard", config))
        return "from clipboard"

    monkeypatch.setattr("clipocr_app.ocr_image", fake_ocr_image)
    monkeypatch.setattr("clipocr_app.ocr_clipboard_image", fake_ocr_clipboard_image)

    worker = OcrWorker({"timeout": 60}, Image.new("RGB", (1, 1), "white"))
    worker.run()

    assert calls[0][0] == "image"


def test_ocr_worker_reads_clipboard_without_provided_image(monkeypatch):
    calls = []

    def fake_ocr_clipboard_image(config):
        calls.append(("clipboard", config))
        return "from clipboard"

    monkeypatch.setattr("clipocr_app.ocr_clipboard_image", fake_ocr_clipboard_image)

    worker = OcrWorker({"timeout": 60})
    worker.run()

    assert calls[0][0] == "clipboard"
