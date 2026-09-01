# Review configuration — schema: v5

## Project
- Stack: Django (Python 3.13, uv-managed) + Bootstrap 5/HTMX/D3 frontend (webpack/yarn) + PostgreSQL 18 (docker-compose) / SQLite fallback
- Platform: github — christoph-teichmeister/yamsa
- Setup scope: team

## Output
- Mode: remote (threads on the MR/PR)
- Report: -

## Comments
- System: conventional-comments
- Labels: issue: security risks, bugs, violated project conventions; suggestion: potential performance problems, working-but-unclean code; nitpick: formatting, naming; question: unclear requirements, "new rule or exception?"
- Change listing at start: yes

## Ticket
- Source: branch-id (pattern: `feature/#<n>-slug` | `bugfix/#<n>-slug`, issues via gh)

## Prerequisites (state before a review runs)
| Service | Check | Owner | Fallback if down |
|---|---|---|---|
| gh CLI auth | `gh auth status` | user | abort |
| Browser (playwright-cli) | `command -v playwright-cli` | user | skip content-review/walkthrough |
| Local Postgres (docker-compose) | `docker compose ps database` | user | fall back to SQLite via `DJANGO_DATABASE_URL` |

## Credentials
- Test login: see environment.md `## Test login`

## Flows
- - (follow the ticket's acceptance criteria)

## Project specifics (pointers only, no rule text)
- AGENTS.md — hard rules, temp-file rule, comment policy (binding)
- docs/ai/architecture.md — project structure, coding conventions, design system, forms-vs-views pattern
- docs/ai/testing.md — test layout and factory conventions
- docs/ai/workflow.md — commit/PR conventions, PR review workflow
- .claude/beyonder/stack.md — review checklist for this stack

## Review behavior
- Confidence: threshold:80 (rest folded into summary)
- Nitpick budget: 3
- Language: de (team decision 2026-09-01 — code/comments stay English, tickets and PR-facing text incl. review findings are German, see AGENTS.md § Language)
