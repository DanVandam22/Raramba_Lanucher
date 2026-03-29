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

        account_block = QFrame()
        account_block.setObjectName("accountBlock")
        acc_layout = QHBoxLayout(account_block)
        acc_layout.setContentsMargins(10, 8, 10, 10)
        acc_layout.setSpacing(8)

        avatar_frame = ClickableFrame()
        avatar_frame.setObjectName("avatarFrame")
        avatar_frame.setAttribute(Qt.WA_StyledBackground, True)
        avatar_frame.setFixedSize(56, 56)
        avatar_frame.setCursor(Qt.PointingHandCursor)
        avatar_layout = QVBoxLayout(avatar_frame)
        avatar_layout.setContentsMargins(4, 4, 4, 4)
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
        self.account_action_button = QPushButton(texts.add_account_icon)
        self.account_avatar_frame = avatar_frame
        self.account_action_button.setObjectName("accountActionButton")
        self.account_action_button.setCursor(Qt.PointingHandCursor)
        self.account_action_button.setFocusPolicy(Qt.NoFocus)
        self.account_action_button.setFixedSize(38, 38)
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
