"""Complete odoorun commands, options, and fixed option values."""

ROOT_CANDIDATES = (
    "completion",
    "doctor",
    "db",
    "addon",
    "--version",
    "--help",
)

GROUP_CANDIDATES = {
    "db": ("list", "--help"),
    "addon": ("list", "--help"),
}

COMMAND_OPTIONS = {
    ("doctor",): ("--help",),
    ("db", "list"): (
        "--odoo-version",
        "--all",
        "--format",
        "--no-header",
        "--help",
    ),
    ("addon", "list"): (
        "--database",
        "-d",
        "--source",
        "--state",
        "--installed",
        "--custom",
        "--core",
        "--addons-path",
        "-a",
        "--format",
        "--no-header",
        "--help",
    ),
}

OPTION_VALUES = {
    ("db", "list"): {
        "--format": ("table", "plain", "json"),
    },
    ("addon", "list"): {
        "--source": ("all", "core", "custom"),
        "--state": ("all", "installed", "uninstalled", "upgrade"),
        "--format": ("table", "plain", "json"),
    },
}

OPTION_ALIASES = {
    ("addon", "list"): (
        ("--database", "-d"),
        ("--source", "--custom", "--core"),
    ),
}


def _matching(candidates: tuple[str, ...], prefix: str) -> list[str]:
    return [candidate for candidate in candidates if candidate.startswith(prefix)]


def _option_was_used(option: str, arguments: list[str]) -> bool:
    return any(
        argument == option or argument.startswith(option + "=")
        for argument in arguments
    )


def _available_options(path: tuple[str, ...], arguments: list[str]) -> tuple[str, ...]:
    options = COMMAND_OPTIONS[path]
    used_aliases = {
        alias
        for aliases in OPTION_ALIASES.get(path, ())
        if any(_option_was_used(alias, arguments) for alias in aliases)
        for alias in aliases
    }
    return tuple(
        option
        for option in options
        if option not in used_aliases and not _option_was_used(option, arguments)
    )


def _complete_command_options(
    path: tuple[str, ...],
    prefix: str,
    arguments: list[str],
) -> list[str]:
    values = OPTION_VALUES.get(path, {})
    previous = arguments[-1] if arguments else ""
    if previous in values:
        return _matching(values[previous], prefix)

    if "=" in prefix:
        option, value_prefix = prefix.split("=", 1)
        if option in values:
            return [
                f"{option}={value}"
                for value in values[option]
                if value.startswith(value_prefix)
            ]

    if prefix and not prefix.startswith("-"):
        return []
    return _matching(_available_options(path, arguments), prefix)


def complete(prefix: str, arguments: list[str] | None = None) -> list[str]:
    """Return candidates valid after the already-completed CLI arguments."""
    completed = arguments or []
    if not completed:
        return _matching(ROOT_CANDIDATES, prefix)

    root = completed[0]
    if root == "completion":
        if len(completed) == 1:
            return _matching(("bash", "install", "--help"), prefix)
        return []
    if root == "doctor":
        return _complete_command_options(("doctor",), prefix, completed[1:])
    if root not in GROUP_CANDIDATES:
        return []
    if len(completed) == 1:
        return _matching(GROUP_CANDIDATES[root], prefix)
    if completed[1] != "list":
        return []

    path = (root, "list")
    return _complete_command_options(path, prefix, completed[2:])
