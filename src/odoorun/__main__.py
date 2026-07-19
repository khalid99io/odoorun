import sys

from .cli import cli
from .runner import run_odoo

ODOORUN_COMMANDS = {
    "doctor",
}


def main() -> None:
    argv = sys.argv[1:]

    if argv and argv[0] in ODOORUN_COMMANDS:
        cli()
        return

    run_odoo(argv)


if __name__ == "__main__":
    main()
