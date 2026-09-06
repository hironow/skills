# Handover

**Last updated:** 2026-09-06 15:30 (JST)
**Updated by:** claude (session 777ca0b0, working in hironow/dotfiles)

## Current State

46 skill directories, each with a `SKILL.md`. `README.md` indexes them and states the conventions (English instructions, Japanese-writing skills and user-facing templates excepted). All instruction text is English except those deliberate cases; no emoji markers remain in self-authored skills. Verified by scanning every `*.md` for Japanese characters and emoji after #9 and #10 merged.

Since 2026-09-02 (`main` 749791a → 328c2d8, PRs #2–#10):

- Dropped `electron`, `linear`, `microsoft-foundry` (#2) and `write-a-skill` (#6, replaced by the upstream anthropics `skill-creator` installed via `bunx skills`).
- `review` and `diagnose` were reconciled with their upstream (mattpocock/skills `code-review` / `diagnosing-bugs`): the upstream improvements were ported, the fork-specific de-cruft kept, and the upstream installs removed from the agent homes. `xcodebuildmcp-cli` is the official CLI skill with one local change (`bun add -g`); its MCP-flavoured sibling was removed because no XcodeBuildMCP MCP server is configured. Each of the three records the compared upstream commit in `metadata.upstream` (#3, #4, #5).
- Five description pairs that competed for the same requests now name each other and state what they are not for (#7). The arcjet skills invoke `bunx` / `bun add` / `uv add` instead of `npx` / `npm` / `pip` (#8).
- Instructions rewritten in English: `decision-record-governance`, `intent-handover-governance`, `update-submodule-changelog` (#9); `gcp-serverless-appdev` (SKILL.md + 16 reference docs), `gcp-serverless-tf`, `sibyl`, `verification-discipline` (#10). Each rewrite passed an independent Japanese-vs-English fidelity check; two unintended generalisations found by that check were reverted before merge.

dotfiles side: submodule pointer bumped to 328c2d8 and the declared skill lock re-dumped (hironow/dotfiles #346); Claude's `skillOverrides` no longer hides `xcodebuildmcp-cli`, `create-mcp-app`, `migrate-oai-app`, `jupyter-notebook` (#345). All eight agent homes hold byte-identical copies of every skill at 328c2d8.

## In Progress

Nothing on a branch. `docs/intent.md` is a draft awaiting the requester's confirmation (see Next Actions).

## Next Actions

1. Requester confirms `docs/intent.md` (the 2026-09-06 decisions are drafted in; the open questions from June are answered there).
2. Decide on the one passage the translators could not resolve: `gcp-serverless-appdev/references/docs/infrastructure-2-data.md` §2.4.3, "Small-scale vector search / when Spanner integration is not needed" (原文「Spanner 統合が不要な場合」) — translated literally; the surrounding paragraph suggests the intended meaning may differ.
3. Optional: move the validation used during #9/#10 (frontmatter parse, relative link and `#anchor` resolution, code-fence balance, emoji and Japanese scan) from the session scratchpad into a `just` recipe in dotfiles so it runs in CI.

## Known Risks / Blockers

- `just sync-agents` treats `skills` as additive: a changed skill is not re-copied into an agent home that already has it. After merging a change here, refresh the home copies by hand (rsync from the submodule at the bumped commit); otherwise agents keep reading the old version while the repository says otherwise.
- `bunx skills check` and `update` rewrite the store copy of any skill the CLI tracks, including forks it once installed. Do not run them before comparing a fork against its upstream; compare against a scratch clone of the upstream instead.
- This repository has no CI; correctness of frontmatter and links is only checked by hand or in dotfiles.

## Context the Next Actor Needs

- Each skill is self-contained: `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, optionally `disable-model-invocation`, `allowed-tools`, `argument-hint`, `metadata.upstream`); some include `references/`, `templates/`, `assets/`, `scripts/`.
- Third-party skills live outside this repository (installed with `bunx skills`, declared in dotfiles `dump/harness/skill-lock.json`). A lock-managed name reappearing here fails `just skills-lock-check` in dotfiles.
- Routing between overlapping skills was measured with pi (`pi -p --tools read --no-session … "which skill would you invoke for …"`) in a fresh session; a session that already discussed a skill keeps naming it after it is removed.
- The `cloudflare-deploy/references/` tree is vendored Cloudflare documentation and is exempt from the emoji rule.

## Relevant Files and Commands

- `README.md` — conventions and the skill index (regenerate the table from frontmatter when skills are added or removed).
- `<skill-name>/SKILL.md` — skill definition (frontmatter + body).
- `writing-great-skills/` — the style reference for authoring skills.
- `git log --oneline -- <skill-name>/` — trace an individual skill's history.
- In dotfiles: `just sync-agents`, `just skills-lock-check`, `just dump-skills-lock`.
