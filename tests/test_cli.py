import tempfile
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

    def test_help_shows_completion_setup(self) -> None:
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("odoorun completion install", result.stdout)

    def test_help_summarizes_launch_and_management_commands(self) -> None:
        result = self.runner.invoke(cli, ["--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("Arguments that are not odoorun tool", result.stdout)
        self.assertIn("odoorun db list", result.stdout)
        self.assertIn("odoorun addon list", result.stdout)
        self.assertIn("Automatic completion", result.stdout)

    def test_addon_help_explains_database_filtering(self) -> None:
        result = self.runner.invoke(cli, ["addon", "list", "--help"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn("not find addons in a database", result.stdout)
        self.assertIn("ir_module_module state", result.stdout)

    def test_prints_bash_completion(self) -> None:
        result = self.runner.invoke(cli, ["completion", "bash"])

        self.assertEqual(result.exit_code, 0)
        self.assertIn('previous" == "-d"', result.stdout)
        self.assertIn('__complete command -- "$current"', result.stdout)
        self.assertIn("complete -F _odoorun_complete odoorun", result.stdout)
        self.assertIn("complete -F _odoorun_complete o", result.stdout)

    def test_install_completion_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            bashrc = Path(temporary_directory) / ".bashrc"
            with patch.dict("os.environ", {"HOME": temporary_directory}):
                first = self.runner.invoke(cli, ["completion", "install"])
                second = self.runner.invoke(cli, ["completion", "install"])

            self.assertEqual(first.exit_code, 0)
            self.assertEqual(second.exit_code, 0)
            source = bashrc.read_text(encoding="utf-8")
            self.assertEqual(source.count("source <(odoorun completion bash)"), 1)

    @patch("odoorun.cli.complete_value", return_value=["demo", "demo_test"])
    def test_internal_completion_prints_database_candidates(self, complete) -> None:
        result = self.runner.invoke(cli, ["__complete", "database", "dem"])

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.splitlines(), ["demo", "demo_test"])
        complete.assert_called_once_with("database", "dem", None)

    def test_internal_completion_prints_command_candidates(self) -> None:
        result = self.runner.invoke(
            cli,
            ["__complete", "command", "--", "--s", "addon", "list"],
        )

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout.splitlines(), ["--source", "--state"])

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
