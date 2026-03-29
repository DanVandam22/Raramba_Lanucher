from __future__ import annotations

import subprocess
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import requests

from launcher.core.account_manager import AccountSession
from launcher.core.config_manager import LauncherConfig
from launcher.core.launcher_service import LauncherService
from launcher.core.profile_manager import Profile


class LauncherServiceTests(unittest.TestCase):
    def _make_service(
        self,
        config: LauncherConfig,
        version: str = "1.12.2",
        auth_client: object | None = None,
    ) -> LauncherService:
        def _update(**kwargs: object) -> None:
            for key, value in kwargs.items():
                setattr(config, key, value)

        config_manager = SimpleNamespace(config=config, update=_update)
        profile_manager = SimpleNamespace(get_selected=lambda: Profile("default", "Default", version))
        return LauncherService(config_manager, profile_manager, auth_client=auth_client)

    def test_launch_game_returns_error_when_java_not_found(self) -> None:
        config = LauncherConfig(game_dir=tempfile.gettempdir(), java_path="")
        service = self._make_service(config)

        with patch("launcher.core.launcher_service.JavaFinder.find", return_value=""):
            result = service.launch_game()

        self.assertFalse(result.ok)
        self.assertIn("Java", result.message)

    def test_launch_game_installs_version_and_starts_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            game_dir = Path(tmp_dir) / ".minecraft"
            java_dir = Path(tmp_dir) / "java" / "bin"
            java_dir.mkdir(parents=True)
            java_exe = java_dir / "java.exe"
            javaw_exe = java_dir / "javaw.exe"
            java_exe.write_text("", encoding="utf-8")
            javaw_exe.write_text("", encoding="utf-8")

            config = LauncherConfig(
                game_dir=str(game_dir),
                java_path=str(java_exe),
                memory_mb=4096,
                player_name="Tester",
            )
            service = self._make_service(config)
            fake_process = MagicMock(spec=subprocess.Popen)
            command = ["javaw.exe", "-jar", "minecraft.jar"]

            with (
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.install.install_minecraft_version"
                ) as install_mock,
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.command.get_minecraft_command",
                    return_value=command,
                ) as command_mock,
                patch("launcher.core.launcher_service.subprocess.Popen", return_value=fake_process) as popen_mock,
            ):
                result = service.launch_game()

            self.assertTrue(result.ok)
            install_mock.assert_called_once()
            command_mock.assert_called_once()
            command_args, _ = command_mock.call_args
            options = command_args[2]
            self.assertEqual(options["username"], "Tester")
            self.assertEqual(options["executablePath"], str(javaw_exe))
            self.assertEqual(options["jvmArguments"], ["-Xmx4096M"])
            popen_mock.assert_called_once_with(
                command,
                cwd=str(game_dir),
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

    def test_is_game_running_clears_finished_process(self) -> None:
        config = LauncherConfig(game_dir=tempfile.gettempdir())
        service = self._make_service(config)
        finished_process = MagicMock()
        finished_process.poll.return_value = 0
        service._last_process = finished_process

        self.assertFalse(service.is_game_running())
        self.assertIsNone(service._last_process)

    def test_launch_game_shows_console_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            game_dir = Path(tmp_dir) / ".minecraft"
            java_dir = Path(tmp_dir) / "java" / "bin"
            java_dir.mkdir(parents=True)
            java_exe = java_dir / "java.exe"
            javaw_exe = java_dir / "javaw.exe"
            java_exe.write_text("", encoding="utf-8")
            javaw_exe.write_text("", encoding="utf-8")

            config = LauncherConfig(
                game_dir=str(game_dir),
                java_path=str(java_exe),
                memory_mb=4096,
                player_name="Tester",
                show_launch_logs=True,
            )
            service = self._make_service(config)
            fake_process = MagicMock(spec=subprocess.Popen)
            command = ["javaw.exe", "-jar", "minecraft.jar"]

            with (
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.install.install_minecraft_version"
                ),
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.command.get_minecraft_command",
                    return_value=command,
                ),
                patch("launcher.core.launcher_service.subprocess.Popen", return_value=fake_process) as popen_mock,
            ):
                result = service.launch_game()

            self.assertTrue(result.ok)
            _, popen_kwargs = popen_mock.call_args
            self.assertEqual(popen_kwargs["cwd"], str(game_dir))
            self.assertNotIn("creationflags", popen_kwargs)

    def test_launch_game_refreshes_expired_ely_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            game_dir = Path(tmp_dir) / ".minecraft"
            java_dir = Path(tmp_dir) / "java" / "bin"
            java_dir.mkdir(parents=True)
            java_exe = java_dir / "java.exe"
            javaw_exe = java_dir / "javaw.exe"
            java_exe.write_text("", encoding="utf-8")
            javaw_exe.write_text("", encoding="utf-8")

            config = LauncherConfig(
                game_dir=str(game_dir),
                java_path=str(java_exe),
                memory_mb=4096,
                player_name="OldName",
                player_uuid="old-uuid",
                access_token="old-token",
                refresh_token="refresh-token",
                token_expires_at=int(time.time()) - 5,
                account_profile_link="https://ely.by/u/old",
            )
            refreshed_session = AccountSession(
                username="NewName",
                uuid="new-uuid",
                access_token="new-token",
                refresh_token="new-refresh",
                expires_at=int(time.time()) + 3600,
                profile_link="https://ely.by/u/new",
            )
            auth_client = MagicMock()
            auth_client.refresh_session.return_value = SimpleNamespace(
                ok=True,
                session=refreshed_session,
                message="refreshed",
            )
            service = self._make_service(config, auth_client=auth_client)
            fake_process = MagicMock(spec=subprocess.Popen)
            command = ["javaw.exe", "-jar", "minecraft.jar"]

            with (
                patch("launcher.core.launcher_service.LauncherService._resolve_authlib_injector_path", return_value="assets/authlib-injector.jar"),
                patch("launcher.core.launcher_service.minecraft_launcher_lib.install.install_minecraft_version"),
                patch("launcher.core.launcher_service.minecraft_launcher_lib.command.get_minecraft_command", return_value=command) as command_mock,
                patch("launcher.core.launcher_service.subprocess.Popen", return_value=fake_process),
            ):
                result = service.launch_game()

            self.assertTrue(result.ok)
            auth_client.refresh_session.assert_called_once()
            options = command_mock.call_args[0][2]
            self.assertEqual(options["username"], "NewName")
            self.assertEqual(options["uuid"], "new-uuid")
            self.assertEqual(options["token"], "new-token")
            self.assertEqual(config.refresh_token, "new-refresh")

    def test_launch_game_returns_readable_message_on_ssl_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            game_dir = Path(tmp_dir) / ".minecraft"
            java_dir = Path(tmp_dir) / "java" / "bin"
            java_dir.mkdir(parents=True)
            java_exe = java_dir / "java.exe"
            javaw_exe = java_dir / "javaw.exe"
            java_exe.write_text("", encoding="utf-8")
            javaw_exe.write_text("", encoding="utf-8")

            config = LauncherConfig(
                game_dir=str(game_dir),
                java_path=str(java_exe),
                memory_mb=4096,
                player_name="Tester",
            )
            service = self._make_service(config)

            with patch(
                "launcher.core.launcher_service.minecraft_launcher_lib.install.install_minecraft_version",
                side_effect=requests.exceptions.SSLError("tls eof"),
            ):
                result = service.launch_game()

            self.assertFalse(result.ok)
            self.assertIn("SSL", result.message)
            self.assertIn("tls eof", result.details)

    def test_launch_game_retries_download_after_ssl_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            game_dir = Path(tmp_dir) / ".minecraft"
            java_dir = Path(tmp_dir) / "java" / "bin"
            java_dir.mkdir(parents=True)
            java_exe = java_dir / "java.exe"
            javaw_exe = java_dir / "javaw.exe"
            java_exe.write_text("", encoding="utf-8")
            javaw_exe.write_text("", encoding="utf-8")

            config = LauncherConfig(
                game_dir=str(game_dir),
                java_path=str(java_exe),
                memory_mb=4096,
                player_name="Tester",
            )
            service = self._make_service(config)
            fake_process = MagicMock(spec=subprocess.Popen)
            command = ["javaw.exe", "-jar", "minecraft.jar"]

            with (
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.install.install_minecraft_version",
                    side_effect=[requests.exceptions.SSLError("tls eof"), None],
                ) as install_mock,
                patch(
                    "launcher.core.launcher_service.minecraft_launcher_lib.command.get_minecraft_command",
                    return_value=command,
                ),
                patch("launcher.core.launcher_service.subprocess.Popen", return_value=fake_process),
                patch("launcher.core.launcher_service.time.sleep"),
            ):
                result = service.launch_game()

            self.assertTrue(result.ok)
            self.assertEqual(install_mock.call_count, 2)


if __name__ == "__main__":
    unittest.main()
