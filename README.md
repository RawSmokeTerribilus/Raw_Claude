# Raw_Claude

Personal Claude Code CLI configuration: skills, hooks, agent charter, recovery scripts.
Source-of-truth for everything Claude Code-related on `rawserver`. Lives inside the
Obsidian vault so notes, skills, and references cross-link naturally.

## Why this exists

Claude Code installs to `~/.local/share/claude/versions/<ver>/` and self-updates on a
fast cadence (multiple minors per week). Data dir `~/.claude/` survives updates, but
its schema, hook contract, and skill loader can change between versions. Anchoring on
a single version is a losing fight. The strategy is the opposite: **no anchor, fast
recovery**.

- `~/.claude/skills/raw/` is a symlink to `skills/` in this repo.
- `~/.claude/` itself is git-tracked separately (or backed up before any update).
- A new Claude Code release that breaks something = `git reset --hard <last-good>` here +
  rollback the binary symlink to the previous version in `~/.local/share/claude/versions/`.

## Layout

```
Raw_Claude/
├── README.md                          this file
├── SOUL.md                            global agent charter (persona/voice/values)
├── settings.json.template             baseline ~/.claude/settings.json
├── smoke-test.sh                      post-update validator
├── hooks/                             SessionStart, UserPromptSubmit, etc.
├── skills/                            ported + adapted from Hermes Agent
│   ├── meta/raw-claude-skill-authoring/   the law for new skills
│   ├── creative/
│   ├── data-science/
│   ├── github/
│   ├── mcp/
│   ├── media/
│   ├── mlops/
│   ├── note-taking/
│   ├── productivity/
│   ├── research/
│   └── software-development/
├── scripts/                           backup/restore, version pin/rollback
└── references/                        long-form reference material
```

## Origins

Skills are adapted from [Hermes Agent](https://github.com/NousResearch/hermes-agent)
under MIT license. Each ported `SKILL.md` retains the original `author: Hermes Agent`
+ `license: MIT` lines. Local modifications:

- `metadata.hermes.*` → `metadata.raw_claude.*`
- Hermes-only tool references (`skill_manage`, `delegate_task`, `/home/bb/hermes-agent/`)
  removed or replaced with Claude Code equivalents (`Write`, `Edit`, `Agent`, this repo's
  path).
- `platforms` reduced to `[linux]` (RHEL 10 target).

## Conventions

All new skills MUST follow `skills/meta/raw-claude-skill-authoring/SKILL.md`. It codifies
the frontmatter shape, size limits, peer-matched structure, and verification checklist.

## Remotes

- Codeberg (primary): `git@codeberg.org:RawSmoke/Raw_Claude.git`
- GitHub (mirror):    `git@github.com:RawSmokeTerribilus/Raw_Claude.git`

Push to both on every release tag. SSH keys, not PATs — no token expiry surface.

## Not in this repo

- Homelab infra docs (`~/Raw_Vault/Hardening/`) — local + encrypted backups only, never
  pushed to a public remote (OPSEC).
- Secrets — `~/.claude/` may contain auth artifacts; see `.gitignore`.
- `~/.claude/projects/` session logs — ephemeral.
