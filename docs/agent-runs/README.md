# Agent runs

Durable state for long or unattended engineering sessions.

One folder per run: `<date>-<task-slug>/`, containing

- `PLAN.md` — milestones, risks, validation commands
- `ACCEPTANCE.json` — atomic `AC-###` criteria
- `RUN.md` — state, decisions, evidence, findings, next action
- `evidence/` — command logs, runtime captures, screenshots

Copy the starting files from `_templates/`.
