"""Yagona output qatlami: terminal'da rich text, --json bilan strukturali JSON.

Schema:
  Read success:   {"ok": true, "data": {...}}
  Read partial:   {"ok": true, "data": {...}, "errors": {"section": "msg"}}
  Write success:  {"ok": true, "message": "...", "data": {...}}
  Error:          {"ok": false, "error_code": "...", "message": "..."}

Foydalanish (commands ichida):
  from router_controller.utils.output import is_json, emit_data, emit_ok, emit_error

  if is_json():
      emit_data({"foo": 123})
  else:
      console.print(...)

  # write komandalar uchun
  emit_ok("Yoqildi", data={"band": "2.4 GHz"})

  # xato (try/except'da)
  emit_error("AUTH_FAILED", str(e))
  raise typer.Exit(1)
"""
import json
import sys
from contextvars import ContextVar
from typing import Optional

_json_mode: ContextVar[bool] = ContextVar("_json_mode", default=False)


def set_json(enabled: bool) -> None:
    """Root callback'da chaqiriladi (--json flag bo'lsa)."""
    _json_mode.set(enabled)


def is_json() -> bool:
    return _json_mode.get()


def _write(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj, ensure_ascii=False))
    sys.stdout.write("\n")
    try:
        sys.stdout.flush()
    except Exception:
        pass


def emit_data(data: dict, errors: Optional[dict] = None) -> None:
    """Read command'lar uchun: ma'lumotni JSON sifatida chiqarish.

    is_json() False bo'lsa hech narsa qilmaydi — terminal output
    chaqiruvchi tomonda alohida amalga oshiriladi.
    """
    if not is_json():
        return
    payload: dict = {"ok": True, "data": data}
    if errors:
        payload["errors"] = errors
    _write(payload)


def emit_ok(message: str = "", data: Optional[dict] = None) -> None:
    """Write command muvaffaqiyati."""
    if not is_json():
        return
    payload: dict = {"ok": True, "message": message}
    if data is not None:
        payload["data"] = data
    _write(payload)


def emit_error(error_code: str, message: str) -> None:
    """Xato. typer.Exit(1) chaqiruvchi tomonda alohida bajariladi."""
    if not is_json():
        return
    _write({"ok": False, "error_code": error_code, "message": message})


# Tipik error code'lar — bir xil ishlatish uchun konstantalar.
class ErrorCode:
    AUTH_FAILED = "AUTH_FAILED"            # Router parol noto'g'ri
    NETWORK_ERROR = "NETWORK_ERROR"        # Router unreachable
    CONFIG_MISSING = "CONFIG_MISSING"      # Konfiguratsiya yo'q
    INVALID_INPUT = "INVALID_INPUT"        # Foydalanuvchi noto'g'ri arg
    USER_CANCELLED = "USER_CANCELLED"      # Y/N bekor qilindi
    EXEC_FAILED = "EXEC_FAILED"            # Boshqa har qanday xato
