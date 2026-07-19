import tempfile
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from odoorun.runner import OdooArgumentError, OdooExecutionError, build_odoo_args, run_odoo


class RunOdooTests(unittest.TestCase):
    def test_adds_default_addons_for_venv_odoo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            venv_root = Path(temporary_directory) / "venvs"
            executable = venv_root / "demo-project" / "bin" / "odoo"
            with patch.dict(os.environ, {"ODOORUN_VENV_ROOT": str(venv_root)}):
                result = build_odoo_args(str(executable), ["-d", "demo"])
            self.assertEqual(
                result,
                ["--addons=odoo/addons", "-d", "demo"],
            )

    def test_preserves_native_addons_path_for_venv_odoo(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            venv_root = Path(temporary_directory) / "venvs"
            executable = venv_root / "demo-project" / "bin" / "odoo"
            with patch.dict(os.environ, {"ODOORUN_VENV_ROOT": str(venv_root)}):
                result = build_odoo_args(
                    str(executable), ["--addons-path=preferred", "-d", "demo"]
                )
            self.assertEqual(result, ["--addons-path=preferred", "-d", "demo"])

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

    def test_preserves_native_addons_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory) / "odoo"
            (repo / "addons").mkdir(parents=True)
            result = build_odoo_args(
                str(repo / "odoo-bin"),
                ["--addons-path=preferred,addons", "-d", "demo"],
            )
            self.assertEqual(result, ["--addons-path=preferred,addons", "-d", "demo"])

    @patch("odoorun.runner.os.execv")
    def test_forwards_arguments_unchanged(self, execv) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            venv_root = Path(temporary_directory) / "venvs"
            executable = venv_root / "demo" / "bin" / "odoo"
            with patch.dict(os.environ, {"ODOORUN_VENV_ROOT": str(venv_root)}):
                with patch(
                    "odoorun.runner.find_odoo_executable",
                    return_value=str(executable),
                ) as find_executable:
                    run_odoo(["--database", "example", "--dev=all"])

            find_executable.assert_called_once_with()
            execv.assert_called_once_with(
                str(executable),
                [str(executable), "--addons=odoo/addons", "--database", "example", "--dev=all"],
            )

    @patch(
        "odoorun.runner.os.execv",
        side_effect=PermissionError(13, "Permission denied"),
    )
    def test_wraps_operating_system_errors(self, execv) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            executable = Path(temporary_directory) / "venvs" / "demo" / "bin" / "odoo"
            with patch(
                "odoorun.runner.find_odoo_executable", return_value=str(executable)
            ):
                with self.assertRaises(OdooExecutionError) as context:
                    run_odoo([])

        self.assertEqual(context.exception.executable, str(executable))
        self.assertEqual(context.exception.reason, "Permission denied")


if __name__ == "__main__":
    unittest.main()
