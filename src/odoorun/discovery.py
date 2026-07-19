import os
import shutil
from pathlib import Path


class OdooExecutableNotFoundError(RuntimeError):
    """Raised when no runnable Odoo executable can be discovered."""

    def __init__(
        self,
        directory: Path,
        non_executable: Path | None = None,
    ) -> None:
        self.directory = directory
        self.non_executable = non_executable
        super().__init__("Could not locate an Odoo executable.")


def find_local_odoo_executable(
    start_directory: Path,
) -> tuple[Path | None, Path | None]:
    """Find an executable ``odoo-bin`` in a directory or one of its parents.

    The second item is the nearest non-executable candidate, when one exists.
    """
    non_executable: Path | None = None

    for directory in (start_directory, *start_directory.parents):
        candidate = directory / "odoo-bin"

        if not candidate.is_file():
            continue

        if os.access(candidate, os.X_OK):
            return candidate, non_executable

        if non_executable is None:
            non_executable = candidate

    return None, non_executable


def _venv_names(project_name: str) -> tuple[str, ...]:
    """Return likely virtual-environment names for a project directory."""
    names = [project_name]
    if project_name.endswith("-2"):
        names.append(f"{project_name[:-2]}-v2")
    elif project_name.endswith("-v2"):
        names.append(f"{project_name[:-3]}-2")
    return tuple(dict.fromkeys(names))


def find_venv_odoo_executable(start_directory: Path) -> str | None:
    """Find ``odoo`` in the conventional ``~/venvs/<project>/bin`` location.

    This is the process-local equivalent of sourcing an activation script:
    invoking the executable from the venv gives Odoo the correct interpreter
    and environment without attempting to modify the caller's shell.
    """
    venv_root = Path.home() / "venvs"
    for directory in (start_directory, *start_directory.parents):
        for name in _venv_names(directory.name):
            candidate = venv_root / name / "bin" / "odoo"
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
    return None


def find_odoo_executable(start_directory: Path | None = None) -> str:
    """Return the best available Odoo executable.

    A project-local ``odoo-bin`` takes precedence over an ``odoo`` command on
    ``PATH``. Parent directories are searched so the command also works from
    inside an add-on or another nested project directory.
    """
    current = (start_directory or Path.cwd()).resolve()
    local_executable, non_executable = find_local_odoo_executable(current)

    if local_executable is not None:
        return str(local_executable)

    venv_executable = find_venv_odoo_executable(current)
    if venv_executable is not None:
        return venv_executable

    path_executable = shutil.which("odoo")

    if path_executable is not None:
        return path_executable

    raise OdooExecutableNotFoundError(current, non_executable)
