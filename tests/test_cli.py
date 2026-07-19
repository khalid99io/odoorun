import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from odoorun.cli import cli
from odoorun.discovery import OdooExecutableNotFoundError


class CliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_version_option(self) -> None:
        result = self.runner.invoke(cli, ["--version"])

        self.assertEqual(result.exit_code, 0)
        self.assertRegex(result.stdout, r"^odoorun \d+\.\d+\.\d+\s*$")

    @patch("odoorun.cli.shutil.which", return_value=None)
    @patch("odoorun.cli.find_odoo_executable")
    def test_doctor_fails_cleanly_when_odoo_is_missing(
        self,
        find_executable,
        _which,
    ) -> None:
        find_executable.side_effect = OdooExecutableNotFoundError(
            Path("/tmp/example-project")
        )

        result = self.runner.invoke(cli, ["doctor"])

        self.assertEqual(result.exit_code, 1)
        self.assertIn("Odoo is not ready", result.stdout)


if __name__ == "__main__":
    unittest.main()
