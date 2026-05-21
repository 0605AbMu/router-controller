import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_status_panel, print_error
from router_controller.utils.output import is_json, emit_data, emit_error
from router_controller.utils.serializers import (
    serialize_status,
    serialize_firmware,
    classify_exception,
)


def command():
    """Router umumiy holati (WiFi, tarmoq, qurilmalar)."""
    client = None
    try:
        client = get_router_client()
        status = client.get_status()
        firmware = client.get_firmware()

        if is_json():
            emit_data({
                "status": serialize_status(status),
                "firmware": serialize_firmware(firmware),
            })
        else:
            print_status_panel(status, None, firmware)
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
