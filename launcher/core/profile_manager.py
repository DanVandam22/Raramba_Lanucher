from __future__ import annotations

from dataclasses import dataclass

from launcher.core.config_manager import ConfigManager


@dataclass(slots=True)
class Profile:
    id: str
    title: str
    version: str
    forge_version: str = ""


class ProfileManager:
    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager
        self._profiles: dict[str, Profile] = {
            "default": Profile(
                id="default",
                title="Основная сборка",
                version="1.20.1",
                forge_version="1.20.1-47.4.0",
            )
        }

    def get_selected(self) -> Profile:
        selected_id = self._config_manager.config.selected_profile
        return self._profiles.get(selected_id, self._profiles["default"])

    def select(self, profile_id: str) -> None:
        if profile_id in self._profiles:
            self._config_manager.update(selected_profile=profile_id)
