import unittest
from unittest.mock import patch

from odoorun.runner import OdooExecutionError, run_odoo


class RunOdooTests(unittest.TestCase):
    @patch("odoorun.runner.os.execv")
    @patch("odoorun.runner.find_odoo_executable", return_value="/opt/odoo/odoo-bin")
    def test_forwards_arguments_unchanged(self, find_executable, execv) -> None:
        run_odoo(["--database", "example", "--dev=all"])

        find_executable.assert_called_once_with()
        execv.assert_called_once_with(
            "/opt/odoo/odoo-bin",
            ["/opt/odoo/odoo-bin", "--database", "example", "--dev=all"],
        )

    @patch(
        "odoorun.runner.os.execv",
        side_effect=PermissionError(13, "Permission denied"),
    )
    @patch("odoorun.runner.find_odoo_executable", return_value="/opt/odoo/odoo-bin")
    def test_wraps_operating_system_errors(self, _find_executable, _execv) -> None:
        with self.assertRaises(OdooExecutionError) as context:
            run_odoo([])

        self.assertEqual(context.exception.executable, "/opt/odoo/odoo-bin")
        self.assertEqual(context.exception.reason, "Permission denied")


if __name__ == "__main__":
    unittest.main()
