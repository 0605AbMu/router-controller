from typing import Optional
import typer
from router_controller.config import Config, STORAGE_FILE, STORAGE_KEYRING
from router_controller.utils.display import console, print_success, print_error, print_warning
from router_controller.utils.output import is_json, emit_data, emit_ok, emit_error

app = typer.Typer(help="Konfiguratsiya boshqarish.", no_args_is_help=True)


def _config_dict(cfg: Config) -> dict:
    return {
        "configured": cfg.is_configured(),
        "host": cfg.get_host(),
        "username": cfg.get_username(),
        "password_saved": bool(cfg.get_password()) if cfg.is_configured() else False,
        "storage": cfg.get_storage(),
    }


@app.command("set")
def config_set(
    host: Optional[str] = typer.Option(
        None, "--host", "-h",
        help="Router manzili. Misol: http://192.168.0.1",
    ),
    password: Optional[str] = typer.Option(
        None, "--password", "-p",
        help="Router paroli.",
    ),
    username: Optional[str] = typer.Option(
        None, "--username", "-u",
        help="Router foydalanuvchi nomi (odatda 'admin').",
    ),
    storage: Optional[str] = typer.Option(
        None, "--storage",
        help=f"Parolni saqlash usuli: {STORAGE_FILE} (default, chmod 600) "
             f"yoki {STORAGE_KEYRING} (OS keychain). macOS da keychain har safar so'rashi mumkin.",
    ),
):
    """Router ulanish sozlamalarini saqlash."""
    cfg = Config()

    if storage:
        try:
            cfg.set_storage(storage)
        except (ValueError, RuntimeError) as e:
            if is_json():
                emit_error("INVALID_INPUT", str(e))
            else:
                print_error(str(e))
            raise typer.Exit(1)

    if not host:
        if is_json():
            emit_error("INVALID_INPUT", "--host majburiy (JSON rejimida prompt ishlamaydi).")
            raise typer.Exit(1)
        host = typer.prompt("Router manzili (misol: http://192.168.0.1)")
    if not password:
        if is_json():
            emit_error("INVALID_INPUT", "--password majburiy (JSON rejimida prompt ishlamaydi).")
            raise typer.Exit(1)
        password = typer.prompt("Parol", hide_input=True)

    cfg.set_host(host.rstrip("/"))
    cfg.set_password(password)

    if username:
        cfg.set_username(username)

    msg = (
        f"Saqlandi! Host: {cfg.get_host()}, Username: {cfg.get_username()}, "
        f"Storage: {cfg.get_storage()}"
    )
    if is_json():
        emit_ok(msg, data=_config_dict(cfg))
    else:
        print_success(msg)


@app.command("show")
def config_show():
    """Hozirgi konfiguratsiyani ko'rsatish."""
    cfg = Config()

    if is_json():
        emit_data(_config_dict(cfg))
        return

    console.print()
    if not cfg.is_configured():
        print_warning("Konfiguratsiya topilmadi. `router config set` bilan sozlang.")
        console.print()
        return

    has_pass = bool(cfg.get_password())
    console.print(f"  [bold]Host:[/bold]      {cfg.get_host()}")
    console.print(f"  [bold]Username:[/bold]  {cfg.get_username()}")
    console.print(f"  [bold]Parol:[/bold]     {'[green]saqlangan[/green]' if has_pass else '[red]topilmadi[/red]'}")
    console.print(f"  [bold]Storage:[/bold]   {cfg.get_storage()}")
    console.print()


@app.command("clear")
def config_clear(
    yes: bool = typer.Option(False, "--yes", "-y", help="Tasdiqlash so'ramasdan o'chirish."),
):
    """Barcha saqlangan sozlamalarni o'chirish."""
    if not yes:
        if is_json():
            emit_error("INVALID_INPUT", "--yes/-y majburiy (JSON rejimida prompt ishlamaydi).")
            raise typer.Exit(1)
        confirmed = typer.confirm("Barcha konfiguratsiya o'chiriladi. Davom ettirasizmi?")
        if not confirmed:
            console.print("Bekor qilindi.")
            raise typer.Exit(0)
    Config().clear()
    msg = "Konfiguratsiya o'chirildi."
    if is_json():
        emit_ok(msg)
    else:
        print_success(msg)
