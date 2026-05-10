# Copilot Request Economy Harness v2

Maximize GitHub Copilot premium request value through clarification-first workflows and efficiency tracking -- achieving 75%+ request savings.

## Quick Install

```bash
git clone <repo-url> request-economy-harness
cd request-economy-harness
./install.sh
```

This installs hooks, instructions, and the Python library to `~/.copilot/`.

## How It Works

### The Core Pattern

```
CLARIFY -> EXECUTE -> ITERATE UNTIL APPROVED
```

Every request flows through mandatory clarification. The assistant asks questions first, executes once, then iterates within the same request window until explicit approval. This turns 4 separate requests into 1 request with 4 iterations -- **75% savings.**

### Hooks

Each hook is a self-contained directory in `~/.copilot/hooks/` with its own `hooks.json` and scripts:

| Hook               | Events                                                     | Purpose                                                                        |
| ------------------ | ---------------------------------------------------------- | ------------------------------------------------------------------------------ |
| **budget-tracker** | sessionStart, sessionEnd, userPromptSubmitted, postToolUse | Budget display, session summary, cost accounting, per-request savings tracking |

### Clarification-First Instructions

The `clarification-first.instructions.md` file is installed to `~/.copilot/instructions/` and enforces the 3-phase behavioral contract:

1. **CLARIFY** -- Identify files, explain approach, ask questions, wait for response
2. **EXECUTE** -- Implement the clarified intent with minimal, targeted changes
3. **ITERATE** -- End every response with a review question; continue refining until user approves

### Superpowers Skill Integration

The clarification-first instruction integrates with superpowers skills for execution guidance:

| Phase      | Primary Skill                    | Supporting Skills                                            |
| ---------- | -------------------------------- | ------------------------------------------------------------ |
| CLARIFY    | `brainstorming`                  | `using-superpowers`                                          |
| EXECUTE    | `executing-plans`                | `subagent-driven-development`, `dispatching-parallel-agents` |
| ITERATE    | `receiving-code-review`          | `systematic-debugging`, `test-driven-development`            |
| Pre-commit | `verification-before-completion` | `requesting-code-review`, `finishing-a-development-branch`   |

When both the instruction file and a superpowers skill apply, follow the skill's detailed steps within the constraints of the instruction's phases. User instructions override both.

### File Structure

```
team-configs/
  hooks/
    budget-tracker/
      hooks.json                   # Hook lifecycle configuration
      track-session.sh             # Session start/end handler
      track-prompt.sh              # Prompt/post-tool handler
      README.md
  instructions/
    clarification-first.instructions.md  # 3-phase behavioral contract + superpowers integration
  lib/
    __init__.py
    account.py                     # Budget tracking with iteration grouping
    classify.py                    # Task type classification (used by budget-tracker)
    config.py                      # Configuration management
  config.json.example              # Settings template
  install.sh                       # Installation script
  pyproject.toml                   # Python project config
  tests/                           # Unit tests
```

## After Installation

Hooks and instructions are installed to `~/.copilot/`.

Budget state lives in `~/.copilot-orchestrator/budget.json`.

## Configuration

Customize `~/.copilot-orchestrator/config.json`:

```json
{
  "quota": {
    "monthlyLimit": 300,
    "resetDate": 1,
    "warningThreshold": 50
  },
  "verbosity": "brief"
}
```

## Success Metrics

- **Target:** Reduce premium requests through clarification-first workflow
- **Measurement:** Conversational turns per request (not tool calls)
- **Actual savings:** Measure your baseline for 30 days, then compare

Note: "75% savings" depends on your specific workflow patterns. Measure your own baseline.

## Troubleshooting

**Hooks not firing:** Verify files exist in `~/.copilot/hooks/` with executable `.sh` scripts.

**Instructions not loading:** Verify `clarification-first.instructions.md` exists in `~/.copilot/instructions/`.

**Python import errors:** Verify `~/.copilot/lib/` contains `classify.py`, `account.py`, `config.py`.

**Superpowers skills not triggering:** Ensure the superpowers skills are present under `~/.agents/skills/`. Skills are invoked automatically when there's even a 1% chance they apply.

## Credits

This project draws inspiration from [Stop Wasting Premium Requests in GitHub Copilot](https://alessio.franceschelli.me/posts/ai/stop-wasting-premium-requests-in-github-copilot/) by Alessio Franceschelli, which demonstrates how clarification-first workflows dramatically reduce premium request consumption.
