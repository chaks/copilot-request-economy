"""Budget tracking, request logging, and efficiency metrics."""

import fcntl
import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any


@dataclass
class BudgetAccount:
    """Tracks premium request usage within a monthly budget."""

    month: str
    used: int
    limit: int
    requests: list[dict[str, Any]] = field(default_factory=list)
    last_session: str | None = None
    total_input_tokens: int = 0
    total_output_tokens: int = 0


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _get_lock_path(budget_path: str) -> str:
    """Get lock file path for a budget file."""
    return budget_path + ".lock"


def load_budget(path: str, current_month: str | None = None) -> BudgetAccount:
    """Load budget from JSON file with locking.

    Uses shared locking to allow concurrent reads while preventing
    writes during read operations.
    """
    month = current_month or _current_month()
    lock_path = _get_lock_path(path)

    try:
        with open(lock_path, "w") as lockf:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_SH)
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("month") != month:
                    # Month rolled over — reset
                    return BudgetAccount(month=month, used=0, limit=data.get("limit", 300))
                return BudgetAccount(
                    month=data["month"],
                    used=data["used"],
                    limit=data["limit"],
                    requests=data.get("requests", []),
                    last_session=data.get("lastSession"),
                    total_input_tokens=data.get("totalInputTokens", 0),
                    total_output_tokens=data.get("totalOutputTokens", 0),
                )
            finally:
                fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return BudgetAccount(month=month, used=0, limit=300)


def save_budget(account: BudgetAccount, path: str) -> None:
    """Persist budget to JSON file atomically with exclusive locking.

    Uses exclusive locking to prevent concurrent writes and reads
    during write operations. Writes to .tmp file then atomically renames.
    """
    lock_path = _get_lock_path(path)
    tmp_path = path + ".tmp"
    data = {
        "month": account.month,
        "used": account.used,
        "limit": account.limit,
        "requests": account.requests,
    }
    if account.total_input_tokens:
        data["totalInputTokens"] = account.total_input_tokens
    if account.total_output_tokens:
        data["totalOutputTokens"] = account.total_output_tokens
    if account.last_session:
        data["lastSession"] = account.last_session

    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, path)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def init_budget(path: str, month: str | None = None, limit: int = 300) -> BudgetAccount:
    """Create and save a fresh budget. Idempotent — overwrites if exists."""
    month = month or _current_month()
    account = BudgetAccount(month=month, used=0, limit=limit)
    save_budget(account, path)
    return account


def get_remaining(account: BudgetAccount) -> int:
    """Return remaining premium requests (never negative)."""
    return max(0, account.limit - account.used)


def log_request(
    account: BudgetAccount,
    budget_path: str,
    *,
    tier: str,
    task_type: str,
    files_affected: int = 0,
    context_before: int = 0,
    context_after: int = 0,
    clarifying_questions: int = 0,
    iterations: int = 0,  # Tool calls (kept for logging)
    conversational_turns: int = 1,  # Actual conversational turns
    outcome: str = "success",
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> None:
    """Log a request to the budget atomically with exclusive locking.

    Performs atomic read-modify-write to prevent lost updates from
    concurrent sessions. The account parameter is updated in place.
    """
    lock_path = _get_lock_path(budget_path)
    tmp_path = budget_path + ".tmp"

    # Acquire exclusive lock for entire read-modify-write cycle
    with open(lock_path, "w") as lockf:
        fcntl.flock(lockf.fileno(), fcntl.LOCK_EX)
        try:
            # Re-read from disk to get current state
            current_month = account.month
            try:
                with open(budget_path) as f:
                    data = json.load(f)
                if data.get("month") == current_month:
                    account.used = data["used"]
                    account.requests = data.get("requests", [])
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                pass  # Use the account state we were given

            # Now perform the modification
            if tier == "premium":
                account.used += 1

            estimated_traditional = conversational_turns if tier == "premium" else 1
            saved = estimated_traditional - 1
            savings_pct = int((saved / estimated_traditional) * 100) if estimated_traditional > 0 else 0

            entry: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tier": tier,
                "taskType": task_type,
                "iterations": iterations,
                "conversationalTurns": conversational_turns,
            }
            if files_affected:
                entry["filesAffected"] = files_affected
            if context_before:
                entry["contextBefore"] = context_before
            if context_after:
                entry["contextAfter"] = context_after
            if clarifying_questions:
                entry["clarifyingQuestionsAsked"] = clarifying_questions

            if tier == "premium":
                entry["outcome"] = outcome
                entry["budgetRemaining"] = get_remaining(account)
                entry["efficiency"] = {
                    "estimatedTraditionalRequests": estimated_traditional,
                    "actualRequestsUsed": 1,
                    "requestsSaved": saved,
                    "savingsPercent": savings_pct,
                }
                entry["inputTokens"] = input_tokens
                entry["outputTokens"] = output_tokens
                entry["requestsSaved"] = saved
                entry["savingsPercent"] = savings_pct

            account.requests.append(entry)
            account.total_input_tokens += input_tokens
            account.total_output_tokens += output_tokens

            # Persist atomically while still holding lock
            data = {
                "month": account.month,
                "used": account.used,
                "limit": account.limit,
                "requests": account.requests,
            }
            if account.total_input_tokens:
                data["totalInputTokens"] = account.total_input_tokens
            if account.total_output_tokens:
                data["totalOutputTokens"] = account.total_output_tokens
            if account.last_session:
                data["lastSession"] = account.last_session

            with open(tmp_path, "w") as f:
                json.dump(data, f, indent=2)
                f.write("\n")
            os.replace(tmp_path, budget_path)
        finally:
            fcntl.flock(lockf.fileno(), fcntl.LOCK_UN)


def get_efficiency_summary(account: BudgetAccount) -> str:
    """Generate a human-readable efficiency summary string."""
    if not account.requests:
        return "No premium requests this month."

    premium_requests = [r for r in account.requests if r.get("tier") == "premium"]
    if not premium_requests:
        return "No premium requests this month."

    total_requests = len(premium_requests)
    total_conversational_turns = sum(r.get("conversationalTurns", 1) for r in premium_requests)
    total_saved = sum(max(0, r.get("conversationalTurns", 1) - 1) for r in premium_requests)
    total_traditional = total_requests + total_saved
    avg_savings = int((total_saved / total_traditional) * 100) if total_traditional > 0 else 0

    lines = [
        "Session Summary:",
        "─" * 30,
        f"Premium requests: {total_requests}",
        f"Total conversational turns: {total_conversational_turns}",
        f"Requests saved: {total_saved}",
        f"Savings: {avg_savings}%",
        f"Remaining: {get_remaining(account)}/{account.limit}",
        "─" * 30,
    ]
    return "\n".join(lines)
