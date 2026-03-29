from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QRadialGradient
from PySide6.QtWidgets import QWidget


class BottomPulseOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pulse = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

    def set_pulse(self, value: float) -> None:
        self._pulse = max(0.0, min(1.0, float(value)))
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return

        clip_path = QPainterPath()
        clip_path.addRoundedRect(self.rect(), 16, 16)
        painter.setClipPath(clip_path)

        intensity = (0.35 + (self._pulse * 0.9)) * 0.65
        alpha_main = int((18 + 44 * intensity) * 0.65)
        alpha_soft = int((10 + 26 * intensity) * 0.65)

        center_x = width / 2
        center_y = height - 16
        radius_main = max(130, int(width * 0.54))
        radius_soft = max(164, int(width * 0.66))

        grad_soft = QRadialGradient(center_x, center_y, radius_soft)
        grad_soft.setColorAt(0.0, QColor(108, 182, 206, alpha_soft))
        grad_soft.setColorAt(0.5, QColor(88, 154, 176, max(0, alpha_soft - 2)))
        grad_soft.setColorAt(1.0, QColor(88, 154, 176, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(grad_soft)
        painter.drawEllipse(int(center_x - radius_soft), int(center_y - radius_soft), radius_soft * 2, radius_soft * 2)

        grad_main = QRadialGradient(center_x, center_y, radius_main)
        grad_main.setColorAt(0.0, QColor(138, 212, 230, alpha_main))
        grad_main.setColorAt(0.42, QColor(110, 180, 202, max(0, alpha_main - 4)))
        grad_main.setColorAt(1.0, QColor(110, 180, 202, 0))
        painter.setBrush(grad_main)
        painter.drawEllipse(int(center_x - radius_main), int(center_y - radius_main), radius_main * 2, radius_main * 2)

        super().paintEvent(event)


class ScenePulseOverlay(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._pulse = 0.0
        self._anchor_x = 0.0
        self._anchor_y = 0.0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

    def set_pulse(self, value: float) -> None:
        self._pulse = max(0.0, min(1.0, float(value)))
        self.update()

    def set_anchor(self, x: float, y: float) -> None:
        self._anchor_x = float(x)
        self._anchor_y = float(y)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if self.width() <= 0 or self.height() <= 0:
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        pulse = max(0.0, min(1.0, self._pulse))
        alpha = int(10 + 20 * pulse)
        radius = max(132, int(min(self.width(), self.height()) * 0.252))

        grad = QRadialGradient(self._anchor_x, self._anchor_y, radius)
        grad.setColorAt(0.0, QColor(92, 170, 194, alpha))
        grad.setColorAt(0.36, QColor(72, 138, 160, max(0, alpha - 4)))
        grad.setColorAt(1.0, QColor(72, 138, 160, 0))
        painter.setPen(Qt.NoPen)
        painter.setBrush(grad)
        painter.drawEllipse(int(self._anchor_x - radius), int(self._anchor_y - radius), radius * 2, radius * 2)
        super().paintEvent(event)
