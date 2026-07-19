from collections.abc import Callable

from . import database

Completer = Callable[[str], list[str]]

COMPLETERS: dict[str, Completer] = {
    "database": database.complete,
}


def complete(kind: str, prefix: str) -> list[str]:
    """Return completion candidates for a registered completion kind."""
    completer = COMPLETERS.get(kind)
    return completer(prefix) if completer is not None else []
