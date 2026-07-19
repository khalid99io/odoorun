from typing import Annotated

import typer
from rich.console import Console

from .common import OutputFormat, render_rows
from .postgres import PostgreSQLError, query

app = typer.Typer(
    help="List PostgreSQL databases and identify Odoo database versions.",
    epilog=(
        "Examples:\n"
        "  odoorun db list\n"
        "  odoorun db list --odoo-version 19\n"
        "  odoorun db list --all --format json"
    ),
    no_args_is_help=True,
)


def _inspect_database(database: str) -> tuple[str, str]:
    """Return the database kind and detected Odoo version."""
    try:
        marker = query(
            "SELECT COALESCE(to_regclass('public.ir_module_module')::text, '');",
            database,
        )
        if not marker or not marker[0][0]:
            return "postgresql", ""
        version = query(
            "SELECT COALESCE(latest_version, '') "
            "FROM ir_module_module WHERE name = 'base' LIMIT 1;",
            database,
        )
        return "odoo", version[0][0] if version else "unknown"
    except PostgreSQLError:
        return "inaccessible", ""


@app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  odoorun db list\n\n"
        "  odoorun db list --odoo-version 19\n\n"
        "  odoorun db list --all --format json"
    ),
)
def list_databases(
    odoo_version: Annotated[
        str | None,
        typer.Option(
            "--odoo-version",
            help=(
                "Only show Odoo databases whose base-module version starts "
                "with this value (for example, 19 or 19.0)."
            ),
        ),
    ] = None,
    all_databases: Annotated[
        bool,
        typer.Option(
            "--all",
            help="Also show regular PostgreSQL and inaccessible databases.",
        ),
    ] = False,
    output: Annotated[
        OutputFormat,
        typer.Option(
            "--format",
            help="Render a Rich table, tab-separated plain text, or JSON.",
        ),
    ] = OutputFormat.table,
    no_header: Annotated[
        bool,
        typer.Option(
            "--no-header",
            help="Hide column headings in table and plain output.",
        ),
    ] = False,
) -> None:
    """List Odoo databases and detect versions from their installed base module.

    By default, regular PostgreSQL databases and databases that cannot be
    inspected are hidden. Use --all to include them.
    """
    try:
        names = query(
            "SELECT datname FROM pg_database "
            "WHERE datistemplate = false AND datallowconn = true ORDER BY datname;"
        )
    except PostgreSQLError as error:
        Console(stderr=True).print(
            f"[bold red]Database listing failed[/bold red]\n{error}"
        )
        raise typer.Exit(1) from None

    rows: list[dict[str, str]] = []
    for values in names:
        database = values[0]
        kind, version = _inspect_database(database)
        if not all_databases and kind != "odoo":
            continue
        if odoo_version and (
            kind != "odoo" or not version.startswith(odoo_version)
        ):
            continue
        rows.append({"database": database, "type": kind, "odoo_version": version})

    render_rows(["database", "type", "odoo_version"], rows, output, no_header)
