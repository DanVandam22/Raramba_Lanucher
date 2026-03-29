from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote
import re

from launcher.core.config_manager import ConfigManager


@dataclass(slots=True)
class AccountSession:
    username: str
    uuid: str
    access_token: str
    refresh_token: str
    expires_at: int
    profile_link: str

    @property
    def skin_url(self) -> str:
        return f"https://skinsystem.ely.by/skins/{quote(self.username)}.png"


class AccountManager:
    def __init__(self, config_manager: ConfigManager) -> None:
        self._config_manager = config_manager

    def get_active_session(self) -> AccountSession | None:
        config = self._config_manager.config
        if not config.access_token or not config.player_uuid or not config.player_name:
            return None
        return AccountSession(
            username=config.player_name,
            uuid=config.player_uuid,
            access_token=config.access_token,
            refresh_token=config.refresh_token,
            expires_at=config.token_expires_at,
            profile_link=config.account_profile_link,
        )

    def save_session(self, session: AccountSession) -> None:
        self._config_manager.update(
            player_name=session.username,
            player_uuid=session.uuid,
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            token_expires_at=session.expires_at,
            account_profile_link=session.profile_link,
            auth_provider="ely.by",
        )

    def clear_session(self) -> None:
        self._config_manager.update(
            player_name="Player",
            player_uuid="",
            access_token="",
            refresh_token="",
            token_expires_at=0,
            account_profile_link="",
            auth_provider="",
        )

    def get_accounts_site_url(self) -> str:
        session = self.get_active_session()
        if session is not None and session.profile_link:
            return session.profile_link
        return "https://ely.by/"

    def get_avatar_cache_path(self, username: str | None = None) -> Path:
        cache_dir = self._config_manager._resolve_base_dir() / "cache" / "avatars"
        cache_dir.mkdir(parents=True, exist_ok=True)
        if username is None:
            session = self.get_active_session()
            username = session.username if session is not None else "default"
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", username.strip().lower()) or "default"
        filename = f"{safe_name}.png"
        return cache_dir / filename
