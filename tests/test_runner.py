import unittest
from unittest.mock import patch

import tempfile
from pathlib import Path

from odoorun.runner import OdooArgumentError, OdooExecutionError, build_odoo_args, run_odoo


class RunOdooTests(unittest.TestCase):
    def test_adds_default_addons_for_venv_odoo(self) -> None:
        self.assertEqual(
            build_odoo_args("/home/khalid/venvs/obusiness-v2/bin/odoo", ["-d", "demo"]),
            ["--addons=odoo/addons", "-d", "demo"],
        )

    def test_builds_and_validates_source_addons_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory) / "odoo"
            (repo / "addons").mkdir(parents=True)
            (repo.parent / "custom-addons").mkdir()
            result = build_odoo_args(
                str(repo / "odoo-bin"), ["-a", "custom-addons", "-d", "demo"]
            )
            self.assertEqual(result[0], f"--addons-path={repo / 'addons'},{repo.parent / 'custom-addons'}")
            self.assertEqual(result[1:], ["-d", "demo"])

    def test_rejects_missing_custom_addons_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory) / "odoo"
            (repo / "addons").mkdir(parents=True)
            with self.assertRaises(OdooArgumentError):
                build_odoo_args(str(repo / "odoo-bin"), ["-a", "missing"])

    @patch("odoorun.runner.os.execv")
    @patch("odoorun.runner.find_odoo_executable", return_value="/opt/venv/bin/odoo")
    def test_forwards_arguments_unchanged(self, find_executable, execv) -> None:
        run_odoo(["--database", "example", "--dev=all"])

        find_executable.assert_called_once_with()
        execv.assert_called_once_with(
            "/opt/venv/bin/odoo",
            ["/opt/venv/bin/odoo", "--addons=odoo/addons", "--database", "example", "--dev=all"],
        )

    @patch(
        "odoorun.runner.os.execv",
        side_effect=PermissionError(13, "Permission denied"),
    )
    @patch("odoorun.runner.find_odoo_executable", return_value="/opt/venv/bin/odoo")
    def test_wraps_operating_system_errors(self, _find_executable, _execv) -> None:
        with self.assertRaises(OdooExecutionError) as context:
            run_odoo([])

        self.assertEqual(context.exception.executable, "/opt/venv/bin/odoo")
        self.assertEqual(context.exception.reason, "Permission denied")


if __name__ == "__main__":
    unittest.main()
