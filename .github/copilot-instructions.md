# Copilot Instructions — Request Economy Harness

## Project Overview

A GitHub Copilot harness that enforces a **clarification-first workflow** (CLARIFY → EXECUTE → ITERATE) to reduce premium request consumption by 75%+. It consists of:

- **Hooks** — shell scripts triggered by Copilot lifecycle events (sessionStart, sessionEnd, userPromptSubmitted, postToolUse)
- **Python library** — budget tracking, task classification, and config management
- **Instructions** — behavioral contract that Copilot follows during sessions

## Build, Test, and Lint Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_account.py -v

# Run a single test
python3 -m pytest tests/test_account.py::TestBudgetAccount::test_default_budget -v

# Install as editable package (for development)
pip install -e .
```

The project uses `pytest` (configured in `pyproject.toml`) with mixed test styles:

- `test_account.py` and `test_classify.py` use `unittest` classes with `sys.path.insert(0, ...)`
- `test_config.py` uses `pytest`-style functions (no class wrapper)

There is **no linting or type-checking setup**.

## High-Level Architecture

### Core Components

#### **Hook System**

Installed to `~/.copilot/hooks/budget-tracker/` via `./install.sh`:

- `track-session.sh` handles `sessionStart` and `sessionEnd` events
- `track-prompt.sh` handles `userPromptSubmitted` and `postToolUse` events
- Hooks communicate via JSON stdin/stdout and environment variables

#### **Runtime State Management**

All persistent state lives in `~/.copilot-orchestrator/`:

- `budget.json` — Monthly budget tracking with request logging
- `config.json` — User configuration (monthly limit, reset date, verbosity)
- `session_state.json` — Queued turn data, flushed at session end
- `current_turn.json` — Active turn data, flushed on new prompt
- `logs/` — Session and prompt activity logs

#### **Root Prompt Grouping Mechanism**

The system distinguishes **root prompts** (new requests) from **clarification answers**:

- `classify.is_root_prompt()` uses heuristics: short replies, approval phrases, and absence of action verbs signal clarifications
- At session end, consecutive non-root entries are bundled with their preceding root entry
- This enables accurate calculation of `conversationalTurns` per actual request

#### **Concurrency and Persistence**

- `account.py` uses `fcntl` file locking: `LOCK_SH` for reads, `LOCK_EX` for writes
- Atomic writes via `.tmp` file + `os.replace()` pattern
- Month rollover detection automatically resets budget while preserving limit

## Key Conventions

### Security: Environment Variables Over String Interpolation

Hooks **never** interpolate user input directly into Python source strings. All user data (prompts, tokens, etc.) is passed via environment variables (`PROMPT_CLASSIFY`, `PROMPT_ENV`, `INPUT_TOKENS`) and safely read with `os.environ.get()`. This prevents shell/Python injection attacks.

### Installation and Verification

The `./install.sh` script:

- Copies hooks, instructions, and lib to `~/.copilot/`
- Creates runtime directories under `~/.copilot-orchestrator/`
- Verifies Python imports work post-installation
- Never overwrites existing `config.json` but creates from template if missing

### Task Classification Priority

The `classify_task()` function uses keyword heuristics with strict priority order:

1. **Debugging** (fix, bug, error, exception, crash)
2. **Refactoring** (refactor, restructure, extract, simplify)
3. **Review** (review, security, solid principle, best practice)
4. **Testing** (test, spec, assert, mock, coverage)
5. **Generation** (add, create, implement, new class/service)
6. **Analysis** (fallback for ambiguous prompts)

### Workflow Enforcement

The clarification-first instructions enforce three phases:

- **CLARIFY**: Always ask questions before implementing, identify affected files, explain approach
- **EXECUTE**: Make minimal, targeted changes once confirmed
- **ITERATE**: Never end without asking for review feedback using specific question patterns
