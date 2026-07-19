import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from odoorun.cli import cli


class ManagementCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    @patch("odoorun.commands.db.query")
    def test_lists_only_odoo_databases_by_default(self, query) -> None:
        def result(_sql, database=None):
            if database is None:
                return [["demo"], ["postgres"]]
            if database == "demo" and "to_regclass" in _sql:
                return [["ir_module_module"]]
            if database == "demo":
                return [["19.0.1.0"]]
            return [[""]]

        query.side_effect = result
        response = self.runner.invoke(cli, ["db", "list", "--format", "json"])

        self.assertEqual(response.exit_code, 0)
        self.assertEqual(
            json.loads(response.stdout),
            [{"database": "demo", "type": "odoo", "odoo_version": "19.0.1.0"}],
        )

    @patch("odoorun.commands.addon.Path.cwd")
    def test_lists_addons_from_current_project(self, cwd) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            repo = Path(temporary_directory) / "odoo"
            executable = repo / "odoo-bin"
            executable.parent.mkdir()
            executable.write_text("#!/bin/sh\n", encoding="utf-8")
            executable.chmod(0o755)
            addon = repo / "addons" / "sale_demo"
            addon.mkdir(parents=True)
            (addon / "__manifest__.py").write_text(
                "{'version': '19.0.1.0'}\n", encoding="utf-8"
            )
            cwd.return_value = repo

            response = self.runner.invoke(
                cli, ["addon", "list", "--format", "json"]
            )

        self.assertEqual(response.exit_code, 0)
        rows = json.loads(response.stdout)
        self.assertEqual(rows[0]["addon"], "sale_demo")
        self.assertEqual(rows[0]["source"], "core")
        self.assertEqual(rows[0]["state"], "available")

    @patch("odoorun.commands.table.query")
    def test_lists_tables_from_required_database(self, query) -> None:
        query.return_value = [["public", "sale_order", "BASE TABLE"]]

        response = self.runner.invoke(
            cli,
            ["table", "list", "-d", "demo", "--format", "json"],
        )

        self.assertEqual(response.exit_code, 0)
        self.assertEqual(
            json.loads(response.stdout),
            [{"schema": "public", "table": "sale_order", "type": "BASE TABLE"}],
        )
        self.assertEqual(query.call_args.args[1], "demo")

    def test_addon_state_requires_database(self) -> None:
        response = self.runner.invoke(
            cli, ["addon", "list", "--state", "installed"]
        )

        self.assertNotEqual(response.exit_code, 0)
        self.assertIn("requires --database", response.output)


if __name__ == "__main__":
    unittest.main()
