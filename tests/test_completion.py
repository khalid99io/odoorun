import subprocess
import unittest
from unittest.mock import patch

from odoorun.completion import database
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


if __name__ == "__main__":
    unittest.main()
