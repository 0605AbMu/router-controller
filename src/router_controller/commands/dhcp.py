import typer
from router_controller.client import get_router_client
from router_controller.utils.display import print_dhcp_table, print_error


def command():
    """DHCP qurilmalar ro'yxati."""
    client = None
    try:
        client = get_router_client()
        leases = client.get_dhcp_leases()
        print_dhcp_table(leases)
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
