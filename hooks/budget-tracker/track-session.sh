#!/bin/bash
# Budget Tracker — sessionStart and sessionEnd handler.
# Receives JSON context via stdin (cat).
#
# SessionStart: Load budget, display remaining, initialize if missing.
# SessionEnd: Generate efficiency summary, persist budget.

set -euo pipefail

RUNTIME_DIR="${HOME}/.copilot-orchestrator"
BUDGET_FILE="${RUNTIME_DIR}/budget.json"
LIB_DIR="${HOME}/.copilot/lib"
LOG_DIR="${RUNTIME_DIR}/logs"

mkdir -p "$LOG_DIR"

# Read stdin (JSON context from Copilot)
INPUT=$(cat)

# Determine event from stdin JSON or env var
EVENT=""
if command -v jq &>/dev/null; then
  EVENT=$(printf '%s' "$INPUT" | jq -r '.event // .hookEvent // empty' 2>/dev/null || echo "")
fi
if [[ -z "$EVENT" ]]; then
  EVENT="${COPILOT_HOOK_EVENT:-unknown}"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Always ensure budget file exists (covers sessionStart)
if [ ! -f "$BUDGET_FILE" ]; then
  CURRENT_MONTH=$(date -u +%Y-%m)
  cat > "$BUDGET_FILE" << EOF
{
  "month": "${CURRENT_MONTH}",
  "used": 0,
  "limit": 300,
  "requests": []
}
EOF
fi

# Check for month rollover and reset
CURRENT_MONTH=$(date -u +%Y-%m)
FILE_MONTH=$(python3 -c "
import sys, json
sys.path.insert(0, '${LIB_DIR}')
from account import load_budget
b = load_budget('${BUDGET_FILE}')
print(b.month)
" 2>/dev/null || echo "$CURRENT_MONTH")
if [[ "$FILE_MONTH" != "$CURRENT_MONTH" ]]; then
  python3 -c "
import sys
sys.path.insert(0, '${LIB_DIR}')
from account import init_budget
init_budget('${BUDGET_FILE}', '${CURRENT_MONTH}')
" 2>/dev/null || true
fi

if [[ "$EVENT" == "sessionStart" || "$EVENT" == "unknown" ]]; then
  # Inject remaining budget into the LLM context via additionalContext
  # so the agent can reference it proactively and answer "how much budget?"
  REMAINING=$(python3 -c "
import sys
sys.path.insert(0, '${LIB_DIR}')
from account import load_budget, get_remaining
b = load_budget('${BUDGET_FILE}')
print(get_remaining(b))
" 2>/dev/null || echo "unknown")

  echo "{\"additionalContext\":\"📊 Budget: ${REMAINING} requests remaining this month. Ask clarifying questions. Iterate freely within each request.\"}"

  # Log session start
  printf '{"timestamp":"%s","event":"sessionStart","remaining":%s}\n' \
    "$TIMESTAMP" "${REMAINING}" >> "${LOG_DIR}/session.log"
fi

if [[ "$EVENT" == "sessionEnd" ]]; then
  # Flush any remaining turn into the session queue, then flush the entire
  # queue to budget.json with the final conversational_turns count.
  SESSION_FILE="${RUNTIME_DIR}/session_state.json"
  TURN_FILE="${RUNTIME_DIR}/current_turn.json"

  # First: flush current turn to queue (reuse track-prompt's flush logic inline)
  if [[ -f "$TURN_FILE" ]]; then
    python3 -c "
import json, os
turn_file = '${TURN_FILE}'
session_file = '${SESSION_FILE}'
if not os.path.exists(turn_file):
    sys.exit(0)
with open(turn_file) as f:
    turn = json.load(f)
tool_count = turn.get('tool_count', 0)
if tool_count == 0:
    sys.exit(0)
if os.path.exists(session_file):
    with open(session_file) as f:
        session = json.load(f)
else:
    session = {'session_turn_count': 0, 'queue': []}
if 'queue' not in session:
    session['queue'] = []
session['queue'].append({
    'tool_count': tool_count,
    'files_affected': turn.get('files_affected', 0),
    'task_type': turn.get('task_type', 'unknown'),
    'flushed_at_session_turn': session.get('session_turn_count', 0),
    'is_root': turn.get('is_root', True),
})
with open(session_file, 'w') as f:
    json.dump(session, f)
" 2>/dev/null || true
    rm -f "$TURN_FILE"
  fi

  # Second: group queue entries by root boundaries and flush to budget.json
  # Consecutive non-root entries are bundled with their preceding root entry.
  python3 -c "
import sys, json, os
sys.path.insert(0, '${LIB_DIR}')
from account import load_budget, log_request

session_file = '${SESSION_FILE}'
if not os.path.exists(session_file):
    sys.exit(0)

with open(session_file) as f:
    session = json.load(f)

queue = session.get('queue', [])

if not queue:
    sys.exit(0)

# Group entries by root boundaries:
# Each root entry starts a new group. Non-root entries join the preceding group.
groups = []
current_group = None
for entry in queue:
    if entry.get('is_root', True):
        if current_group:
            groups.append(current_group)
        current_group = [entry]
    else:
        if current_group:
            current_group.append(entry)
        else:
            # Leading non-root entries get their own group
            current_group = [entry]
if current_group:
    groups.append(current_group)

budget = load_budget('${BUDGET_FILE}')

for group in groups:
    # Calculate per-request conversational_turns as delta between flush points
    prev_flush = 0
    total_turns = 0
    total_tools = 0
    total_files = 0
    task_type = group[0].get('task_type', 'unknown')
    for entry in group:
        at = entry.get('flushed_at_session_turn', 0)
        total_turns += max(1, at - prev_flush)
        prev_flush = at
        total_tools += entry.get('tool_count', 0)
        total_files += entry.get('files_affected', 0)

    log_request(
        budget, '${BUDGET_FILE}',
        tier='premium',
        task_type=task_type,
        iterations=total_tools,
        files_affected=total_files,
        conversational_turns=total_turns,
        outcome='success',
    )

os.remove(session_file)
" 2>/dev/null || true

  # Generate and display session summary
  python3 -c "
import sys
sys.path.insert(0, '${LIB_DIR}')
from account import load_budget, save_budget, get_efficiency_summary
from datetime import datetime, timezone

budget = load_budget('${BUDGET_FILE}')
summary = get_efficiency_summary(budget)
print(summary)

budget.last_session = datetime.now(timezone.utc).isoformat()
save_budget(budget, '${BUDGET_FILE}')
" 2>/dev/null || echo "Session summary unavailable."
fi

exit 0
