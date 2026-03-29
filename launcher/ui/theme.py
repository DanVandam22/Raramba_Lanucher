from __future__ import annotations


def build_main_window_styles() -> str:
    return """
        * {
            font-family: Segoe UI;
            color: #f8fafc;
            font-size: 14px;
        }
        #rootWidget {
            background-color: #070b13;
        }
        #titleBar {
            background: #151a2b;
            border: none;
            border-bottom: none;
        }
        #titleBarIcon {
            background: transparent;
        }
        #titleBarLabel {
            color: #d9dfeb;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.2px;
        }
        #titleBarButton {
            background: transparent;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            min-width: 34px;
            max-width: 34px;
            min-height: 26px;
            max-height: 26px;
            padding: 0;
            color: #dbe3ff;
        }
        #titleBarButton:hover {
            background: #232a43;
        }
        #titleBarButton:focus {
            outline: none;
            border: none;
            background: transparent;
        }
        #titleBarButton:pressed {
            background: #1b2238;
        }
        #titleBarCloseButton {
            background: transparent;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            min-width: 34px;
            max-width: 34px;
            min-height: 26px;
            max-height: 26px;
            padding: 0;
            color: #e5eafc;
        }
        #titleBarCloseButton:hover {
            background: #9f3a47;
            color: #ffffff;
        }
        #titleBarCloseButton:focus {
            outline: none;
            border: none;
            background: transparent;
        }
        #titleBarCloseButton:pressed {
            background: #872f3a;
            color: #ffffff;
        }
        #centerCard {
            background: transparent;
            border: none;
        }
        #accountBlock {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(28, 19, 55, 0.72),
                stop: 1 rgba(15, 14, 35, 0.78)
            );
            border: 1px solid rgba(154, 120, 230, 0.32);
            border-radius: 12px;
        }
        #avatarFrame {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(44, 24, 82, 0.92),
                stop: 1 rgba(17, 16, 39, 0.94)
            );
            border: 1px solid rgba(167, 132, 244, 0.54);
            border-radius: 10px;
        }
        #avatarFrame:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(58, 31, 102, 0.96),
                stop: 1 rgba(22, 20, 49, 0.98)
            );
            border: 1px solid rgba(199, 168, 255, 0.8);
        }
        #avatar {
            font-size: 20px;
            min-width: 24px;
        }
        #accountName {
            font-size: 16px;
            font-weight: 800;
            color: #e8f6ff;
        }
        #accountStatus {
            font-size: 11px;
            color: #b8addc;
        }
        #cardDivider {
            background: rgba(136, 104, 212, 0.32);
        }
        #iconButton {
            background: rgba(45, 60, 100, 0.65);
            border: 1px solid rgba(129, 161, 255, 0.36);
            border-radius: 8px;
            color: #d6ddff;
            font-size: 14px;
            font-weight: 600;
            padding: 0;
        }
        #iconButton:disabled {
            background: rgba(28, 36, 58, 0.46);
            border: 1px solid rgba(108, 122, 166, 0.18);
            color: #9ca9d6;
        }
        #accountActionButton {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(74, 45, 134, 0.98),
                stop: 0.54 rgba(44, 27, 88, 0.98),
                stop: 1 rgba(23, 19, 52, 0.99)
            );
            border: 1px solid rgba(202, 169, 255, 0.5);
            border-radius: 11px;
            color: #f5ecff;
            padding: 0;
        }
        #accountActionButton:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(95, 56, 170, 0.99),
                stop: 0.56 rgba(56, 33, 108, 0.99),
                stop: 1 rgba(29, 23, 62, 0.99)
            );
            border: 1px solid rgba(226, 200, 255, 0.82);
        }
        #accountActionButton:pressed {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(42, 24, 77, 1.0),
                stop: 1 rgba(19, 16, 41, 1.0)
            );
            border: 1px solid rgba(171, 133, 244, 0.84);
            padding-top: 1px;
        }
        #accountActionButton:disabled {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(35, 26, 60, 0.74),
                stop: 1 rgba(18, 17, 35, 0.74)
            );
            border: 1px solid rgba(126, 100, 182, 0.2);
            color: rgba(218, 202, 236, 0.42);
        }
        #modButton {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(42, 26, 74, 0.98),
                stop: 0.52 rgba(22, 18, 48, 0.99),
                stop: 1 rgba(12, 11, 28, 1.0)
            );
            border: 2px solid #7d58bf;
            border-radius: 12px;
            font-family: "Roboto", "Segoe UI", "Arial", sans-serif;
            font-size: 18px;
            font-weight: 700;
            letter-spacing: 0.6px;
            min-height: 54px;
            color: #f0e7ff;
            text-align: center;
            padding: 0 12px;
        }
        #modButton:focus {
            outline: none;
            border: 2px solid #9b74e1;
        }
        #modButton:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(57, 34, 98, 0.99),
                stop: 0.52 rgba(30, 22, 62, 1.0),
                stop: 1 rgba(15, 13, 33, 1.0)
            );
            border: 2px solid #b28cff;
            color: #fbf6ff;
        }
        #modButton:pressed {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(24, 18, 49, 1.0),
                stop: 1 rgba(11, 10, 25, 1.0)
            );
            border: 2px solid #6b48aa;
            color: #ddcff3;
            padding-top: 1px;
        }
        #playButton {
            border-radius: 10px;
            font-family: "Minecraftia", "Press Start 2P", "Segoe UI";
            font-size: 25px;
            font-weight: 800;
            letter-spacing: 1.0px;
            min-height: 62px;
            color: #f2f3cc;
            padding-top: 6px;
            padding-bottom: 6px;
        }
        #playButton:focus {
            outline: none;
        }
        #playButton[playState="idle"] {
            background: rgba(40, 128, 95, 0.92);
            border: 2px solid #4ab587;
        }
        #playButton[playState="idle"]:hover {
            background: rgba(53, 154, 113, 0.95);
            border: 2px solid #63d5a2;
        }
        #playButton[playState="idle"][pressedVisual="true"] {
            background: rgba(34, 108, 80, 0.98);
            border: 2px solid #3f9d76;
            padding-top: 6px;
            padding-bottom: 6px;
        }
        #playButton[playState="loading"] {
            background: rgba(34, 108, 80, 0.96);
            border: 2px solid #449d78;
            color: #dcfce7;
        }
        #playButton[playState="running"] {
            background: rgba(34, 108, 80, 0.96);
            color: #dcfce7;
            border: 2px solid #449d78;
        }
        #hintText {
            color: #d1d5db;
            font-size: 12px;
        }
        #launchProgress {
            min-height: 20px;
            background: rgba(15, 23, 42, 0.9);
            border: 1px solid #334155;
            border-radius: 6px;
            text-align: center;
            color: #e2e8f0;
        }
        #launchProgress::chunk {
            background: #22c55e;
            border-radius: 6px;
        }
        #settingsToast {
            background: rgba(26, 18, 46, 0.96);
            border: 1px solid rgba(180, 145, 245, 0.72);
            border-radius: 11px;
            color: #f7f0ff;
            font-size: 12px;
            font-weight: 700;
            padding: 8px 14px;
        }
        #directorybutton, #settingbutton {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(20, 17, 44, 0.94),
                stop: 1 rgba(12, 12, 27, 0.96)
            );
            border: 2px solid rgba(117, 88, 188, 0.88);
            border-radius: 12px;
        }
        #settingsScrollArea, #settingsScrollContent {
            background: transparent;
        }
        #settingsScrollArea QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 6px 0 6px 0;
        }
        #settingsScrollArea QScrollBar::handle:vertical {
            background: rgba(129, 96, 194, 0.48);
            border-radius: 5px;
            min-height: 36px;
        }
        #settingsScrollArea QScrollBar::handle:vertical:hover {
            background: rgba(159, 122, 230, 0.72);
        }
        #settingsScrollArea QScrollBar::add-line:vertical,
        #settingsScrollArea QScrollBar::sub-line:vertical,
        #settingsScrollArea QScrollBar::add-page:vertical,
        #settingsScrollArea QScrollBar::sub-page:vertical {
            background: transparent;
            height: 0px;
        }
        #directorybutton QPushButton, #settingbutton QPushButton {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(42, 25, 74, 0.96),
                stop: 1 rgba(20, 17, 45, 0.98)
            );
            border: 2px solid rgba(125, 90, 201, 0.92);
            border-radius: 8px;
            color: #efe7ff;
            font-weight: 700;
            padding: 8px 12px;
        }
        #directorybutton QPushButton:hover, #settingbutton QPushButton:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(58, 33, 102, 0.98),
                stop: 1 rgba(29, 22, 62, 0.99)
            );
            border: 2px solid rgba(166, 127, 244, 0.96);
            color: #fcf7ff;
        }
        #directorybutton QPushButton:pressed, #settingbutton QPushButton:pressed {
            background: rgba(23, 17, 44, 0.98);
            border: 2px solid rgba(103, 76, 164, 0.96);
            color: #dbcdf0;
        }
        #directorybutton QPushButton:focus, #settingbutton QPushButton:focus {
            outline: none;
        }
        #panelTitle {
            font-size: 21px;
            font-weight: 800;
        }
        #modTitle {
            font-size: 26px;
            font-weight: 800;
            color: #f59e0b;
        }
        #panelText {
            color: #cbd5e1;
        }
        #settingTitle {
            font-size: 15px;
            font-weight: 700;
            color: #f0e7ff;
        }
        #settingsSectionTitle {
            font-size: 13px;
            font-weight: 700;
            color: #bda4f2;
            letter-spacing: 0.4px;
            text-transform: uppercase;
        }
        #launchOptionsSection {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(24, 19, 47, 0.84),
                stop: 1 rgba(14, 13, 31, 0.9)
            );
            border: 1px solid rgba(140, 109, 214, 0.26);
            border-radius: 12px;
        }
        #toggleRow {
            background: rgba(31, 21, 54, 0.76);
            border: 1px solid rgba(126, 95, 188, 0.24);
            border-radius: 10px;
        }
        #toggleLabel {
            color: #efe5ff;
            font-size: 12px;
            font-weight: 600;
        }
        #secondarySettingsButton {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(40, 24, 72, 0.96),
                stop: 1 rgba(20, 18, 46, 0.98)
            );
            border: 1px solid rgba(141, 108, 220, 0.58);
            border-radius: 9px;
            color: #f1e8ff;
            font-size: 12px;
            font-weight: 700;
            min-height: 34px;
            padding: 6px 10px;
        }
        #secondarySettingsButton:hover {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(58, 34, 104, 0.98),
                stop: 1 rgba(30, 23, 63, 0.99)
            );
            border: 1px solid rgba(181, 145, 252, 0.82);
            color: #fff9ff;
        }
        #secondarySettingsButton:pressed {
            background: rgba(23, 17, 45, 0.98);
            border: 1px solid rgba(111, 82, 177, 0.84);
        }
        #switchToggle {
            spacing: 0;
        }
        #switchToggle::indicator {
            width: 38px;
            height: 22px;
            border-radius: 11px;
            background: rgba(31, 24, 53, 0.96);
            border: 1px solid rgba(110, 87, 170, 0.6);
        }
        #switchToggle::indicator:unchecked {
            image: none;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(48, 34, 79, 0.96),
                stop: 1 rgba(25, 20, 44, 0.96)
            );
            border: 1px solid rgba(112, 87, 174, 0.58);
        }
        #switchToggle::indicator:checked {
            image: none;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(170, 92, 255, 0.98),
                stop: 1 rgba(110, 72, 210, 0.98)
            );
            border: 1px solid rgba(231, 192, 255, 0.88);
        }
        #settingHint {
            font-size: 11px;
            color: #aa9dcb;
        }
        #memorySection {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 0, y2: 1,
                stop: 0 rgba(31, 20, 56, 0.98),
                stop: 0.58 rgba(18, 16, 42, 0.99),
                stop: 1 rgba(12, 11, 28, 1.0)
            );
            border: 1px solid rgba(149, 113, 228, 0.46);
            border-radius: 13px;
        }
        #memorySliderShell {
            background: rgba(18, 15, 36, 0.82);
            border: 1px solid rgba(110, 86, 168, 0.26);
            border-radius: 11px;
        }
        #memoryValueBadge {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(182, 132, 255, 0.24),
                stop: 1 rgba(98, 69, 176, 0.3)
            );
            border: 1px solid rgba(198, 160, 255, 0.62);
            border-radius: 10px;
            color: #fbf4ff;
            font-size: 12px;
            font-weight: 800;
            padding: 5px 10px;
        }
        #memoryMark {
            background: rgba(27, 19, 48, 0.78);
            border: 1px solid rgba(108, 79, 166, 0.36);
            border-radius: 10px;
            color: #b4a6d5;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 0.3px;
            min-height: 22px;
            padding: 2px 8px;
        }
        #memoryMark[active="true"] {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 1,
                stop: 0 rgba(176, 116, 255, 0.32),
                stop: 1 rgba(97, 67, 176, 0.4)
            );
            border: 1px solid rgba(226, 190, 255, 0.86);
            color: #fff7ff;
        }
        #memorySectionHint {
            color: #aa9dcb;
            font-size: 10px;
            letter-spacing: 0.2px;
        }
        #settingsPrimaryButton {
            background: #6c43bb;
            border: 2px solid #9a70ef;
        }
        #settingsPrimaryButton:hover {
            background: #8457dc;
            border: 2px solid #bc92ff;
        }
        #settingsPrimaryButton:pressed {
            background: #55329b;
            border: 2px solid #8457d8;
        }
        QLineEdit {
            background: rgba(23, 18, 43, 0.92);
            border: 1px solid rgba(106, 81, 166, 0.52);
            border-radius: 8px;
            padding: 8px;
        }
        #memorySlider::groove:horizontal {
            height: 10px;
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(43, 30, 72, 0.98),
                stop: 0.5 rgba(34, 25, 58, 0.99),
                stop: 1 rgba(22, 18, 40, 0.99)
            );
            border: 1px solid rgba(117, 90, 184, 0.78);
            border-radius: 5px;
        }
        #memorySlider::sub-page:horizontal {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(210, 135, 255, 0.98),
                stop: 0.52 rgba(166, 97, 248, 0.99),
                stop: 1 rgba(108, 70, 214, 0.99)
            );
            border: 1px solid rgba(239, 195, 255, 0.42);
            border-radius: 5px;
        }
        #memorySlider::add-page:horizontal {
            background: qlineargradient(
                x1: 0, y1: 0, x2: 1, y2: 0,
                stop: 0 rgba(29, 22, 52, 0.96),
                stop: 1 rgba(18, 16, 38, 0.96)
            );
            border-radius: 5px;
        }
        #memorySlider::handle:horizontal {
            background: qradialgradient(
                cx: 0.5, cy: 0.42, radius: 1.0,
                fx: 0.48, fy: 0.34,
                stop: 0 rgba(255, 252, 255, 1.0),
                stop: 0.26 rgba(235, 214, 255, 1.0),
                stop: 0.62 rgba(193, 136, 255, 1.0),
                stop: 1 rgba(119, 74, 214, 1.0)
            );
            border: 2px solid rgba(249, 228, 255, 0.78);
            width: 20px;
            margin: -8px 0;
            border-radius: 10px;
        }
        #memorySlider::handle:horizontal:hover {
            background: qradialgradient(
                cx: 0.5, cy: 0.42, radius: 1.0,
                fx: 0.48, fy: 0.34,
                stop: 0 rgba(255, 255, 255, 1.0),
                stop: 0.28 rgba(246, 232, 255, 1.0),
                stop: 0.62 rgba(214, 160, 255, 1.0),
                stop: 1 rgba(135, 86, 232, 1.0)
            );
            border: 2px solid rgba(255, 239, 255, 0.96);
        }
        #memorySlider::handle:horizontal:pressed {
            background: qradialgradient(
                cx: 0.5, cy: 0.45, radius: 1.0,
                fx: 0.5, fy: 0.38,
                stop: 0 rgba(245, 235, 255, 1.0),
                stop: 0.45 rgba(182, 123, 255, 1.0),
                stop: 1 rgba(98, 63, 183, 1.0)
            );
            border: 2px solid rgba(239, 212, 255, 0.92);
        }
        QPushButton {
            background: #0891b2;
            border: none;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: #0ea5e9;
        }
        QPushButton:disabled {
            background: #1e293b;
            color: #64748b;
        }
        #roundButton {
            background: rgba(20, 15, 40, 0.92);
            border: 2px solid #7d59bf;
            border-radius: 10px;
            color: #f0e5ff;
            padding: 0;
        }
        #roundButton:hover {
            background: rgba(31, 21, 58, 0.96);
            border: 2px solid #a37af1;
            color: #fcf5ff;
        }
        #roundButton:pressed {
            background: rgba(16, 12, 32, 0.98);
            border: 2px solid #6b4baa;
            color: #ddcff4;
        }
        #roundButton:focus {
            outline: none;
            border: 2px solid #8d63d6;
        }
        #smallButton {
            font-size: 16px;
            padding: 0;
        }
        #ghostButton {
            background: rgba(10, 16, 36, 0.86);
        }
    """
