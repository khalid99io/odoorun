import os

from .discovery import find_odoo_executable


def run_odoo(args: list[str]) -> None:
    executable = find_odoo_executable()

    command = [
        executable,
        *args,
    ]

    os.execvp(executable, command)
