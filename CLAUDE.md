# pyworkforce — Claude Code Instructions

This file currently carries only the shared engineering workflow. Add this
project's stack, commands, architecture, and gotchas as they are established.

## Autonomous engineering workflow

For multi-step, unattended, high-risk, or mockup-driven implementation, invoke
`/autonomous-run` and follow its companion-skill graph.

- Build atomic acceptance criteria with `/acceptance-contract` before material code changes.
- Use `/verification-loop` for every material behavior change.
- Use `/visual-fidelity` for every mockup, screenshot, Figma, responsive, or UI-state requirement.
- Use `/security-domain-review` for auth, payments, permissions, tenancy, secrets,
  entitlements, sensitive data, webhooks, or destructive migrations.
- The implementer cannot be the sole reviewer. No evidence means not complete.
- When Jira exists, Jira is the canonical work/backlog/status source. Do not maintain a second backlog locally.
- When Confluence exists, persist only long-lived project knowledge there; do not store execution logs or temporary agent state.
- Long sessions may use `.agent-runs/<task>/SESSION.md` plus optional evidence as ephemeral memory only. Do not commit it.
- Prefer `.git/info/exclude` for local exclusion of `.agent-runs/`.
- At normal session finalization, synchronize durable state to canonical systems and delete the run directory automatically.

These five skills are installed at user scope and are available in every repository.
