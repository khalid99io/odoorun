import ast
from enum import Enum
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ..completion.module import (
    MANIFEST_NAMES,
    find_addon_paths,
    find_core_addon_paths,
)
from .common import OutputFormat, render_rows
from .postgres import PostgreSQLError, query

app = typer.Typer(
    help="Inspect addons available to the current project.",
    no_args_is_help=True,
)


class AddonSource(str, Enum):
    all = "all"
    core = "core"
    custom = "custom"


class AddonState(str, Enum):
    all = "all"
    installed = "installed"
    uninstalled = "uninstalled"
    upgrade = "upgrade"


def _manifest_data(directory: Path) -> dict[str, object]:
    for filename in MANIFEST_NAMES:
        path = directory / filename
        if not path.is_file():
            continue
        try:
            value = ast.literal_eval(path.read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, SyntaxError, ValueError):
            return {}
    return {}


def _database_states(database: str) -> dict[str, tuple[str, str]]:
    rows = query(
        "SELECT name, state, COALESCE(latest_version, '') "
        "FROM ir_module_module ORDER BY name;",
        database,
    )
    return {row[0]: (row[1], row[2]) for row in rows}


def _matches_state(actual: str, requested: AddonState) -> bool:
    if requested == AddonState.all:
        return True
    if requested == AddonState.upgrade:
        return actual == "to upgrade"
    return actual == requested.value


@app.command("list")
def list_addons(
    database: Annotated[
        str | None,
        typer.Option("--database", "-d", help="Show module state in this database."),
    ] = None,
    source: Annotated[
        AddonSource,
        typer.Option("--source", help="Filter by core or custom source."),
    ] = AddonSource.all,
    state: Annotated[
        AddonState,
        typer.Option("--state", help="Filter by database installation state."),
    ] = AddonState.all,
    installed: Annotated[
        bool,
        typer.Option("--installed", help="Shortcut for --state installed."),
    ] = False,
    custom: Annotated[
        bool,
        typer.Option("--custom", help="Shortcut for --source custom."),
    ] = False,
    addons_path: Annotated[
        str | None,
        typer.Option("--addons-path", help="Use this native Odoo addons path."),
    ] = None,
    additional: Annotated[
        str | None,
        typer.Option("-a", help="Comma-separated custom addon directories."),
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
    """List addon modules found in the effective addon paths."""
    if installed:
        if state != AddonState.all:
            raise typer.BadParameter("use either --installed or --state, not both")
        state = AddonState.installed
    if custom:
        if source != AddonSource.all:
            raise typer.BadParameter("use either --custom or --source, not both")
        source = AddonSource.custom
    if state != AddonState.all and not database:
        raise typer.BadParameter("--state/--installed requires --database")

    arguments: list[str] = []
    if addons_path is not None:
        arguments.append(f"--addons-path={addons_path}")
    if additional is not None:
        arguments.extend(["-a", additional])

    current = Path.cwd().resolve()
    roots = find_addon_paths(current, arguments)
    core_roots = {path.resolve() for path in find_core_addon_paths(current)}
    states: dict[str, tuple[str, str]] = {}
    if database:
        try:
            states = _database_states(database)
        except PostgreSQLError as error:
            Console(stderr=True).print(
                f"[bold red]Could not inspect database {database}[/bold red]\n{error}"
            )
            raise typer.Exit(1) from None

    records: dict[str, dict[str, str]] = {}
    for root in roots:
        source_name = "core" if root.resolve() in core_roots else "custom"
        if source != AddonSource.all and source.value != source_name:
            continue
        try:
            children = root.iterdir()
        except OSError:
            continue
        for directory in children:
            if not directory.is_dir() or not any(
                (directory / manifest).is_file() for manifest in MANIFEST_NAMES
            ):
                continue
            db_state, db_version = states.get(directory.name, ("unregistered", ""))
            if database and not _matches_state(db_state, state):
                continue
            metadata = _manifest_data(directory)
            records.setdefault(
                directory.name,
                {
                    "addon": directory.name,
                    "source": source_name,
                    "state": db_state if database else "available",
                    "version": db_version or str(metadata.get("version", "")),
                    "path": str(directory),
                },
            )

    render_rows(
        ["addon", "source", "state", "version", "path"],
        [records[name] for name in sorted(records)],
        output,
        no_header,
    )
