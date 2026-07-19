import json
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table


class OutputFormat(str, Enum):
    table = "table"
    plain = "plain"
    json = "json"


def render_rows(
    columns: list[str],
    rows: list[dict[str, str]],
    output: OutputFormat,
    no_header: bool,
) -> None:
    """Render records consistently for humans and shell scripts."""
    if output == OutputFormat.json:
        typer.echo(json.dumps(rows, indent=2))
        return
    if output == OutputFormat.plain:
        if not no_header:
            typer.echo("\t".join(columns))
        for row in rows:
            typer.echo("\t".join(row.get(column, "") for column in columns))
        return

    table = Table(show_header=not no_header)
    for column in columns:
        table.add_column(column.replace("_", " ").title())
    for row in rows:
        table.add_row(*(row.get(column, "") for column in columns))
    Console().print(table)
