"""Router object'larni JSON-uchun dict ko'rinishiga aylantiradigan funksiyalar.

Har bir command shu funksiyalarni ishlatsa, GUI/script integratsiyasi
uchun JSON shape doim bir xil bo'ladi.
"""
from typing import Optional


def device_band(connection_type) -> str:
    """`connection_type` (router'dan) ni standart band nomiga aylantiradi."""
    s = str(connection_type).lower()
    if "2g" in s:
        return "2.4 GHz"
    if "5g" in s:
        return "5 GHz"
    if "wired" in s:
        return "Kabel"
    return "Noma'lum"


def serialize_device(d) -> dict:
    return {
        "hostname": d.hostname or None,
        "ip": str(d.ipaddress) if d.ipaddress else None,
        "mac": str(d.macaddress) if d.macaddress else None,
        "band": device_band(d.type),
        "down_speed": getattr(d, "down_speed", 0) or 0,
        "up_speed": getattr(d, "up_speed", 0) or 0,
        "active": bool(getattr(d, "active", True)),
    }


def serialize_lease(l) -> dict:
    return {
        "hostname": l.hostname or None,
        "ip": str(l.ipaddress),
        "mac": str(l.macaddress),
        "lease_time": str(l.lease_time),
    }


def serialize_firmware(fw) -> dict:
    return {
        "model": fw.model,
        "hardware": fw.hardware_version,
        "firmware": fw.firmware_version,
    }


def serialize_status(s) -> dict:
    return {
        "wifi_2g": bool(s.wifi_2g_enable),
        "wifi_5g": bool(s.wifi_5g_enable),
        "guest_2g": bool(getattr(s, "guest_2g_enable", False)),
        "guest_5g": bool(getattr(s, "guest_5g_enable", False)),
        "wan_ipv4": str(s.wan_ipv4_addr) if s.wan_ipv4_addr else None,
        "lan_ipv4": str(s.lan_ipv4_addr) if s.lan_ipv4_addr else None,
        "wan_gateway": str(s.wan_ipv4_gateway) if s.wan_ipv4_gateway else None,
        "clients_total": getattr(s, "clients_total", 0),
        "wifi_clients_total": getattr(s, "wifi_clients_total", 0),
        "wired_total": getattr(s, "wired_total", 0),
        "guest_clients_total": getattr(s, "guest_clients_total", 0),
    }


def serialize_wifi(status_obj, radio_info: Optional[dict] = None) -> dict:
    """WiFi bo'limining to'liq dict ko'rinishi (snapshot va `wifi status` uchun bir xil)."""
    channels = {}
    radio = {}
    if radio_info:
        radio = radio_info
        channels = {
            band: data.get("channel")
            for band, data in radio_info.items()
            if data.get("channel") is not None
        }
    bands = {}
    if status_obj is not None:
        bands = {
            "2.4 GHz": {
                "host": bool(status_obj.wifi_2g_enable),
                "guest": bool(getattr(status_obj, "guest_2g_enable", False)),
            },
            "5 GHz": {
                "host": bool(status_obj.wifi_5g_enable),
                "guest": bool(getattr(status_obj, "guest_5g_enable", False)),
            },
        }
    return {"channels": channels, "radio": radio, "bands": bands}


def classify_exception(exc: Exception) -> str:
    """Exception'ni standart error_code'ga aylantiradi (heuristic)."""
    msg = str(exc).lower()
    name = type(exc).__name__.lower()
    if any(k in msg for k in ("auth", "password", "login", "unauthorized", "credentials")):
        return "AUTH_FAILED"
    if any(k in msg for k in ("connect", "timeout", "unreachable", "refused", "network", "dns")):
        return "NETWORK_ERROR"
    if "config" in msg and "miss" in msg:
        return "CONFIG_MISSING"
    if "timeout" in name:
        return "NETWORK_ERROR"
    return "EXEC_FAILED"
