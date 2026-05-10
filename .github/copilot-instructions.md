# Copilot Instructions — Request Economy Harness

## Project Overview

A GitHub Copilot harness that enforces a **clarification-first workflow** (CLARIFY → EXECUTE → ITERATE) to reduce premium request consumption by 75%+. It consists of:

- **Hooks** — shell scripts triggered by Copilot lifecycle events (sessionStart, sessionEnd, userPromptSubmitted, postToolUse)
- **Python library** — budget tracking, task classification, and config management
- **Instructions** — behavioral contract that Copilot follows during sessions

## Build, Test, Lint

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_account.py -v

# Run a single test
python3 -m pytest tests/test_account.py::TestBudgetAccount::test_default_budget -v

# Install dependencies (if needed)
pip install -e .
```

The project uses `pytest` (configured in `pyproject.toml`), `unittest`-style tests, and has **no linting or type-checking setup**.

## Architecture

### Runtime State

All runtime state lives in `~/.copilot-orchestrator/`:

| File                 | Purpose                                              |
| -------------------- | ---------------------------------------------------- |
| `budget.json`        | Persistent monthly budget (used, limit, request log) |
| `budget.json.lock`   | File lock for concurrent access safety               |
| `config.json`        | User configuration (quota limits, verbosity)         |
| `session_state.json` | Temp: queued turn data, flushed at sessionEnd        |
| `current_turn.json`  | Temp: active turn data, flushed on new prompt        |
| `logs/session.log`   | Session start/end events                             |
| `logs/prompts.log`   | Logged prompts (truncated to 200 chars)              |

### Hook Lifecycle

Hooks are installed to `~/.copilot/hooks/` via `./install.sh`. The **budget-tracker** hook fires on four events:

1. **`sessionStart`** → `track-session.sh`: Load budget, display remaining requests via `additionalContext` JSON output
2. **`userPromptSubmitted`** → `track-prompt.sh`: Flush previous turn to session queue, start new turn (classify prompt, detect root vs clarification)
3. **`postToolUse`** → `track-prompt.sh`: Increment tool counter for current turn
4. **`sessionEnd`** → `track-session.sh`: Flush all queued entries, group by root boundaries, calculate conversational turns via delta, log to `budget.json`, display efficiency summary

### Key Mechanism: Root Prompt Grouping

The system distinguishes **root prompts** (new requests) from **clarification answers** (responses to Copilot's questions). `classify.is_root_prompt()` uses heuristics — short replies, approval phrases, and absence of action verbs signal clarifications. At sessionEnd, consecutive non-root entries are bundled with their preceding root to compute accurate `conversationalTurns` per request.

### Python Library (`lib/`)

| Module        | Responsibility                                                                                                                                                                                        |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `account.py`  | `BudgetAccount` dataclass, file I/O with `fcntl` locking (shared for reads, exclusive for writes), atomic writes via `.tmp` + `os.replace`, `log_request()` with atomic read-modify-write             |
| `classify.py` | `classify_task()` — keyword-heuristic classification into 6 types (debugging > refactoring > review > testing > generation, fallback: analysis). `is_root_prompt()` — root vs clarification detection |
| `config.py`   | `load_config()` — reads JSON, returns `DEFAULT_CONFIG` on failure                                                                                                                                     |

### Concurrency Model

`account.py` uses `fcntl` file locking:

- `load_budget()` → `LOCK_SH` (shared, allows concurrent reads)
- `save_budget()` / `log_request()` → `LOCK_EX` (exclusive, blocks all other access)
- `log_request()` performs full read-modify-write under one exclusive lock to prevent lost updates

## Key Conventions

### Security: Environment Variables Over Bash Interpolation

Hooks **never** interpolate user prompt text directly into Python source. Prompts are passed via environment variables (`PROMPT_CLASSIFY`, `PROMPT_ENV`) and read with `os.environ.get()`. This prevents bash/Python string-break injection. Tests in `test_account.py::TestJSONInjection` verify this.

### Atomic Writes

Budget writes use a two-step pattern: write to `.tmp` file, then `os.replace()` for atomic rename. This prevents corruption on crash during write.

### Month Rollover

Budget automatically resets when the calendar month changes. `load_budget()` detects month mismatch and returns a fresh account (preserving the limit from the old file).

### Hook Output Format

Hooks output JSON to stdout for Copilot to consume. The `sessionStart` hook outputs `{"additionalContext": "..."}` to inject budget info into the LLM context.

### Install Script

`./install.sh` copies hooks, instructions, and lib to `~/.copilot/`, creates runtime directories under `~/.copilot-orchestrator/`, and verifies Python imports work post-install. Do not modify target paths without updating both `install.sh` and the hooks.

### Test Structure

- Tests use `unittest` with `sys.path.insert(0, ...)` to import from `lib/`
- Use `tempfile.mkdtemp()` for isolated budget file tests
- `test_config.py` uses `pytest`-style functions (no class wrapper) — both styles coexist
