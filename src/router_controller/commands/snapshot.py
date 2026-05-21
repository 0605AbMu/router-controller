"""Routerning umumiy holat snimkasi — bitta CLI chaqiriq, bitta authorize(), JSON output.

GUI ilovalar (WiFiPilot) har bir tab uchun alohida CLI ishga tushirmasligi uchun.
"""
import json
import sys
from typing import Optional
import typer
from router_controller.client import get_router_client, get_wifi_channels
from router_controller.utils.display import print_error


def _safe(fn, *args, **kwargs):
    """Xatosi bo'lsa None qaytaradi (boshqa bo'limlar buzilmasin)."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, str(e)


def _device_band(t) -> str:
    s = str(t).lower()
    if "2g" in s:
        return "2.4 GHz"
    if "5g" in s:
        return "5 GHz"
    if "wired" in s:
        return "Kabel"
    return "Noma'lum"


def _serialize_device(d) -> dict:
    return {
        "hostname": d.hostname or None,
        "ip": str(d.ipaddress) if d.ipaddress else None,
        "mac": str(d.macaddress) if d.macaddress else None,
        "band": _device_band(d.type),
        "down_speed": getattr(d, "down_speed", 0) or 0,
        "up_speed": getattr(d, "up_speed", 0) or 0,
        "active": bool(getattr(d, "active", True)),
    }


def _serialize_lease(l) -> dict:
    return {
        "hostname": l.hostname or None,
        "ip": str(l.ipaddress),
        "mac": str(l.macaddress),
        "lease_time": str(l.lease_time),
    }


def command(
    json_out: bool = typer.Option(
        True, "--json/--no-json",
        help="JSON formatda chiqarish (default).",
    ),
    include: Optional[str] = typer.Option(
        None, "--include", "-i",
        help="Vergul bilan ajratilgan bo'limlar: status,firmware,wifi,devices,dhcp",
    ),
):
    """UI uchun barcha ma'lumotni bitta chaqiriqda qaytaradi (status+wifi+devices+dhcp+firmware).

    authorize() faqat bir marta ishlaydi → 5 CLI chaqiriq o'rniga 1 ta.
    """
    sections = (include.split(",") if include else
                ["status", "firmware", "wifi", "devices", "dhcp"])
    sections = {s.strip().lower() for s in sections}

    out: dict = {"sections": list(sections), "errors": {}}
    client = None
    try:
        client = get_router_client()
        out["router_class"] = type(client).__name__

        if "firmware" in sections:
            fw, err = _safe(client.get_firmware)
            if err:
                out["errors"]["firmware"] = err
            else:
                out["firmware"] = {
                    "model": fw.model,
                    "hardware": fw.hardware_version,
                    "firmware": fw.firmware_version,
                }

        status_obj = None
        if "status" in sections or "devices" in sections:
            status_obj, err = _safe(client.get_status)
            if err:
                out["errors"]["status"] = err

        if "status" in sections and status_obj is not None:
            out["status"] = {
                "wifi_2g": bool(status_obj.wifi_2g_enable),
                "wifi_5g": bool(status_obj.wifi_5g_enable),
                "guest_2g": bool(getattr(status_obj, "guest_2g_enable", False)),
                "guest_5g": bool(getattr(status_obj, "guest_5g_enable", False)),
                "wan_ipv4": str(status_obj.wan_ipv4_addr) if status_obj.wan_ipv4_addr else None,
                "lan_ipv4": str(status_obj.lan_ipv4_addr) if status_obj.lan_ipv4_addr else None,
                "wan_gateway": str(status_obj.wan_ipv4_gateway) if status_obj.wan_ipv4_gateway else None,
                "clients_total": getattr(status_obj, "clients_total", 0),
                "wifi_clients_total": getattr(status_obj, "wifi_clients_total", 0),
                "wired_total": getattr(status_obj, "wired_total", 0),
                "guest_clients_total": getattr(status_obj, "guest_clients_total", 0),
            }

        if "wifi" in sections:
            channels, err = _safe(get_wifi_channels, client)
            if err:
                out["errors"]["wifi_channels"] = err
            else:
                out["wifi"] = {
                    "channels": channels,  # {"2.4GHz": int, "5GHz": int}
                    "bands": {
                        "2.4 GHz": {
                            "host": bool(status_obj.wifi_2g_enable) if status_obj else None,
                            "guest": bool(getattr(status_obj, "guest_2g_enable", False)) if status_obj else None,
                        },
                        "5 GHz": {
                            "host": bool(status_obj.wifi_5g_enable) if status_obj else None,
                            "guest": bool(getattr(status_obj, "guest_5g_enable", False)) if status_obj else None,
                        },
                    },
                }

        if "devices" in sections and status_obj is not None:
            out["devices"] = [_serialize_device(d) for d in status_obj.devices]

        if "dhcp" in sections:
            leases, err = _safe(client.get_dhcp_leases)
            if err:
                out["errors"]["dhcp"] = err
            else:
                out["dhcp"] = [_serialize_lease(l) for l in leases]

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass

    if json_out:
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        sys.stdout.write("\n")
    else:
        # Inson o'qiy oladigan ko'rinish — debug uchun
        from router_controller.utils.display import console
        console.print(out)
