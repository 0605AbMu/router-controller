import sys

# Windows'da stdout/stderr standart cp1252 (charmap) encoding bilan
# ochiladi. PyInstaller bundle'i ichidagi Python interpreter
# PYTHONIOENCODING env var'ni boot vaqtidan keyin qabul qiladi va
# allaqachon ochilgan stream'larga ta'sir qilmaydi. Natija: '✓' va
# boshqa Unicode belgilar bilan UnicodeEncodeError. Yechim: kod ichida
# stream'larni qayta UTF-8'ga sozlash (env var'larsiz, ishonchli).
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass

import typer
from router_controller import __version__
from router_controller.commands import status, devices, firmware, dhcp, reboot, snapshot
from router_controller.commands import wifi, config_cmd

app = typer.Typer(
    name="router",
    help="[bold cyan]TP-Link Router Controller[/bold cyan] — CLI boshqaruv vositasi.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)

# Sub-command guruhlari
app.add_typer(wifi.app, name="wifi")
app.add_typer(config_cmd.app, name="config")

# Oddiy buyruqlar
app.command("status")(status.command)
app.command("devices")(devices.command)
app.command("firmware")(firmware.command)
app.command("dhcp")(dhcp.command)
app.command("reboot")(reboot.command)
app.command("snapshot")(snapshot.command)


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"router-controller v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Versiyani ko'rsatish.",
    ),
) -> None:
    pass


if __name__ == "__main__":
    app()
