#!/usr/bin/env bash
# SessionStart hook: inject SOUL.md (agent charter) + USER.md (operator profile)
# into Claude Code context. Claude Code hooks read JSON on stdout; the
# `hookSpecificOutput.additionalContext` field is appended to the system prompt
# for the session.
set -euo pipefail

REPO="${HOME}/Raw_Vault/Raw_Claude"
SOUL="${REPO}/SOUL.md"
USER="${REPO}/USER.md"

# Build the concatenated context. If either file is missing, the hook still
# emits valid JSON (no-op) rather than failing SessionStart.
python3 - "$SOUL" "$USER" <<'PY'
import json, sys, pathlib
parts = []
labels = ["SOUL", "USER"]
for label, path in zip(labels, sys.argv[1:]):
    p = pathlib.Path(path)
    if p.is_file():
        parts.append(f"<!-- {label} from {p} -->\n{p.read_text()}")
if not parts:
    print(json.dumps({}))
    sys.exit(0)
ctx = "\n\n".join(parts)
print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": ctx,
    }
}))
PY
