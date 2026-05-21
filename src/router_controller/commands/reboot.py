import typer
from router_controller.client import get_router_client
from router_controller.utils.display import console, print_success, print_error
from router_controller.utils.output import is_json, emit_ok, emit_error
from router_controller.utils.serializers import classify_exception


def command(
    yes: bool = typer.Option(
        False, "--yes", "-y",
        help="Tasdiqlash so'ramasdan qayta ishga tushirish.",
    ),
):
    """Routerni qayta ishga tushirish."""
    if not yes:
        if is_json():
            # JSON rejimida interaktiv prompt yo'q — --yes majburiy
            emit_error(
                "INVALID_INPUT",
                "Reboot uchun --yes/-y flag majburiy (JSON rejimida prompt ishlamaydi).",
            )
            raise typer.Exit(1)
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
        msg = "Router qayta ishga tushirilmoqda..."
        if is_json():
            emit_ok(msg)
        else:
            print_success(msg)
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
