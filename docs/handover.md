# Handover

**Last updated:** 2026-06-10 (JST)
**Updated by:** claude (AI draft from git history — review before trusting)

## Current State

69 skill directories exist at the repository root, each with a `SKILL.md` (YAML frontmatter: name, description) and optionally `references/` / `assets/`. There is no README, no CI, and no task runner. Last commit: "add sibyl skill" (2026-06-10). Recent history is a stream of "add ..." / "update" commits plus one cleanup, "remove plugin-duplicated and unused skills" (6e41dcc).

## In Progress

不明 (git 履歴からは判別できず). History suggests ongoing incremental addition of skills.

## Next Actions

1. requester による docs/intent.md ドラフトのレビューと確定
2. (Pending review) decide whether to add a README / index of skills

## Known Risks / Blockers

- Commit messages are mostly "update", so per-skill change history is hard to trace without `git log -- <dir>`

## Context the Next Actor Needs

- Each skill is self-contained: `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`); some include `references/` and `assets/`
- Plugin-duplicated skills were removed previously (6e41dcc) — check for duplication with plugin-provided skills before adding new ones
- No linting or validation tooling is configured in this repo

## Relevant Files and Commands

- `<skill-name>/SKILL.md` — skill definition (frontmatter + body)
- `sibyl/` — most recently added skill (2026-06-10)
- `writing-great-skills/` — the style reference for authoring skills; skill creation itself is delegated to the upstream anthropics `skill-creator` (installed via `bunx skills`), so this repo carries no authoring workflow skill
- `git log --oneline -- <skill-name>/` — trace an individual skill's history
