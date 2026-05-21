import typer
from tplinkrouterc6u.common.package_enum import Connection

from router_controller.client import (
    get_router_client,
    get_wifi_channels,
    get_wifi_radio_info,
    set_wifi_channel,
    VALID_CHANNELS_2G,
    VALID_CHANNELS_5G,
)
from router_controller.utils.display import (
    console,
    print_wifi_status,
    print_channel_info,
    print_success,
    print_error,
)
from router_controller.utils.output import is_json, emit_data, emit_ok, emit_error
from router_controller.utils.serializers import serialize_wifi, classify_exception

app = typer.Typer(help="WiFi boshqarish.", no_args_is_help=True)

_BAND_MAP = {
    "2.4": ("2.4GHz", Connection.HOST_2G),
    "2":   ("2.4GHz", Connection.HOST_2G),
    "5":   ("5GHz",   Connection.HOST_5G),
    "5.0": ("5GHz",   Connection.HOST_5G),
}


def _resolve_band(band_str: str):
    result = _BAND_MAP.get(band_str.lower())
    if not result:
        msg = f"Noto'g'ri band: '{band_str}'. '2.4' yoki '5' deb yozing."
        if is_json():
            emit_error("INVALID_INPUT", msg)
        else:
            print_error(msg)
        raise typer.Exit(1)
    return result


@app.command("status")
def wifi_status():
    """WiFi holati (yoqilgan/o'chirilgan)."""
    client = None
    try:
        client = get_router_client()
        status = client.get_status()
        radio_info = get_wifi_radio_info(client)

        if is_json():
            emit_data(serialize_wifi(status, radio_info))
        else:
            print_wifi_status(status)
            channels = get_wifi_channels(client)
            console.print("  Channellar:")
            for band, ch in channels.items():
                print_channel_info(band, ch)
            console.print()
    except Exception as e:
        if is_json():
            emit_error(classify_exception(e), str(e))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass


@app.command("on")
def wifi_on(
    band: str = typer.Argument(..., help="Band: 2.4 | 5"),
):
    """WiFi yoqish. Misol: router wifi on 2.4"""
    label, connection = _resolve_band(band)
    client = None
    try:
        client = get_router_client()
        client.set_wifi(connection, True)
        msg = f"{label} WiFi yoqildi."
        if is_json():
            emit_ok(msg, data={"band": label, "enabled": True})
        else:
            print_success(msg)
    except Exception as e:
        if is_json():
            emit_error(classify_exception(e), str(e))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass


@app.command("off")
def wifi_off(
    band: str = typer.Argument(..., help="Band: 2.4 | 5"),
):
    """WiFi o'chirish. Misol: router wifi off 5"""
    label, connection = _resolve_band(band)
    client = None
    try:
        client = get_router_client()
        client.set_wifi(connection, False)
        msg = f"{label} WiFi o'chirildi."
        if is_json():
            emit_ok(msg, data={"band": label, "enabled": False})
        else:
            print_success(msg)
    except Exception as e:
        if is_json():
            emit_error(classify_exception(e), str(e))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass


@app.command("channel")
def wifi_channel(
    band: str = typer.Argument(..., help="Band: 2.4 | 5"),
    channel: int = typer.Argument(..., help="Channel raqami (0 = avtomatik)"),
):
    """WiFi channelni o'zgartirish. Misol: router wifi channel 2.4 6

    \b
    2.4 GHz uchun: 0 (auto), 1-13
    5 GHz uchun:   0 (auto), 36, 40, 44, 48, 52, 56, 60, 64 ...
    """
    label, _ = _resolve_band(band)
    band_key = "2.4GHz" if "2" in band else "5GHz"
    valid = VALID_CHANNELS_2G if band_key == "2.4GHz" else VALID_CHANNELS_5G

    if channel not in valid:
        msg = (
            f"{label} uchun noto'g'ri channel: {channel}. "
            f"Mumkin bo'lganlar: {', '.join(map(str, valid))}"
        )
        if is_json():
            emit_error("INVALID_INPUT", msg)
        else:
            print_error(msg)
        raise typer.Exit(1)

    client = None
    try:
        client = get_router_client()
        set_wifi_channel(client, band_key, channel)
        msg = (
            f"{label} channel avtomatik rejimga o'tkazildi."
            if channel == 0
            else f"{label} channel {channel} ga o'zgartirildi."
        )
        if is_json():
            emit_ok(msg, data={"band": label, "channel": channel})
        else:
            print_success(msg)
    except Exception as e:
        if is_json():
            emit_error(classify_exception(e), str(e))
        else:
            print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
