import shutil
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.markup import escape
from rich.table import Table

from . import __version__
from .completion.engine import complete as complete_value
from .completion.shell import (
    BASH_COMPLETION,
    BASH_COMPLETION_COMMAND,
    BASH_COMPLETION_SOURCE,
)
from .commands.addon import app as addon_app
from .commands.db import app as db_app
from .discovery import OdooExecutableNotFoundError, find_odoo_executable

HELP_EPILOG = (
    "[bold]Run Odoo[/bold]\n\n"
    "[cyan]odoorun [ODOO_OPTIONS][/cyan] — Forward ordinary options to Odoo."
    "\n\n"
    "[cyan]odoorun -d DATABASE -u MODULE[,MODULE...][/cyan] — Start Odoo and "
    "update modules.\n\n"
    "[cyan]odoorun -a CUSTOM_DIR[,CUSTOM_DIR...] -d DATABASE[/cyan] — Add "
    "custom source-checkout directories.\n\n"
    "[bold]Tool commands[/bold]\n\n"
    "[cyan]odoorun doctor[/cyan] — Check Odoo discovery and the optional psql "
    "client.\n\n"
    "[cyan]odoorun completion MODE[/cyan] (bash or install) — Print or "
    "permanently enable Bash completion.\n\n"
    "[cyan]odoorun db list[/cyan] [--odoo-version VERSION] [--all] "
    "[--format table|plain|json] [--no-header] — List databases and detect "
    "Odoo versions.\n\n"
    "[cyan]odoorun addon list[/cyan] [-d DATABASE] "
    "[--source all|core|custom] [--state all|installed|uninstalled|upgrade] "
    "[--installed] [--custom] [--core] [--addons-path PATHS] [-a PATHS] "
    "[--format table|plain|json] [--no-header] — List filesystem addons and "
    "optional database state.\n\n"
    "[bold]Automatic completion[/bold]\n\n"
    "After [cyan]odoorun completion install[/cyan], press Tab to complete "
    "commands and options, after -d/--database for database names, and after "
    "-u/--update or -i/--init for module names.\n\n"
    "Run [bold]odoorun COMMAND --help[/bold] for detailed command examples."
)

cli = typer.Typer(
    add_completion=False,
    help=(
        "Find the correct Odoo executable, prepare addon paths, and launch "
        "Odoo from source or virtual-environment projects. Arguments that "
        "are not odoorun tool commands are passed to Odoo."
    ),
    epilog=HELP_EPILOG,
    no_args_is_help=True,
    rich_markup_mode="rich",
)
cli.add_typer(db_app, name="db")
cli.add_typer(addon_app, name="addon")


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
    """Launch Odoo or use one of odoorun's inspection/setup commands."""


@cli.command(
    "completion",
    epilog=(
        "Examples:\n\n"
        "  odoorun completion bash\n\n"
        "  odoorun completion install"
    ),
)
def shell_completion(
    mode: Annotated[
        str,
        typer.Argument(
            help=(
                "'bash' prints the integration script; 'install' adds it "
                "idempotently to ~/.bashrc."
            )
        ),
    ] = "bash",
) -> None:
    """Enable Bash completion for commands, options, databases, and modules."""
    if mode == "install":
        bashrc = Path.home() / ".bashrc"
        existing = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
        if BASH_COMPLETION_COMMAND not in existing:
            separator = "" if not existing or existing.endswith("\n") else "\n"
            bashrc.write_text(
                existing + separator + "\n" + BASH_COMPLETION_SOURCE,
                encoding="utf-8",
            )
            typer.echo(f"Bash completion enabled in {bashrc}")
        else:
            typer.echo(f"Bash completion is already enabled in {bashrc}")
        return
    if mode != "bash":
        raise typer.BadParameter("use 'bash' or 'install'")
    typer.echo(BASH_COMPLETION, nl=False)


@cli.command("__complete", hidden=True)
def internal_completion(
    kind: str,
    prefix: Annotated[str, typer.Argument()] = "",
    arguments: Annotated[list[str] | None, typer.Argument()] = None,
) -> None:
    """Return completion candidates for the shell integration."""
    for candidate in complete_value(kind, prefix, arguments):
        typer.echo(candidate)


@cli.command()
def doctor() -> None:
    """Diagnose Odoo executable discovery and PostgreSQL client availability."""
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
