#!/bin/bash
# Budget Tracker — userPromptSubmitted and postToolUse handler.
# Receives JSON context via stdin (cat).
#
# One user prompt = one budget entry, regardless of how many tools ran.
# Tool calls within a prompt turn are counted as "iterations" for that single entry.
#
# Mechanism:
# - userPromptSubmitted: flush the previous turn to the session queue, start a new turn.
# - postToolUse: increment the tool counter for the current turn (no budget write).
# - sessionEnd: flush all queued entries to budget.json with the final session
#   turn count, so each entry gets accurate conversational_turns.

set -euo pipefail

RUNTIME_DIR="${HOME}/.copilot-orchestrator"
BUDGET_FILE="${RUNTIME_DIR}/budget.json"
LIB_DIR="${HOME}/.copilot/lib"
LOG_DIR="${RUNTIME_DIR}/logs"
TURN_FILE="${RUNTIME_DIR}/current_turn.json"
SESSION_FILE="${RUNTIME_DIR}/session_state.json"

mkdir -p "$LOG_DIR"

# Read stdin (JSON context from Copilot)
INPUT=$(cat)

# Extract fields from stdin JSON
EVENT=""
TOOL_NAME=""
PROMPT_TEXT=""
INPUT_TOKENS=""
OUTPUT_TOKENS=""
if command -v jq &>/dev/null; then
  EVENT=$(printf '%s' "$INPUT" | jq -r '.event // .hookEvent // empty' 2>/dev/null || echo "")
  TOOL_NAME=$(printf '%s' "$INPUT" | jq -r '.toolName // empty' 2>/dev/null || echo "")
  PROMPT_TEXT=$(printf '%s' "$INPUT" | jq -r '.prompt // .userMessage // empty' 2>/dev/null || echo "")
  INPUT_TOKENS=$(printf '%s' "$INPUT" | jq -r '.inputTokens // empty' 2>/dev/null || echo "")
  OUTPUT_TOKENS=$(printf '%s' "$INPUT" | jq -r '.outputTokens // empty' 2>/dev/null || echo "")
fi
if [[ -z "$EVENT" ]]; then
  EVENT="${COPILOT_HOOK_EVENT:-unknown}"
fi

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# ── Flush previous turn to session queue ───────────────────────────
# Writes the previous turn's data into the session queue file.
# The actual budget.json update happens at sessionEnd with the final count.
flush_turn() {
  if [[ ! -f "$TURN_FILE" ]]; then
    return
  fi

  python3 -c "
import sys, json, os

turn_file = '${TURN_FILE}'
session_file = '${SESSION_FILE}'
if not os.path.exists(turn_file):
    sys.exit(0)

with open(turn_file) as f:
    turn = json.load(f)

tool_count = turn.get('tool_count', 0)
if tool_count == 0:
    sys.exit(0)

# Append this turn's data to the session queue
if os.path.exists(session_file):
    with open(session_file) as f:
        session = json.load(f)
else:
    session = {'session_turn_count': 0, 'queue': []}

entry = {
    'tool_count': tool_count,
    'files_affected': turn.get('files_affected', 0),
    'task_type': turn.get('task_type', 'unknown'),
    'flushed_at_session_turn': session.get('session_turn_count', 0),
    'is_root': turn.get('is_root', True),
}
session['queue'].append(entry)

with open(session_file, 'w') as f:
    json.dump(session, f)
" 2>/dev/null || true

  rm -f "$TURN_FILE"
}

# ── Start a new turn ───────────────────────────────────────────────
start_turn() {
  local prompt="$1"

  # Determine task type from the prompt - use env var to prevent injection
  local task_type
  export PROMPT_CLASSIFY="${prompt}"
  task_type=$(python3 -c "
import sys, os
sys.path.insert(0, '${LIB_DIR}')
from classify import classify_task
try:
    prompt = os.environ.get('PROMPT_CLASSIFY', '')
    print(classify_task(prompt).value)
except Exception:
    print('unknown')
" 2>/dev/null || echo "unknown")

  # Export variables for Python to read safely (prevents bash injection)
  export TIMESTAMP_ENV="${TIMESTAMP}"
  export PROMPT_ENV="${prompt}"
  export TASK_TYPE_ENV="${task_type}"

  # Determine if this is a root prompt (starts new request) or clarification answer
  export IS_ROOT_ENV
  IS_ROOT_ENV=$(python3 -c "
import sys, os
sys.path.insert(0, '${LIB_DIR}')
from classify import is_root_prompt
try:
    prompt = os.environ.get('PROMPT_CLASSIFY', '')
    print('true' if is_root_prompt(prompt) else 'false')
except Exception:
    print('true')
" 2>/dev/null || echo "true")

  # Use Python to write JSON safely - reads from env vars, not bash interpolation
  python3 -c "
import json, os
turn = {
    'timestamp': os.environ.get('TIMESTAMP_ENV', ''),
    'prompt': os.environ.get('PROMPT_ENV', ''),
    'tool_count': 0,
    'files_affected': 0,
    'task_type': os.environ.get('TASK_TYPE_ENV', 'unknown'),
    'is_root': os.environ.get('IS_ROOT_ENV', 'true') == 'true',
}
print(json.dumps(turn))
" > "$TURN_FILE"

  # Log the prompt for debugging - reads from env vars
  python3 -c "
import os, json
prompt = os.environ.get('PROMPT_ENV', '')
entry = {
    'timestamp': os.environ.get('TIMESTAMP_ENV', ''),
    'event': 'userPromptSubmitted',
    'prompt_length': len(prompt),
    'prompt': prompt[:200]
}
print(json.dumps(entry))
" >> "${LOG_DIR}/prompts.log"
}

# ── Increment tool counter for current turn ────────────────────────
increment_turn() {
  local tool_name="$1"
  local input_tokens="$2"
  local output_tokens="$3"

  # Export for safe Python access
  export TOOL_NAME_ENV="${tool_name}"
  export INPUT_TOKENS_ENV="${input_tokens}"
  export OUTPUT_TOKENS_ENV="${output_tokens}"

  python3 -c "
import sys, json, os
turn_file = '${TURN_FILE}'
if not os.path.exists(turn_file):
    sys.exit(0)

with open(turn_file) as f:
    turn = json.load(f)

turn['tool_count'] = turn.get('tool_count', 0) + 1

# Track file-modifying tools - safely read tool name
tool = os.environ.get('TOOL_NAME_ENV', '')
if tool in ('edit', 'write', 'create', 'notebook_edit'):
    turn['files_affected'] = turn.get('files_affected', 0) + 1

# Accumulate token usage
input_tokens = os.environ.get('INPUT_TOKENS_ENV', '')
output_tokens = os.environ.get('OUTPUT_TOKENS_ENV', '')
if input_tokens.isdigit():
    turn['input_tokens'] = turn.get('input_tokens', 0) + int(input_tokens)
if output_tokens.isdigit():
    turn['output_tokens'] = turn.get('output_tokens', 0) + int(output_tokens)

with open(turn_file, 'w') as f:
    json.dump(turn, f)
" 2>/dev/null || true
}

# ── Increment session-level turn counter ───────────────────────────
increment_session_count() {
  python3 -c "
import json, os
sf = '${SESSION_FILE}'
if os.path.exists(sf):
    with open(sf) as f:
        data = json.load(f)
else:
    data = {'session_turn_count': 0, 'queue': []}
data['session_turn_count'] = data.get('session_turn_count', 0) + 1
if 'queue' not in data:
    data['queue'] = []
with open(sf, 'w') as f:
    json.dump(data, f)
" 2>/dev/null || true
}

# ── Event dispatch ─────────────────────────────────────────────────
case "$EVENT" in
  userPromptSubmitted)
    if [[ -n "$PROMPT_TEXT" ]]; then
      increment_session_count
      flush_turn
      start_turn "$PROMPT_TEXT"
    fi
    ;;
  postToolUse)
    if [[ -n "$TOOL_NAME" ]]; then
      increment_turn "$TOOL_NAME" "$INPUT_TOKENS" "$OUTPUT_TOKENS"
    fi
    ;;
  # sessionEnd is handled by track-session.sh
esac

exit 0
