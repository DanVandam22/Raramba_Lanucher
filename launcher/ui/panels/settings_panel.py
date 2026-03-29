from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QWheelEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from launcher.ui.localization import UIStrings


class MemorySlider(QSlider):
    def wheelEvent(self, event: QWheelEvent) -> None:  # type: ignore[override]
        event.ignore()


class SettingsPanel(QFrame):
    browse_requested = Signal()
    save_requested = Signal()
    close_requested = Signal()
    open_logs_requested = Signal()

    def __init__(self, texts: UIStrings, memory_presets_mb: tuple[int, ...], game_dir_placeholder: str, parent: QFrame | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("settingbutton")
        self.setMaximumWidth(0)
        self.setMinimumWidth(0)
        self.setMaximumHeight(548)
        self.setMinimumHeight(0)

        box = QVBoxLayout(self)
        box.setContentsMargins(0, 0, 0, 0)
        box.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName("settingsScrollArea")
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        content = QWidget()
        content.setObjectName("settingsScrollContent")
        self.scroll_area.setWidget(content)

        content_box = QVBoxLayout(content)
        content_box.setContentsMargins(18, 18, 12, 18)
        content_box.setSpacing(10)

        title = QLabel(texts.settings_title)
        title.setObjectName("panelTitle")

        memory_section = QFrame()
        memory_section.setObjectName("memorySection")
        memory_box = QVBoxLayout(memory_section)
        memory_box.setContentsMargins(12, 10, 12, 12)
        memory_box.setSpacing(8)

        memory_head = QHBoxLayout()
        memory_head.setContentsMargins(0, 0, 0, 0)
        memory_head.setSpacing(8)

        mem_label = QLabel(texts.memory_label)
        mem_label.setObjectName("settingTitle")

        self.memory_value_label = QLabel("")
        self.memory_value_label.setObjectName("memoryValueBadge")
        self.memory_value_label.setAlignment(Qt.AlignCenter)
        self.memory_value_label.setMinimumWidth(96)

        memory_head.addWidget(mem_label)
        memory_head.addStretch(1)
        memory_head.addWidget(self.memory_value_label)

        self.memory_slider = MemorySlider(Qt.Horizontal)
        self.memory_slider.setObjectName("memorySlider")
        self.memory_slider.setRange(0, len(memory_presets_mb) - 1)
        self.memory_slider.setSingleStep(1)
        self.memory_slider.setPageStep(1)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(1)

        slider_shell = QFrame()
        slider_shell.setObjectName("memorySliderShell")
        slider_shell_layout = QVBoxLayout(slider_shell)
        slider_shell_layout.setContentsMargins(6, 6, 6, 3)
        slider_shell_layout.setSpacing(8)
        slider_shell_layout.addWidget(self.memory_slider)

        memory_marks_row = QHBoxLayout()
        memory_marks_row.setContentsMargins(2, 0, 2, 0)
        memory_marks_row.setSpacing(8)
        self.memory_mark_labels: list[QLabel] = []
        for index, memory_mb in enumerate(memory_presets_mb):
            mark = QLabel(f"{memory_mb // 1024} GB")
            mark.setObjectName("memoryMark")
            mark.setAlignment(Qt.AlignCenter)
            mark.setProperty("active", index == 0)
            align = Qt.AlignCenter
            if index == 0:
                align = Qt.AlignLeft
            elif index == len(memory_presets_mb) - 1:
                align = Qt.AlignRight
            memory_marks_row.addWidget(mark, 1, align)
            self.memory_mark_labels.append(mark)

        slider_shell_layout.addLayout(memory_marks_row)

        memory_hint = QLabel(texts.memory_section_hint)
        memory_hint.setObjectName("memorySectionHint")
        memory_hint.setWordWrap(True)

        memory_box.addLayout(memory_head)
        memory_box.addWidget(slider_shell)
        memory_box.addWidget(memory_hint)

        game_dir_label = QLabel(texts.game_dir_label)
        game_dir_label.setObjectName("settingTitle")

        game_dir_row = QHBoxLayout()
        self.game_dir_input = QLineEdit()
        self.game_dir_input.setPlaceholderText(game_dir_placeholder)
        browse_btn = QPushButton("...")
        browse_btn.setObjectName("smallButton")
        browse_btn.setFixedWidth(44)
        browse_btn.clicked.connect(self.browse_requested.emit)
        game_dir_row.addWidget(self.game_dir_input, 1)
        game_dir_row.addWidget(browse_btn)

        hint = QLabel(texts.game_dir_hint)
        hint.setObjectName("settingHint")
        hint.setWordWrap(True)

        launch_title = QLabel(texts.launch_options_title)
        launch_title.setObjectName("settingsSectionTitle")

        launch_section = QFrame()
        launch_section.setObjectName("launchOptionsSection")
        launch_box = QVBoxLayout(launch_section)
        launch_box.setContentsMargins(10, 10, 10, 10)
        launch_box.setSpacing(8)

        close_row = QFrame()
        close_row.setObjectName("toggleRow")
        close_row_layout = QHBoxLayout(close_row)
        close_row_layout.setContentsMargins(10, 8, 10, 8)
        close_row_layout.setSpacing(10)
        close_label = QLabel(texts.close_after_launch_label)
        close_label.setObjectName("toggleLabel")
        close_label.setWordWrap(True)
        self.close_after_launch_checkbox = QCheckBox()
        self.close_after_launch_checkbox.setObjectName("switchToggle")
        close_row_layout.addWidget(close_label, 1)
        close_row_layout.addWidget(self.close_after_launch_checkbox, 0, Qt.AlignRight | Qt.AlignVCenter)

        logs_row = QFrame()
        logs_row.setObjectName("toggleRow")
        logs_row_layout = QHBoxLayout(logs_row)
        logs_row_layout.setContentsMargins(10, 8, 10, 8)
        logs_row_layout.setSpacing(10)
        logs_label = QLabel(texts.show_launch_logs_label)
        logs_label.setObjectName("toggleLabel")
        logs_label.setWordWrap(True)
        self.show_launch_logs_checkbox = QCheckBox()
        self.show_launch_logs_checkbox.setObjectName("switchToggle")
        logs_row_layout.addWidget(logs_label, 1)
        logs_row_layout.addWidget(self.show_launch_logs_checkbox, 0, Qt.AlignRight | Qt.AlignVCenter)

        self.open_logs_button = QPushButton(texts.open_logs_button)
        self.open_logs_button.setObjectName("secondarySettingsButton")
        self.open_logs_button.clicked.connect(self.open_logs_requested.emit)

        launch_box.addWidget(close_row)
        launch_box.addWidget(logs_row)
        launch_box.addWidget(self.open_logs_button)

        controls = QHBoxLayout()
        save_btn = QPushButton(texts.save_button)
        save_btn.setObjectName("settingsPrimaryButton")
        save_btn.clicked.connect(self.save_requested.emit)

        close_btn = QPushButton(texts.close_button)
        close_btn.setObjectName("ghostButton")
        close_btn.clicked.connect(self.close_requested.emit)

        controls.addWidget(save_btn)
        controls.addWidget(close_btn)

        content_box.addWidget(title)
        content_box.addSpacing(1)
        content_box.addWidget(memory_section)
        content_box.addSpacing(5)
        content_box.addWidget(game_dir_label)
        content_box.addLayout(game_dir_row)
        content_box.addWidget(hint)
        content_box.addWidget(launch_title)
        content_box.addWidget(launch_section)
        content_box.addStretch(1)
        content_box.addLayout(controls)

        box.addWidget(self.scroll_area)
