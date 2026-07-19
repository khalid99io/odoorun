"""Discover installable Odoo modules for shell completion."""

import os
from pathlib import Path

from ..discovery import find_local_odoo_executable, find_venv_odoo_executable

MANIFEST_NAMES = ("__manifest__.py", "__openerp__.py")


def _option_values(arguments: list[str], option: str) -> list[str] | None:
    """Return comma-separated values for an option, or ``None`` if absent."""
    values: list[str] = []
    found = False
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument == option:
            found = True
            index += 1
            if index < len(arguments):
                values.extend(arguments[index].split(","))
        elif argument.startswith(option + "="):
            found = True
            values.extend(argument.split("=", 1)[1].split(","))
        index += 1
    return values if found else None


def _resolve_paths(values: list[str], base: Path) -> list[Path]:
    paths: list[Path] = []
    for value in values:
        if not value.strip():
            continue
        path = Path(value.strip()).expanduser()
        paths.append(path.resolve() if path.is_absolute() else (base / path).resolve())
    return paths


def _venv_root(current: Path) -> Path | None:
    active = os.environ.get("VIRTUAL_ENV", "").strip()
    if active:
        return Path(active).expanduser().resolve()
    executable = find_venv_odoo_executable(current)
    return Path(executable).parent.parent if executable else None


def _venv_addons(venv: Path) -> list[Path]:
    patterns = (
        "lib/python*/site-packages/odoo/addons",
        "lib/python*/dist-packages/odoo/addons",
        "lib64/python*/site-packages/odoo/addons",
    )
    return [path for pattern in patterns for path in venv.glob(pattern)]


def find_core_addon_paths(start_directory: Path) -> list[Path]:
    """Return addon roots supplied by the Odoo source or installed package."""
    current = start_directory.resolve()
    executable, _ = find_local_odoo_executable(current)
    if executable is not None:
        path = executable.parent / "addons"
        return [path] if path.is_dir() else []
    venv = _venv_root(current)
    return _venv_addons(venv) if venv is not None else []


def find_addon_paths(
    start_directory: Path,
    arguments: list[str],
) -> list[Path]:
    """Resolve effective addon roots from the project, venv, and CLI options."""
    current = start_directory.resolve()
    native = _option_values(arguments, "--addons-path")
    if native is not None:
        return _resolve_paths(native, current)

    paths: list[Path] = []
    executable, _ = find_local_odoo_executable(current)
    if executable is not None:
        repo_root = executable.parent
        paths.append(repo_root / "addons")
        custom = _option_values(arguments, "-a") or []
        paths.extend(_resolve_paths(custom, repo_root.parent))
    else:
        for directory in (current, *current.parents):
            project_addons = directory / "odoo" / "addons"
            if project_addons.is_dir():
                paths.append(project_addons)
                break
        venv = _venv_root(current)
        if venv is not None:
            paths.extend(_venv_addons(venv))

    return list(dict.fromkeys(path for path in paths if path.is_dir()))


def complete(
    prefix: str,
    arguments: list[str] | None = None,
    start_directory: Path | None = None,
) -> list[str]:
    """Return module names matching ``prefix`` from all effective addon roots."""
    modules: set[str] = set()
    for addons in find_addon_paths(
        start_directory or Path.cwd(),
        arguments or [],
    ):
        try:
            children = addons.iterdir()
        except OSError:
            continue
        for child in children:
            if child.name.startswith(prefix) and child.is_dir():
                if any((child / manifest).is_file() for manifest in MANIFEST_NAMES):
                    modules.add(child.name)
    return sorted(modules)
