import typer
from router_controller.client import get_router_client
from router_controller.utils.display import console, print_status_panel, print_error


def command():
    """Router umumiy holati (WiFi, tarmoq, qurilmalar)."""
    client = None
    try:
        client = get_router_client()
        status = client.get_status()
        firmware = client.get_firmware()
        print_status_panel(status, None, firmware)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
