from __future__ import annotations

from dataclasses import dataclass
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import secrets
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen
import webbrowser

from launcher.core.account_manager import AccountSession


@dataclass(slots=True)
class ElyAuthResult:
    ok: bool
    session: AccountSession | None
    message: str


class ElyAuthClient:
    AUTH_URL = "https://account.ely.by/oauth2/v1"
    TOKEN_URL = "https://account.ely.by/api/oauth2/v1/token"
    INFO_URL = "https://account.ely.by/api/account/v1/info"
    CLIENT_ID = "raramba-launcher3"
    CLIENT_SECRET = "WJzCd-5PgxCJ9oJnJbqurVK3sPNijJ2XRccWRW75bMcku7RT-QXvZrb4ztUnvtFo"
    REDIRECT_URI = "http://127.0.0.1:47831/oauth/ely"
    SCOPES = "account_info minecraft_server_session offline_access"

    def authorize(self, timeout_seconds: int = 180) -> ElyAuthResult:
        state = secrets.token_urlsafe(24)
        callback_data: dict[str, str] = {}
        callback_event = threading.Event()

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # type: ignore[override]
                parsed = urlparse(self.path)
                if parsed.path != "/oauth/ely":
                    self.send_response(404)
                    self.end_headers()
                    return

                query = parse_qs(parsed.query)
                for key in ("code", "state", "error", "error_message"):
                    if key in query and query[key]:
                        callback_data[key] = query[key][0]

                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    (
                        "<html><body style='background:#0b1220;color:#e2f6fb;"
                        "font-family:Segoe UI,sans-serif;padding:24px'>"
                        "<h2>Авторизация завершена</h2>"
                        "<p>Можно вернуться в лаунчер.</p>"
                        "</body></html>"
                    ).encode("utf-8")
                )
                callback_event.set()

            def log_message(self, format: str, *args: Any) -> None:
                return

        try:
            server = HTTPServer(("127.0.0.1", 47831), CallbackHandler)
        except OSError as exc:
            return ElyAuthResult(False, None, f"Не удалось открыть локальный callback-сервер: {exc}")

        server_thread = threading.Thread(target=server.handle_request, daemon=True)
        server_thread.start()

        auth_params = {
            "client_id": self.CLIENT_ID,
            "redirect_uri": self.REDIRECT_URI,
            "response_type": "code",
            "scope": self.SCOPES,
            "state": state,
            "prompt": "select_account",
        }
        webbrowser.open(f"{self.AUTH_URL}?{urlencode(auth_params)}")

        if not callback_event.wait(timeout_seconds):
            server.server_close()
            return ElyAuthResult(False, None, "Время ожидания авторизации Ely.by истекло.")

        server.server_close()

        if callback_data.get("state") != state:
            return ElyAuthResult(False, None, "Не удалось проверить состояние OAuth-сессии.")
        if "error" in callback_data:
            message = callback_data.get("error_message") or callback_data["error"]
            return ElyAuthResult(False, None, f"Авторизация Ely.by отменена: {message}")

        code = callback_data.get("code")
        if not code:
            return ElyAuthResult(False, None, "Ely.by не вернул код авторизации.")

        try:
            session = self._exchange_code_for_session(code)
        except RuntimeError as exc:
            return ElyAuthResult(False, None, str(exc))

        return ElyAuthResult(True, session, "Аккаунт Ely.by подключён.")

    def refresh_session(self, current_session: AccountSession) -> ElyAuthResult:
        if not current_session.refresh_token:
            return ElyAuthResult(False, None, "У аккаунта Ely.by отсутствует refresh token.")

        token_payload = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": current_session.refresh_token,
        }
        try:
            token_response = self._post_form(self.TOKEN_URL, token_payload)
            session = self._build_session_from_token_response(token_response, current_session)
        except RuntimeError as exc:
            return ElyAuthResult(False, None, str(exc))

        return ElyAuthResult(True, session, "Сессия Ely.by обновлена.")

    def _exchange_code_for_session(self, code: str) -> AccountSession:
        token_payload = {
            "client_id": self.CLIENT_ID,
            "client_secret": self.CLIENT_SECRET,
            "redirect_uri": self.REDIRECT_URI,
            "grant_type": "authorization_code",
            "code": code,
        }
        token_response = self._post_form(self.TOKEN_URL, token_payload)
        return self._build_session_from_token_response(token_response)

    def _build_session_from_token_response(
        self,
        token_response: dict[str, Any],
        fallback_session: AccountSession | None = None,
    ) -> AccountSession:
        access_token = str(token_response.get("access_token") or "")
        if not access_token:
            raise RuntimeError("Ely.by не вернул access_token.")

        info_response = self._get_json(
            self.INFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        username = str(info_response.get("username") or getattr(fallback_session, "username", "")).strip()
        uuid = str(info_response.get("uuid") or getattr(fallback_session, "uuid", "")).strip()
        if not username or not uuid:
            raise RuntimeError("Не удалось получить данные аккаунта Ely.by.")

        fallback_refresh = getattr(fallback_session, "refresh_token", "")
        refresh_token = str(token_response.get("refresh_token") or fallback_refresh)
        expires_in = int(token_response.get("expires_in") or 0)
        fallback_expires = getattr(fallback_session, "expires_at", 0)
        expires_at = int(time.time()) + expires_in if expires_in > 0 else int(fallback_expires)
        profile_link = str(info_response.get("profileLink") or getattr(fallback_session, "profile_link", ""))
        return AccountSession(
            username=username,
            uuid=uuid,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            profile_link=profile_link,
        )

    @staticmethod
    def _post_form(url: str, payload: dict[str, str]) -> dict[str, Any]:
        request = Request(
            url,
            data=urlencode(payload).encode("utf-8"),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ely.by token error ({exc.code}): {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Не удалось связаться с Ely.by: {exc.reason}") from exc

    @staticmethod
    def _get_json(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
        request = Request(url, headers=headers or {})
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Ely.by account info error ({exc.code}): {body}") from exc
        except URLError as exc:
            raise RuntimeError(f"Не удалось связаться с Ely.by: {exc.reason}") from exc
