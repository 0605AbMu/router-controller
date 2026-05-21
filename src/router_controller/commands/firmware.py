import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_firmware, print_error
from router_controller.utils.output import is_json, emit_data, emit_error
from router_controller.utils.serializers import serialize_firmware, classify_exception


def command():
    """Firmware va hardware versiyasi."""
    client = None
    try:
        client = get_router_client()
        firmware = client.get_firmware()

        if is_json():
            emit_data(serialize_firmware(firmware))
        else:
            print_firmware(firmware)
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
