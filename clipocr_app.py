from __future__ import annotations

import ctypes
import json
import sys
from ctypes import wintypes
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Union

from PIL import Image
from PySide6.QtCore import QAbstractNativeEventFilter, QThread, QTimer, Signal
from PySide6.QtGui import QAction, QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from clipocr_core import (
    ClipOCRError,
    default_config_path,
    image_fingerprint,
    ocr_image,
    ocr_clipboard_image,
    read_clipboard_image,
    write_text_to_clipboard,
    validate_config,
)

APP_DIR = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
CONFIG_PATH = default_config_path()
LOG_PATH = APP_DIR / "logs" / "clipocr.log"
MAX_LOG_BYTES = 1_000_000

STATUS_STOPPED = "closed"
STATUS_WAITING = "waiting"
STATUS_WORKING = "working"
STATUS_DONE = "done"
STATUS_ERROR = "error"
HOTKEY_ID = 0x434F
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
VK_O = 0x4F
WM_HOTKEY = 0x0312


class HotkeyFilter(QAbstractNativeEventFilter):
    def __init__(self, callback: Callable[[], None]) -> None:
        super().__init__()
        self.callback = callback

    def nativeEventFilter(self, event_type, message):
        if event_type != "windows_generic_MSG":
            return False, 0
        msg = wintypes.MSG.from_address(int(message))
        if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
            self.callback()
            return True, 0
        return False, 0


def register_hotkey() -> bool:
    if sys.platform != "win32":
        return False
    return bool(ctypes.windll.user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_ALT, VK_O))


def unregister_hotkey() -> None:
    if sys.platform == "win32":
        ctypes.windll.user32.UnregisterHotKey(None, HOTKEY_ID)


class OcrWorker(QThread):
    finished_ok = Signal(str)
    failed = Signal(str)

    def __init__(self, config: Dict[str, Union[str, int]], image: Image.Image | None = None) -> None:
        super().__init__()
        self.config = config
        self.image = image

    def run(self) -> None:
        try:
            if self.image is None:
                self.finished_ok.emit(ocr_clipboard_image(self.config))
            else:
                self.finished_ok.emit(ocr_image(self.image, self.config))
        except Exception as exc:
            self.failed.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ClipOCR")
        self.resize(720, 520)

        self.listening = False
        self.shutting_down = False
        self.confirming_send = False
        self.pending_quit = False
        self.worker: OcrWorker | None = None
        self.last_fingerprint: tuple[str, tuple[int, int]] | None = None
        self.last_done_timer = QTimer(self)
        self.last_done_timer.setSingleShot(True)
        self.last_done_timer.timeout.connect(lambda: self.set_status(STATUS_WAITING if self.listening else STATUS_STOPPED))

        self.poll_timer = QTimer(self)
        self.poll_timer.setInterval(1200)
        self.poll_timer.timeout.connect(self.check_clipboard)
        self.hotkey_filter = HotkeyFilter(self.toggle_listening)
        QApplication.instance().installNativeEventFilter(self.hotkey_filter)
        QApplication.instance().aboutToQuit.connect(self.cleanup)
        self.hotkey_registered = register_hotkey()
        self.config_ready = False
        self.config_save_timer = QTimer(self)
        self.config_save_timer.setSingleShot(True)
        self.config_save_timer.setInterval(500)
        self.config_save_timer.timeout.connect(lambda: self.save_config(log_result=False))

        self.api_base_url = QLineEdit("")
        self.api_key = QLineEdit("")
        self.api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.model = QLineEdit("")
        self.timeout = QSpinBox()
        self.timeout.setRange(5, 600)
        self.timeout.setValue(60)
        self.start_on_launch = QCheckBox("Start listening when app opens")
        self.confirm_auto_send = QCheckBox("Confirm before sending images while listening")
        self.confirm_auto_send.setChecked(True)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.status_label = QLabel("Status: closed")

        self.listen_button = QPushButton("Start listening")
        self.listen_button.clicked.connect(self.toggle_listening)
        self.run_once_button = QPushButton("Recognize current clipboard")
        self.run_once_button.clicked.connect(self.recognize_once)
        self.save_button = QPushButton("Save config")
        self.save_button.clicked.connect(lambda: self.save_config())

        form = QFormLayout()
        form.addRow("API Base URL", self.api_base_url)
        form.addRow("API Key", self.api_key)
        form.addRow("Model", self.model)
        form.addRow("Timeout seconds", self.timeout)
        form.addRow("Global hotkey", QLabel("Ctrl+Alt+O toggles monitoring"))
        form.addRow("", self.start_on_launch)
        form.addRow("", self.confirm_auto_send)

        buttons = QHBoxLayout()
        buttons.addWidget(self.listen_button)
        buttons.addWidget(self.run_once_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addLayout(form)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Logs"))
        layout.addWidget(self.log_box)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)

        self.tray = QSystemTrayIcon(self)
        self.tray.setContextMenu(self.build_tray_menu())
        self.tray.activated.connect(self.on_tray_activated)
        self.tray.show()
        if not self.hotkey_registered:
            self.log("Global hotkey Ctrl+Alt+O is unavailable")

        self.load_saved_config()
        self.connect_config_autosave()
        self.config_ready = True
        self.set_status(STATUS_STOPPED)
        self.log("Application started")

        if self.start_on_launch.isChecked():
            self.start_listening()

    def build_tray_menu(self) -> QMenu:
        menu = QMenu()
        show_action = QAction("Open ClipOCR", self)
        show_action.triggered.connect(self.show_window)
        self.toggle_action = QAction("Start listening", self)
        self.toggle_action.triggered.connect(self.toggle_listening)
        run_once_action = QAction("Recognize current clipboard", self)
        run_once_action.triggered.connect(self.recognize_once)
        quit_action = QAction("Quit", self)
        quit_action.triggered.connect(self.request_quit)
        menu.addAction(show_action)
        menu.addAction(self.toggle_action)
        menu.addAction(run_once_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        return menu

    def load_saved_config(self) -> None:
        if not CONFIG_PATH.exists():
            return
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            self.log(f"Failed to load config: {exc}")
            return

        self.api_base_url.setText(data.get("api_base_url", self.api_base_url.text()))
        self.api_key.setText(data.get("api_key", self.api_key.text()))
        self.model.setText(data.get("model", self.model.text()))
        try:
            self.timeout.setValue(int(data.get("timeout", self.timeout.value())))
        except (TypeError, ValueError):
            self.log("Invalid saved timeout; using default value")
            self.timeout.setValue(60)
        self.start_on_launch.setChecked(bool(data.get("start_on_launch", False)))
        self.confirm_auto_send.setChecked(bool(data.get("confirm_auto_send", True)))

    def connect_config_autosave(self) -> None:
        self.api_base_url.textChanged.connect(self.schedule_config_save)
        self.api_key.textChanged.connect(self.schedule_config_save)
        self.model.textChanged.connect(self.schedule_config_save)
        self.timeout.valueChanged.connect(self.schedule_config_save)
        self.start_on_launch.stateChanged.connect(self.schedule_config_save)
        self.confirm_auto_send.stateChanged.connect(self.schedule_config_save)

    def schedule_config_save(self) -> None:
        if self.config_ready:
            self.config_save_timer.start()

    def save_config(self, log_result: bool = True) -> None:
        data = {
            "api_base_url": self.api_base_url.text().strip(),
            "api_key": self.api_key.text().strip(),
            "model": self.model.text().strip(),
            "timeout": self.timeout.value(),
            "start_on_launch": self.start_on_launch.isChecked(),
            "confirm_auto_send": self.confirm_auto_send.isChecked(),
        }
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
        if log_result:
            self.log("Config saved")

    def current_config(self) -> Dict[str, Union[str, int]]:
        return validate_config(
            self.api_base_url.text().strip(),
            self.api_key.text().strip(),
            self.model.text().strip(),
            str(self.timeout.value()),
        )

    def toggle_listening(self) -> None:
        if self.listening:
            self.stop_listening()
        else:
            self.start_listening()

    def start_listening(self) -> None:
        try:
            self.current_config()
        except ClipOCRError as exc:
            self.set_status(STATUS_ERROR)
            self.log(f"Cannot start: {exc}")
            return
        self.listening = True
        self.poll_timer.start()
        self.listen_button.setText("Stop listening")
        self.toggle_action.setText("Stop listening")
        self.set_status(STATUS_WAITING)
        self.log("Clipboard monitoring started")

    def stop_listening(self) -> None:
        self.listening = False
        self.poll_timer.stop()
        self.listen_button.setText("Start listening")
        self.toggle_action.setText("Start listening")
        self.set_status(STATUS_STOPPED)
        self.log("Clipboard monitoring stopped")

    def check_clipboard(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            return
        try:
            image = read_clipboard_image()
            fingerprint = image_fingerprint(image)
        except ClipOCRError:
            return
        except Exception as exc:
            self.set_status(STATUS_ERROR)
            self.log(f"Clipboard read failed: {exc}")
            return

        if fingerprint == self.last_fingerprint:
            return
        if self.confirm_auto_send.isChecked() and not self.confirm_send_image():
            self.last_fingerprint = fingerprint
            self.log("Recognition skipped by user")
            return
        self.recognize_once(fingerprint, image)

    def confirm_send_image(self) -> bool:
        if self.confirming_send:
            return False
        self.confirming_send = True
        was_listening = self.listening
        if was_listening:
            self.poll_timer.stop()
        self.show_window()
        try:
            result = QMessageBox.question(
                self,
                "Send clipboard image?",
                "Send the detected clipboard image to the configured OCR API?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            return result == QMessageBox.StandardButton.Yes
        finally:
            self.confirming_send = False
            if was_listening and self.listening and not self.shutting_down:
                self.poll_timer.start()

    def recognize_once(
        self,
        fingerprint: tuple[str, tuple[int, int]] | None = None,
        image: Image.Image | None = None,
    ) -> None:
        if self.worker is not None and self.worker.isRunning():
            self.log("Recognition already running")
            return
        try:
            config = self.current_config()
        except ClipOCRError as exc:
            self.set_status(STATUS_ERROR)
            self.log(str(exc))
            return

        if fingerprint is not None:
            self.last_fingerprint = fingerprint

        self.set_status(STATUS_WORKING)
        self.log("Recognition started")
        self.worker = OcrWorker(config, image)
        self.worker.finished_ok.connect(self.on_recognition_done)
        self.worker.failed.connect(self.on_recognition_failed)
        self.worker.start()

    def on_recognition_done(self, markdown: str) -> None:
        try:
            QApplication.clipboard().setText(markdown)
            if QApplication.clipboard().text() != markdown:
                write_text_to_clipboard(markdown)
        except Exception as exc:
            self.set_status(STATUS_ERROR)
            self.log(f"Clipboard write failed: {exc}")
            return

        self.log(f"Recognition completed: {len(markdown)} characters copied")
        self.set_status(STATUS_DONE)
        self.last_done_timer.start(1800)
        self.finish_pending_quit()

    def on_recognition_failed(self, message: str) -> None:
        self.set_status(STATUS_ERROR)
        self.log(f"Recognition failed: {message}")
        if self.listening:
            self.last_done_timer.start(1800)
        self.finish_pending_quit()

    def set_status(self, status: str) -> None:
        labels = {
            STATUS_STOPPED: "closed",
            STATUS_WAITING: "running: waiting for screenshot",
            STATUS_WORKING: "running: recognizing",
            STATUS_DONE: "running: completed",
            STATUS_ERROR: "error",
        }
        colors = {
            STATUS_STOPPED: QColor("#8a8a8a"),
            STATUS_WAITING: QColor("#2f80ed"),
            STATUS_WORKING: QColor("#f2994a"),
            STATUS_DONE: QColor("#27ae60"),
            STATUS_ERROR: QColor("#eb5757"),
        }
        label = labels[status]
        self.status_label.setText(f"Status: {label}")
        self.tray.setToolTip(f"ClipOCR - {label}")
        self.tray.setIcon(self.status_icon(colors[status]))

    def status_icon(self, color: QColor) -> QIcon:
        pixmap = QPixmap(64, 64)
        pixmap.fill(QColor("transparent"))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(color)
        painter.setPen(color)
        painter.drawEllipse(8, 8, 48, 48)
        painter.end()
        return QIcon(pixmap)

    def log(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}"
        self.log_box.append(line)
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        self.rotate_log_if_needed()
        with LOG_PATH.open("a", encoding="utf-8") as file:
            file.write(line + "\n")

    def rotate_log_if_needed(self) -> None:
        try:
            if LOG_PATH.exists() and LOG_PATH.stat().st_size > MAX_LOG_BYTES:
                backup_path = LOG_PATH.with_suffix(".log.1")
                if backup_path.exists():
                    backup_path.unlink()
                LOG_PATH.replace(backup_path)
        except OSError:
            pass

    def show_window(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def request_quit(self) -> None:
        if self.worker is not None and self.worker.isRunning():
            if not self.pending_quit:
                self.pending_quit = True
                self.stop_listening()
                self.run_once_button.setEnabled(False)
                self.listen_button.setEnabled(False)
                self.save_button.setEnabled(False)
                self.log("Recognition is running; ClipOCR will quit when it finishes")
            return
        QApplication.quit()

    def finish_pending_quit(self) -> None:
        if self.pending_quit:
            QApplication.quit()

    def closeEvent(self, event) -> None:  # noqa: N802
        if self.tray.isVisible():
            self.hide()
            event.ignore()
        else:
            event.accept()

    def cleanup(self) -> None:
        self.shutting_down = True
        self.poll_timer.stop()
        self.last_done_timer.stop()
        if self.hotkey_registered:
            unregister_hotkey()
            self.hotkey_registered = False
        if self.worker is not None and self.worker.isRunning():
            self.worker.wait()


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
