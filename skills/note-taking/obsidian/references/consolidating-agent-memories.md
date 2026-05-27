# Consolidating Agent-Specific Memories into Agent-Agnostic Notes

After triaging an imported AI memory dump (see `triaging-imported-ai-memories.md`), the retained files are typically still split by source agent: `memories/claude/`, `memories/copilot/`, etc. Inside Hermes — where any model can be swapped in — this split is meaningless. Consolidate into topical, agent-agnostic notes.

## Why consolidate

- Any model behind Hermes uses the same `read_file`/`write_file`/`search_files` against the vault. There's no `.claude/` convention, no `.copilot/` convention.
- Agent-specific dirs create duplicate coverage (both Claude and Copilot may have notes about the same system).
- A flat topical structure makes `search_files` results unambiguous.

## Workflow

### 1. Read everything first

Read all memory files from all agent dirs. Use `execute_code` to batch-read and print previews (filename, size, first 500-800 chars) — faster than individual `read_file` calls when there are 40+ files.

### 2. Identify topical clusters

Group by infrastructure domain, not by source agent. Common clusters for a homelab user:
- Per-service notes (tracker, SIEM, monitoring, media management)
- Network/hardware topology
- Security posture and audit state
- Operational gotchas and lessons learned
- Git/deploy workflows
- Session logs (historical incident summaries)

### 3. Write consolidated notes

One markdown file per topic under a `Knowledge/` (or similar) top-level dir. Each note should:
- Merge overlapping content from multiple agent sources into a single coherent document
- Preserve specific technical details: exact paths, ports, container names, config values, error strings
- Flag status (deployed, pending, shelved) where the source memories had it
- Include "why" context when it existed — gotchas are only useful if the reason is preserved

### 4. Handle hash-named blobs (snippets)

Claude Code stores conversation snippets as hash-named `.txt` files. These are raw terminal output, debug logs, and session transcripts — not readable as notes.

**Don't just delete them.** Summarize first:
- Batch-read with `execute_code`, categorize by content keywords
- Write a single `Snippets-Archive-Summary.md` that distills the operational history by topic
- Then the raw blobs can be safely removed

### 5. Remove old agent-specific dirs

Once consolidated notes are written and verified, `rm -rf` the `memories/claude/`, `memories/copilot/` dirs. The information now lives in the topical notes.

### 6. Final structure

Target shape:
```
Vault/
├── Knowledge/
│   ├── Infrastructure/
│   │   ├── <Service-A>.md
│   │   ├── <Service-B>.md
│   │   └── ...
│   ├── Operational-Gotchas.md
│   ├── Git-Deploy.md
│   └── Session-Logs.md
├── <retained raw history>/    (chats, plans, topics — kept as reference)
└── 00 - Start Here.md
```

## Pitfalls

- **Don't skip the snippet summarization step.** Hash-named blobs look like junk but often contain the only record of deployment sequences, debug sessions, and config states.
- **Copilot repo-state files often overlap with Claude project files.** The Copilot version tends to have tighter container/port tables; Claude's tend to have more narrative context. Merge the best of both.
- **User profile notes from different agents may conflict** (e.g., one says GitHub banned, another says restored). Use the most recent information and note the timeline.
- **Export `OBSIDIAN_VAULT_PATH`** (in your shell profile or a personal env file outside this repo) after consolidation so all future sessions resolve the vault path without guessing.
