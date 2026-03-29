from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from launcher.core.config_manager import ConfigManager
from launcher.core.profile_manager import ProfileManager
from launcher.core.launcher_service import LauncherService
from launcher.ui.main_window import MainWindow


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Raramba Launcher")

    config_manager = ConfigManager()
    profile_manager = ProfileManager(config_manager)
    launcher_service = LauncherService(config_manager, profile_manager)

    window = MainWindow(config_manager, profile_manager, launcher_service)
    window.show()

    return app.exec()
