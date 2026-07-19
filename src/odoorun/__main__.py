import sys

from rich.console import Console
from rich.markup import escape

from .cli import cli
from .discovery import OdooExecutableNotFoundError
from .runner import OdooArgumentError, OdooExecutionError, run_odoo

ODOORUN_ARGUMENTS = {
    "--help",
    "--version",
    "-h",
    "doctor",
}

error_console = Console(stderr=True)


def show_odoo_not_found(error: OdooExecutableNotFoundError) -> None:
    error_console.print()
    error_console.print("[bold red]Odoo executable not found[/bold red]")
    error_console.print(
        "odoorun looked for [bold]odoo-bin[/bold] in "
        f"[cyan]{escape(str(error.directory))}[/cyan] or its parents, and "
        "[bold]odoo[/bold] on your PATH."
    )
    error_console.print()
    error_console.print("[bold]Try one of these:[/bold]")

    if error.non_executable is not None:
        candidate = escape(str(error.non_executable))
        error_console.print(
            f"  • Make [cyan]{candidate}[/cyan] executable with "
            f"[bold]chmod +x {candidate}[/bold]."
        )
    else:
        error_console.print(
            "  • Run [bold]odoorun[/bold] from inside an Odoo source directory."
        )

    error_console.print("  • Install Odoo or add its executable to your PATH.")


def show_execution_error(error: OdooExecutionError) -> None:
    error_console.print()
    error_console.print("[bold red]Odoo could not be started[/bold red]")
    error_console.print(
        f"[cyan]{escape(error.executable)}[/cyan]: {escape(error.reason)}"
    )
    error_console.print("Check the file permissions and try again.")


def show_argument_error(error: OdooArgumentError) -> None:
    error_console.print()
    error_console.print("[bold red]Invalid Odoo addons configuration[/bold red]")
    error_console.print(f"[yellow]{escape(str(error))}[/yellow]")


def main() -> None:
    argv = sys.argv[1:]

    if argv and argv[0] in ODOORUN_ARGUMENTS:
        cli(args=argv, prog_name="odoorun")
        return

    try:
        run_odoo(argv)
    except OdooExecutableNotFoundError as error:
        show_odoo_not_found(error)
        raise SystemExit(1) from None
    except OdooExecutionError as error:
        show_execution_error(error)
        raise SystemExit(1) from None
    except OdooArgumentError as error:
        show_argument_error(error)
        raise SystemExit(2) from None


if __name__ == "__main__":
    main()
