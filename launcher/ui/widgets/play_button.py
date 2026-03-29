from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QPushButton, QStyle, QStyleOptionButton, QWidget


class PlayButton(QPushButton):
    def __init__(self, text: str, parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setObjectName("playButton")
        self.setFocusPolicy(Qt.NoFocus)
        self._dust_texture = QPixmap()
        self._dust_opacity = 0.0

    def set_dust_texture(self, texture: QPixmap, opacity: float = 0.06) -> None:
        if texture.isNull():
            self._dust_texture = QPixmap()
            self._dust_opacity = 0.0
            self.update()
            return
        self._dust_texture = self._to_white_texture(texture)
        self._dust_opacity = max(0.0, min(1.0, opacity))
        self.update()

    @staticmethod
    def _to_white_texture(source: QPixmap) -> QPixmap:
        white = QPixmap(source.size())
        white.fill(Qt.transparent)
        painter = QPainter(white)
        painter.drawPixmap(0, 0, source)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(white.rect(), QColor(255, 255, 255))
        painter.end()
        return white

    def paintEvent(self, event) -> None:  # type: ignore[override]
        option = QStyleOptionButton()
        self.initStyleOption(option)
        text = option.text
        option.text = ""

        painter = QPainter(self)
        self.style().drawControl(QStyle.CE_PushButton, option, painter, self)

        if not self._dust_texture.isNull() and self._dust_opacity > 0.0:
            painter.save()
            painter.setOpacity(self._dust_opacity)
            inner = self.rect().adjusted(2, 2, -2, -2)
            painter.setClipRect(inner)
            painter.drawTiledPixmap(inner, self._dust_texture)
            painter.restore()

        if (
            self.objectName() == "playButton"
            and self.underMouse()
            and self.isEnabled()
            and str(self.property("playState") or "idle") == "idle"
        ):
            inner = self.rect().adjusted(4, 4, -4, -4)
            cx = inner.center().x()
            cy = inner.center().y()
            radius = max(24, int(inner.width() * 0.34))
            grad = QRadialGradient(cx, cy, radius)
            grad.setColorAt(0.0, QColor(155, 255, 205, 48))
            grad.setColorAt(0.55, QColor(135, 255, 190, 20))
            grad.setColorAt(1.0, QColor(120, 255, 180, 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(grad)
            painter.drawRoundedRect(inner, 12, 12)

        text_rect = self.style().subElementRect(QStyle.SE_PushButtonContents, option, self)
        flags = Qt.AlignCenter | Qt.TextSingleLine

        shadow_color = QColor(11, 16, 27, 180 if self.isEnabled() else 120)
        painter.setPen(shadow_color)
        painter.drawText(text_rect.translated(1, 1), flags, text)

        text_color = self.palette().buttonText().color()
        painter.setPen(text_color)
        painter.drawText(text_rect, flags, text)
