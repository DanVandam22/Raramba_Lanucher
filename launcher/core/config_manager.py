from __future__ import annotations

from dataclasses import dataclass, asdict, field
from pathlib import Path
import json
import os
import sys
from tempfile import NamedTemporaryFile


@dataclass(slots=True)
class LauncherConfig:
    game_dir: str = field(
        default_factory=lambda: str(
            Path(os.getenv("APPDATA", str(Path.home()))) / ".minecraft"
        )
    )
    java_path: str = ""
    memory_mb: int = 4096
    selected_profile: str = "default"
    access_token: str = ""
    player_name: str = "Player"
    player_uuid: str = ""
    refresh_token: str = ""
    token_expires_at: int = 0
    account_profile_link: str = ""
    auth_provider: str = ""
    close_after_launch: bool = False
    show_launch_logs: bool = False


class ConfigManager:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or (self._resolve_base_dir() / "config.json")
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        self._config = self._load()

    @property
    def config(self) -> LauncherConfig:
        return self._config

    def _load(self) -> LauncherConfig:
        if not self._config_path.exists():
            config = LauncherConfig()
            self._save(config)
            return config

        try:
            raw = json.loads(self._config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            # Recover from unreadable/corrupted config by recreating defaults.
            config = LauncherConfig()
            self._save(config)
            return config

        if not isinstance(raw, dict):
            config = LauncherConfig()
            self._save(config)
            return config

        # Merge with defaults to stay compatible with older/newer config schemas.
        defaults = asdict(LauncherConfig())
        merged = {**defaults, **raw}
        return LauncherConfig(**self._normalize_values(merged))

    def save(self) -> None:
        self._save(self._config)

    def _save(self, config: LauncherConfig) -> None:
        payload = json.dumps(asdict(config), ensure_ascii=False, indent=2)
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=str(self._config_path.parent),
            delete=False,
        ) as tmp:
            tmp.write(payload)
            temp_path = Path(tmp.name)
        temp_path.replace(self._config_path)

    def update(self, **kwargs: object) -> None:
        for key, value in self._normalize_values(kwargs).items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)
        self.save()

    @staticmethod
    def _resolve_base_dir() -> Path:
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            portable_dir = exe_dir / "data"
            if portable_dir.exists():
                return portable_dir
            local_app_data = Path(os.getenv("LOCALAPPDATA", str(Path.home())))
            return local_app_data / "Raramba Launcher"
        return Path.home() / ".raramba_launcher"

    @staticmethod
    def _normalize_values(values: dict[str, object]) -> dict[str, object]:
        normalized = dict(values)

        memory_value = normalized.get("memory_mb", 4096)
        if not isinstance(memory_value, int):
            try:
                memory_value = int(memory_value)
            except (TypeError, ValueError):
                memory_value = 4096
        normalized["memory_mb"] = max(1024, min(16384, memory_value))

        expires_value = normalized.get("token_expires_at", 0)
        if not isinstance(expires_value, int):
            try:
                expires_value = int(expires_value)
            except (TypeError, ValueError):
                expires_value = 0
        normalized["token_expires_at"] = max(0, expires_value)

        for key in (
            "game_dir",
            "java_path",
            "selected_profile",
            "access_token",
            "player_name",
            "player_uuid",
            "refresh_token",
            "account_profile_link",
            "auth_provider",
        ):
            if key not in normalized:
                continue
            value = normalized.get(key, "")
            normalized[key] = value if isinstance(value, str) else str(value)

        for key in ("close_after_launch", "show_launch_logs"):
            if key not in normalized:
                continue
            normalized[key] = bool(normalized[key])

        return normalized
