# Intent

**Last updated:** 2026-09-06
**Requester:** hironow
**Status:** Accepted — 2026-09-06 のセッションで requester が決めた内容を書き起こし、同日 requester の merge 指示で確定
**Work unit:** skills — personal collection of agent skills (SKILL.md directories) for AI coding agents

## Goal

Keep one curated set of reusable agent skills that hironow's agents (Claude Code, pi, Codex, Gemini) share through the dotfiles `skills/` submodule, so that each capability exists exactly once, is written in English, and is kept deliberately in step with — or deliberately different from — its upstream where one exists.

## Success Criteria

- Every skill here is the only skill for its purpose across the agent homes: no installed third-party skill shares its trigger, or the two descriptions name each other and state what each is not for.
- Skill instructions are English (Japanese-writing skills excepted); anything printed or filled in for a person stays in that person's language.
- A skill that started from an upstream records its provenance in frontmatter (compared upstream commit, upstream license, what changed here), keeps the upstream license file, and is credited in the README, so nothing here is used without attribution; a comparison against upstream is repeatable (quantitative pass plus an independent reader).
- After a change merges, the agent homes are refreshed and an agent's routing dry-run picks the intended skill without a same-purpose runner-up.

## Scope

### In scope

- Self-authored skills and forks that carry a deliberate local change (for example the bun/uv tooling rules).
- The tooling that checks the skills (`scripts/`, `tests/`, `justfile`, CI running `just check`). It lives here so that skill maintenance does not span two repositories; dotfiles only wraps these recipes.
- The repository README and these two docs.

### Out of scope (Non-goals)

- Vendoring skills that a plugin or `bunx skills` already provides (declared in dotfiles `dump/harness/skill-lock.json`); a lock-managed name must not reappear here.
- Translating user-facing output templates (`templates/`, `assets/`, Slack messages, report formats, setup notices) — they stay in the reader's language.
- Editing vendored reference material such as `cloudflare-deploy/references/` for style.
- Hosting skill-maintenance scripts in dotfiles, or distributing the tooling directories to the agent homes (only skill directories are copied).

## Constraints

- Operator tooling rules apply inside skill text: `uv` only for Python, `bun` / `bunx` only for Node, `just` as the task runner, `.yaml` not `.yml`.
- `main` is not pushed to directly; changes go through a pull request and are squash-merged, then the submodule pointer is bumped in dotfiles.
- "Newest upstream" is not automatically "better": a fork that passed the 2026-09-02 de-cruft pass is compared on substance before anything is ported.

## Open Questions

- [ ] `infrastructure-2-data.md` §2.4.3 の pgvector の一文 (「Spanner 統合が不要な場合」) の意図
- [ ] この repository を public にするか (2026-09-06 の公開可否判定は「条件付き可」: 削除済みファイル履歴の secret 様の値、`sibyl/` の本人プロファイル、`consume-hub-actions/` の組織内部 CI、origin 未確認 24 skill、repo 自身の LICENSE 無し)
