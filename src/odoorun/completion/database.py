from __future__ import annotations

import subprocess

QUERY_TIMEOUT_SECONDS = 2


def complete(prefix: str) -> list[str]:
    """Return PostgreSQL databases matching ``prefix``.

    Completion must stay responsive, so unavailable or slow PostgreSQL
    connections are treated as having no suggestions.
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
            timeout=QUERY_TIMEOUT_SECONDS,
        )
    except (subprocess.SubprocessError, OSError, UnicodeError):
        return []

    return sorted(
        {
            database
            for database in result.stdout.splitlines()
            if database and database.startswith(prefix)
        }
    )
