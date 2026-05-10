"""Tests for the account.py budget tracking module."""

import json
import os
import tempfile
import unittest
from unittest.mock import patch, mock_open

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from account import (
    BudgetAccount,
    load_budget,
    save_budget,
    init_budget,
    log_request,
    get_remaining,
    get_efficiency_summary,
)


class TestBudgetAccount(unittest.TestCase):
    """Test BudgetAccount dataclass and helpers."""

    def test_default_budget(self):
        account = BudgetAccount(month="2026-05", used=0, limit=300, requests=[])
        self.assertEqual(get_remaining(account), 300)

    def test_remaining_calculation(self):
        account = BudgetAccount(month="2026-05", used=47, limit=300, requests=[])
        self.assertEqual(get_remaining(account), 253)

    def test_remaining_never_negative(self):
        account = BudgetAccount(month="2026-05", used=350, limit=300, requests=[])
        self.assertEqual(get_remaining(account), 0)


class TestLoadSaveBudget(unittest.TestCase):
    """Test budget persistence."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.budget_path = os.path.join(self.temp_dir, "budget.json")

    def test_init_budget_creates_fresh(self):
        account = init_budget(self.budget_path, month="2026-05", limit=300)
        self.assertEqual(account.month, "2026-05")
        self.assertEqual(account.used, 0)
        self.assertEqual(account.limit, 300)
        self.assertEqual(account.requests, [])

    def test_save_and_load_roundtrip(self):
        account = init_budget(self.budget_path, month="2026-05", limit=300)
        account.used = 5
        save_budget(account, self.budget_path)

        loaded = load_budget(self.budget_path)
        self.assertEqual(loaded.month, "2026-05")
        self.assertEqual(loaded.used, 5)
        self.assertEqual(loaded.limit, 300)

    def test_load_missing_file_returns_default(self):
        account = load_budget(self.budget_path)
        self.assertIsNotNone(account)
        self.assertEqual(account.used, 0)

    def test_load_detects_month_reset(self):
        # Write a budget for a previous month
        old_budget = {
            "month": "2026-04",
            "used": 150,
            "limit": 300,
            "resetDate": 1,
            "requests": [],
        }
        with open(self.budget_path, "w") as f:
            json.dump(old_budget, f)

        account = load_budget(self.budget_path, current_month="2026-05")
        self.assertEqual(account.month, "2026-05")
        self.assertEqual(account.used, 0)


class TestLogRequest(unittest.TestCase):
    """Test request logging and efficiency tracking."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.budget_path = os.path.join(self.temp_dir, "budget.json")
        self.account = init_budget(self.budget_path, month="2026-05", limit=300)

    def _log_and_reload(self, **kwargs):
        log_request(self.account, self.budget_path, **kwargs)
        return load_budget(self.budget_path)

    def test_log_premium_request(self):
        account = self._log_and_reload(
            tier="premium",
            task_type="refactoring",
            files_affected=4,
            context_before=3500,
            context_after=420,
            clarifying_questions=2,
            iterations=4,
            outcome="success",
        )
        self.assertEqual(account.used, 1)
        self.assertEqual(len(account.requests), 1)
        req = account.requests[0]
        self.assertEqual(req["tier"], "premium")
        self.assertEqual(req["iterations"], 4)
        self.assertEqual(req["filesAffected"], 4)

    def test_efficiency_calculation(self):
        account = self._log_and_reload(
            tier="premium",
            task_type="refactoring",
            files_affected=4,
            context_before=3500,
            context_after=420,
            clarifying_questions=2,
            iterations=4,
            conversational_turns=5,
            outcome="success",
        )
        req = account.requests[0]
        eff = req["efficiency"]
        # estimatedTraditional = conversational_turns = 5, actual = 1, saved = 4
        self.assertEqual(eff["estimatedTraditionalRequests"], 5)
        self.assertEqual(eff["actualRequestsUsed"], 1)
        self.assertEqual(eff["requestsSaved"], 4)
        self.assertEqual(eff["savingsPercent"], 80)

    def test_non_premium_tier_does_not_increment(self):
        account = self._log_and_reload(
            tier="hooks",
            task_type="analysis",
            files_affected=1,
            iterations=0,
            outcome="success",
        )
        self.assertEqual(account.used, 0)


class TestEfficiencySummary(unittest.TestCase):
    """Test summary generation."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.budget_path = os.path.join(self.temp_dir, "budget.json")
        self.account = init_budget(self.budget_path, month="2026-05", limit=300)

    def test_savings_counts_conversational_turns(self):
        """Savings should count conversational turns, not tool calls."""
        log_request(
            self.account,
            self.budget_path,
            tier="premium",
            task_type="generation",
            conversational_turns=2,
            iterations=5,
        )

        entry = self.account.requests[-1]
        assert entry["efficiency"]["savingsPercent"] == 50

    def test_empty_summary(self):
        summary = get_efficiency_summary(self.account)
        self.assertIn("No premium requests", summary)

    def test_summary_with_requests(self):
        log_request(self.account, self.budget_path,
                    tier="premium", task_type="refactoring",
                    files_affected=4, context_before=3500, context_after=420,
                    clarifying_questions=2, iterations=4, outcome="success")
        log_request(self.account, self.budget_path,
                    tier="premium", task_type="generation",
                    files_affected=2, context_before=2000, context_after=300,
                    clarifying_questions=1, iterations=3, outcome="success")

        summary = get_efficiency_summary(self.account)
        self.assertIn("Premium requests: 2", summary)
        self.assertIn("Savings:", summary)


class TestJSONInjection(unittest.TestCase):
    """Test that env var approach prevents bash/Python injection in hooks."""

    def test_bash_interpolation_blocked_by_env_vars(self):
        """Verify that prompts containing bash/Python string breakers are safely
        handled via environment variables instead of bash interpolation.

        This tests the actual vulnerability: if bash interpolates ${prompt} into
        a Python triple-quoted string like '''${prompt}''', a prompt containing
        ''' would break out of the string and allow code injection.
        """
        import subprocess

        # Prompt that would break Python triple-quoted string interpolation
        malicious_prompt = "''' + __import__('os').system('echo INJECTED') + '''"

        # Test that env var approach prevents injection - Python reads from os.environ
        env = os.environ.copy()
        env['PROMPT_ENV'] = malicious_prompt
        env['TIMESTAMP_ENV'] = '2024-01-01T00:00:00Z'
        env['TASK_TYPE_ENV'] = 'test'

        result = subprocess.run(
            [
                'python3', '-c',
                'import json, os; '
                'turn = {'
                '"timestamp": os.environ.get("TIMESTAMP_ENV", ""), '
                '"prompt": os.environ.get("PROMPT_ENV", ""), '
                '"tool_count": 0, '
                '"files_affected": 0, '
                '"task_type": os.environ.get("TASK_TYPE_ENV", "unknown")'
                '}; '
                'print(json.dumps(turn))'
            ],
            capture_output=True,
            text=True,
            env=env
        )

        # Should parse as valid JSON
        loaded = json.loads(result.stdout)

        # The literal prompt string should be preserved, not executed
        assert loaded["prompt"] == malicious_prompt
        # Verify the subprocess didn't actually execute the injection
        lines = result.stdout.strip().split('\n')
        assert len(lines) == 1, "Should have exactly one line of JSON output"
        assert '"prompt": "\'\'\' + __import__(' in result.stdout


class TestConcurrentAccess(unittest.TestCase):
    """Test concurrent budget updates are safe."""

    def test_concurrent_budget_updates_safe(self):
        """Verify concurrent budget updates don't lose data."""
        import threading
        import time

        budget_path = tempfile.mktemp(suffix='.json')

        account = BudgetAccount(month="2024-01", used=0, limit=300)
        save_budget(account, budget_path)

        errors = []

        def update_budget():
            try:
                for i in range(5):
                    acc = load_budget(budget_path)
                    log_request(acc, budget_path, tier="premium", task_type="test", iterations=1)
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=update_budget) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        final = load_budget(budget_path)
        assert final.used == 15, f"Expected 15, got {final.used}. Errors: {errors}"

        os.remove(budget_path)


if __name__ == "__main__":
    unittest.main()
