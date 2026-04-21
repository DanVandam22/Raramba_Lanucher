from __future__ import annotations

import socket
import sys
from pathlib import Path

from PySide6.QtCore import QDir
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication, QMessageBox

from launcher.core.config_manager import ConfigManager
from launcher.core.profile_manager import ProfileManager
from launcher.core.launcher_service import LauncherService
from launcher.ui.localization import get_ui_strings
from launcher.ui.main_window import MainWindow


class SingleInstanceLock:
    """Prevents multiple launcher instances by binding a fixed localhost port."""

    HOST = "127.0.0.1"
    PORT = 45873

    def __init__(self) -> None:
        self._socket: socket.socket | None = None

    def try_acquire(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.bind((self.HOST, self.PORT))
            self._socket.listen(1)
            return True
        except OSError:
            if self._socket is not None:
                self._socket.close()
                self._socket = None
            return False

    def release(self) -> None:
        if self._socket is None:
            return
        try:
            self._socket.close()
        except OSError:
            pass
        self._socket = None

    def __enter__(self) -> "SingleInstanceLock":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.release()


def run() -> int:
    texts = get_ui_strings("ru")
    with SingleInstanceLock() as lock:
        if not lock.try_acquire():
            app = QApplication.instance()
            if app is None:
                app = QApplication(sys.argv)
                app.setApplicationName(texts.app_name)
            QMessageBox.information(
                None,
                texts.app_name,
                "Лаунчер уже запущен.\n\nЗакройте текущий экземпляр, чтобы открыть новый.",
            )
            return 0

        app = QApplication(sys.argv)
        app.setApplicationName(texts.app_name)

        QDir.addSearchPath("fonts", str(Path(__file__).resolve().parents[1] / "assets"))
        app.setFont(QFont("Segoe UI", 10))

        config_manager = ConfigManager()
        profile_manager = ProfileManager(config_manager)
        launcher_service = LauncherService(config_manager, profile_manager)

        window = MainWindow(config_manager, profile_manager, launcher_service)
        window.show()

        return app.exec()
