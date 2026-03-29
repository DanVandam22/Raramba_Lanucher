from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from launcher.core.config_manager import ConfigManager


class ConfigManagerTests(unittest.TestCase):
    def test_load_recovers_from_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            config_path.write_text("{invalid", encoding="utf-8")

            manager = ConfigManager(config_path=config_path)

            self.assertEqual(manager.config.player_name, "Player")
            saved = json.loads(config_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["player_name"], "Player")

    def test_update_normalizes_values_before_save(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = Path(tmp_dir) / "config.json"
            manager = ConfigManager(config_path=config_path)

            manager.update(
                memory_mb="999999",
                player_name=123,
                selected_profile=7,
                close_after_launch=1,
                show_launch_logs=0,
            )

            self.assertEqual(manager.config.memory_mb, 16384)
            self.assertEqual(manager.config.player_name, "123")
            self.assertEqual(manager.config.selected_profile, "7")
            self.assertTrue(manager.config.close_after_launch)
            self.assertFalse(manager.config.show_launch_logs)

    def test_resolve_base_dir_uses_portable_data_folder_for_frozen_builds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            exe_path = Path(tmp_dir) / "RarambaLauncher.exe"
            exe_path.write_text("", encoding="utf-8")
            portable_dir = Path(tmp_dir) / "data"
            portable_dir.mkdir()

            with (
                patch.object(sys, "frozen", True, create=True),
                patch.object(sys, "executable", str(exe_path)),
            ):
                resolved = ConfigManager._resolve_base_dir()

            self.assertEqual(resolved, portable_dir)


if __name__ == "__main__":
    unittest.main()
