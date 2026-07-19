from pathlib import Path
import shutil


def find_odoo_executable() -> str:
    current = Path.cwd()

    odoo_bin = current / "odoo-bin"

    if odoo_bin.is_file():
        return str(odoo_bin)

    odoo = shutil.which("odoo")

    if odoo:
        return odoo

    raise RuntimeError(
        "Could not locate an Odoo executable."
    )
