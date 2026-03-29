from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QEasingCurve, QObject, QPropertyAnimation, Signal, Slot
from PySide6.QtWidgets import QFrame, QGraphicsOpacityEffect

from launcher.core.launcher_service import LauncherService


class LaunchWorker(QObject):
    progress_changed = Signal(int)
    maximum_changed = Signal(int)
    status_changed = Signal(str)
    finished = Signal(bool, str, str)

    def __init__(self, launcher_service: LauncherService) -> None:
        super().__init__()
        self._launcher_service = launcher_service

    @Slot()
    def run(self) -> None:
        try:
            result = self._launcher_service.launch_game(
                progress_callback=self.progress_changed.emit,
                max_callback=self.maximum_changed.emit,
                status_callback=self.status_changed.emit,
            )
        except Exception as exc:
            result = SimpleNamespace(
                ok=False,
                message="Не удалось подготовить или запустить Minecraft.",
                details=f"Тип ошибки: {type(exc).__name__}\nПодробности: {exc}",
            )
        self.finished.emit(result.ok, result.message, result.details)


class WindowController:
    def __init__(self, left_panel: QFrame, right_panel: QFrame, parent: QObject) -> None:
        self._left_panel = left_panel
        self._right_panel = right_panel
        self.left_panel_open = False
        self.right_panel_open = False

        self.left_anim = QPropertyAnimation(self._left_panel, b"maximumWidth", parent)
        self.left_anim.setDuration(320)
        self.left_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.left_opacity_effect = QGraphicsOpacityEffect(self._left_panel)
        self.left_opacity_effect.setOpacity(0.0)
        self._left_panel.setGraphicsEffect(self.left_opacity_effect)
        self.left_fade_anim = QPropertyAnimation(self.left_opacity_effect, b"opacity", parent)
        self.left_fade_anim.setDuration(260)
        self.left_fade_anim.setEasingCurve(QEasingCurve.InOutCubic)

        self.right_anim = QPropertyAnimation(self._right_panel, b"maximumWidth", parent)
        self.right_anim.setDuration(320)
        self.right_anim.setEasingCurve(QEasingCurve.InOutCubic)
        self.right_opacity_effect = QGraphicsOpacityEffect(self._right_panel)
        self.right_opacity_effect.setOpacity(0.0)
        self._right_panel.setGraphicsEffect(self.right_opacity_effect)
        self.right_fade_anim = QPropertyAnimation(self.right_opacity_effect, b"opacity", parent)
        self.right_fade_anim.setDuration(260)
        self.right_fade_anim.setEasingCurve(QEasingCurve.InOutCubic)

    def toggle_left_panel(self) -> None:
        self.left_panel_open = not self.left_panel_open
        target = 360 if self.left_panel_open else 0
        self.left_anim.stop()
        self.left_anim.setStartValue(self._left_panel.maximumWidth())
        self.left_anim.setEndValue(target)
        self.left_fade_anim.stop()
        self.left_fade_anim.setStartValue(self.left_opacity_effect.opacity())
        self.left_fade_anim.setEndValue(1.0 if self.left_panel_open else 0.0)
        self.left_anim.start()
        self.left_fade_anim.start()

    def toggle_right_panel(self) -> None:
        self.right_panel_open = not self.right_panel_open
        target = 340 if self.right_panel_open else 0
        self.right_anim.stop()
        self.right_anim.setStartValue(self._right_panel.maximumWidth())
        self.right_anim.setEndValue(target)
        self.right_fade_anim.stop()
        self.right_fade_anim.setStartValue(self.right_opacity_effect.opacity())
        self.right_fade_anim.setEndValue(1.0 if self.right_panel_open else 0.0)
        self.right_anim.start()
        self.right_fade_anim.start()
