#!/usr/bin/env bash
# Post-update validator for Claude Code on rawserver.
# Run after every `~/.local/bin/claude` symlink bump.
# Exits non-zero if anything Raw_Claude depends on is broken.
set -uo pipefail

PASS=0
FAIL=0
fail() { printf '  [FAIL] %s\n' "$1"; FAIL=$((FAIL+1)); }
pass() { printf '  [ OK ] %s\n' "$1"; PASS=$((PASS+1)); }

printf '== Claude Code binary ==\n'
if claude --version >/dev/null 2>&1; then
    pass "claude --version: $(claude --version)"
else
    fail "claude --version failed"
fi

printf '\n== Versions dir state ==\n'
VDIR="${HOME}/.local/share/claude/versions"
if [[ -d "$VDIR" ]]; then
    pass "versions dir exists: $(ls "$VDIR" | tr '\n' ' ')"
else
    fail "versions dir missing: $VDIR"
fi
LINK="${HOME}/.local/bin/claude"
if [[ -L "$LINK" ]]; then
    pass "symlink resolves: $(readlink "$LINK")"
else
    fail "symlink missing or not a link: $LINK"
fi

printf '\n== Raw_Claude paths ==\n'
for p in \
    "${HOME}/Raw_Vault/Raw_Claude/SOUL.md" \
    "${HOME}/Raw_Vault/Raw_Claude/skills" \
    "${HOME}/Raw_Vault/Raw_Claude/hooks/inject-soul.sh" \
    "${HOME}/.claude/settings.json" \
    "${HOME}/.claude/skills/raw"; do
    if [[ -e "$p" ]]; then pass "$p"; else fail "$p missing"; fi
done

printf '\n== Symlink ~/.claude/skills/raw -> Raw_Claude/skills ==\n'
EXPECTED="${HOME}/Raw_Vault/Raw_Claude/skills"
ACTUAL=$(readlink "${HOME}/.claude/skills/raw" 2>/dev/null || echo "")
if [[ "$ACTUAL" == "$EXPECTED" ]]; then
    pass "symlink target correct"
else
    fail "symlink target wrong: expected '$EXPECTED', got '$ACTUAL'"
fi

printf '\n== SessionStart hook is executable ==\n'
HOOK="${HOME}/Raw_Vault/Raw_Claude/hooks/inject-soul.sh"
if [[ -x "$HOOK" ]]; then pass "$HOOK executable"; else fail "$HOOK not executable"; fi

printf '\n== Hook emits valid JSON ==\n'
if "$HOOK" 2>/dev/null | python3 -c 'import json,sys; json.load(sys.stdin)' 2>/dev/null; then
    pass "hook stdout is valid JSON"
else
    fail "hook stdout is NOT valid JSON"
fi

printf '\n== Skill SKILL.md frontmatter validity ==\n'
BAD=0
while IFS= read -r f; do
    python3 - "$f" <<'PY' || BAD=$((BAD+1))
import sys, yaml, re, pathlib
p = pathlib.Path(sys.argv[1])
c = p.read_text()
if not c.startswith('---'):
    print(f"  [FAIL] {p}: no leading ---"); sys.exit(1)
m = re.search(r'\n---\s*\n', c[3:])
if not m:
    print(f"  [FAIL] {p}: no closing ---"); sys.exit(1)
fm = yaml.safe_load(c[3:m.start()+3])
if not isinstance(fm, dict):
    print(f"  [FAIL] {p}: frontmatter not a mapping"); sys.exit(1)
if 'name' not in fm or 'description' not in fm:
    print(f"  [FAIL] {p}: missing name/description"); sys.exit(1)
if len(fm['description']) > 1024:
    print(f"  [FAIL] {p}: description >1024 chars"); sys.exit(1)
if len(c) > 100_000:
    print(f"  [FAIL] {p}: file >100k chars"); sys.exit(1)
PY
done < <(find "${HOME}/Raw_Vault/Raw_Claude/skills" -name SKILL.md 2>/dev/null)
if [[ "$BAD" -eq 0 ]]; then
    pass "all SKILL.md frontmatters valid"
else
    fail "$BAD skill(s) failed validation"
fi

printf '\n== Summary ==\n'
printf '  PASS: %d   FAIL: %d\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]]
