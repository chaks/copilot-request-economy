"""Tests for the classify.py task classification module."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "lib"))

from classify import classify_task, TaskType


class TestClassifyTask(unittest.TestCase):
    """Test task type classification from prompt text."""

    def test_debugging_classification(self):
        prompts = [
            "Fix null pointer in UserService.createOrder",
            "Debug why the payment fails intermittently",
            "Stack trace shows NPE at line 147",
            "Investigate the error in the checkout flow",
            "Trace the root cause of 500 errors",
            "Fix the failing test in test_auth.py",  # Fixing broken tests = DEBUGGING
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.DEBUGGING, f"'{prompt}' should be debugging, got {result}")

    def test_refactoring_classification(self):
        prompts = [
            "Refactor auth system to support OAuth2 + SAML",
            "Restructure the service layer to use repository pattern",
            "Extract the validation logic into a separate class",
            "Rename UserService to UserManagementService across all files",
            "Apply composition over inheritance in the payment module",
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.REFACTORING, f"'{prompt}' should be refactoring, got {result}")

    def test_generation_classification(self):
        prompts = [
            "Add standard CRUD endpoints to OrderResource",
            "Create a new PaymentService class",
            "Draft initial implementation of the notification handler",
            "Build a REST endpoint for user registration",
            "Scaffold the controller for the admin dashboard",
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.GENERATION, f"'{prompt}' should be generation, got {result}")

    def test_review_classification(self):
        prompts = [
            "Review this pull request for security issues",
            "Code review the recent changes to auth module",
            "Analyze the diff for potential bugs",
            "Check if the PR follows SOLID principles",
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.REVIEW, f"'{prompt}' should be review, got {result}")

    def test_analysis_classification(self):
        prompts = [
            "Find all uses of UserService in src/",
            "Understand how the caching layer works",
            "Map the dependency graph between services",
            "Which files import the Config class?",
            "Explore the codebase structure",
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.ANALYSIS, f"'{prompt}' should be analysis, got {result}")

    def test_testing_classification(self):
        prompts = [
            "Write unit tests for UserService.createOrder",
            "Add integration tests for the payment endpoint",
            "Create test cases for the validation logic",
        ]
        for prompt in prompts:
            result = classify_task(prompt)
            self.assertEqual(result, TaskType.TESTING, f"'{prompt}' should be testing, got {result}")


class TestFallbackAndPriority(unittest.TestCase):
    """Test fallback to ANALYSIS and priority ordering."""

    def test_ambiguous_prompt_defaults_to_analysis(self):
        """Very generic prompts should default to analysis."""
        result = classify_task("help me with this code")
        self.assertEqual(result, TaskType.ANALYSIS)

    def test_fix_tests_is_debugging_not_testing(self):
        """'fix the failing tests' should be DEBUGGING, not TESTING."""
        result = classify_task("fix the failing tests")
        self.assertEqual(result, TaskType.DEBUGGING)

    def test_add_debug_logging_is_debugging_not_generation(self):
        """'add logging to debug this' should be DEBUGGING, not GENERATION."""
        result = classify_task("add logging to debug this")
        self.assertEqual(result, TaskType.DEBUGGING)


if __name__ == "__main__":
    unittest.main()
