"""Console UI helpers."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()


def info(message: str) -> None:
    console.print(f"[cyan]{message}[/cyan]")


def success(message: str) -> None:
    console.print(f"[green]{message}[/green]")


def warning(message: str) -> None:
    console.print(f"[yellow]{message}[/yellow]")


def error(message: str) -> None:
    console.print(f"[red]{message}[/red]")


def render_result(result) -> None:
    console.print(
        f"[bold]{result.action}[/bold]: success={result.success}, failed={result.failed}, skipped={result.skipped}"
    )
    for err in result.errors[:20]:
        console.print(f"  [red]{err}[/red]")
    if len(result.errors) > 20:
        console.print(f"  [red]... {len(result.errors) - 20} more errors[/red]")


def render_guilds(guilds) -> None:
    table = Table(title="Guilds")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Members", justify="right")
    for guild in guilds:
        table.add_row(str(guild.id), guild.name, str(guild.member_count))
    console.print(table)


def render_channels(channels) -> None:
    table = Table(title="Channels")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Type")
    for channel in channels:
        table.add_row(str(channel.id), channel.name, str(channel.type))
    console.print(table)


def render_roles(roles) -> None:
    table = Table(title="Roles")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Position", justify="right")
    for role in roles:
        table.add_row(str(role.id), role.name, str(role.position))
    console.print(table)


def ask(prompt: str, default: str | None = None) -> str:
    return Prompt.ask(prompt, default=default)


def confirm(prompt: str, default: bool = False) -> bool:
    return Confirm.ask(prompt, default=default)


def menu(title: str, options: list[tuple[str, str]]) -> None:
    table = Table(title=f"[bold magenta]{title}[/bold magenta]", border_style="bright_magenta", header_style="bold cyan")
    table.add_column("Key", style="bold yellow", justify="center", width=6)
    table.add_column("Action", style="white")
    for key, label in options:
        table.add_row(key, label)
    console.print(table)


def banner() -> None:
    console.print(
        Panel.fit(
            "[bold red]██████╗  █████╗ ██████╗ ██╗  ██╗[/bold red]\n"
            "[bold red]██╔══██╗██╔══██╗██╔══██╗██║ ██╔╝[/bold red]\n"
            "[bold red]██║  ██║███████║██████╔╝█████╔╝ [/bold red]\n"
            "[bold red]██║  ██║██╔══██║██╔══██╗██╔═██╗ [/bold red]\n"
            "[bold red]██████╔╝██║  ██║██║  ██║██║  ██╗[/bold red]\n"
            "[bold red]╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝[/bold red]\n"
            "[bold magenta]███╗   ██╗██╗   ██╗██╗  ██╗███████╗██████╗ [/bold magenta]\n"
            "[bold magenta]████╗  ██║██║   ██║██║ ██╔╝██╔════╝██╔══██╗[/bold magenta]\n"
            "[bold magenta]██╔██╗ ██║██║   ██║█████╔╝ █████╗  ██████╔╝[/bold magenta]\n"
            "[bold magenta]██║╚██╗██║██║   ██║██╔═██╗ ██╔══╝  ██╔══██╗[/bold magenta]\n"
            "[bold magenta]██║ ╚████║╚██████╔╝██║  ██╗███████╗██║  ██║[/bold magenta]\n"
            "[bold magenta]╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝[/bold magenta]\n"
            "[bold cyan]DARK NUKER — ultra advanced[/bold cyan]\n"
            "[bold yellow]Developed by Mahdi[/bold yellow]",
            border_style="red",
        )
    )
