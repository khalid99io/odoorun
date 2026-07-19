from . import database

COMPLETERS = {
    "database": database.complete,
}


def complete(kind: str, prefix: str) -> list[str]:
    completer = COMPLETERS.get(kind)

    if completer is None:
        return []

    return completer(prefix)
