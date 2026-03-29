from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QLabel, QPushButton, QVBoxLayout

from launcher.ui.localization import UIStrings


class LeftPanel(QFrame):
    close_requested = Signal()

    def __init__(self, texts: UIStrings, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("directorybutton")
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)

        box = QVBoxLayout(self)
        box.setContentsMargins(22, 22, 22, 22)
        box.setSpacing(14)

        self.mod_title_label = QLabel(texts.mod_title)
        self.mod_title_label.setObjectName("modTitle")

        self.mod_desc_label = QLabel(texts.mod_description)
        self.mod_desc_label.setWordWrap(True)
        self.mod_desc_label.setObjectName("panelText")

        close_btn = QPushButton(texts.close_button)
        close_btn.setObjectName("ghostButton")
        close_btn.clicked.connect(self.close_requested.emit)

        box.addWidget(self.mod_title_label)
        box.addWidget(self.mod_desc_label)
        box.addStretch(1)
        box.addWidget(close_btn, alignment=Qt.AlignRight)
