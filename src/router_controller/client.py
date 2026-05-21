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
    body = client._encrypt_body("32|1,0,0#32|2,0,0")
    response = client.request(2, 1, True, data=body)
    text = client._decrypt_data(response.text)

    channels = {}
    current_band = None
    for line in text.split("\n"):
        line = line.strip()
        if line == "id 32|1,0,0":
            current_band = "2.4GHz"
        elif line == "id 32|2,0,0":
            current_band = "5GHz"
        elif line.startswith("uChannel ") and current_band:
            channels[current_band] = int(line.split()[1])
    return channels


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
