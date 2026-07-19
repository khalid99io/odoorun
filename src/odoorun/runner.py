import os
from pathlib import Path
from typing import NoReturn

from .discovery import find_odoo_executable


class OdooExecutionError(RuntimeError):
    """Raised when a discovered Odoo executable cannot be started."""

    def __init__(self, executable: str, reason: str) -> None:
        self.executable = executable
        self.reason = reason
        super().__init__(f"Could not start {executable}: {reason}")


class OdooArgumentError(RuntimeError):
    """Raised when odoorun cannot construct a valid Odoo command."""


def _custom_addons(args: list[str]) -> tuple[list[str], list[str]]:
    """Remove odoorun's ``-a`` option and return its comma-separated values."""
    forwarded: list[str] = []
    custom: list[str] = []
    index = 0
    while index < len(args):
        value = args[index]
        if value in {"-a", "--addons-path"}:
            index += 1
            if index == len(args) or not args[index].strip():
                raise OdooArgumentError(f"{value} requires a comma-separated path list")
            custom.extend(part.strip() for part in args[index].split(",") if part.strip())
        elif value.startswith("-a=") or value.startswith("--addons-path="):
            custom.extend(part.strip() for part in value.split("=", 1)[1].split(",") if part.strip())
        else:
            forwarded.append(value)
        index += 1
    return forwarded, custom


def build_odoo_args(executable: str, args: list[str]) -> list[str]:
    """Add context-specific addon paths and validate custom addon folders."""
    forwarded, custom = _custom_addons(args)
    if Path(executable).name != "odoo-bin":
        if not any(arg == "--addons" or arg.startswith("--addons=") for arg in forwarded):
            forwarded.insert(0, "--addons=odoo/addons")
        return forwarded

    repo_root = Path(executable).parent
    addons = repo_root / "addons"
    if not addons.is_dir():
        raise OdooArgumentError(f"Odoo addons directory not found: {addons}")
    paths = [str(addons)]
    for item in custom:
        candidate = Path(item).expanduser()
        if not candidate.is_absolute():
            candidate = repo_root.parent / candidate
        if not candidate.is_dir():
            raise OdooArgumentError(f"Custom addons directory not found: {candidate}")
        paths.append(str(candidate))
    return ["--addons-path=" + ",".join(paths), *forwarded]


def run_odoo(args: list[str]) -> NoReturn:
    """Replace the current process with Odoo and forward all arguments."""
    executable = find_odoo_executable()
    command = [executable, *build_odoo_args(executable, args)]

    try:
        os.execv(executable, command)
    except OSError as error:
        raise OdooExecutionError(executable, error.strerror or str(error)) from error
