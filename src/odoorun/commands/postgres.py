import subprocess

FIELD_SEPARATOR = "\x1f"
QUERY_TIMEOUT_SECONDS = 10


class PostgreSQLError(RuntimeError):
    """Raised when a read-only PostgreSQL query cannot be completed."""


def query(
    sql: str,
    database: str | None = None,
    timeout: int = QUERY_TIMEOUT_SECONDS,
) -> list[list[str]]:
    """Execute a read-only query through psql and return unaligned rows."""
    command = ["psql", "-XAtq", "-F", FIELD_SEPARATOR, "-v", "ON_ERROR_STOP=1"]
    if database:
        command.extend(["-d", database])
    command.extend(["-c", sql])
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
            timeout=timeout,
        )
    except FileNotFoundError as error:
        raise PostgreSQLError("psql is not installed or is not on PATH") from error
    except subprocess.TimeoutExpired as error:
        raise PostgreSQLError("PostgreSQL query timed out") from error
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or str(error)).strip()
        raise PostgreSQLError(detail) from error
    except (OSError, UnicodeError) as error:
        raise PostgreSQLError(str(error)) from error

    return [line.split(FIELD_SEPARATOR) for line in result.stdout.splitlines() if line]


def quote_literal(value: str) -> str:
    """Quote a string as a PostgreSQL text literal."""
    return "'" + value.replace("'", "''") + "'"
