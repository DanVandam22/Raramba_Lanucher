from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import ssl
import subprocess
import sys
import time
from typing import Callable
import uuid

import minecraft_launcher_lib
import minecraft_launcher_lib.forge
import requests
import urllib3

from launcher.core.account_manager import AccountSession
from launcher.core.config_manager import ConfigManager
from launcher.core.ely_auth import ElyAuthClient
from launcher.core.java_finder import JavaFinder
from launcher.core.profile_manager import ProfileManager


@dataclass(slots=True)
class LaunchResult:
    ok: bool
    message: str
    details: str = ""


class LauncherService:
    DOWNLOAD_RETRY_ATTEMPTS = 3
    DOWNLOAD_RETRY_DELAY_SECONDS = 1.5

    def __init__(
        self,
        config_manager: ConfigManager,
        profile_manager: ProfileManager,
        auth_client: ElyAuthClient | None = None,
    ) -> None:
        self._config_manager = config_manager
        self._profile_manager = profile_manager
        self._auth_client = auth_client or ElyAuthClient()
        self._last_process: subprocess.Popen | None = None

    @staticmethod
    def _is_download_error(exc: BaseException) -> bool:
        return isinstance(
            exc,
            (
                requests.exceptions.RequestException,
                urllib3.exceptions.HTTPError,
                ssl.SSLError,
                ConnectionError,
                TimeoutError,
            ),
        )

    def launch_game(
        self,
        progress_callback: Callable[[int], None] | None = None,
        max_callback: Callable[[int], None] | None = None,
        status_callback: Callable[[str], None] | None = None,
    ) -> LaunchResult:
        if self.is_game_running():
            return LaunchResult(ok=False, message="Игра уже запущена.")

        config = self._config_manager.config
        profile = self._profile_manager.get_selected()
        version = profile.version or "1.20.1"
        forge_version = getattr(profile, "forge_version", "").strip()

        java_path = self._resolve_java_path(
            JavaFinder.find(config.java_path.strip(), self._config_manager.base_dir)
        )
        if not java_path:
            return LaunchResult(
                ok=False,
                message="Java не найдена. Укажите путь в настройках.",
                details=(
                    "Лаунчер не смог найти исполняемый файл Java.\n"
                    "Проверьте путь к Java в настройках или установите подходящую версию."
                ),
            )

        game_dir = Path(config.game_dir).expanduser().resolve()
        game_dir.mkdir(parents=True, exist_ok=True)

        def _set_progress(value: int) -> None:
            if progress_callback is not None:
                progress_callback(max(0, value))

        def _set_max(value: int) -> None:
            if max_callback is not None:
                max_callback(max(1, value))

        def _set_status(text: str) -> None:
            if status_callback is not None and text:
                status_callback(self._format_launch_status(text, version))

        try:
            if config.access_token:
                refresh_result = self._refresh_ely_session_if_needed()
                if refresh_result is not None:
                    return refresh_result
                config = self._config_manager.config

            _set_status(f"Подготовка Minecraft {version}...")
            callback_dict = {
                "setStatus": _set_status,
                "setProgress": _set_progress,
                "setMax": _set_max,
            }
            launch_version = version
            if forge_version:
                self._install_forge_with_retries(
                    forge_version,
                    game_dir,
                    callback_dict,
                    java_path=java_path,
                    status_callback=_set_status,
                )
                launch_version = self._resolve_installed_forge_version_id(game_dir, forge_version)
            else:
                self._install_version_with_retries(
                    version,
                    game_dir,
                    callback_dict,
                    status_callback=_set_status,
                )

            player_name = (config.player_name or "").strip() or "Player"
            memory_mb = max(1024, min(16384, int(config.memory_mb)))
            player_uuid = (config.player_uuid or "").strip() or str(uuid.uuid4())
            access_token = config.access_token or ""
            jvm_arguments = [f"-Xmx{memory_mb}M"]
            injector_path = self._resolve_authlib_injector_path()

            if access_token:
                if not injector_path:
                    return LaunchResult(
                        ok=False,
                        message="Для Ely.by требуется authlib-injector.jar.",
                        details=(
                            "Файл authlib-injector.jar не найден.\n"
                            "Положите его в папку assets рядом с лаунчером."
                        ),
                    )
                jvm_arguments.insert(0, f"-javaagent:{injector_path}=ely.by")

            options: dict[str, object] = {
                "username": player_name,
                "uuid": player_uuid,
                "token": access_token,
                "jvmArguments": jvm_arguments,
                "executablePath": java_path,
            }
            _set_status("Запуск клиента...")
            command = minecraft_launcher_lib.command.get_minecraft_command(
                launch_version,
                str(game_dir),
                options,
            )
            popen_kwargs: dict[str, object] = {"cwd": str(game_dir)}
            if os.name == "nt" and not config.show_launch_logs:
                popen_kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
            self._last_process = subprocess.Popen(command, **popen_kwargs)
            return LaunchResult(ok=True, message=f"Minecraft {launch_version} запущен.")
        except (requests.exceptions.SSLError, urllib3.exceptions.SSLError, ssl.SSLError) as exc:
            return LaunchResult(
                ok=False,
                message="Не удалось скачать файлы Minecraft из-за SSL/TLS ошибки.",
                details=(
                    "Во время скачивания зависимостей Minecraft возникла ошибка защищённого соединения.\n"
                    "Обычно это связано с нестабильной сетью, антивирусом, прокси/VPN или проблемой сертификатов.\n\n"
                    f"Версия: {version}\n"
                    f"Папка игры: {game_dir}\n"
                    f"Подробности: {exc}"
                ),
            )
        except (requests.exceptions.RequestException, urllib3.exceptions.HTTPError, ConnectionError, TimeoutError) as exc:
            return LaunchResult(
                ok=False,
                message="Не удалось скачать файлы Minecraft из сети.",
                details=(
                    "Во время скачивания зависимостей Minecraft произошла сетевая ошибка.\n"
                    "Проверьте подключение к интернету, VPN/прокси\n\n"
                    f"Версия: {version}\n"
                    f"Папка игры: {game_dir}\n"
                    f"Подробности: {exc}"
                ),
            )
        except Exception as exc:
            return LaunchResult(
                ok=False,
                message="Ошибка запуска Minecraft.",
                details=(
                    f"Версия: {version}\n"
                    f"Папка игры: {game_dir}\n"
                    f"Java: {java_path or 'не найдено'}\n"
                    f"Тип ошибки: {type(exc).__name__}\n"
                    f"Подробности: {exc}"
                ),
            )

    def is_game_running(self) -> bool:
        if self._last_process is None:
            return False
        if self._last_process.poll() is None:
            return True
        self._last_process = None
        return False

    def get_logs_dir(self) -> Path:
        return Path(self._config_manager.config.game_dir).expanduser().resolve() / "logs"

    @staticmethod
    def _format_launch_status(text: str, version: str) -> str:
        normalized = " ".join((text or "").replace("_", " ").split()).strip()
        if not normalized:
            return f"Подготавливаем Minecraft {version}..."

        lower_text = normalized.lower()
        replacements: list[tuple[tuple[str, ...], str]] = [
            (("preparing", "prepare", "checking"), f"Подготавливаем Minecraft {version}..."),
            (("downloading assets", "assets"), "Загружаем ресурсы игры..."),
            (("downloading libraries", "libraries"), "Загружаем библиотеки Minecraft..."),
            (("downloading client", "client.jar", "jar"), "Загружаем файлы клиента..."),
            (("downloading", "download"), "Скачиваем файлы игры..."),
            (("extracting natives", "natives"), "Подготавливаем системные компоненты..."),
            (("extracting", "extract"), "Распаковываем игровые файлы..."),
            (("logging in", "authenticating"), "Проверяем данные аккаунта..."),
            (("installing forge", "forge"), "Устанавливаем компоненты сборки..."),
            (("finalizing", "verifying", "patching"), "Проверяем и завершаем установку..."),
            (("launching", "starting"), "Запускаем игру..."),
        ]
        for keywords, message in replacements:
            if any(keyword in lower_text for keyword in keywords):
                return message
        return f"Подготавливаем игру: {normalized}..."

    def _install_version_with_retries(
        self,
        version: str,
        game_dir: Path,
        callback: dict[str, Callable[..., None]],
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        last_error: BaseException | None = None
        for attempt in range(1, self.DOWNLOAD_RETRY_ATTEMPTS + 1):
            try:
                minecraft_launcher_lib.install.install_minecraft_version(
                    version,
                    str(game_dir),
                    callback=callback,
                )
                return
            except Exception as exc:
                if not self._is_download_error(exc):
                    raise
                last_error = exc
                if attempt >= self.DOWNLOAD_RETRY_ATTEMPTS:
                    raise
                if status_callback is not None:
                    status_callback(
                        f"Соединение прервалось. Повторяем загрузку ({attempt + 1}/{self.DOWNLOAD_RETRY_ATTEMPTS})..."
                    )
                time.sleep(self.DOWNLOAD_RETRY_DELAY_SECONDS * attempt)

        if last_error is not None:
            raise last_error

    def _install_forge_with_retries(
        self,
        forge_version: str,
        game_dir: Path,
        callback: dict[str, Callable[..., None]],
        java_path: str,
        status_callback: Callable[[str], None] | None = None,
    ) -> None:
        last_error: BaseException | None = None
        for attempt in range(1, self.DOWNLOAD_RETRY_ATTEMPTS + 1):
            try:
                minecraft_launcher_lib.forge.install_forge_version(
                    forge_version,
                    str(game_dir),
                    callback=callback,
                    java=java_path,
                )
                return
            except Exception as exc:
                if not self._is_download_error(exc):
                    raise
                last_error = exc
                if attempt >= self.DOWNLOAD_RETRY_ATTEMPTS:
                    raise
                if status_callback is not None:
                    status_callback(
                        f"Соединение прервалось. Повторяем установку Forge ({attempt + 1}/{self.DOWNLOAD_RETRY_ATTEMPTS})..."
                    )
                time.sleep(self.DOWNLOAD_RETRY_DELAY_SECONDS * attempt)

        if last_error is not None:
            raise last_error

    @staticmethod
    def _resolve_installed_forge_version_id(game_dir: Path, forge_version: str) -> str:
        versions_dir = game_dir / "versions"
        if not versions_dir.exists():
            return forge_version

        direct_json = versions_dir / forge_version / f"{forge_version}.json"
        if direct_json.exists():
            return forge_version

        suffix = forge_version.split("-", 1)[-1]
        candidates: list[str] = []
        for child in versions_dir.iterdir():
            if not child.is_dir():
                continue
            version_id = child.name
            version_json = child / f"{version_id}.json"
            if not version_json.exists():
                continue
            if version_id == forge_version or forge_version in version_id or suffix in version_id:
                candidates.append(version_id)

        if candidates:
            return max(candidates, key=len)
        return forge_version

    def _refresh_ely_session_if_needed(self) -> LaunchResult | None:
        config = self._config_manager.config
        if not config.access_token or not config.refresh_token:
            return None
        if config.token_expires_at and time.time() < (config.token_expires_at - 90):
            return None

        current_session = AccountSession(
            username=(config.player_name or "").strip() or "Player",
            uuid=(config.player_uuid or "").strip(),
            access_token=config.access_token,
            refresh_token=config.refresh_token,
            expires_at=config.token_expires_at,
            profile_link=config.account_profile_link,
        )
        refresh_result = self._auth_client.refresh_session(current_session)
        if not refresh_result.ok or refresh_result.session is None:
            return LaunchResult(
                ok=False,
                message="Не удалось обновить сессию Ely.by.",
                details=refresh_result.message,
            )

        session = refresh_result.session
        self._config_manager.update(
            player_name=session.username,
            player_uuid=session.uuid,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_expires_at=session.expires_at,
            account_profile_link=session.profile_link,
            auth_provider="ely.by",
        )
        return None

    @staticmethod
    def _resolve_java_path(java_path: str) -> str:
        if not java_path:
            return ""
        path = Path(java_path)
        if not path.exists():
            return ""
        lower_name = path.name.lower()
        if lower_name in {"java", "java.exe"}:
            javaw_path = path.with_name("javaw.exe")
            if javaw_path.exists():
                return str(javaw_path)
        return str(path)

    @staticmethod
    def _resolve_authlib_injector_path() -> str:
        search_dirs: list[Path] = []
        if getattr(sys, "frozen", False):
            exe_base = Path(sys.executable).resolve().parent
            search_dirs.append(exe_base / "assets")
            if hasattr(sys, "_MEIPASS"):
                search_dirs.append(Path(getattr(sys, "_MEIPASS")) / "assets")
        search_dirs.append(Path(__file__).resolve().parents[2] / "assets")

        for search_dir in search_dirs:
            direct_path = search_dir / "authlib-injector.jar"
            if direct_path.exists():
                return str(direct_path)

            versioned_matches = sorted(search_dir.glob("authlib-injector*.jar"))
            if versioned_matches:
                return str(versioned_matches[0])
        return ""
