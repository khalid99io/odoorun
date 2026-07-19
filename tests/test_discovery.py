import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from odoorun.discovery import (
    OdooExecutableNotFoundError,
    find_odoo_executable,
)


class FindOdooExecutableTests(unittest.TestCase):
    def make_executable(self, path: Path) -> None:
        path.write_text("#!/bin/sh\n", encoding="utf-8")
        path.chmod(0o755)

    def test_finds_odoo_bin_in_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            nested = root / "addons" / "custom"
            nested.mkdir(parents=True)
            executable = root / "odoo-bin"
            self.make_executable(executable)

            with patch.dict(os.environ, {"PATH": ""}):
                result = find_odoo_executable(nested)

            self.assertEqual(result, str(executable))

    def test_local_odoo_bin_takes_precedence_over_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            local_executable = root / "odoo-bin"
            path_executable = root / "odoo"
            self.make_executable(local_executable)
            self.make_executable(path_executable)

            with patch.dict(os.environ, {"PATH": str(root)}):
                result = find_odoo_executable(root)

            self.assertEqual(result, str(local_executable))

    def test_falls_back_to_odoo_on_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            executable = root / "odoo"
            self.make_executable(executable)

            with patch.dict(os.environ, {"PATH": str(root)}):
                result = find_odoo_executable(root)

            self.assertEqual(result, str(executable))

    def test_finds_odoo_from_project_virtual_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            home = Path(temporary_directory)
            project = home / "PycharmProjects" / "obusiness-2"
            project.mkdir(parents=True)
            executable = home / "venvs" / "obusiness-v2" / "bin" / "odoo"
            executable.parent.mkdir(parents=True)
            self.make_executable(executable)

            with patch.dict(os.environ, {"PATH": "", "HOME": str(home)}):
                result = find_odoo_executable(project)

            self.assertEqual(result, str(executable))

    def test_reports_nearest_non_executable_odoo_bin(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            nested = root / "addons"
            nested.mkdir()
            candidate = root / "odoo-bin"
            candidate.write_text("#!/bin/sh\n", encoding="utf-8")
            candidate.chmod(0o644)

            with patch.dict(os.environ, {"PATH": ""}):
                with self.assertRaises(OdooExecutableNotFoundError) as context:
                    find_odoo_executable(nested)

            self.assertEqual(context.exception.directory, nested.resolve())
            self.assertEqual(context.exception.non_executable, candidate)


if __name__ == "__main__":
    unittest.main()
