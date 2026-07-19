import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from . import __version__
from .discovery import OdooExecutableNotFoundError, find_odoo_executable

cli = typer.Typer(
    add_completion=False,
    help="Run Odoo from any directory inside an Odoo project.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)


def show_version(value: bool) -> None:
    if value:
        typer.echo(f"odoorun {__version__}")
        raise typer.Exit()


@cli.callback()
def root(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=show_version,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
) -> None:
    """Inspect the environment or pass arguments directly to Odoo."""


@cli.command()
def doctor() -> None:
    """Check whether odoorun can locate its external dependencies."""
    console = Console()
    current = Path.cwd().resolve()
    psql = shutil.which("psql")

    try:
        executable = find_odoo_executable(current)
        odoo_status = f"[green]found[/green] — {escape(executable)}"
        healthy = True
    except OdooExecutableNotFoundError as error:
        if error.non_executable is not None:
            detail = f"not executable — {escape(str(error.non_executable))}"
        else:
            detail = "not found"
        odoo_status = f"[red]{detail}[/red]"
        healthy = False

    table = Table(title="odoorun doctor", show_header=False, box=None)
    table.add_column(style="bold")
    table.add_column()
    table.add_row("Working directory", escape(str(current)))
    table.add_row("Odoo", odoo_status)
    table.add_row(
        "PostgreSQL client",
        (
            f"[green]found[/green] — {escape(psql)}"
            if psql
            else "[yellow]not found[/yellow]"
        ),
    )
    console.print(table)

    if not healthy:
        console.print(
            "\n[red]Odoo is not ready.[/red] Run this command inside an Odoo "
            "checkout or add [bold]odoo[/bold] to your PATH."
        )
        raise typer.Exit(1)

    if psql is None:
        console.print(
            "\n[yellow]Odoo is ready, but database completion requires psql.[/yellow]"
        )
    else:
        console.print("\n[green]Everything looks ready.[/green]")
