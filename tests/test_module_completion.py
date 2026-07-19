import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from odoorun.completion import module


class ModuleCompletionTests(unittest.TestCase):
    def make_module(self, addons: Path, name: str) -> None:
        directory = addons / name
        directory.mkdir(parents=True)
        (directory / "__manifest__.py").write_text("{}\n", encoding="utf-8")

    def test_completes_source_and_custom_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            parent = Path(temporary_directory)
            repo = parent / "odoo"
            executable = repo / "odoo-bin"
            executable.parent.mkdir()
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            self.make_module(repo / "addons", "sale_management")
            self.make_module(parent / "custom-addons", "sale_custom")

            result = module.complete(
                "sale_", ["-a", "custom-addons"], start_directory=repo
            )

            self.assertEqual(result, ["sale_custom", "sale_management"])

    def test_native_addons_path_controls_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            project = Path(temporary_directory)
            self.make_module(project / "preferred", "stock_custom")

            result = module.complete(
                "stock", ["--addons-path=preferred"], start_directory=project
            )

            self.assertEqual(result, ["stock_custom"])

    def test_completes_project_and_installed_venv_modules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            project = home / "projects" / "demo-project"
            venv = home / "venvs" / "demo-venv"
            executable = venv / "bin" / "odoo"
            executable.parent.mkdir(parents=True)
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            self.make_module(project / "odoo" / "addons", "sale_custom")
            self.make_module(
                venv / "lib" / "python3.13" / "site-packages" / "odoo" / "addons",
                "sale_management",
            )

            with patch.dict(
                os.environ,
                {
                    "HOME": str(home),
                    "PATH": "",
                    "ODOORUN_VENV_NAME": "demo-venv",
                },
                clear=True,
            ):
                result = module.complete("sale_", start_directory=project)

            self.assertEqual(result, ["sale_custom", "sale_management"])


if __name__ == "__main__":
    unittest.main()
