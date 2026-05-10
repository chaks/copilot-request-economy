#!/bin/bash
set -e

echo "Installing Copilot Request Economy Harness v2..."
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Target directories
HOOKS_DIR="${HOME}/.copilot/hooks"
INSTR_DIR="${HOME}/.copilot/instructions"
LIB_DIR="${HOME}/.copilot/lib"
RUNTIME_DIR="${HOME}/.copilot-orchestrator"

# Copy hooks
mkdir -p "$HOOKS_DIR"
for hook_dir in "${SCRIPT_DIR}/hooks/"*; do
  if [ -d "$hook_dir" ]; then
    hook_name=$(basename "$hook_dir")
    rm -rf "${HOOKS_DIR}/${hook_name}" 2>/dev/null || true
    cp -r "$hook_dir" "${HOOKS_DIR}/${hook_name}"
    chmod +x "${HOOKS_DIR}/${hook_name}"/*.sh 2>/dev/null || true
    echo "  Installed hook: ${HOOKS_DIR}/${hook_name}"
  fi
done

# Copy instructions
if [ -d "${SCRIPT_DIR}/instructions" ]; then
  mkdir -p "$INSTR_DIR"
  cp "${SCRIPT_DIR}/instructions/"* "$INSTR_DIR"/ 2>/dev/null || true
  echo "  Installed instructions: ${INSTR_DIR}"
fi

# Copy Python library
if [ -d "${SCRIPT_DIR}/lib" ]; then
  rm -rf "$LIB_DIR" 2>/dev/null || true
  cp -r "${SCRIPT_DIR}/lib" "$LIB_DIR"
  echo "  Installed lib: ${LIB_DIR}"
fi

# Copy config template (don't overwrite existing config)
mkdir -p "$RUNTIME_DIR"
if [ ! -f "${RUNTIME_DIR}/config.json" ]; then
  cp "${SCRIPT_DIR}/config.json.example" "${RUNTIME_DIR}/config.json"
  echo "  Created config.json from template -- edit to customize settings."
fi

# Initialize budget if not exists
if [ ! -f "${RUNTIME_DIR}/budget.json" ]; then
  CURRENT_MONTH=$(date -u +%Y-%m)
  cat > "${RUNTIME_DIR}/budget.json" << EOF
{
  "month": "${CURRENT_MONTH}",
  "used": 0,
  "limit": 300,
  "requests": []
}
EOF
  echo "  Initialized budget.json"
fi

# Ensure dependencies
if ! command -v python3 &> /dev/null; then
  echo "ERROR: python3 is required but not installed."
  exit 1
fi

# Post-install verification: ensure the lib is importable
PYTHON_CHECK=$(python3 -c "
import sys; sys.path.insert(0, '${LIB_DIR}')
try:
    from classify import classify_task
    from account import load_budget
    from config import load_config
    print('ok')
except Exception as e:
    print(f'error: {e}')
" 2>&1)
if [[ "$PYTHON_CHECK" != "ok" ]]; then
  echo ""
  echo "WARNING: Python lib verification failed: ${PYTHON_CHECK}"
  echo "  The hooks will not work until this is fixed."
fi

echo ""
echo "Copilot Request Economy Harness v2 installed!"
echo ""
echo "Installed to: ${HOME}/.copilot/"
echo ""
echo "Next steps:"
echo "  1. Run 'copilot' to start a new session"
echo "  2. Budget tracking is active immediately"
echo ""
