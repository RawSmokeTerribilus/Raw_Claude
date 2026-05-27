---
name: raw-claude-skill-authoring
description: "Use when authoring or editing a SKILL.md inside Raw_Claude. Defines frontmatter shape, size limits, peer-matched structure, and verification checklist for every skill in this repo."
version: 1.0.0
author: Raw_Claude (adapted from Hermes Agent)
license: MIT
platforms: [linux]
metadata:
  raw_claude:
    tags: [ported, meta, skills, authoring, conventions, skill-md]
    related_skills: []
---

# Authoring Raw_Claude Skills

## Overview

Every skill in this repo lives at `skills/<category>/<name>/SKILL.md` (or
`skills/<category>/<group>/<name>/SKILL.md` for grouped skills). This file is the
law: any new or edited SKILL.md must conform to the rules below, because the
smoke-test (`smoke-test.sh`) enforces a subset of them and a fresh Claude Code
session will silently ignore malformed skills.

Source-of-truth for the validator: `smoke-test.sh` `Skill SKILL.md frontmatter
validity` block. The full ruleset below is broader than what smoke-test checks —
treat smoke-test as the floor, not the ceiling.

## When to Use

- You are creating a new skill in `Raw_Claude/skills/`.
- You are editing an existing skill (frontmatter or body).
- You are porting a Hermes Agent skill into this repo.
- You are reviewing a skill in PR.

Do not use for: writing a project-local `.claude/skills/` skill (those follow the
host project's conventions), authoring a hook, or writing top-level docs.

## Required Frontmatter

Hard requirements (smoke-test enforces these):

- File starts with `---` as the first bytes. No leading blank line, no BOM.
- Frontmatter closes with `\n---\n` before the body.
- Frontmatter parses as a YAML mapping.
- `name` field present, lowercase + hyphens, ≤ 64 chars.
- `description` field present, ≤ 1024 chars, starts with `"Use when ..."`.
- Total file ≤ 100,000 chars (target: 8-15k).

Peer-matched shape (every skill in this repo uses this; omit fields = sticks out):

```yaml
---
name: my-skill-name
description: "Use when <trigger>. <one-line behavior>."
version: 1.0.0
author: Raw_Claude
license: MIT
platforms: [linux]
metadata:
  raw_claude:
    tags: [short, descriptive, tags]
    related_skills: [other-skill, another-skill]
---
```

For ported Hermes skills, keep `author: Hermes Agent` and add a second line in
`metadata.raw_claude.tags` indicating `[ported]`. The license attribution must
remain.

## Description Style

The `description` is what Claude Code matches against user prompts. Bad
descriptions = skill never triggers. Good descriptions:

- Start with `"Use when ..."` — describes the **trigger class**, not the task.
- Name concrete nouns: tool names, file types, file paths the skill operates on.
- Stay under 200 chars where possible. 1024 is the cap, not the target.

Bad: `"Debugging Python code."`
Good: `"Use when a Python script throws an unexpected exception, hangs, or needs
remote debug — drives pdb / debugpy / DAP sessions, sets breakpoints, inspects
state."`

## Size Limits

- Description: ≤ 1024 chars (enforced).
- Full SKILL.md: ≤ 100,000 chars (enforced).
- Target: **8-15k chars**. If pushing past 20k, split into
  `references/<topic>.md` and reference them from SKILL.md.

## Peer-Matched Structure

```
# <Title>

## Overview
One or two paragraphs: what and why.

## When to Use
- Bulleted triggers.
- "Don't use for:" counter-triggers.

## <Topic sections specific to the skill>
- Quick-reference tables are common.
- Code blocks with exact commands.
- Concrete paths, not placeholders.

## Common Pitfalls
Numbered list of mistakes and their fixes.

## Verification Checklist
- [ ] Checkbox list of post-action verifications.

## One-Shot Recipes (optional)
Named scenarios → concrete command sequences.
```

Mandatory: `Overview`, `When to Use`, body, `Common Pitfalls`. Verification
checklist is strongly recommended.

## Directory Placement

```
skills/<category>/<skill-name>/SKILL.md
skills/<category>/<group>/<skill-name>/SKILL.md   # for related sets, e.g. github/
```

Categories currently in use (run `ls skills/` to confirm before inventing new
ones):

`creative`, `data-science`, `github`, `mcp`, `media`, `meta`, `mlops`,
`note-taking`, `productivity`, `research`, `software-development`.

Pick the closest existing category. Don't invent new top-level categories without
a real fit — if a skill needs a new category, it probably belongs in an existing
one with a sub-group instead.

## Supporting Files

Allowed subdirs inside a skill dir:

- `references/<file>.md` — long-form material referenced from SKILL.md.
- `templates/<file>` — boilerplate the skill outputs or fills in.
- `scripts/<file>` — runnable helpers (mark `chmod +x`).
- `assets/<file>` — images, sample data.

Anything else triggers a smoke-test warning (TODO: add to smoke-test).

## Workflow

1. **Survey peers** in the target category:
   ```bash
   ls ~/Raw_Vault/Raw_Claude/skills/<category>/
   ```
   Read 2-3 peer SKILL.md files. Match tone, section order, table style.

2. **Draft** with `Write` to `skills/<category>/<name>/SKILL.md`.

3. **Validate locally** before commit:
   ```bash
   ~/Raw_Vault/Raw_Claude/smoke-test.sh
   ```
   Look for the `Skill SKILL.md frontmatter validity` block — must report
   `all SKILL.md frontmatters valid`.

4. **Commit on a branch**:
   ```bash
   cd ~/Raw_Vault/Raw_Claude && git checkout -b skill/<name>
   git add skills/<category>/<name>/
   git commit -m "skills: add <name>"
   ```

5. **Reload in a new Claude Code session.** The skill loader caches at session
   start — the current session will not see a new skill. This is expected.

## Cross-Referencing Other Skills

Claude Code does not resolve `related_skills` at load time the way Hermes does.
Use `[[skill-name]]` wiki-links in the body for human/Obsidian navigation.

The `metadata.raw_claude.related_skills` array stays for documentation: it tells
a human reader what to read next. Keep it. It's free.

## Porting Hermes Skills

Adapter rules:

1. Copy the entire skill dir under `~/.hermes/skills/<category>/<name>/` to
   `Raw_Vault/Raw_Claude/skills/<category>/<name>/`.
2. In SKILL.md frontmatter, rename `metadata.hermes` → `metadata.raw_claude`.
3. Add `[ported]` to `tags` so the source is greppable.
4. Reduce `platforms` to `[linux]` (this repo's target).
5. Body edits:
   - Replace any `/home/bb/hermes-agent/` paths with `~/Raw_Vault/Raw_Claude/`.
   - Replace `skill_manage(...)`, `write_file(...)`, `delegate_task(...)`, or
     other Hermes-only tool references with Claude Code equivalents (`Write`,
     `Edit`, `Agent`, `Bash`).
   - Drop sections that only make sense inside the Hermes runtime (e.g.
     "Hermes-specific recipes" about `scripts/run_tests.sh`).
   - Keep MIT attribution.
6. Re-run smoke-test before commit.

## Common Pitfalls

1. **Leading whitespace or BOM before `---`.** Validator checks
   `content.startswith("---")`; anything before fails.

2. **Description doesn't start with "Use when".** Claude Code's fuzzy matcher
   pairs user prompts against the trigger phrasing. "Debug Python" matches less
   reliably than "Use when a Python script throws an unexpected exception".

3. **Description >1024 chars.** Looks fine in your editor, fails at load. Run
   smoke-test before commit.

4. **Forgetting `author` / `license` / `metadata.raw_claude`.** Not validator-
   enforced, but every peer has them. Omitting makes the skill look half-finished
   and breaks PR review polish.

5. **Writing a skill that duplicates a peer.** Before creating, `ls` the
   category dir and open 2-3 peers. Prefer extending an existing skill to
   creating a narrow sibling.

6. **Expecting the current session to load the new skill.** It won't. The skill
   loader is initialized at session start. Verify in a fresh session.

7. **Hardcoding `/home/bb/` or `~/.hermes/` paths in a ported skill.** Grep for
   them after porting:
   ```bash
   grep -rE '/(home/bb|\.hermes)/' skills/<category>/<name>/
   ```

8. **Skipping `references/` split on large skills.** If a SKILL.md is past 20k
   chars, the agent's context cost per load goes up. Split.

## Verification Checklist

- [ ] File is at `skills/<category>/<name>/SKILL.md` (or grouped subdir).
- [ ] Frontmatter starts at byte 0 with `---`, closes with `\n---\n`.
- [ ] `name`, `description`, `version`, `author`, `license`, `platforms`,
      `metadata.raw_claude.{tags, related_skills}` all present.
- [ ] `name` ≤ 64 chars, lowercase + hyphens.
- [ ] `description` ≤ 1024 chars and starts with `"Use when ..."`.
- [ ] Total file ≤ 100,000 chars (aim 8-15k).
- [ ] Structure: `# Title` → `## Overview` → `## When to Use` → body →
      `## Common Pitfalls` → `## Verification Checklist`.
- [ ] No `/home/bb/` or `~/.hermes/` paths in body (for ported skills).
- [ ] `smoke-test.sh` reports `all SKILL.md frontmatters valid`.
- [ ] Commit on a branch named `skill/<name>` (or `skill/edit-<name>`).
