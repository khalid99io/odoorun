from __future__ import annotations

import subprocess


def complete(prefix: str) -> list[str]:
    """
    Return PostgreSQL databases matching the given prefix.
    """
    command = [
        "psql",
        "-Atqc",
        "SELECT datname FROM pg_database WHERE datistemplate = false;",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    databases = result.stdout.splitlines()

    return sorted(
        db
        for db in databases
        if db.startswith(prefix)
    )
