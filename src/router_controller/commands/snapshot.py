"""Routerning umumiy holat snimkasi — bitta CLI chaqiriq, bitta authorize().

GUI ilovalar (WiFiPilot) har bir tab uchun alohida CLI ishga tushirmasligi uchun.
Default'da JSON chiqaradi. Global --json flag bilan unified schema'da bo'ladi:
  {"ok": true, "data": {...}, "errors": {section: msg}}

--no-json bilan inson o'qiy oladigan dict ko'rinishi.
"""
import json
import sys
from typing import Optional
import typer
from router_controller.client import get_router_client, get_wifi_radio_info
from router_controller.utils.display import console, print_error
from router_controller.utils.output import is_json, emit_data, emit_error
from router_controller.utils.serializers import (
    serialize_device,
    serialize_lease,
    serialize_firmware,
    serialize_status,
    serialize_wifi,
    classify_exception,
)


def _safe(fn, *args, **kwargs):
    """Xatosi bo'lsa None qaytaradi (boshqa bo'limlar buzilmasin)."""
    try:
        return fn(*args, **kwargs), None
    except Exception as e:
        return None, str(e)


def command(
    json_out: bool = typer.Option(
        True, "--json/--no-json",
        help="JSON formatda chiqarish (default). Eski flag — global --json bilan "
             "moslashtirish uchun saqlanadi.",
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

    data: dict = {"sections": sorted(sections), "router_class": None}
    errors: dict = {}
    client = None
    try:
        client = get_router_client()
        data["router_class"] = type(client).__name__

        if "firmware" in sections:
            fw, err = _safe(client.get_firmware)
            if err:
                errors["firmware"] = err
            else:
                data["firmware"] = serialize_firmware(fw)

        status_obj = None
        if "status" in sections or "devices" in sections or "wifi" in sections:
            status_obj, err = _safe(client.get_status)
            if err:
                errors["status"] = err

        if "status" in sections and status_obj is not None:
            data["status"] = serialize_status(status_obj)

        if "wifi" in sections:
            radio_info, err = _safe(get_wifi_radio_info, client)
            if err:
                errors["wifi_channels"] = err
                data["wifi"] = serialize_wifi(status_obj, None)
            else:
                data["wifi"] = serialize_wifi(status_obj, radio_info)

        if "devices" in sections and status_obj is not None:
            data["devices"] = [serialize_device(d) for d in status_obj.devices]

        if "dhcp" in sections:
            leases, err = _safe(client.get_dhcp_leases)
            if err:
                errors["dhcp"] = err
            else:
                data["dhcp"] = [serialize_lease(l) for l in leases]

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

    # Output rejimi:
    # - Global --json bo'lsa: unified {ok, data, errors} (yangi)
    # - --json/--no-json local flag (eski) hali ham qo'llab-quvvatlanadi
    if is_json():
        emit_data(data, errors=errors or None)
    elif json_out:
        # Eski xulq — flat JSON (backwards compatibility, lekin endi global
        # --json afzal). errors data ichiga qaytariladi.
        out = dict(data)
        if errors:
            out["errors"] = errors
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
        sys.stdout.write("\n")
    else:
        console.print({"data": data, "errors": errors})
