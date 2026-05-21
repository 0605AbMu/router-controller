import typer
from router_controller.client import get_router_client
from router_controller.utils.display import console, print_success, print_error


def command(
    yes: bool = typer.Option(
        False, "--yes", "-y",
        help="Tasdiqlash so'ramasdan qayta ishga tushirish.",
    ),
):
    """Routerni qayta ishga tushirish."""
    if not yes:
        confirmed = typer.confirm(
            "Router qayta ishga tushiriladi. Barcha ulanishlar uziladi. Davom ettirasizmi?"
        )
        if not confirmed:
            console.print("Bekor qilindi.")
            raise typer.Exit(0)

    client = None
    try:
        client = get_router_client()
        client.reboot()
        print_success("Router qayta ishga tushirilmoqda...")
    except Exception as e:
        print_error(str(e))
        raise typer.Exit(1)
    finally:
        if client:
            try:
                client.logout()
            except Exception:
                pass
