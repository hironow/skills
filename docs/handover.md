# Handover

**Last updated:** 2026-11-14 03:20 (JST)
**Updated by:** Claude Code session 6cfdaf0a-55b6-49f5-a763-654e2b6e7a97 (working in hironow/spec-ddd and hironow/dotfiles)

## Current State

45 skill directories, each with a `SKILL.md`; `README.md` indexes them in generated tables and credits the upstream of every derived skill. `just check` (ruff, ty, tests, `audit`, `readme-check`) runs in CI on every ready pull request and passed on `main` at `7f0ea46` (#30). The repository has been public since 2026-09-07. No pull request is open and `main` is the only branch.

`provable-glossary` arrived in #18 and was reworked in #19–#30 (2026-11-13 and 2026-11-14). Its source of truth is the private repository `m4k3-co/spec-ddd` (`skills/provable-glossary/`); this copy is written by `just skill-export` there and must not be edited here first. Its contract tests are `tests/unit/test_provable_glossary_contract.py`. On the operator's Mac the installed copy is byte-identical to `main` at `7f0ea46`, and `just audit-consumers` reports 0 findings (2026-11-14).

The history before 2026-11 (de-cruft pass, English rewrites, provenance of the derived skills, tooling move from dotfiles) is in `git log` and the merged pull requests #2–#17.

## In Progress

None.

## Next Actions

1. When `provable-glossary` changes, change `m4k3-co/spec-ddd` first, run `just skill-export <this checkout>` there, then open a pull request here. Squash-merge it once every CI check passes (the operator's standing permission for this repository).
2. After any merge, refresh the agent homes from dotfiles: `just skills-update`, then `just audit-consumers` here (0 findings expected).
3. `develop-web-game` ships an Apache-2.0 `LICENSE.txt` whose origin is unknown (`upstream: unknown`); name the source if it ever turns up.

## Known Risks / Blockers

- `docs/intent.md` (2026-09-06) still describes a dotfiles `skills/` submodule and an open question about going public. Both are out of date (the submodule was retired by dotfiles ADR 0043; the repository is public). Updating the intent is the requester's call; it is unchanged.
- `bunx skills check` and `update` rewrite the store copy of any skill the CLI tracks, including forks it once installed. Compare a fork against a scratch clone of its upstream before running them.
- `just audit-consumers` can only run on the machine that hosts the agent homes; CI does not run it.
- A `: ` inside a frontmatter value makes Claude Code drop that skill's frontmatter. Quote the value or rephrase it (#13). The `provable-glossary` checks in spec-ddd do not catch this.

## Context the Next Actor Needs

- Each skill is self-contained: `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, optional `license`, `metadata.provenance` / `upstream` / `changes`); some include `references/`, `templates/`, `assets/`, `scripts/`.
- Third-party skills live outside this repository (installed with `bunx skills`, declared in dotfiles `dump/harness/skill-lock.json`). A lock-managed name reappearing here fails `just skills-lock-check` in dotfiles.
- Changing a description changes the generated `README.md`; run `just readme-index` and commit both, or `readme-check` fails in CI (#30).
- CI does not run on draft pull requests; `gh pr ready` starts it.
- Routing between overlapping skills is measured in a fresh session (`claude -p` or `pi -p`); a session that already discussed a skill keeps naming it.
- `cloudflare-deploy/references/` is vendored Cloudflare documentation and is exempt from the emoji rule.

## Relevant Files and Commands

- `README.md` — conventions, the "Maintaining" recipe table, and the generated index and credits tables.
- `<skill-name>/SKILL.md` — skill definition.
- `just check` — the full local gate (same as CI).
- `just compare <fork> /abs/upstream` — fork-versus-upstream pass.
- `just audit-consumers` — are the agent homes up to date?
- In dotfiles: `just skills-update`, `just skills-place`, `just dump-skills-lock`, `just skills-lock-check`, and `docs/agents/skills-maintenance.md`.
