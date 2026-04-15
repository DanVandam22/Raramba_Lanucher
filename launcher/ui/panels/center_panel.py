from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
)

from launcher.ui.localization import UIStrings
from launcher.ui.overlays import BottomPulseOverlay, DustOverlay
from launcher.ui.widgets import PlayButton


class ClickableFrame(QFrame):
    clicked = Signal()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class AvatarFrame(ClickableFrame):
    def __init__(self, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        hovered = self.underMouse()
        rect = self.rect().adjusted(1, 1, -1, -1)
        fill_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if hovered:
            fill_gradient.setColorAt(0.0, QColor(72, 39, 128, 250))
            fill_gradient.setColorAt(1.0, QColor(26, 23, 57, 252))
            border_color = QColor(231, 204, 255, 240)
        else:
            fill_gradient.setColorAt(0.0, QColor(56, 30, 102, 245))
            fill_gradient.setColorAt(1.0, QColor(20, 18, 45, 250))
            border_color = QColor(196, 164, 255, 189)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(rect, 12, 12)

        inner_rect = rect.adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(248, 240, 255, 24 if hovered else 18), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(inner_rect, 11, 11)

        super().paintEvent(event)


class AccountActionButton(QPushButton):
    def __init__(self, text: str, parent: QFrame | None = None) -> None:
        super().__init__(text, parent)
        self.setAttribute(Qt.WA_Hover, True)

    def enterEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # type: ignore[override]
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        super().mousePressEvent(event)
        self.update()

    def mouseReleaseEvent(self, event) -> None:  # type: ignore[override]
        super().mouseReleaseEvent(event)
        self.update()

    def changeEvent(self, event) -> None:  # type: ignore[override]
        super().changeEvent(event)
        self.update()

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        fill_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())

        if not self.isEnabled():
            fill_gradient.setColorAt(0.0, QColor(35, 26, 60, 189))
            fill_gradient.setColorAt(1.0, QColor(18, 17, 35, 189))
            border_color = QColor(126, 100, 182, 61)
            text_color = QColor(218, 202, 236, 107)
        elif self.isDown():
            fill_gradient.setColorAt(0.0, QColor(54, 31, 97, 255))
            fill_gradient.setColorAt(1.0, QColor(22, 18, 46, 255))
            border_color = QColor(183, 145, 248, 224)
            text_color = QColor(245, 236, 255)
        elif self.underMouse():
            fill_gradient.setColorAt(0.0, QColor(114, 68, 194, 255))
            fill_gradient.setColorAt(0.56, QColor(66, 39, 126, 255))
            fill_gradient.setColorAt(1.0, QColor(31, 25, 66, 255))
            border_color = QColor(239, 220, 255, 245)
            text_color = QColor(245, 236, 255)
        else:
            fill_gradient.setColorAt(0.0, QColor(92, 56, 160, 252))
            fill_gradient.setColorAt(0.54, QColor(52, 31, 103, 252))
            fill_gradient.setColorAt(1.0, QColor(25, 21, 57, 255))
            border_color = QColor(222, 193, 255, 189)
            text_color = QColor(245, 236, 255)

        painter.setPen(QPen(border_color, 2))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(rect, 12, 12)

        inner_rect = rect.adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(250, 244, 255, 18), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(inner_rect, 11, 11)

        content_rect = rect.adjusted(4, 4, -4, -4)
        if not self.icon().isNull():
            icon_size = self.iconSize()
            pixmap = self.icon().pixmap(icon_size)
            x = int(content_rect.center().x() - pixmap.width() / 2)
            y = int(content_rect.center().y() - pixmap.height() / 2)
            painter.drawPixmap(x, y, pixmap)
        elif self.text():
            painter.setPen(text_color)
            painter.drawText(content_rect, Qt.AlignCenter, self.text())

class AccountBlock(QFrame):
    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        rect = self.rect().adjusted(1, 1, -1, -1)
        fill_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill_gradient.setColorAt(0.0, QColor(34, 23, 66, 210))
        fill_gradient.setColorAt(0.52, QColor(20, 18, 43, 224))
        fill_gradient.setColorAt(1.0, QColor(13, 13, 32, 235))

        painter.setPen(QPen(QColor(177, 142, 248, 153), 2))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(rect, 14, 14)

        inner_rect = rect.adjusted(1, 1, -1, -1)
        painter.setPen(QPen(QColor(245, 233, 255, 32), 1))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(inner_rect, 13, 13)

        super().paintEvent(event)


class CenterPanel(QFrame):
    mod_requested = Signal()
    play_requested = Signal()
    add_account_requested = Signal()
    account_settings_requested = Signal()

    def __init__(self, texts: UIStrings, dust_path: Path, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.texts = texts
        self.setObjectName("centerCard")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedWidth(440)

        self.dust_overlay: DustOverlay | None = None
        if dust_path.exists():
            dust_texture = QPixmap(str(dust_path))
            if not dust_texture.isNull():
                self.dust_overlay = DustOverlay(dust_texture, opacity=0.035, parent=self)
                self.dust_overlay.setGeometry(self.rect())
                self.dust_overlay.lower()

        self.bottom_pulse_overlay: BottomPulseOverlay | None = BottomPulseOverlay(self)
        self.bottom_pulse_overlay.setGeometry(self.rect())
        self.bottom_pulse_overlay.lower()
        if self.dust_overlay is not None:
            self.dust_overlay.raise_()

        box = QVBoxLayout(self)
        box.setContentsMargins(24, 20, 24, 24)
        box.setSpacing(0)

        account_block = AccountBlock()
        account_block.setObjectName("accountBlock")
        acc_layout = QHBoxLayout(account_block)
        acc_layout.setContentsMargins(12, 10, 12, 10)
        acc_layout.setSpacing(10)

        avatar_frame = AvatarFrame()
        avatar_frame.setObjectName("avatarFrame")
        avatar_frame.setFixedSize(60, 60)
        avatar_frame.setCursor(Qt.PointingHandCursor)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(5, 5, 5, 5)
        avatar_layout.setSpacing(0)
        self.avatar_label = QLabel(texts.avatar_icon)
        self.avatar_label.setObjectName("avatar")
        self.avatar_label.setAlignment(Qt.AlignCenter)
        avatar_layout.addWidget(self.avatar_label)

        acc_texts = QVBoxLayout()
        acc_texts.setSpacing(2)
        self.account_name_label = QLabel("Player")
        self.account_name_label.setObjectName("accountName")
        self.account_status_label = QLabel(texts.account_status_local)
        self.account_status_label.setObjectName("accountStatus")
        self.account_status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        acc_texts.addWidget(self.account_name_label)
        acc_texts.addWidget(self.account_status_label)

        acc_buttons = QHBoxLayout()
        acc_buttons.setSpacing(6)
        self.account_action_button = AccountActionButton(texts.add_account_icon)
        self.account_avatar_frame = avatar_frame
        self.account_action_button.setObjectName("accountActionButton")
        self.account_action_button.setCursor(Qt.PointingHandCursor)
        self.account_action_button.setFocusPolicy(Qt.NoFocus)
        self.account_action_button.setFixedSize(40, 40)
        acc_buttons.addWidget(self.account_action_button)
        self.account_action_button.clicked.connect(self.add_account_requested.emit)
        self.account_avatar_frame.clicked.connect(self.account_settings_requested.emit)

        acc_layout.addWidget(avatar_frame, alignment=Qt.AlignTop | Qt.AlignLeft)
        acc_layout.addLayout(acc_texts, 1)
        acc_layout.addLayout(acc_buttons)

        divider = QFrame()
        divider.setObjectName("cardDivider")
        divider.setFixedHeight(1)

        self.mod_button = QPushButton(texts.mod_title)
        self.mod_button.setObjectName("modButton")
        self.mod_button.setFocusPolicy(Qt.NoFocus)
        self.mod_button.clicked.connect(self.mod_requested.emit)

        self.play_button = PlayButton(texts.play_button_idle)
        self.play_button.setFixedHeight(62)
        self.play_button.clicked.connect(self.play_requested.emit)
        if dust_path.exists():
            dust_texture = QPixmap(str(dust_path))
            if not dust_texture.isNull():
                self.play_button.set_dust_texture(dust_texture, opacity=0.10)

        self.launch_progress = QProgressBar()
        self.launch_progress.setObjectName("launchProgress")
        self.launch_progress.setMinimum(0)
        self.launch_progress.setMaximum(100)
        self.launch_progress.setValue(0)
        self.launch_progress.setTextVisible(True)
        self.launch_progress.setFixedWidth(440)
        self.launch_progress.setFixedHeight(20)
        self.launch_progress.hide()

        box.addWidget(account_block)
        box.addSpacing(14)
        box.addWidget(divider)
        box.addSpacing(14)
        box.addWidget(self.mod_button)
        box.addSpacing(10)
        box.addWidget(self.play_button)

    def paintEvent(self, event) -> None:  # type: ignore[override]
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        outer_glow_rect = self.rect().adjusted(3, 3, -3, -3)
        middle_glow_rect = self.rect().adjusted(2, 2, -2, -2)
        rect = self.rect().adjusted(1, 1, -1, -1)
        fill_gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        fill_gradient.setColorAt(0.0, QColor(14, 12, 32, 242))
        fill_gradient.setColorAt(0.5, QColor(10, 11, 26, 245))
        fill_gradient.setColorAt(1.0, QColor(7, 9, 19, 250))

        painter.setPen(QPen(QColor(176, 126, 255, 26), 6))
        painter.setBrush(Qt.NoBrush)
        painter.drawRoundedRect(outer_glow_rect, 18, 18)

        painter.setPen(QPen(QColor(149, 105, 236, 42), 3))
        painter.drawRoundedRect(middle_glow_rect, 17, 17)

        painter.setPen(QPen(QColor(148, 108, 232, 196), 2))
        painter.setBrush(fill_gradient)
        painter.drawRoundedRect(rect, 16, 16)

        super().paintEvent(event)
