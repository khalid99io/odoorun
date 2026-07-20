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
    help="List addon manifests from project, source, venv, or explicit paths.",
    epilog=(
        "Examples:\n"
        "  odoorun addon list\n"
        "  odoorun addon list --custom\n"
        "  odoorun addon list --core\n"
        "  odoorun addon list -d demo --installed --custom\n"
        "  odoorun addon list --addons-path addons,../enterprise"
    ),
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


@app.command(
    "list",
    epilog=(
        "Examples:\n\n"
        "  odoorun addon list --custom\n\n"
        "  odoorun addon list --core\n\n"
        "  odoorun addon list -d demo --installed --custom\n\n"
        "  odoorun addon list --addons-path addons,../enterprise"
    ),
)
def list_addons(
    database: Annotated[
        str | None,
        typer.Option(
            "--database",
            "-d",
            help=(
                "Query ir_module_module in this database and show each "
                "filesystem addon's installation state."
            ),
        ),
    ] = None,
    source: Annotated[
        AddonSource,
        typer.Option(
            "--source",
            help="Show all addons, Odoo core addons, or project/custom addons.",
        ),
    ] = AddonSource.all,
    state: Annotated[
        AddonState,
        typer.Option(
            "--state",
            help=(
                "Filter by database state; installed/uninstalled/upgrade "
                "requires -d/--database."
            ),
        ),
    ] = AddonState.all,
    installed: Annotated[
        bool,
        typer.Option(
            "--installed",
            help="Show installed filesystem addons; shortcut requiring -d.",
        ),
    ] = False,
    custom: Annotated[
        bool,
        typer.Option(
            "--custom",
            help="Show only project/custom addons; shortcut for --source custom.",
        ),
    ] = False,
    core: Annotated[
        bool,
        typer.Option(
            "--core",
            help="Show only Odoo core addons; shortcut for --source core.",
        ),
    ] = False,
    addons_path: Annotated[
        str | None,
        typer.Option(
            "--addons-path",
            help=(
                "Override automatic discovery with a comma-separated native "
                "Odoo addons path."
            ),
        ),
    ] = None,
    additional: Annotated[
        str | None,
        typer.Option(
            "-a",
            help=(
                "Add comma-separated custom directories. Relative paths use "
                "the parent of an Odoo source checkout."
            ),
        ),
    ] = None,
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
    """List filesystem addons containing an Odoo manifest.

    Discovery uses the current source checkout, linked virtual environment,
    project odoo/addons directory, or explicit path options. Supplying -d does
    not find addons in a database; it annotates discovered addons with their
    ir_module_module state and enables --state/--installed filtering.
    """
    if installed:
        if state != AddonState.all:
            raise typer.BadParameter("use either --installed or --state, not both")
        state = AddonState.installed
    source_shortcuts = [
        value
        for enabled, value in (
            (custom, AddonSource.custom),
            (core, AddonSource.core),
        )
        if enabled
    ]
    if source_shortcuts:
        if source != AddonSource.all or len(source_shortcuts) > 1:
            raise typer.BadParameter(
                "use only one of --source, --custom, or --core"
            )
        source = source_shortcuts[0]
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
