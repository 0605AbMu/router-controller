from typing import Optional
import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_devices_table, print_error


def command(
    sort_by: str = typer.Option(
        "name", "--sort", "-s",
        help="Saralash usuli: name | ip | mac | band",
    ),
    band: Optional[str] = typer.Option(
        None, "--band", "-b",
        help="Band bo'yicha filtrlash: 2.4 | 5 | wired",
    ),
    all_devices: bool = typer.Option(
        False, "--all", "-a",
        help="Oflayn qurilmalarni ham ko'rsatish",
    ),
):
    """Ulangan qurilmalar ro'yxati."""
    client = None
    try:
        client = get_router_client()
        status = client.get_status()
        devices = status.devices

        if not all_devices:
            devices = [d for d in devices if d.active]

        if band:
            band_lower = band.lower()
            def band_match(d) -> bool:
                t = str(d.type).lower()
                if band_lower in ("2.4", "2"):
                    return "2g" in t
                if band_lower in ("5",):
                    return "5g" in t
                if band_lower in ("wired", "kabel"):
                    return "wired" in t
                return True
            devices = [d for d in devices if band_match(d)]

        def sort_key(d):
            if sort_by == "ip":
                return str(d.ipaddress or "")
            if sort_by == "mac":
                return str(d.macaddress or "")
            if sort_by == "band":
                return str(d.type)
            return (d.hostname or "").lower()

        devices = sorted(devices, key=sort_key)
        print_devices_table(devices)

    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
