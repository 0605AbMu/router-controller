import json
import os
import stat
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

# Saqlash usuli — keyring (OS keychain) yoki file (chmod 600 lokal JSON).
# macOS Keychain har safar so'ragani uchun "file" default, foydalanuvchi xohlasa
# `config set --storage keyring` bilan keyring ga o'tishi mumkin.
STORAGE_FILE = "file"
STORAGE_KEYRING = "keyring"
DEFAULT_STORAGE = STORAGE_FILE


def _has_keyring() -> bool:
    if not _KEYRING_AVAILABLE:
        return False
    try:
        backend = keyring.get_keyring()
        # `fail.Keyring` keyring topa olmaganida qaytariladi.
        return backend.__class__.__name__ != "fail.Keyring"
    except Exception:
        return False


class Config:
    def __init__(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Mavjud config faylini chmod 600 ga keltirish (oldingi versiyalar 644 yaratgan).
        if CONFIG_FILE.exists():
            try:
                os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
            except OSError:
                pass

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
        try:
            os.chmod(CONFIG_FILE, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass

    # --- storage strategy ---
    def get_storage(self) -> str:
        return self._read().get("_storage", DEFAULT_STORAGE)

    def set_storage(self, storage: str) -> None:
        if storage not in (STORAGE_FILE, STORAGE_KEYRING):
            raise ValueError(f"Noma'lum storage: {storage}")
        if storage == STORAGE_KEYRING and not _has_keyring():
            raise RuntimeError("keyring kutubxonasi mavjud emas yoki backend topilmadi.")
        data = self._read()
        data["_storage"] = storage
        self._write(data)

    # --- host ---
    def get_host(self) -> Optional[str]:
        return self._read().get("host")

    def set_host(self, host: str) -> None:
        data = self._read()
        data["host"] = host
        self._write(data)

    # --- username ---
    def get_username(self) -> str:
        return self._read().get("username", "admin")

    def set_username(self, username: str) -> None:
        data = self._read()
        data["username"] = username
        self._write(data)

    # --- password ---
    def get_password(self) -> Optional[str]:
        storage = self.get_storage()
        data = self._read()
        file_pw = data.get("_password")

        if storage == STORAGE_KEYRING and _has_keyring():
            try:
                pw = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
                if pw is not None:
                    return pw
            except Exception:
                pass
            return file_pw

        # storage == file
        if file_pw is not None:
            return file_pw

        # Migration: oldingi versiya parolni keyring'ga saqlagan bo'lishi mumkin.
        # Bir martagina o'qib, fileni yangilab qo'yamiz — keyin keyring tegilmaydi.
        if _has_keyring():
            try:
                legacy = keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception:
                legacy = None
            if legacy is not None:
                data["_password"] = legacy
                self._write(data)
                try:
                    keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
                except Exception:
                    pass
                return legacy
        return None

    def set_password(self, password: str) -> None:
        storage = self.get_storage()
        if storage == STORAGE_KEYRING and _has_keyring():
            try:
                keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, password)
                # Eski file-based parolni tozalash, har yerda saqlanib qolmaslik uchun.
                data = self._read()
                data.pop("_password", None)
                self._write(data)
                return
            except Exception:
                pass
        # File rejimi (default) — chmod 600 bilan saqlanadi.
        data = self._read()
        data["_password"] = password
        self._write(data)

    def is_configured(self) -> bool:
        return bool(self.get_host() and self.get_password())

    def clear(self) -> None:
        if _has_keyring():
            try:
                keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
            except Exception:
                pass
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
