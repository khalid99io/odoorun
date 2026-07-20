import subprocess
import unittest
from unittest.mock import patch

from odoorun.completion import command, database
from odoorun.completion.engine import complete


class DatabaseCompletionTests(unittest.TestCase):
    @patch("odoorun.completion.database.subprocess.run")
    def test_returns_sorted_unique_prefix_matches(self, run) -> None:
        run.return_value.stdout = "test_z\nproduction\ntest_a\ntest_a\n"

        result = database.complete("test_")

        self.assertEqual(result, ["test_a", "test_z"])
        self.assertEqual(
            run.call_args.kwargs["timeout"],
            database.QUERY_TIMEOUT_SECONDS,
        )

    @patch(
        "odoorun.completion.database.subprocess.run",
        side_effect=subprocess.TimeoutExpired("psql", 2),
    )
    def test_returns_no_results_when_psql_times_out(self, _run) -> None:
        self.assertEqual(database.complete(""), [])

    def test_unknown_completion_kind_returns_no_results(self) -> None:
        self.assertEqual(complete("unknown", ""), [])


class CommandCompletionTests(unittest.TestCase):
    def test_completes_root_commands(self) -> None:
        self.assertEqual(command.complete("d"), ["doctor", "db"])

    def test_completes_group_subcommands(self) -> None:
        self.assertEqual(command.complete("", ["db"]), ["list", "--help"])

    def test_completes_addon_options(self) -> None:
        self.assertEqual(
            command.complete("--s", ["addon", "list"]),
            ["--source", "--state"],
        )

    def test_completes_separate_and_attached_option_values(self) -> None:
        self.assertEqual(
            command.complete("c", ["addon", "list", "--source"]),
            ["core", "custom"],
        )
        self.assertEqual(
            command.complete("--state=in", ["addon", "list"]),
            ["--state=installed"],
        )
        self.assertEqual(
            command.complete("j", ["db", "list", "--format"]),
            ["json"],
        )

    def test_completes_completion_modes(self) -> None:
        self.assertEqual(
            command.complete("", ["completion"]),
            ["bash", "install", "--help"],
        )

    def test_does_not_complete_odoo_passthrough_arguments(self) -> None:
        self.assertEqual(command.complete("--", ["-d", "demo"]), [])


if __name__ == "__main__":
    unittest.main()
