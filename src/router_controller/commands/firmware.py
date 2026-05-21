import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_firmware, print_error


def command():
    """Firmware va hardware versiyasi."""
    client = None
    try:
        client = get_router_client()
        firmware = client.get_firmware()
        print_firmware(firmware)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
