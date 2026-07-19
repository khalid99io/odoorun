from typing import Annotated

import typer
from rich.console import Console

from .common import OutputFormat, render_rows
from .postgres import PostgreSQLError, query, quote_literal

app = typer.Typer(help="Inspect PostgreSQL tables safely.", no_args_is_help=True)


@app.command("list")
def list_tables(
    database: Annotated[
        str,
        typer.Option("--database", "-d", help="Database to inspect."),
    ],
    schema: Annotated[
        str,
        typer.Option("--schema", help="PostgreSQL schema to inspect."),
    ] = "public",
    pattern: Annotated[
        str | None,
        typer.Option("--pattern", help="Table pattern; '*' acts as a wildcard."),
    ] = None,
    output: Annotated[
        OutputFormat,
        typer.Option("--format", help="Output format."),
    ] = OutputFormat.table,
    no_header: Annotated[
        bool,
        typer.Option("--no-header", help="Hide headings in table/plain output."),
    ] = False,
) -> None:
    """List actual tables in a required database and schema."""
    conditions = [f"table_schema = {quote_literal(schema)}"]
    if pattern is not None:
        conditions.append(f"table_name LIKE {quote_literal(pattern.replace('*', '%'))}")
    sql = (
        "SELECT table_schema, table_name, table_type "
        "FROM information_schema.tables WHERE "
        + " AND ".join(conditions)
        + " ORDER BY table_schema, table_name;"
    )
    try:
        values = query(sql, database)
    except PostgreSQLError as error:
        Console(stderr=True).print(
            f"[bold red]Could not list tables in {database}[/bold red]\n{error}"
        )
        raise typer.Exit(1) from None

    rows = [
        {"schema": row[0], "table": row[1], "type": row[2]}
        for row in values
    ]
    render_rows(["schema", "table", "type"], rows, output, no_header)
