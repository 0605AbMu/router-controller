import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_dhcp_table, print_error
from router_controller.utils.output import is_json, emit_data, emit_error
from router_controller.utils.serializers import serialize_lease, classify_exception


def command():
    """DHCP qurilmalar ro'yxati."""
    client = None
    try:
        client = get_router_client()
        leases = client.get_dhcp_leases()

        if is_json():
            emit_data({"leases": [serialize_lease(l) for l in leases]})
        else:
            print_dhcp_table(leases)
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
