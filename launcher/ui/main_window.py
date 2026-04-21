from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from PySide6.QtCore import QEvent, QEasingCurve, QPropertyAnimation, QSize, QThread, QTimer, Qt, QUrl, Slot, QVariantAnimation
from PySide6.QtGui import QColor, QDesktopServices, QFont, QFontDatabase, QFontMetrics, QIcon, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGraphicsOpacityEffect,
    QGraphicsDropShadowEffect,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QWidget,
    QVBoxLayout,
)

from launcher.core.config_manager import ConfigManager
from launcher.core.java_finder import JavaFinder
from launcher.core.java_installer import JavaInstaller
from launcher.core.profile_manager import ProfileManager
from launcher.core.launcher_service import LauncherService
from launcher.ui.account_controller import AccountController
from launcher.ui.localization import UIStrings, get_ui_strings
from launcher.ui.overlays import ScenePulseOverlay
from launcher.ui.panels import CenterPanel, LeftPanel, SettingsPanel
from launcher.ui.theme import build_main_window_styles
from launcher.ui.title_bar import TitleBar
from launcher.ui.widgets import BackgroundWidget
from launcher.ui.window_controller import JavaInstallWorker, LaunchWorker, WindowController


class MainWindow(QMainWindow):
    MEMORY_PRESETS_MB = (6144, 8192, 10240)

    def __init__(
        self,
        config_manager: ConfigManager,
        profile_manager: ProfileManager,
        launcher_service: LauncherService,
    ) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.profile_manager = profile_manager
        self.launcher_service = launcher_service
        self.texts: UIStrings = get_ui_strings("ru")

        self.setWindowTitle(self.texts.app_name)
        self.setFixedSize(1280, 760)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.launch_thread: QThread | None = None
        self.launch_worker: LaunchWorker | None = None
        self.java_install_thread: QThread | None = None
        self.java_install_worker: JavaInstallWorker | None = None
        self.java_installer = JavaInstaller(config_manager)
        self.game_watch_timer = QTimer(self)
        self.game_watch_timer.setInterval(1500)
        self.game_watch_timer.timeout.connect(self._sync_game_running_state)

        icon_path = self._resolve_icon_path()
        icon: QIcon | None = None
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            self.setWindowIcon(icon)

        root = BackgroundWidget(self)
        root.setObjectName("rootWidget")
        self.setCentralWidget(root)
        self.scene_pulse_overlay = ScenePulseOverlay(root)
        self.scene_pulse_overlay.setGeometry(root.rect())

        outer = QVBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.title_bar = TitleBar(self.windowTitle(), icon, self)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.close_requested.connect(self.close)
        outer.addWidget(self.title_bar)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 18, 28, 24)
        content_layout.setSpacing(16)

        self.main_area = QGridLayout()
        self.main_area.setColumnStretch(0, 1)
        self.main_area.setColumnStretch(1, 0)
        self.main_area.setColumnStretch(2, 1)
        self.main_area.setRowStretch(0, 1)
        self.main_area.setRowStretch(1, 0)

        self.left_panel = LeftPanel(self.texts)
        self.left_panel.close_requested.connect(self._toggle_left_panel)
        self.left_mod_title = self.left_panel.mod_title_label
        self.left_mod_desc = self.left_panel.mod_desc_label

        dust_path = self._resolve_asset_path("dust.png")
        self.center_card = CenterPanel(self.texts, dust_path)
        self.center_card.mod_requested.connect(self._toggle_left_panel)
        self.center_card.play_requested.connect(self._on_play_clicked)
        self.mod_button = self.center_card.mod_button
        self.play_button = self.center_card.play_button
        self.launch_progress = self.center_card.launch_progress
        self.card_dust_overlay = self.center_card.dust_overlay
        self.card_bottom_pulse_overlay = self.center_card.bottom_pulse_overlay
        self.account_controller = AccountController(
            config_manager=self.config_manager,
            texts=self.texts,
            account_name_label=self.center_card.account_name_label,
            account_status_label=self.center_card.account_status_label,
            account_avatar_label=self.center_card.avatar_label,
            account_action_button=self.center_card.account_action_button,
            parent=self,
        )
        self.center_card.add_account_requested.connect(self.account_controller.handle_action_click)
        self.center_card.account_settings_requested.connect(self.account_controller.open_account_settings)
        self.account_controller.toast_requested.connect(self._show_save_toast)
        self.account_controller.warning_requested.connect(self._show_warning_dialog)

        self.right_panel = SettingsPanel(
            self.texts,
            self.MEMORY_PRESETS_MB,
            self._default_minecraft_dir(),
        )
        self.right_panel.browse_requested.connect(self._browse_game_dir)
        self.right_panel.save_requested.connect(self._save_settings)
        self.right_panel.close_requested.connect(self._toggle_right_panel)
        self.right_panel.open_logs_requested.connect(self._open_logs_folder)
        self.memory_value = self.right_panel.memory_value_label
        self.memory_slider = self.right_panel.memory_slider
        self.memory_slider.valueChanged.connect(self._on_memory_changed)
        self.game_dir_input = self.right_panel.game_dir_input
        self.close_after_launch_checkbox = self.right_panel.close_after_launch_checkbox
        self.show_launch_logs_checkbox = self.right_panel.show_launch_logs_checkbox

        self.center_card_wrapper = QWidget()
        center_wrap_layout = QVBoxLayout(self.center_card_wrapper)
        center_wrap_layout.setContentsMargins(0, 20, 0, 0)
        center_wrap_layout.setSpacing(0)
        self.center_logo = QLabel()
        self.center_logo.setObjectName("centerLogo")
        self.center_logo.setAlignment(Qt.AlignCenter)
        self.center_logo.setFixedHeight(280)
        logo_path = self._resolve_asset_path("logo.png")
        center_wrap_layout.addWidget(self.center_logo, alignment=Qt.AlignHCenter | Qt.AlignTop)
        center_wrap_layout.addSpacing(10)
        self._center_logo_source = QPixmap()
        if logo_path.exists():
            logo_pixmap = QPixmap(str(logo_path))
            if not logo_pixmap.isNull():
                self._center_logo_source = logo_pixmap
                self._update_center_logo_pixmap()
        center_wrap_layout.addWidget(self.center_card, alignment=Qt.AlignHCenter | Qt.AlignTop)

        self.main_area.addWidget(self.left_panel, 0, 0, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        self.main_area.addWidget(self.center_card_wrapper, 0, 1, alignment=Qt.AlignCenter)
        self.main_area.addWidget(self.right_panel, 0, 2, alignment=Qt.AlignRight | Qt.AlignVCenter)

        content_layout.addLayout(self.main_area)
        content_layout.addLayout(self._build_bottom_controls())
        outer.addWidget(content, 1)
        self.launch_progress.setParent(root)
        self.scene_pulse_overlay.lower()
        self._position_launch_progress()
        self.launch_progress.raise_()
        self._setup_save_toast(root)

        self.window_controller = WindowController(self.left_panel, self.right_panel, self)
        self._setup_logo_pulse()
        self._setup_center_card_depth()
        self._setup_center_card_bottom_pulse()
        self._setup_play_button_glow()
        self._setup_mod_button_glow()
        self._set_play_state("idle")
        self._apply_minecraft_play_font()
        self._apply_styles()
        self._load_state()

    def _setup_center_card_depth(self) -> None:
        self._card_shadow_effect = QGraphicsDropShadowEffect(self.center_card)
        self._card_shadow_effect.setOffset(0, 10)
        self._card_shadow_effect.setBlurRadius(36)
        self._card_shadow_effect.setColor(QColor(4, 10, 20, 175))
        self.center_card.setGraphicsEffect(self._card_shadow_effect)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        self._update_center_logo_pixmap()
        self._position_launch_progress()
        self._position_save_toast()
        root = self.centralWidget()
        if isinstance(root, QWidget):
            self.scene_pulse_overlay.setGeometry(root.rect())
        self._update_scene_pulse_anchor()
        if hasattr(self, "card_dust_overlay") and self.card_dust_overlay is not None:
            self.card_dust_overlay.setGeometry(self.center_card.rect())
        if hasattr(self, "card_bottom_pulse_overlay") and self.card_bottom_pulse_overlay is not None:
            self.card_bottom_pulse_overlay.setGeometry(self.center_card.rect())
        super().resizeEvent(event)

    def _setup_center_card_bottom_pulse(self) -> None:
        if not hasattr(self, "card_bottom_pulse_overlay") or self.card_bottom_pulse_overlay is None:
            return
        self._card_bottom_pulse_anim = QVariantAnimation(self)
        self._card_bottom_pulse_anim.setDuration(3000)
        self._card_bottom_pulse_anim.setStartValue(0.0)
        self._card_bottom_pulse_anim.setEndValue(1.0)
        self._card_bottom_pulse_anim.setLoopCount(-1)
        self._card_bottom_pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._card_bottom_pulse_anim.valueChanged.connect(self._on_card_bottom_pulse_value)
        self._card_bottom_pulse_anim.start()

    def _on_card_bottom_pulse_value(self, value) -> None:
        if not hasattr(self, "card_bottom_pulse_overlay") or self.card_bottom_pulse_overlay is None:
            return
        t = float(value)
        pulse = (math.sin(2 * math.pi * t) + 1.0) * 0.5
        self.card_bottom_pulse_overlay.set_pulse(pulse)
        self.scene_pulse_overlay.set_pulse(pulse)
        self._update_scene_pulse_anchor()

    def _update_scene_pulse_anchor(self) -> None:
        root = self.centralWidget()
        if not isinstance(root, QWidget):
            return
        card_pos = self.center_card.mapTo(root, self.center_card.rect().bottomLeft())
        center_x = card_pos.x() + (self.center_card.width() / 2.0)
        center_y = card_pos.y() - 8.0
        self.scene_pulse_overlay.set_anchor(center_x, center_y)

    def _position_launch_progress(self) -> None:
        if not hasattr(self, "launch_progress"):
            return
        root = self.centralWidget()
        if root is None:
            return
        w = root.width()
        h = root.height()
        x = max(0, (w - self.launch_progress.width()) // 2)
        y = max(0, h - self.launch_progress.height() - 8)
        self.launch_progress.move(x, y)

    def _setup_save_toast(self, root: QWidget) -> None:
        self.settings_toast = QLabel(root)
        self.settings_toast.setObjectName("settingsToast")
        self.settings_toast.setAlignment(Qt.AlignCenter)
        self.settings_toast.hide()
        self.settings_toast_effect = QGraphicsOpacityEffect(self.settings_toast)
        self.settings_toast_effect.setOpacity(0.0)
        self.settings_toast.setGraphicsEffect(self.settings_toast_effect)
        self.settings_toast_anim = QPropertyAnimation(self.settings_toast_effect, b"opacity", self)
        self.settings_toast_anim.setDuration(180)
        self.settings_toast_hide_timer = QTimer(self)
        self.settings_toast_hide_timer.setSingleShot(True)
        self.settings_toast_hide_timer.timeout.connect(self._hide_save_toast)

    def _position_save_toast(self) -> None:
        if not hasattr(self, "settings_toast"):
            return
        root = self.centralWidget()
        if not isinstance(root, QWidget):
            return
        self.settings_toast.adjustSize()
        margin = 18
        x = max(margin, root.width() - self.settings_toast.width() - margin)
        y = max(margin, self.title_bar.height() + 14)
        self.settings_toast.move(x, y)

    def _show_save_toast(self, message: str | None = None) -> None:
        if not hasattr(self, "settings_toast"):
            return
        self.settings_toast.setText(message or self.texts.settings_saved_message)
        self._position_save_toast()
        self.settings_toast.raise_()
        self.settings_toast.show()
        self.settings_toast_anim.stop()
        self.settings_toast_hide_timer.stop()
        self.settings_toast_anim.setStartValue(self.settings_toast_effect.opacity())
        self.settings_toast_anim.setEndValue(1.0)
        self.settings_toast_anim.start()
        self.settings_toast_hide_timer.start(1800)

    def _hide_save_toast(self) -> None:
        if not hasattr(self, "settings_toast"):
            return
        try:
            self.settings_toast_anim.finished.disconnect(self._finalize_hide_save_toast)
        except (RuntimeError, TypeError):
            pass
        self.settings_toast_anim.stop()
        self.settings_toast_anim.setStartValue(self.settings_toast_effect.opacity())
        self.settings_toast_anim.setEndValue(0.0)
        self.settings_toast_anim.finished.connect(self._finalize_hide_save_toast)
        self.settings_toast_anim.start()

    def _finalize_hide_save_toast(self) -> None:
        if not hasattr(self, "settings_toast"):
            return
        try:
            self.settings_toast_anim.finished.disconnect(self._finalize_hide_save_toast)
        except (RuntimeError, TypeError):
            pass
        if self.settings_toast_effect.opacity() <= 0.01:
            self.settings_toast.hide()

    def _show_warning_dialog(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _update_center_logo_pixmap(self) -> None:
        if not hasattr(self, "_center_logo_source") or self._center_logo_source.isNull():
            self.center_logo.clear()
            return
        max_w = max(420, self.center_card_wrapper.width() - 24)
        pix = self._center_logo_source.scaled(
            max_w,
            self.center_logo.height(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.center_logo.setPixmap(pix)

    def _setup_logo_pulse(self) -> None:
        self._logo_glow_effect = QGraphicsDropShadowEffect(self.center_logo)
        self._logo_glow_effect.setOffset(0, 0)
        self._logo_glow_effect.setBlurRadius(18)
        self._logo_glow_effect.setColor(QColor(228, 104, 223, 95))
        self.center_logo.setGraphicsEffect(self._logo_glow_effect)

        self._logo_pulse_anim = QVariantAnimation(self)
        self._logo_pulse_anim.setDuration(2600)
        self._logo_pulse_anim.setStartValue(0.0)
        self._logo_pulse_anim.setEndValue(1.0)
        self._logo_pulse_anim.setLoopCount(-1)
        self._logo_pulse_anim.setEasingCurve(QEasingCurve.InOutSine)
        self._logo_pulse_anim.valueChanged.connect(self._on_logo_pulse_value)
        self._logo_pulse_anim.start()

    def _on_logo_pulse_value(self, value) -> None:
        if not hasattr(self, "_logo_glow_effect"):
            return
        t = float(value)
        blend = (math.sin(2 * math.pi * t) + 1.0) * 0.5
        intensity = (math.sin(math.pi * t) + 1.0) * 0.5

        c1 = QColor("#e468df")
        c2 = QColor("#aa2cd6")
        red = int(c1.red() * (1.0 - blend) + c2.red() * blend)
        green = int(c1.green() * (1.0 - blend) + c2.green() * blend)
        blue = int(c1.blue() * (1.0 - blend) + c2.blue() * blend)
        alpha = int(75 + 95 * intensity)
        blur = 14 + 20 * intensity

        self._logo_glow_effect.setBlurRadius(blur)
        self._logo_glow_effect.setColor(QColor(red, green, blue, alpha))

    def _apply_minecraft_play_font(self) -> None:
        # Optional pixel font auto-load from assets with safe fallback.
        font_candidates = [
            "Minecraftia-Regular.ttf",
            "Minecraftia.ttf",
            "PressStart2P-Regular.ttf",
        ]
        for filename in font_candidates:
            path = self._resolve_asset_path(filename)
            if not path.exists():
                continue
            font_id = QFontDatabase.addApplicationFont(str(path))
            if font_id < 0:
                continue
            families = QFontDatabase.applicationFontFamilies(font_id)
            if not families:
                continue
            play_font = QFont(families[0])
            self.play_button.setFont(play_font)
            break
        self._fit_mod_button_text()

    def _fit_mod_button_text(self) -> None:
        text = self.mod_button.text().strip()
        if not text:
            return
        target_width = max(40, self.mod_button.contentsRect().width() - 16)
        font = QFont(self.mod_button.font())
        for size in range(20, 11, -1):
            font.setPointSize(size)
            if QFontMetrics(font).horizontalAdvance(text) <= target_width:
                self.mod_button.setFont(font)
                return
        font.setPointSize(12)
        self.mod_button.setFont(font)

    def _setup_play_button_glow(self) -> None:
        self._play_glow_effect = QGraphicsDropShadowEffect(self.play_button)
        self._play_glow_effect.setOffset(0, 0)
        self._play_glow_effect.setBlurRadius(0)
        self._play_glow_effect.setColor(QColor(34, 197, 94, 0))
        self.play_button.setGraphicsEffect(self._play_glow_effect)
        self.play_button.installEventFilter(self)
        self._play_hovered = False
        self._play_glow_value = 0.0
        self._play_glow_anim = QVariantAnimation(self)
        self._play_glow_anim.setDuration(180)
        self._play_glow_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._play_glow_anim.valueChanged.connect(self._on_play_glow_animated)

    def _setup_mod_button_glow(self) -> None:
        self._mod_glow_effect = QGraphicsDropShadowEffect(self.mod_button)
        self._mod_glow_effect.setOffset(0, 0)
        self._mod_glow_effect.setBlurRadius(12)
        self._mod_glow_effect.setColor(QColor(152, 114, 214, 54))
        self.mod_button.setGraphicsEffect(self._mod_glow_effect)
        self.mod_button.installEventFilter(self)

    def _set_play_state(self, state: str) -> None:
        self.play_button.setProperty("playState", state)
        self.play_button.setProperty("pressedVisual", False)
        self._refresh_play_button_style()
        self._update_play_glow_target(animated=True)

    def _refresh_play_button_style(self) -> None:
        self.play_button.style().unpolish(self.play_button)
        self.play_button.style().polish(self.play_button)
        self.play_button.update()

    def _on_play_glow_animated(self, value) -> None:
        self._play_glow_value = float(value)
        self._apply_play_glow()

    def _apply_play_glow(self) -> None:
        if not hasattr(self, "_play_glow_effect"):
            return
        state = str(self.play_button.property("playState") or "idle")
        glow_rgb = (245, 158, 11) if state == "loading" else (34, 197, 94)

        intensity = max(0.0, min(1.0, self._play_glow_value))
        blur = 8 + (18 * intensity)
        alpha = int(35 + (115 * intensity))
        self._play_glow_effect.setBlurRadius(blur)
        self._play_glow_effect.setColor(QColor(glow_rgb[0], glow_rgb[1], glow_rgb[2], alpha))

    def _update_play_glow_target(self, animated: bool) -> None:
        state = str(self.play_button.property("playState") or "idle")
        if state == "idle":
            target = 1.0 if self._play_hovered and self.play_button.isEnabled() else 0.18
        elif state == "loading":
            target = 0.42
        elif state == "running":
            target = 0.28
        else:
            target = 0.0

        if animated:
            self._play_glow_anim.stop()
            self._play_glow_anim.setStartValue(self._play_glow_value)
            self._play_glow_anim.setEndValue(target)
            self._play_glow_anim.start()
        else:
            self._play_glow_value = target
            self._apply_play_glow()

    def eventFilter(self, watched, event) -> bool:  # type: ignore[override]
        if watched is self.play_button:
            if event.type() == QEvent.Enter:
                self._play_hovered = True
                self._update_play_glow_target(animated=True)
            elif event.type() == QEvent.Leave:
                self._play_hovered = False
                self.play_button.setProperty("pressedVisual", False)
                self._refresh_play_button_style()
                self._update_play_glow_target(animated=True)
            elif event.type() == QEvent.MouseButtonPress and self.play_button.isEnabled():
                self.play_button.setProperty("pressedVisual", True)
                self._refresh_play_button_style()
            elif event.type() == QEvent.MouseButtonRelease:
                self.play_button.setProperty("pressedVisual", False)
                self._refresh_play_button_style()
        elif watched is self.mod_button and hasattr(self, "_mod_glow_effect"):
            if event.type() == QEvent.Enter:
                self._mod_glow_effect.setBlurRadius(16)
                self._mod_glow_effect.setColor(QColor(170, 132, 236, 86))
            elif event.type() == QEvent.Leave:
                self._mod_glow_effect.setBlurRadius(12)
                self._mod_glow_effect.setColor(QColor(152, 114, 214, 54))
        return super().eventFilter(watched, event)

    def _resolve_asset_path(self, filename: str) -> Path:
        if getattr(sys, "frozen", False):
            exe_base = Path(sys.executable).resolve().parent
            candidates = [exe_base / "assets" / filename]
            if hasattr(sys, "_MEIPASS"):
                candidates.append(Path(getattr(sys, "_MEIPASS")) / "assets" / filename)
            return next((path for path in candidates if path.exists()), candidates[0])
        return Path(__file__).resolve().parents[2] / "assets" / filename

    def _resolve_icon_path(self) -> Path:
        ico_path = self._resolve_asset_path("ico.ico")
        if ico_path.exists():
            return ico_path
        return self._resolve_asset_path("ico.png")

    def _build_bottom_controls(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        self.open_folder_btn = QPushButton()
        self.open_folder_btn.setObjectName("roundButton")
        self.open_folder_btn.setFixedSize(52, 52)
        self.open_folder_btn.setIcon(QIcon(str(self._resolve_asset_path("folder.svg"))))
        self.open_folder_btn.setIconSize(QSize(24, 24))
        self.open_folder_btn.clicked.connect(self._open_game_folder)

        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("roundButton")
        self.settings_btn.setFixedSize(52, 52)
        self.settings_btn.setIcon(QIcon(str(self._resolve_asset_path("gear-six.svg"))))
        self.settings_btn.setIconSize(QSize(24, 24))
        self.settings_btn.clicked.connect(self._toggle_right_panel)

        row.addWidget(self.open_folder_btn, alignment=Qt.AlignLeft)
        row.addStretch(1)
        row.addWidget(self.settings_btn, alignment=Qt.AlignRight)
        return row

    def _toggle_left_panel(self) -> None:
        self.window_controller.toggle_left_panel()

    def _toggle_right_panel(self) -> None:
        self.window_controller.toggle_right_panel()

    def _on_memory_changed(self, value: int) -> None:
        memory_mb = self._memory_mb_from_slider(value)
        self.memory_value.setText(
            self.texts.memory_value_format.format(gb=memory_mb // 1024, mb=memory_mb)
        )
        if hasattr(self.right_panel, "memory_mark_labels"):
            for index, label in enumerate(self.right_panel.memory_mark_labels):
                is_active = index == int(value)
                if bool(label.property("active")) == is_active:
                    continue
                label.setProperty("active", is_active)
                label.style().unpolish(label)
                label.style().polish(label)
                label.update()

    def _browse_game_dir(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self,
            self.texts.browse_game_dir_title,
            self.game_dir_input.text(),
        )
        if selected:
            self.game_dir_input.setText(selected)

    def _save_settings(self) -> None:
        self._persist_settings(notify=True)

    def _on_play_clicked(self) -> None:
        if self._is_launch_in_progress():
            return
        if self._is_java_install_in_progress():
            return
        self._persist_settings()
        if not self._ensure_java_ready():
            return
        self._start_game_launch()

    def _start_game_launch(self) -> None:
        self.game_watch_timer.stop()
        self._set_play_state("loading")
        self.play_button.setEnabled(False)
        self.play_button.setText(self.texts.play_button_loading)
        self.launch_progress.setFormat(self.texts.launch_progress_preparing)
        self.launch_progress.setMaximum(0)
        self.launch_progress.setValue(0)
        self._position_launch_progress()
        self.launch_progress.raise_()
        self.launch_progress.show()

        self.launch_thread = QThread(self)
        self.launch_worker = LaunchWorker(self.launcher_service)
        self.launch_worker.moveToThread(self.launch_thread)

        self.launch_thread.started.connect(self.launch_worker.run)
        self.launch_worker.progress_changed.connect(self._on_launch_progress)
        self.launch_worker.maximum_changed.connect(self._on_launch_maximum)
        self.launch_worker.status_changed.connect(self._on_launch_status)
        self.launch_worker.finished.connect(self._on_launch_finished)
        self.launch_worker.finished.connect(self.launch_thread.quit)
        self.launch_worker.finished.connect(self.launch_worker.deleteLater)
        self.launch_thread.finished.connect(self.launch_thread.deleteLater)
        self.launch_thread.finished.connect(self._on_launch_thread_finished)
        self.launch_thread.start()

    def _ensure_java_ready(self) -> bool:
        java_path = JavaFinder.find(
            self.config_manager.config.java_path,
            self.config_manager.base_dir,
        )
        if java_path:
            if self.config_manager.config.java_path != java_path:
                self.config_manager.update(java_path=java_path)
            return True

        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Question)
        dialog.setWindowTitle("Java не найдена")
        dialog.setText("Лаунчер не обнаружил установленную Java 17.")
        dialog.setInformativeText("Установить Java автоматически сейчас?")
        yes_button = dialog.addButton("Да", QMessageBox.AcceptRole)
        dialog.addButton("Нет", QMessageBox.RejectRole)
        dialog.exec()

        if dialog.clickedButton() is not yes_button:
            return False

        self._start_java_install()
        return False

    def _start_java_install(self) -> None:
        self.game_watch_timer.stop()
        self._set_play_state("loading")
        self.play_button.setEnabled(False)
        self.play_button.setText("Установка Java")
        self.launch_progress.setFormat("Подготавливаем установку Java...")
        self.launch_progress.setMaximum(0)
        self.launch_progress.setValue(0)
        self._position_launch_progress()
        self.launch_progress.raise_()
        self.launch_progress.show()

        self.java_install_thread = QThread(self)
        self.java_install_worker = JavaInstallWorker(self.java_installer)
        self.java_install_worker.moveToThread(self.java_install_thread)

        self.java_install_thread.started.connect(self.java_install_worker.run)
        self.java_install_worker.progress_changed.connect(self._on_launch_progress)
        self.java_install_worker.maximum_changed.connect(self._on_launch_maximum)
        self.java_install_worker.status_changed.connect(self._on_launch_status)
        self.java_install_worker.finished.connect(self._on_java_install_finished)
        self.java_install_worker.finished.connect(self.java_install_thread.quit)
        self.java_install_worker.finished.connect(self.java_install_worker.deleteLater)
        self.java_install_thread.finished.connect(self.java_install_thread.deleteLater)
        self.java_install_thread.finished.connect(self._on_java_install_thread_finished)
        self.java_install_thread.start()

    @Slot(int)
    def _on_launch_progress(self, value: int) -> None:
        if self.launch_progress.maximum() == 0:
            return
        self.launch_progress.setValue(value)

    @Slot(int)
    def _on_launch_maximum(self, value: int) -> None:
        self.launch_progress.setMaximum(max(1, value))
        if self.launch_progress.value() > value:
            self.launch_progress.setValue(value)

    @Slot(str)
    def _on_launch_status(self, text: str) -> None:
        clean_text = " ".join(text.split()).strip() or self.texts.launch_progress_preparing
        self.launch_progress.setToolTip(clean_text)
        if self.launch_progress.maximum() == 0:
            self.launch_progress.setFormat(clean_text)
        else:
            self.launch_progress.setFormat(f"{clean_text}  %p%")

    @Slot(bool, str, str)
    def _on_launch_finished(self, ok: bool, message: str, details: str) -> None:
        self.account_controller.sync_from_saved_session()
        if ok:
            self._set_play_state("running")
            self.play_button.setEnabled(False)
            self.play_button.setText(self.texts.play_button_running)
            self.game_watch_timer.start()
            if self.config_manager.config.close_after_launch:
                self.close()
                return
        else:
            self.game_watch_timer.stop()
            self._set_play_state("idle")
            self.play_button.setEnabled(True)
            self.play_button.setText(self.texts.play_button_idle)
        self.launch_progress.hide()
        self.launch_progress.setMaximum(100)
        self.launch_progress.setValue(0)

        if not ok:
            self._show_launch_error_dialog(message, details)

    @Slot(bool, str, str, str)
    def _on_java_install_finished(self, ok: bool, message: str, details: str, java_path: str) -> None:
        if ok:
            if java_path:
                self.config_manager.update(java_path=java_path)
            self._show_save_toast(message)
            self._start_game_launch()
            return

        self.launch_progress.hide()
        self.launch_progress.setMaximum(100)
        self.launch_progress.setValue(0)
        self._set_play_state("idle")
        self.play_button.setEnabled(True)
        self.play_button.setText(self.texts.play_button_idle)
        self._show_warning_dialog("Установка Java", details or message)

    def _show_launch_error_dialog(self, message: str, details: str) -> None:
        dialog = QMessageBox(self)
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle(self.texts.launch_error_title)
        dialog.setText(message)
        dialog.setInformativeText(self.texts.launch_error_help)
        dialog.setDetailedText(details or message)

        open_logs_button = dialog.addButton(self.texts.open_logs_button, QMessageBox.ActionRole)
        open_game_button = dialog.addButton(self.texts.open_game_folder_button, QMessageBox.ActionRole)
        dialog.addButton(QMessageBox.Close)
        dialog.exec()

        clicked = dialog.clickedButton()
        if clicked is open_logs_button:
            self._open_logs_folder()
        elif clicked is open_game_button:
            self._open_game_folder()

    def _sync_game_running_state(self) -> None:
        if self.launcher_service.is_game_running():
            return
        self.game_watch_timer.stop()
        self._set_play_state("idle")
        self.play_button.setEnabled(True)
        self.play_button.setText(self.texts.play_button_idle)

    @Slot()
    def _on_launch_thread_finished(self) -> None:
        self.launch_thread = None
        self.launch_worker = None

    @Slot()
    def _on_java_install_thread_finished(self) -> None:
        self.java_install_thread = None
        self.java_install_worker = None

    def _save_settings_silent(self) -> None:
        self._persist_settings()

    def _persist_settings(self, notify: bool = False) -> None:
        memory_mb = self._memory_mb_from_slider(self.memory_slider.value())
        self.config_manager.update(
            game_dir=self.game_dir_input.text().strip() or self._default_minecraft_dir(),
            memory_mb=memory_mb,
            close_after_launch=self.close_after_launch_checkbox.isChecked(),
            show_launch_logs=self.show_launch_logs_checkbox.isChecked(),
        )
        saved_slider_value = self._slider_from_memory_mb(self.config_manager.config.memory_mb)
        if self.memory_slider.value() != saved_slider_value:
            self.memory_slider.setValue(saved_slider_value)
        else:
            self._on_memory_changed(saved_slider_value)
        if notify:
            self._show_save_toast()

    def _is_launch_in_progress(self) -> bool:
        return self.launch_thread is not None and self.launch_thread.isRunning()

    def _is_java_install_in_progress(self) -> bool:
        return self.java_install_thread is not None and self.java_install_thread.isRunning()

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self.game_watch_timer.stop()
        self.account_controller.shutdown()
        if self._is_launch_in_progress():
            self.launch_thread.quit()
            self.launch_thread.wait(3000)
        if self._is_java_install_in_progress():
            self.java_install_thread.quit()
            self.java_install_thread.wait(3000)
        super().closeEvent(event)

    def _open_game_folder(self) -> None:
        game_dir = Path(self.config_manager.config.game_dir).expanduser().resolve()
        game_dir.mkdir(parents=True, exist_ok=True)

        if os.name == "nt":
            os.startfile(str(game_dir))
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(game_dir)))

    def _open_logs_folder(self) -> None:
        logs_dir = self.launcher_service.get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)

        if os.name == "nt":
            os.startfile(str(logs_dir))
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(logs_dir)))

    def _load_state(self) -> None:
        config = self.config_manager.config

        self.account_controller.load_state()
        self.mod_button.setText(self.texts.mod_title)
        self._fit_mod_button_text()
        self.left_mod_title.setText(self.texts.mod_title)
        self.left_mod_desc.setText(self.texts.mod_description)

        self.game_dir_input.setText(config.game_dir)
        self.close_after_launch_checkbox.setChecked(config.close_after_launch)
        self.show_launch_logs_checkbox.setChecked(config.show_launch_logs)
        slider_value = self._slider_from_memory_mb(config.memory_mb)
        self.memory_slider.setValue(slider_value)
        self._on_memory_changed(slider_value)

    @classmethod
    def _memory_mb_from_slider(cls, slider_value: int) -> int:
        idx = max(0, min(len(cls.MEMORY_PRESETS_MB) - 1, int(slider_value)))
        return cls.MEMORY_PRESETS_MB[idx]

    @classmethod
    def _slider_from_memory_mb(cls, memory_mb: int) -> int:
        candidates = list(enumerate(cls.MEMORY_PRESETS_MB))
        return min(candidates, key=lambda item: abs(item[1] - int(memory_mb)))[0]

    @staticmethod
    def _default_minecraft_dir() -> str:
        return str(Path(os.getenv("APPDATA", str(Path.home()))) / ".minecraft")

    def _apply_styles(self) -> None:
        bg_file = self._resolve_asset_path("background.png")
        root = self.centralWidget()
        if isinstance(root, BackgroundWidget):
            root.set_background(bg_file.resolve())
        self.setStyleSheet(build_main_window_styles())
