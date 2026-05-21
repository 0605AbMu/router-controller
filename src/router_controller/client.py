import logging
from typing import Callable, TypeVar
from tplinkrouterc6u import TplinkRouterProvider
from tplinkrouterc6u.common.exception import ClientException

from router_controller.config import Config
from router_controller.utils.errors import (
    NotConfiguredError,
    ConnectionError,
    AuthenticationError,
)

T = TypeVar("T")

VALID_CHANNELS_2G = list(range(0, 14))   # 0=auto, 1-13
VALID_CHANNELS_5G = [
    0, 36, 40, 44, 48, 52, 56, 60, 64,
    100, 104, 108, 112, 116, 120, 124, 128,
    132, 136, 140, 144, 149, 153, 157, 161, 165,
]

# tplinkrouterc6u'ning bir nechta client'lari (c80, re330, ...) network xatolarida
# self._logger.error(...) chaqiradi va logger=None bo'lsa
# "'NoneType' object has no attribute 'error'" AttributeError sodir bo'ladi.
# Real logger uzatish bilan bu yashirin bug'ni oldini olamiz.
_logger = logging.getLogger("router_controller")
if not _logger.handlers:
    _logger.addHandler(logging.NullHandler())


def get_router_client():
    cfg = Config()
    if not cfg.is_configured():
        raise NotConfiguredError(
            "Router sozlanmagan. Avval ishga tushiring:\n"
            "  router config set --host http://192.168.0.1 --password PAROL"
        )
    try:
        client = TplinkRouterProvider.get_client(
            cfg.get_host(),
            cfg.get_password(),
            username=cfg.get_username(),
            logger=_logger,
        )
        client.authorize()
        return client
    except ClientException as e:
        msg = str(e).lower()
        if "password" in msg or "auth" in msg or "login" in msg:
            raise AuthenticationError(
                "Parol noto'g'ri. `router config set` bilan qayta kiriting."
            ) from e
        raise ConnectionError(
            f"Router ga ulanib bo'lmadi: {cfg.get_host()}\n"
            "Router yoqilgan va bir xil tarmoqda ekanligini tekshiring."
        ) from e
    except Exception as e:
        raise ConnectionError(f"Ulanishda xato: {e}") from e


def with_client(func: Callable) -> Callable:
    """Decorator: authorize → func(client) → logout"""
    def wrapper(*args, **kwargs):
        client = get_router_client()
        try:
            return func(client, *args, **kwargs)
        finally:
            try:
                client.logout()
            except Exception:
                pass
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def get_wifi_channels(client) -> dict:
    """Eski API'ni saqlash uchun: faqat kanal raqamlari. Yangi GUI ilovalar
    `get_wifi_radio_info` ni ishlatishi kerak — u mode + bandwidth ham qaytaradi."""
    info = get_wifi_radio_info(client)
    return {band: data["channel"] for band, data in info.items() if data.get("channel") is not None}


# TP-Link mode kodlari -> PHY belgilar. Routerlar orasida farq bo'lishi mumkin;
# noma'lum kodlar uchun "unknown" qaytariladi.
_MODE_CODES_24 = {
    0: "11b",
    1: "11g",
    2: "11bg",
    3: "11bgn",
    4: "11n",
    5: "11gn",
    6: "11bgnax",  # 802.11ax 2.4 GHz (Wi-Fi 6) — mavjud routerlarda
}
_MODE_CODES_5 = {
    0: "11a",
    1: "11n",
    2: "11an",
    3: "11anac",
    4: "11ac",
    5: "11nacax",  # 802.11ax 5 GHz (Wi-Fi 6)
}

# TP-Link bandwidth kodlari -> MHz. Auto (0) holatida router driverni o'zi tanlaydi
# (odatda 2.4 da 20 MHz, 5 da 80 MHz).
_BANDWIDTH_MHZ = {
    0: None,    # auto
    1: 20,
    2: 40,
    3: 80,
    4: 160,
}


def _decode_mode(band: str, code) -> str | None:
    if code is None:
        return None
    table = _MODE_CODES_24 if band == "2.4GHz" else _MODE_CODES_5
    return table.get(int(code), "unknown")


def get_wifi_radio_info(client) -> dict:
    """Har bir band uchun {channel, mode_code, mode, bandwidth_mhz} qaytaradi.

    Bitta CLI chaqiriqda routerdan ikkala radio konfiguratsiyasini o'qiydi.
    Format:
        {
          "2.4GHz": {"channel": 6, "mode_code": 3, "mode": "11bgn", "bandwidth_mhz": 20},
          "5GHz":   {"channel": 44, "mode_code": 3, "mode": "11anac", "bandwidth_mhz": 80},
        }

    Maydon yo'q yoki nofahmi kod bo'lsa, qiymat None qaytaradi (kelin tomon
    defensive bo'lishi kerak).
    """
    body = client._encrypt_body("32|1,0,0#32|2,0,0")
    response = client.request(2, 1, True, data=body)
    text = client._decrypt_data(response.text)

    result = {}
    current_band = None
    for line in text.split("\n"):
        line = line.strip()
        if line == "id 32|1,0,0":
            current_band = "2.4GHz"
            result.setdefault(current_band, {})
        elif line == "id 32|2,0,0":
            current_band = "5GHz"
            result.setdefault(current_band, {})
        elif not current_band:
            continue
        elif line.startswith("uChannel "):
            try:
                result[current_band]["channel"] = int(line.split()[1])
            except (ValueError, IndexError):
                pass
        elif line.startswith("uMode "):
            try:
                code = int(line.split()[1])
                result[current_band]["mode_code"] = code
                result[current_band]["mode"] = _decode_mode(current_band, code)
            except (ValueError, IndexError):
                pass
        elif line.startswith("uBandWidth "):
            try:
                code = int(line.split()[1])
                result[current_band]["bandwidth_code"] = code
                result[current_band]["bandwidth_mhz"] = _BANDWIDTH_MHZ.get(code)
            except (ValueError, IndexError):
                pass
    return result


def set_wifi_channel(client, band: str, channel: int) -> None:
    if band == "2.4GHz":
        request_id = "32|1,0,0"
        valid = VALID_CHANNELS_2G
    elif band == "5GHz":
        request_id = "32|2,0,0"
        valid = VALID_CHANNELS_5G
    else:
        raise ValueError(f"Noto'g'ri band: {band}")

    if channel not in valid:
        raise ValueError(
            f"{band} uchun noto'g'ri channel: {channel}\n"
            f"Mumkin bo'lgan qiymatlar: {valid}"
        )

    text = f"id {request_id}\r\nuChannel {channel}"
    body = client._encrypt_body(text)
    client.request(1, 0, True, data=body)
