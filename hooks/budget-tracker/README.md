---
name: 'Budget Tracker'
description: 'Tracks Copilot premium request usage, displays budget at session start, and generates efficiency summaries'
tags: ['budget', 'analytics', 'cost-tracking']
---

# Budget Tracker Hook

Tracks GitHub Copilot premium request usage (300/month limit) with session-level efficiency reporting.

## Features

- **Session Start**: Displays remaining requests and budget status
- **Session End**: Generates efficiency summary (iterations, savings %, remaining)
- **Prompt Logging**: Tracks prompts for budget analysis
- **Post-Tool Accounting**: Increments counter and shows per-request savings

## Installation

1. Copy this hook folder to your repository's `~/.copilot/hooks/` directory:
   ```bash
   cp -r hooks/budget-tracker ~/.copilot/hooks/
   ```

2. Copy the Python library to `~/.copilot/hooks/request-economy-lib/`:
   ```bash
   cp -r hooks/request-economy-lib ~/.copilot/hooks/request-economy-lib/
   ```

3. Ensure scripts are executable:
   ```bash
   chmod +x ~/.copilot/hooks/budget-tracker/*.sh
   ```

4. Commit to your repository's default branch

## Configuration

Budget state is stored in `~/.copilot-orchestrator/budget.json`.
Customize settings in `~/.copilot-orchestrator/config.json` (see config.json.example).

## Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `COPILOT_ITERATIONS` | Default: `1` | Iteration count for savings calculation |
| `COPILOT_HOOK_EVENT` | Set via `env` in `hooks.json` | Event name passed explicitly by hooks config — not auto-injected by Copilot |
