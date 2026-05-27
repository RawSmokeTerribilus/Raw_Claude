# Triaging Imported AI Memory Dumps

When a vault contains bulk-imported memories from other AI tools (Claude Code `.claude/`, Copilot `.copilot/`, etc.), the dump is usually a messy flat export that mixes real user context with stock scaffolding.

## Triage approach

1. **Map the structure first.** `search_files(target="files", pattern="*.md")` on the vault, then `find` with `wc -l` and `du -sh` to get scale and weight. Don't read individual files until the shape is clear.

2. **Classify by directory, not by file.**
   - `memories/claude/` — user project context, feedback, references. Almost always worth keeping.
   - `memories/copilot/` — repo state snapshots, translation notes. Usually worth keeping.
   - `topics/`, `chats/`, `plans/`, `prompts/` — real work history. Keep.
   - `skills/claude-plugins/plugins/` — stock Claude Code plugin scaffolding (LSP READMEs for every language, plugin-dev boilerplate, math-olympiad, playground templates). Almost never the user's own work. **Smash.**
   - `catalog/`, `snippets/` — inspect before deciding; often stock.
   - Stray source files (`.php.md`, `.js.md`) — someone wrapped a source file in markdown. Doesn't belong in a vault.

3. **Quantify the junk.** Break down file counts per plugin dir with a loop:
   ```bash
   find "<skills-dir>/plugins" -mindepth 1 -maxdepth 1 -type d | while read d; do
     count=$(find "$d" -type f | wc -l)
     printf "%3d  %s\n" "$count" "$(basename "$d")"
   done | sort -rn
   ```
   This makes the bloat visible and lets the user make a fast smash/pass call.

4. **Present the verdict as keep-list vs nuke-list.** User decides scope, agent executes.

## Common stock plugin dirs (safe to nuke)

These are default Claude Code plugin scaffolding — not user-created:
- `plugin-dev` (45+ files of boilerplate)
- `mcp-server-dev` (20+ files)
- `code-modernization`
- `hookify`, `math-olympiad`, `playground`
- All `*-lsp` dirs (swift, typescript, rust-analyzer, ruby, pyright, php, lua, kotlin, jdtls, gopls, csharp, clangd)
- `example-plugin`, `cwc-makers`, `agent-sdk-dev`
- `explanatory-output-style`, `learning-output-style`

## Snippets deserve a second look

`snippets/` dirs (hash-named `.txt` files) look like disposable blobs but often contain the only record of deployment sequences, terminal sessions, debug chains, and config states. **Before nuking, ask the user if they want a summary.** Batch-read → categorize by keyword → write a single consolidated summary note. The raw blobs can go after that.

## After cleanup

- Flatten the directory structure if it's needlessly nested.
- Export `OBSIDIAN_VAULT_PATH` in your shell profile or a personal env file (kept outside this repo).
- Consider wikilinks between retained notes for Obsidian graph navigation.
- If the retained memories are still split by source agent, consolidate into agent-agnostic topical notes. See `consolidating-agent-memories.md`.
