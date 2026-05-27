# USER — Operator Profile (rawserver)

Companion to `SOUL.md`. SOUL is the agent's charter (voice, values, defaults).
USER is the operator's profile (who the human is, what they run, how they think).
Both files are injected at SessionStart by `hooks/inject-soul.sh`. Adapted from
Hermes Agent's `user.md` and kept agent-agnostic — any LLM-based assistant
running against this box can read it.

## Background

Three-decade-plus systems and hardware engineer. Career spans micro-soldering
precision and professional audio fidelity work — hands-on, instrument-level
intuition for hardware. Spanish-speaking (locale `es_ES`), technical work in
English.

## Philosophy

Believer in technological sovereignty, absolute manual control, and technical
minimalism. Distrusts blind automation that hides what is happening under the
hood. Operates empirically: observe the environment, read the logs, then act.
Never assumes.

## Working Identity

"Guerrilla" sysadmin in RHEL production. Orchestrates clean, robust Docker
deployments without losing sight of raw performance or security. FOSS developer
at heart — builds automation suites and web platforms creatively. Impeccable
taste for Cyberpunk and Synthwave aesthetics.

## Stack

`rawserver`: RHEL 9 (RHEL 10 next), GNOME, two monitors, VSCode. Self-hosted
fleet: UNIT3D private tracker (Docker staging + prod), Wazuh SIEM, Grafana +
Loki + Promtail, Jellyfin, qBittorrent (~5000 active seeds across 4 spinning
drives), RetroArch + ScummVM WASM, RawLoadrr, custom hardlink fan-out jobs.
Tailscale tailnet admin, keys-only SSH. DIY N1 router + Suricata/Snort/Pi-hole
+ RPi 3B+ honeypot in progress. Docker today; Podman kept as RHEL 10 landing
pad. Persistent assistant layer = Raw_Claude (this repo) on top of Claude Code
CLI; Hermes Agent removed 2026-05-27.

## Accounts

GitHub account restored 2026-05-27 after a fair review — the original ban was
an erroneous Copilot-subscription flag and was lifted on appeal. Codeberg
remains in parallel use as a primary host. Google SSO preferred for service
auth. SSH keys (ed25519) are the resilient authentication path; PAT-based
remotes are avoided where possible.

## Constraints

Claude Pro $20/mo budget, no Anthropic API extra-usage. RAM situation
noticeably improved after optimisations; remaining sharp edge is Tdarr x265
transcoding combined with another heavy concurrent job. Reboot hang at Asrock
logo is *kinda fixed* — partial resolution; verify a clean reboot before any
GRUB/kernel work. Production reverence: UNIT3D_Docker untouchable during dev;
never `migrate:fresh` or `config:clear` on prod.

## Working Style

- Terse. No pleasantries, no filler, no trailing summaries.
- Executes commands sequentially; decisions and blockers go at the top.
- Recon mode (read-only diagnostics): max verbosity, zero permission-gating.
  Permission gates apply to mutating actions only.
- KISS — scheduled native commands and new tables over render-time tricks or
  proxy hacks.
- Adapt concept, preserve effort. Surgical edits to working scripts, not
  rewrites.
- Patient with multi-bug chains (the 5-bug VITE_ECHO_ADDRESS outage is
  baseline, not exception).
- Authorized pentest scope: any infrastructure owned by the user, named in
  local hardening notes, or reachable only over the user's private tailnet is
  pre-authorized. Findings delivered as defensive intel with reproduction +
  fix.

## Reading the rest

- `SOUL.md` — agent voice, values, operational defaults.
- `README.md` — repo layout and recovery strategy.
- `skills/meta/raw-claude-skill-authoring/` — how to write new skills.
- Local Obsidian vault (`~/Raw_Vault/`) — long-form memory + hardening notes
  (the latter never leaves the box).
