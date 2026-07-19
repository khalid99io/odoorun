import os
from typing import NoReturn

from .discovery import find_odoo_executable


class OdooExecutionError(RuntimeError):
    """Raised when a discovered Odoo executable cannot be started."""

    def __init__(self, executable: str, reason: str) -> None:
        self.executable = executable
        self.reason = reason
        super().__init__(f"Could not start {executable}: {reason}")


def run_odoo(args: list[str]) -> NoReturn:
    """Replace the current process with Odoo and forward all arguments."""
    executable = find_odoo_executable()
    command = [executable, *args]

    try:
        os.execv(executable, command)
    except OSError as error:
        raise OdooExecutionError(executable, error.strerror or str(error)) from error
