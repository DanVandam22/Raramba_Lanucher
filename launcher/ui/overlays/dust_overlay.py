from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget


class DustOverlay(QWidget):
    def __init__(self, texture: QPixmap, opacity: float = 0.05, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._texture = self._to_white_texture(texture)
        self._opacity = max(0.0, min(1.0, opacity))
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)

    @staticmethod
    def _to_white_texture(source: QPixmap) -> QPixmap:
        if source.isNull():
            return source
        white = QPixmap(source.size())
        white.fill(Qt.transparent)
        painter = QPainter(white)
        painter.drawPixmap(0, 0, source)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(white.rect(), QColor(255, 255, 255))
        painter.end()
        return white

    def paintEvent(self, event) -> None:  # type: ignore[override]
        if self._texture.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.setRenderHint(QPainter.Antialiasing, True)
        clip_path = QPainterPath()
        clip_path.addRoundedRect(self.rect(), 16, 16)
        painter.setClipPath(clip_path)
        painter.setOpacity(self._opacity)
        painter.drawTiledPixmap(self.rect(), self._texture)
        super().paintEvent(event)
