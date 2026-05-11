# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**copilot-request-economy** is a harness that reduces GitHub Copilot Premium request consumption by 75%+ through a structured **CLARIFY -> EXECUTE -> ITERATE** workflow. It installs shell hooks, a Python library, and behavioral instructions into `~/.copilot/`.

## Tech Stack

- Python 3.10+ (stdlib only — no external dependencies beyond pytest)
- Bash shell hooks
- Uses `fcntl` for file locking, `os.replace()` for atomic writes
- Runtime state in `~/.copilot-orchestrator/`

## Key Commands

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run a single test file
python3 -m pytest tests/test_account.py -v

# Run a single test
python3 -m pytest tests/test_account.py::TestBudgetAccount::test_default_budget -v

# Install as editable package
pip install -e .
```

There is no linting or type-checking setup. Tests use mixed styles: `unittest.TestCase` classes in `test_account.py` and `test_classify.py`, pytest-style functions in `test_config.py`.

## Architecture

### Three-Layer Design

1. **Hooks** (`hooks/budget-tracker/`) — Shell scripts mapped to 4 Copilot lifecycle events via `hooks.json`:
   - `sessionStart` / `sessionEnd` → `track-session.sh`
   - `userPromptSubmitted` / `postToolUse` → `track-prompt.sh`

2. **Python Library** (`lib/`):
   - `account.py` — `BudgetAccount` dataclass with `fcntl` file locking (`LOCK_SH`/`LOCK_EX`), atomic writes, month rollover, `log_request()`, and efficiency summary
   - `classify.py` — Keyword-heuristic task classification (6 types) + `is_root_prompt()` heuristic
   - `config.py` — Simple config loader with defaults

3. **Instructions** (`instructions/`) — `clarification-first.instructions.md` enforces the behavioral contract

### Root Prompt Grouping

The system distinguishes **root prompts** (new requests) from **clarification answers** using `classify.is_root_prompt()`. At session end, consecutive non-root entries are bundled with their preceding root entry to calculate accurate `conversationalTurns` per actual request.

### Security

All user input is passed via environment variables (`PROMPT_CLASSIFY`, `PROMPT_ENV`, `INPUT_TOKENS`) — never interpolated into Python source strings. Tested in `test_account.py::TestJSONInjection`.

### Concurrency

`account.py` uses `fcntl` locking and atomic `.tmp` + `os.replace()` writes. Verified by concurrent threading test (3 threads x 5 updates = 15, no lost writes).

## Source Organization

```
├── hooks/budget-tracker/       # Lifecycle event handlers + hooks.json
├── instructions/               # Behavioral contract (clarification-first)
├── lib/                        # Python library (account, classify, config)
├── tests/                      # Test suite
├── install.sh                  # One-click installer
├── config.json.example         # Configuration template
└── pyproject.toml              # Package metadata + pytest config
```

## Conventions

- **Task classification priority**: debugging > refactoring > review > testing > generation > analysis (fallback)
- **Never overwrites** existing `config.json` — creates from template only if missing
- **`install.sh`** copies hooks/lib/instructions to `~/.copilot/`, creates runtime state under `~/.copilot-orchestrator/`, verifies Python imports post-install
- **Budget defaults** to 300 requests/month, configurable via `~/.copilot-orchestrator/config.json`
