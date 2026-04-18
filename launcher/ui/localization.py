from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True, slots=True)
class UIStrings:
    app_name: str
    mod_title: str
    mod_description: str
    settings_title: str
    memory_label: str
    game_dir_label: str
    game_dir_hint: str
    launch_options_title: str
    close_after_launch_label: str
    show_launch_logs_label: str
    open_logs_button: str
    open_game_folder_button: str
    launch_error_help: str
    memory_section_hint: str
    save_button: str
    close_button: str
    play_button_idle: str
    play_button_loading: str
    play_button_running: str
    launch_progress_preparing: str
    browse_game_dir_title: str
    settings_saved_title: str
    settings_saved_message: str
    launch_error_title: str
    account_status_local: str
    account_status_connected: str
    account_status_authorizing: str
    account_auth_error_title: str
    account_logged_out_message: str
    memory_value_format: str
    add_account_icon: str
    avatar_icon: str


_RU_STRINGS = UIStrings(
    app_name="Raramba Launcher",
    mod_title="Lost on the Island",
    mod_description="Скоро...",
    settings_title="Настройки",
    memory_label="Выделение ОЗУ",
    game_dir_label="Папка игры",
    game_dir_hint="Если путь пустой, используется %APPDATA%\\.minecraft",
    launch_options_title="Параметры запуска",
    close_after_launch_label="Закрывать после старта",
    show_launch_logs_label="Показывать консоль/логи",
    open_logs_button="Открыть папку логов",
    open_game_folder_button="Открыть папку игры",
    launch_error_help="Проверьте подробности, затем при необходимости откройте папку логов или папку игры.",
    memory_section_hint="Выберите объём памяти",
    save_button="Сохранить",
    close_button="Закрыть",
    play_button_idle="ИГРАТЬ",
    play_button_loading="Загрузка",
    play_button_running="Запущено",
    launch_progress_preparing="Подготовка запуска...",
    browse_game_dir_title="Выберите папку игры",
    settings_saved_title="Настройки",
    settings_saved_message="Настройки сохранены.",
    launch_error_title="Ошибка запуска",
    account_status_local="Аккаунты: временно локальный режим",
    account_status_connected="Ely.by аккаунт подключён",
    account_status_authorizing="Ожидание авторизации Ely.by...",
    account_auth_error_title="Ошибка авторизации",
    account_logged_out_message="Аккаунт отключён.",
    memory_value_format="{gb} ({mb} MB)",
    add_account_icon="👤+",
    avatar_icon="👤",
)


def get_ui_strings(locale: str = "ru") -> UIStrings:
    if locale.lower().startswith("ru"):
        return replace(_RU_STRINGS, play_button_idle="Играть")
    return replace(_RU_STRINGS, play_button_idle="Играть")
