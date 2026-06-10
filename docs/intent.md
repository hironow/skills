# Intent

**Last updated:** 2026-06-10
**Requester:** hironow
**Status:** DRAFT — AI が README / git 履歴から起草。requester 未確認
**Work unit:** skills — personal collection of agent skills (SKILL.md directories) for AI coding agents

## Goal

Maintain a personal collection of reusable agent skills — currently 69 top-level directories, each containing a `SKILL.md` with name/description frontmatter (some with `references/` and `assets/`) — covering cloud platforms (GCP, Cloudflare, Vercel), development workflows (tdd, diagnose, release, triage), and personal governance (sibyl). Inferred from directory contents and git history; no README exists.

## Success Criteria

- 未定義 — Open Questions 参照 (no README, tests, or CI exist in this repo)

## Scope

### In scope

- Skill directories with `SKILL.md` (and optional `references/` / `assets/`), added and updated incrementally (git history: "add skills", "add sibyl skill", "update skill")

### Out of scope (Non-goals)

- 未確認 — no README documents non-goals. History shows "remove plugin-duplicated and unused skills" (6e41dcc), suggesting skills already provided by plugins are intentionally excluded, but this is unconfirmed

## Constraints

- None evident from the repo (no tooling, lockfiles, or CI present)

## Open Questions

- [ ] requester による本ドラフトのレビュー
- [ ] How this repo is consumed (e.g. symlinked/synced into an agent's skills directory) — not documented anywhere in the repo
- [ ] Whether a README / skill index should be added
- [ ] Naming and quality conventions for new skills (is `write-a-skill/` the intended style guide?)
