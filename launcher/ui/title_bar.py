from __future__ import annotations

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class WindowControlButton(QPushButton):
    def __init__(self, mode: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mode = mode
        self._icon_color = QColor("#d9dfeb")
        self.setCursor(Qt.ArrowCursor)

    def paintEvent(self, event: QPaintEvent) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        pen = QPen(self._icon_color)
        pen.setWidthF(1.25)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        r = self.rect()
        cx = r.center().x()
        cy = r.center().y()
        icon_half = 5

        if self._mode == "minimize":
            painter.drawLine(cx - icon_half, cy, cx + icon_half, cy)
            return

        # close
        painter.drawLine(cx - icon_half, cy - icon_half, cx + icon_half, cy + icon_half)
        painter.drawLine(cx + icon_half, cy - icon_half, cx - icon_half, cy + icon_half)


class TitleBar(QFrame):
    minimize_requested = Signal()
    close_requested = Signal()

    def __init__(self, title: str, icon: QIcon | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(38)

        self._manual_drag_active = False
        self._manual_drag_offset = QPoint()

        row = QHBoxLayout(self)
        row.setContentsMargins(10, 0, 6, 0)
        row.setSpacing(8)

        self.icon_label = QLabel()
        self.icon_label.setObjectName("titleBarIcon")
        self.icon_label.setFixedSize(18, 18)
        if icon and not icon.isNull():
            self.icon_label.setPixmap(icon.pixmap(18, 18))

        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleBarLabel")

        self.min_button = WindowControlButton("minimize")
        self.min_button.setObjectName("titleBarButton")
        self.min_button.setFixedSize(34, 26)
        self.min_button.setFocusPolicy(Qt.NoFocus)
        self.min_button.clicked.connect(self.minimize_requested.emit)

        self.close_button = WindowControlButton("close")
        self.close_button.setObjectName("titleBarCloseButton")
        self.close_button.setFixedSize(34, 26)
        self.close_button.setFocusPolicy(Qt.NoFocus)
        self.close_button.clicked.connect(self.close_requested.emit)

        row.addWidget(self.icon_label)
        row.addWidget(self.title_label)
        row.addStretch(1)
        row.addWidget(self.min_button)
        row.addWidget(self.close_button)

    def set_title(self, title: str) -> None:
        self.title_label.setText(title)

    def _is_control_hit(self, pos) -> bool:
        target = self.childAt(pos)
        while target is not None:
            if isinstance(target, QPushButton):
                return True
            target = target.parentWidget()
        return False

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and not self._is_control_hit(event.position().toPoint()):
            window = self.window()
            handle = window.windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
            if not window.isMaximized():
                self._manual_drag_active = True
                self._manual_drag_offset = event.globalPosition().toPoint() - window.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        if self._manual_drag_active and event.buttons() & Qt.LeftButton:
            window = self.window()
            if not window.isMaximized():
                window.move(event.globalPosition().toPoint() - self._manual_drag_offset)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self._manual_drag_active = False
        super().mouseReleaseEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton and not self._is_control_hit(event.position().toPoint()):
            event.accept()
            return
        super().mouseDoubleClickEvent(event)
