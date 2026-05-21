from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

console = Console()


def print_success(msg: str) -> None:
    console.print(f"[bold green]✓[/bold green] {msg}")


def print_error(msg: str) -> None:
    console.print(f"[bold red]✗[/bold red] {msg}")


def print_warning(msg: str) -> None:
    console.print(f"[bold yellow]![/bold yellow] {msg}")


def print_info(msg: str) -> None:
    console.print(f"[bold cyan]i[/bold cyan] {msg}")


def _band_label(connection_type: str) -> str:
    t = str(connection_type)
    if "2g" in t.lower() or "2G" in t:
        return "[cyan]2.4 GHz[/cyan]"
    elif "5g" in t.lower() or "5G" in t:
        return "[magenta]5 GHz[/magenta]"
    elif "wired" in t.lower():
        return "[blue]Kabel[/blue]"
    return "[dim]Noma'lum[/dim]"


def _speed_fmt(bps: int) -> str:
    if bps == 0:
        return "[dim]—[/dim]"
    if bps < 1024:
        return f"{bps} B/s"
    if bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    return f"{bps / 1024 / 1024:.1f} MB/s"


def print_status_panel(status, ipv4, firmware) -> None:
    wifi_2g = "[green]Yoqilgan[/green]" if status.wifi_2g_enable else "[red]O'chirilgan[/red]"
    wifi_5g = "[green]Yoqilgan[/green]" if status.wifi_5g_enable else "[red]O'chirilgan[/red]"

    general = (
        f"  [bold]Model:[/bold]       {firmware.model}\n"
        f"  [bold]Hardware:[/bold]    {firmware.hardware_version}\n"
        f"  [bold]Firmware:[/bold]    {firmware.firmware_version}\n"
    )

    network = (
        f"  [bold]WAN IP:[/bold]      {status.wan_ipv4_addr}\n"
        f"  [bold]LAN IP:[/bold]      {status.lan_ipv4_addr}\n"
        f"  [bold]Gateway:[/bold]     {status.wan_ipv4_gateway}\n"
    )

    wifi = (
        f"  [bold]2.4 GHz:[/bold]     {wifi_2g}\n"
        f"  [bold]5 GHz:[/bold]       {wifi_5g}\n"
    )

    clients = (
        f"  [bold]Jami:[/bold]        {status.clients_total}\n"
        f"  [bold]WiFi:[/bold]        {status.wifi_clients_total}\n"
        f"  [bold]Kabel:[/bold]       {status.wired_total}\n"
        f"  [bold]Mehmon:[/bold]      {status.guest_clients_total}\n"
    )

    console.print()
    console.print(Panel(general.rstrip(), title="[bold]Router", border_style="blue", expand=False))
    console.print(Panel(network.rstrip(), title="[bold]Tarmoq", border_style="cyan", expand=False))
    console.print(Panel(wifi.rstrip(), title="[bold]WiFi", border_style="magenta", expand=False))
    console.print(Panel(clients.rstrip(), title="[bold]Qurilmalar", border_style="green", expand=False))
    console.print()


def print_devices_table(devices: list) -> None:
    table = Table(
        title="Ulangan qurilmalar",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Nomi", min_width=18)
    table.add_column("IP manzil", min_width=15)
    table.add_column("MAC manzil", min_width=19)
    table.add_column("Ulanish", min_width=10)
    table.add_column("Yuklab olish", min_width=12, justify="right")
    table.add_column("Yuklash", min_width=12, justify="right")

    active = [d for d in devices if d.active]
    inactive = [d for d in devices if not d.active]

    for i, device in enumerate(active + inactive, 1):
        name = device.hostname or "[dim]Nomsiz[/dim]"
        ip = str(device.ipaddress) if device.ipaddress else "[dim]—[/dim]"
        mac = str(device.macaddress) if device.macaddress else "[dim]—[/dim]"
        band = _band_label(device.type)
        dl = _speed_fmt(device.down_speed or 0)
        ul = _speed_fmt(device.up_speed or 0)

        if not device.active:
            name = f"[dim]{device.hostname or 'Nomsiz'}[/dim]"
            ip = f"[dim]{ip}[/dim]"
            mac = f"[dim]{mac}[/dim]"
            band = "[dim]Oflayn[/dim]"

        table.add_row(str(i), name, ip, mac, band, dl, ul)

    console.print()
    console.print(table)
    console.print(
        f"  Jami: [bold]{len(active)}[/bold] faol, "
        f"[dim]{len(inactive)} oflayn[/dim]\n"
    )


def print_wifi_status(status) -> None:
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Band", min_width=10)
    table.add_column("Host WiFi", min_width=14)
    table.add_column("Mehmon WiFi", min_width=14)

    def on_off(val):
        if val is None:
            return "[dim]—[/dim]"
        return "[green]Yoqilgan[/green]" if val else "[red]O'chirilgan[/red]"

    table.add_row("2.4 GHz", on_off(status.wifi_2g_enable), on_off(status.guest_2g_enable))
    table.add_row("5 GHz", on_off(status.wifi_5g_enable), on_off(status.guest_5g_enable))

    console.print()
    console.print(table)
    console.print()


def print_firmware(firmware) -> None:
    lines = (
        f"  [bold]Model:[/bold]       {firmware.model}\n"
        f"  [bold]Hardware:[/bold]    {firmware.hardware_version}\n"
        f"  [bold]Firmware:[/bold]    {firmware.firmware_version}\n"
    )
    console.print()
    console.print(Panel(lines.rstrip(), title="[bold]Firmware", border_style="blue", expand=False))
    console.print()


def print_dhcp_table(leases: list) -> None:
    table = Table(
        title="DHCP ro'yxati",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Hostname", min_width=20)
    table.add_column("IP manzil", min_width=15)
    table.add_column("MAC manzil", min_width=19)
    table.add_column("Tugash vaqti", min_width=16)

    for i, lease in enumerate(leases, 1):
        table.add_row(
            str(i),
            lease.hostname or "[dim]—[/dim]",
            str(lease.ipaddress),
            str(lease.macaddress),
            str(lease.lease_time),
        )

    console.print()
    console.print(table)
    console.print(f"  Jami: [bold]{len(leases)}[/bold] ta qurilma\n")


def print_channel_info(band: str, channel: int) -> None:
    label = "[yellow]Avtomatik[/yellow]" if channel == 0 else f"[bold]{channel}[/bold]"
    console.print(f"  {band}: channel {label}")
