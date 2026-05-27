#!/usr/bin/env bash
# SessionStart hook: inject SOUL.md into Claude Code context.
# Claude Code hooks read JSON on stdout; the `additionalContext` field is appended
# to the system prompt for the session.
set -euo pipefail

SOUL_PATH="${HOME}/Raw_Vault/Raw_Claude/SOUL.md"

if [[ ! -f "$SOUL_PATH" ]]; then
    # No SOUL file = no-op, don't fail SessionStart.
    printf '{}\n'
    exit 0
fi

# Emit JSON with the SOUL file contents as additionalContext.
# Using python for safe JSON escaping (jq may not be on every host).
python3 -c '
import json, sys, pathlib
soul = pathlib.Path(sys.argv[1]).read_text()
print(json.dumps({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": soul}}))
' "$SOUL_PATH"
