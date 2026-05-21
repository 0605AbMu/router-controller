import json
from pathlib import Path
from typing import Optional

try:
    import keyring
    _KEYRING_AVAILABLE = True
except ImportError:
    _KEYRING_AVAILABLE = False

CONFIG_DIR = Path.home() / ".router-controller"
CONFIG_FILE = CONFIG_DIR / "config.json"
KEYRING_SERVICE = "router-controller"
KEYRING_USERNAME = "router-password"


class Config:
    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    def _read(self) -> dict:
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _write(self, data: dict) -> None:
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def get_host(self) -> Optional[str]:
        return self._read().get("host")

    def set_host(self, host: str) -> None:
        data = self._read()
        data["host"] = host
        self._write(data)

    def get_password(self) -> Optional[str]:
        if _KEYRING_AVAILABLE:
            try:
                return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception:
                pass
        return self._read().get("_password")

    def set_password(self, password: str) -> None:
        if _KEYRING_AVAILABLE:
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, password)
                return
            except Exception:
                pass
        # Keyring ishlamasa, config faylga yozamiz (kamroq xavfsiz)
        data = self._read()
        data["_password"] = password
        self._write(data)

    def get_username(self) -> str:
        return self._read().get("username", "admin")

    def set_username(self, username: str) -> None:
        data = self._read()
        data["username"] = username
        self._write(data)

    def is_configured(self) -> bool:
        return bool(self.get_host() and self.get_password())

    def clear(self) -> None:
        if _KEYRING_AVAILABLE:
            try:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception:
                pass
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
