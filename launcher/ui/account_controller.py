from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import HTTPErrorProcessor, HTTPHandler, HTTPSHandler, build_opener

from PySide6.QtCore import QObject, QSize, QThread, QUrl, Signal, Slot, Qt
from PySide6.QtGui import QDesktopServices, QIcon, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QLabel, QPushButton

from launcher.core.account_manager import AccountManager, AccountSession
from launcher.core.config_manager import ConfigManager
from launcher.core.ely_auth import ElyAuthClient, ElyAuthResult
from launcher.ui.localization import UIStrings


class ElyAuthWorker(QObject):
    finished = Signal(bool, object, str)

    def __init__(self, auth_client: ElyAuthClient) -> None:
        super().__init__()
        self._auth_client = auth_client

    @Slot()
    def run(self) -> None:
        result: ElyAuthResult = self._auth_client.authorize()
        self.finished.emit(result.ok, result.session, result.message)


class AvatarLoaderWorker(QObject):
    finished = Signal(str, bytes)
    failed = Signal(str)

    def __init__(self, username: str, avatar_url: str, cache_path: Path) -> None:
        super().__init__()
        self._username = username
        self._avatar_url = avatar_url
        self._cache_path = cache_path

    @Slot()
    def run(self) -> None:
        try:
            opener = build_opener(HTTPHandler, HTTPSHandler, _SilentHTTPErrorProcessor)
            with opener.open(self._avatar_url, timeout=20) as response:
                if getattr(response, "status", 200) >= 400:
                    self.failed.emit(self._username)
                    return
                skin_bytes = response.read()
        except (URLError, TimeoutError, OSError):
            self.failed.emit(self._username)
            return

        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            self._cache_path.write_bytes(skin_bytes)
        except OSError:
            pass
        self.finished.emit(self._username, skin_bytes)


class _SilentHTTPErrorProcessor(HTTPErrorProcessor):
    def http_response(self, request, response):  # type: ignore[override]
        return response

    https_response = http_response


class AccountController(QObject):
    toast_requested = Signal(str)
    warning_requested = Signal(str, str)
    avatar_loading_started = Signal()
    avatar_loading_finished = Signal()

    def __init__(
        self,
        config_manager: ConfigManager,
        texts: UIStrings,
        account_name_label: QLabel,
        account_status_label: QLabel,
        account_avatar_label: QLabel,
        account_action_button: QPushButton,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._texts = texts
        self._account_manager = AccountManager(config_manager)
        self._auth_client = ElyAuthClient()
        self._account_name_label = account_name_label
        self._account_status_label = account_status_label
        self._account_avatar_label = account_avatar_label
        self._account_action_button = account_action_button

        self._auth_thread: QThread | None = None
        self._auth_worker: ElyAuthWorker | None = None
        self._avatar_thread: QThread | None = None
        self._avatar_worker: AvatarLoaderWorker | None = None
        self._avatar_request_username = ""
        self._account_add_icon = self._load_svg_icon("user-plus.svg")
        self._account_logout_icon = self._load_svg_icon("user-minus.svg")

        self._account_action_button.setIconSize(QSize(16, 16))
        self._account_action_button.setText("")
        self._update_account_action_button(False)

    def load_state(self) -> None:
        self._apply_account_session(self._account_manager.get_active_session())

    def sync_from_saved_session(self) -> None:
        self._apply_account_session(self._account_manager.get_active_session())

    def shutdown(self) -> None:
        self._stop_avatar_loader()
        if self._auth_thread is not None and self._auth_thread.isRunning():
            self._auth_thread.quit()
            self._auth_thread.wait(1000)

    def handle_action_click(self) -> None:
        if self._account_manager.get_active_session() is not None:
            self._logout_account()
            return
        if self._auth_thread is not None and self._auth_thread.isRunning():
            return

        self._account_status_label.setText(self._texts.account_status_authorizing)
        self._account_action_button.setEnabled(False)

        self._auth_thread = QThread(self)
        self._auth_worker = ElyAuthWorker(self._auth_client)
        self._auth_worker.moveToThread(self._auth_thread)

        self._auth_thread.started.connect(self._auth_worker.run)
        self._auth_worker.finished.connect(self._on_auth_finished)
        self._auth_worker.finished.connect(self._auth_thread.quit)
        self._auth_worker.finished.connect(self._auth_worker.deleteLater)
        self._auth_thread.finished.connect(self._auth_thread.deleteLater)
        self._auth_thread.finished.connect(self._on_auth_thread_finished)
        self._auth_thread.start()

    def open_account_settings(self) -> None:
        if self._account_manager.get_active_session() is None:
            return
        QDesktopServices.openUrl(QUrl(self._account_manager.get_accounts_site_url()))

    @Slot(bool, object, str)
    def _on_auth_finished(self, ok: bool, session_obj: object, message: str) -> None:
        self._account_action_button.setEnabled(True)
        if ok and isinstance(session_obj, AccountSession):
            self._account_manager.save_session(session_obj)
            self._apply_account_session(session_obj)
            self.toast_requested.emit(message)
            return

        self._account_status_label.setText(self._texts.account_status_local)
        self.warning_requested.emit(self._texts.account_auth_error_title, message)

    @Slot()
    def _on_auth_thread_finished(self) -> None:
        self._auth_thread = None
        self._auth_worker = None

    def _logout_account(self) -> None:
        if self._account_manager.get_active_session() is None:
            return
        self._account_manager.clear_session()
        self._apply_account_session(None)
        self.toast_requested.emit(self._texts.account_logged_out_message)

    def _apply_account_session(self, session: AccountSession | None) -> None:
        if session is None:
            self._avatar_request_username = ""
            self._stop_avatar_loader()
            self._account_name_label.setText("Player")
            self._account_status_label.setText(self._texts.account_status_local)
            self._account_avatar_label.setPixmap(QPixmap())
            self._account_avatar_label.setText(self._texts.avatar_icon)
            self._update_account_action_button(False)
            return

        self._account_name_label.setText(session.username)
        self._account_status_label.setText(self._texts.account_status_connected)
        self._update_account_action_button(True)
        self._load_account_avatar(session)

    def _update_account_action_button(self, has_session: bool) -> None:
        icon = self._account_logout_icon if has_session else self._account_add_icon
        if icon is not None:
            self._account_action_button.setIcon(icon)
            self._account_action_button.setText("")
        else:
            self._account_action_button.setText("-" if has_session else self._texts.add_account_icon)
        self._account_action_button.setEnabled(True)

    def _load_svg_icon(self, filename: str) -> QIcon | None:
        icon_path = self._resolve_asset_path(filename)
        if not icon_path.exists():
            return None
        icon = QIcon(str(icon_path))
        if icon.isNull():
            return None
        return icon

    def _load_account_avatar(self, session: AccountSession) -> None:
        self._avatar_request_username = session.username
        cache_path = self._account_manager.get_avatar_cache_path(session.username)
        if cache_path.exists():
            try:
                self._apply_avatar_bytes(session.username, cache_path.read_bytes())
                return
            except OSError:
                pass

        self._account_avatar_label.setPixmap(QPixmap())
        self._account_avatar_label.setText(self._texts.avatar_icon)
        self._account_status_label.setText(self._texts.account_status_loading_avatar)

        self._stop_avatar_loader()
        try:
            opener = build_opener(HTTPHandler, HTTPSHandler, _SilentHTTPErrorProcessor)
            avatar_url = self._resolve_avatar_url(opener, session)
        except (URLError, TimeoutError, OSError, json.JSONDecodeError):
            self._account_status_label.setText(self._texts.account_status_connected)
            return

        self.avatar_loading_started.emit()
        self._avatar_thread = QThread(self)
        self._avatar_worker = AvatarLoaderWorker(session.username, avatar_url, cache_path)
        self._avatar_worker.moveToThread(self._avatar_thread)
        self._avatar_thread.started.connect(self._avatar_worker.run)
        self._avatar_worker.finished.connect(self._on_avatar_loaded)
        self._avatar_worker.failed.connect(self._on_avatar_failed)
        self._avatar_worker.finished.connect(self._avatar_thread.quit)
        self._avatar_worker.failed.connect(self._avatar_thread.quit)
        self._avatar_worker.finished.connect(self._avatar_worker.deleteLater)
        self._avatar_worker.failed.connect(self._avatar_worker.deleteLater)
        self._avatar_thread.finished.connect(self._avatar_thread.deleteLater)
        self._avatar_thread.finished.connect(self._on_avatar_thread_finished)
        self._avatar_thread.start()

    def _apply_avatar_bytes(self, username: str, skin_bytes: bytes) -> None:
        if username != self._avatar_request_username:
            return

        image = QImage.fromData(skin_bytes)
        if image.isNull() or image.width() < 16 or image.height() < 16:
            self._account_avatar_label.setPixmap(QPixmap())
            self._account_avatar_label.setText(self._texts.avatar_icon)
            return

        face = image.copy(8, 8, 8, 8)
        overlay = image.copy(40, 8, 8, 8) if image.width() >= 48 else QImage()
        face_pixmap = QPixmap.fromImage(face.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.FastTransformation))
        if not overlay.isNull():
            overlay_pixmap = QPixmap.fromImage(overlay.scaled(40, 40, Qt.IgnoreAspectRatio, Qt.FastTransformation))
            painter = QPainter(face_pixmap)
            painter.drawPixmap(0, 0, overlay_pixmap)
            painter.end()

        self._account_avatar_label.setText("")
        self._account_avatar_label.setPixmap(face_pixmap)

    @Slot(str, bytes)
    def _on_avatar_loaded(self, username: str, skin_bytes: bytes) -> None:
        if username != self._avatar_request_username:
            return
        self._apply_avatar_bytes(username, skin_bytes)
        self._account_status_label.setText(self._texts.account_status_connected)
        self.avatar_loading_finished.emit()

    @Slot(str)
    def _on_avatar_failed(self, username: str) -> None:
        if username != self._avatar_request_username:
            return
        self._account_avatar_label.setPixmap(QPixmap())
        self._account_avatar_label.setText(self._texts.avatar_icon)
        self._account_status_label.setText(self._texts.account_status_connected)
        self.avatar_loading_finished.emit()

    @Slot()
    def _on_avatar_thread_finished(self) -> None:
        self._avatar_thread = None
        self._avatar_worker = None

    def _stop_avatar_loader(self) -> None:
        if self._avatar_thread is not None and self._avatar_thread.isRunning():
            self._avatar_thread.quit()
            self._avatar_thread.wait(1000)

    def _resolve_avatar_url(self, opener, session: AccountSession) -> str:
        textures_url = f"https://skinsystem.ely.by/textures/{session.username}"
        try:
            with opener.open(textures_url, timeout=20) as response:
                if getattr(response, "status", 200) >= 400:
                    return session.skin_url
                payload = response.read().decode("utf-8", errors="replace").strip()
        except (URLError, TimeoutError, OSError):
            return session.skin_url

        if not payload:
            return session.skin_url

        textures = json.loads(payload)
        skin_info = textures.get("SKIN")
        if isinstance(skin_info, dict):
            url = skin_info.get("url")
            if isinstance(url, str) and url:
                return url
        return session.skin_url

    @staticmethod
    def _resolve_asset_path(filename: str) -> Path:
        if getattr(sys, "frozen", False):
            exe_base = Path(sys.executable).resolve().parent
            candidates = [exe_base / "assets" / filename]
            if hasattr(sys, "_MEIPASS"):
                candidates.append(Path(getattr(sys, "_MEIPASS")) / "assets" / filename)
            return next((path for path in candidates if path.exists()), candidates[0])
        return Path(__file__).resolve().parents[2] / "assets" / filename
