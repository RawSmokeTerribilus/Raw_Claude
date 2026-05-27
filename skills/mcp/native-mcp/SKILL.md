---
name: native-mcp
description: "Use when configuring MCP servers for Claude Code — adding new servers (stdio or HTTP), debugging discovery failures, scoping tool permissions, or auditing which servers are loaded."
version: 1.0.0
author: Raw_Claude (adapted from Hermes Agent / native-mcp)
license: MIT
platforms: [linux]
metadata:
  raw_claude:
    tags: [ported, mcp, tools, integrations, config]
    related_skills: []
---

# Native MCP Configuration for Claude Code

## Overview

Claude Code has a built-in MCP client. Configured servers are launched at session start,
their tools are discovered, and each tool is exposed under the name
`mcp__<server>__<tool>`. Tools from MCP servers behave like first-class tools alongside
`Read`, `Bash`, `Edit`, etc.

This skill covers: where to configure servers, the JSON schema, transport types (stdio
vs HTTP), permission scoping, and the most common discovery failures.

## When to Use

- You want to add an MCP server (filesystem, GitHub, Postgres, a custom one).
- A previously-working server stops loading and you need to debug discovery.
- You're auditing which MCP tools the agent has access to in a given project.
- You're tightening permissions around an MCP server (e.g. read-only filesystem).

Don't use for: writing an MCP **server** from scratch (that's a separate skill);
operating MCP via Anthropic's hosted Managed MCP — this is the local stdio/HTTP path.

## Where MCP Config Lives

Three scopes, in increasing specificity:

| Scope     | File                            | Loaded for                              |
|-----------|---------------------------------|-----------------------------------------|
| User      | `~/.claude/settings.json`       | Every Claude Code session for this user |
| Project   | `<repo>/.mcp.json`              | Sessions started inside that repo       |
| Local     | `~/.claude/settings.local.json` | This user, this machine (not synced)    |

Project-scope wins over user-scope; local overrides both. The key in all three files
is `mcpServers` (camelCase, distinct from Hermes' `mcp_servers:` YAML block).

## Minimal Setup

User-wide time server via `uvx`:

```jsonc
// ~/.claude/settings.json
{
  "mcpServers": {
    "time": {
      "command": "uvx",
      "args": ["mcp-server-time"]
    }
  }
}
```

Restart Claude Code. The tool will appear as `mcp__time__get_current_time` (or similar,
depending on what the server exports).

## Adding Servers via CLI

You can also add servers without hand-editing JSON:

```bash
# stdio server, user scope
claude mcp add --scope user time uvx mcp-server-time

# stdio server with args + env
claude mcp add --scope user github \
  --env GITHUB_PERSONAL_ACCESS_TOKEN \
  -- npx -y @modelcontextprotocol/server-github

# list, view, remove
claude mcp list
claude mcp get time
claude mcp remove time --scope user
```

The CLI is preferred when you're scripting setup; the JSON file is preferred when you
want the config tracked in source control (project-scope `.mcp.json`).

## Configuration Reference

Each entry under `mcpServers` is a server name mapped to its config. Two transport
types: **stdio** (local subprocess) and **HTTP** (remote URL).

### Stdio Transport

```jsonc
{
  "mcpServers": {
    "server_name": {
      "command": "npx",                  // required: executable to run
      "args": ["-y", "pkg-name"],        // optional: command args, default []
      "env": { "API_KEY": "value" }      // optional: env vars passed to subprocess
    }
  }
}
```

### HTTP Transport

```jsonc
{
  "mcpServers": {
    "server_name": {
      "url": "https://my-server.example.com/mcp",
      "headers": { "Authorization": "Bearer ..." }
    }
  }
}
```

A server config must have either `command` (stdio) or `url` (HTTP), never both.

## Tool Naming

MCP tools appear inside Claude Code as:

```
mcp__<server>__<tool>
```

Note **double underscore** between server and tool — different from Hermes' single
underscore convention. Hyphens and dots in names become underscores for API
compatibility.

Examples:
- Server `filesystem`, tool `read_file` → `mcp__filesystem__read_file`
- Server `github`, tool `list-issues` → `mcp__github__list_issues`

## Permissions

By default, MCP tools require interactive approval on each call. To pre-allow specific
tools, add them to `permissions.allow` in `~/.claude/settings.json`:

```jsonc
{
  "permissions": {
    "allow": [
      "mcp__filesystem__read_file",
      "mcp__filesystem__list_directory",
      "mcp__time__*"
    ]
  }
}
```

Wildcards work at the tool level. Prefer narrow allowlists for any server that can
mutate state (write, delete, exec).

## Environment Variable Handling

For stdio servers, Claude Code passes only the variables you explicitly list under
`env:`. The rest of your shell environment is **not** inherited. This is intentional —
it stops you from leaking arbitrary API keys to a third-party MCP server.

If you need an env var, pass it explicitly:

```jsonc
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

The `${env:VAR}` syntax pulls from the parent shell at server-launch time. Never
hardcode secrets in `settings.json` — use this indirection or pass via a wrapper
script.

## Auditing Loaded Servers

In a session:

```bash
# from the Claude Code prompt
/mcp
```

The `/mcp` slash command shows: each server name, transport, connection status,
and the list of tools it exposed. If a server failed to load, the reason is reported
here.

From the shell:

```bash
claude mcp list                  # configured servers across scopes
claude mcp get <server>          # show resolved config for one server
```

## Common Pitfalls

1. **Editing `settings.json` while a session is open.** MCP discovery happens at
   session start. You must exit and re-launch the CLI for changes to take effect.

2. **Wrong key name.** It's `mcpServers` (camelCase) in JSON. The Hermes YAML
   convention was `mcp_servers:` — don't carry that habit over.

3. **Forgetting `-y` for npx servers.** Without `-y`, npm prompts interactively
   to install the package and the subprocess hangs at startup. Discovery times out.

4. **Hardcoded secrets in `settings.json`.** If `settings.json` is ever committed
   or shared, the secret leaks. Use `${env:VAR}` indirection or a wrapper script.

5. **PATH not finding `uvx` / `npx`.** Claude Code inherits the PATH of the shell
   that launched it. If `uvx` is installed in a Python venv that isn't activated,
   discovery fails. Either activate the venv before launching or use absolute paths
   (`/home/<user>/.local/bin/uvx`).

6. **Project `.mcp.json` overrides user `settings.json` silently.** If a server
   you expect from user scope doesn't appear in a project, check for a
   `.mcp.json` in the repo root — project scope wins.

7. **HTTP transport URL without `/mcp` suffix.** Most servers require the path
   suffix; copy-pasting the bare host gets a 404 with no useful error.

## Troubleshooting

### Tool doesn't appear under `mcp__<server>__*`

- Run `/mcp` in-session and check the server's status line. `failed` = read the
  error message there.
- If `unknown server`: the server name in `settings.json` doesn't match what
  you're looking at. Spelling counts.
- If `connected` but no tools: the server's `list_tools` returned empty.
  Usually means the server itself is misconfigured (wrong DB URL, missing token,
  etc).

### "Command not found"

The `command:` value isn't on PATH at the time Claude Code launches the
subprocess. Test:

```bash
which <command>
# if empty: it's not on PATH; use absolute path in args
```

### Subprocess hangs at startup

Most common cause: an npm package not yet installed, with `-y` missing from args.
Less common: server expects an env var you didn't pass.

Run the command manually:

```bash
<command> <args...>
# observe what it asks for; fix env or args
```

### HTTP transport unreachable

```bash
curl -i -H "Authorization: Bearer <token>" "https://your-mcp-host/mcp"
# expect HTTP 200 with an SSE or JSON-RPC handshake
```

If `curl` works but Claude Code reports failure, check that your token has the
expected scope and that the URL exactly matches what's in `settings.json`.

## Verification Checklist

- [ ] `mcpServers` key (camelCase, JSON).
- [ ] Each server has `command` (stdio) **or** `url` (HTTP), never both.
- [ ] Stdio servers: `command` resolves on PATH from a fresh shell.
- [ ] Secrets passed via `${env:VAR}` indirection, not hardcoded.
- [ ] Tool allow-list narrowed to specific tools (or `<server>__*` wildcards),
      not blanket `*`.
- [ ] `/mcp` in a fresh session shows the server as `connected` with the
      expected tool list.
- [ ] No `mcp_servers:` YAML leftover from a Hermes config — Claude Code reads
      only JSON.

## One-Shot Recipes

### Filesystem server, read-only over a single directory

```jsonc
{
  "mcpServers": {
    "fs_docs": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/<user>/Documents"]
    }
  },
  "permissions": {
    "allow": [
      "mcp__fs_docs__read_file",
      "mcp__fs_docs__list_directory"
    ]
  }
}
```

Excludes `write_file` from the allowlist → server can still expose the tool, but the
agent must request approval to use it.

### GitHub server with env-passed PAT

```jsonc
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  }
}
```

Export the PAT in your shell profile, not in `settings.json`. If `gh auth` is already
set up, you can fetch the token at shell startup:

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN="$(gh auth token 2>/dev/null)"
```

### Remote HTTP server

```jsonc
{
  "mcpServers": {
    "team_mcp": {
      "url": "https://mcp.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:TEAM_MCP_TOKEN}"
      }
    }
  }
}
```
