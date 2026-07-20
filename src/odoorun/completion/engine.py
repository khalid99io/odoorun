from . import command, database, module


def complete(
    kind: str,
    prefix: str,
    arguments: list[str] | None = None,
) -> list[str]:
    """Return completion candidates for a registered completion kind."""
    if kind == "database":
        return database.complete(prefix)
    if kind == "module":
        return module.complete(prefix, arguments)
    if kind == "command":
        return command.complete(prefix, arguments)
    return []
