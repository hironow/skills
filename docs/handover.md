# Handover

**Last updated:** 2026-09-06 17:20 (JST)
**Updated by:** claude (session 777ca0b0, working in hironow/dotfiles)

## Current State

46 skill directories, each with a `SKILL.md`. `README.md` indexes them (generated tables), states the conventions (English instructions, Japanese-writing skills and user-facing templates excepted), and credits the upstream of every derived skill. All instruction text is English except those deliberate cases; no emoji markers remain in self-authored skills. The maintenance tooling lives here (`scripts/`, `tests/`, `justfile`, `.github/workflows/ci.yaml`): `just check` = ruff + mypy + tests + `audit` + `readme-check`, run by CI on every pull request; `audit` reports 0 findings at `main`.

Since 2026-09-02 (`main` 749791a → 0bf2e29, PRs #2–#13):

- Dropped `electron`, `linear`, `microsoft-foundry` (#2) and `write-a-skill` (#6, replaced by the upstream anthropics `skill-creator` installed via `bunx skills`).
- `review` and `diagnose` were reconciled with their upstream (mattpocock/skills `code-review` / `diagnosing-bugs`): the upstream improvements were ported, the fork-specific de-cruft kept, and the upstream installs removed from the agent homes. `xcodebuildmcp-cli` is the official CLI skill with one local change (`bun add -g`); its MCP-flavoured sibling was removed because no XcodeBuildMCP MCP server is configured. Each of the three records the compared upstream commit in `metadata.upstream` (#3, #4, #5).
- Five description pairs that competed for the same requests now name each other and state what they are not for (#7). The arcjet skills invoke `bunx` / `bun add` / `uv add` instead of `npx` / `npm` / `pip` (#8).
- Instructions rewritten in English: `decision-record-governance`, `intent-handover-governance`, `update-submodule-changelog` (#9); `gcp-serverless-appdev` (SKILL.md + 16 reference docs), `gcp-serverless-tf`, `sibyl`, `verification-discipline` (#10). Each rewrite passed an independent Japanese-vs-English fidelity check; two unintended generalisations found by that check were reverted before merge.
- Provenance and licenses recorded for the 22 derived skills (`license`, `metadata.provenance` / `upstream` / `upstream-license` / `changes`, upstream LICENSE copied into the skill, modification notices on the 17 bundled files that differ from upstream); `README.md` gained the generated index and credits tables (#12). Three `metadata.changes` values containing `: ` were quoted after Claude Code dropped the frontmatter of those skills (#13).

dotfiles side: submodule pointer bumped to 328c2d8 and the declared skill lock re-dumped (hironow/dotfiles #346); Claude's `skillOverrides` no longer hides `xcodebuildmcp-cli`, `create-mcp-app`, `migrate-oai-app`, `jupyter-notebook` (#345). hironow/dotfiles #347 adds the spoke `docs/agents/skills-maintenance.md` (the procedure around the recipes) and thin wrappers (`just skills-audit` etc.) that delegate into this repository's `justfile`. All eight agent homes hold byte-identical copies of every skill at 0bf2e29.

Tooling history: #14 moved the tooling here from dotfiles; #15 hardened it after an independent review (Windows shell prelude in the justfile, pytest `pythonpath` instead of a `sys.path` hack, a test pinning the Flatt PyPI index and a raw-pypi-free lock, the exact per-skill rsync for refreshing agent homes); #16 stops CI on draft pull requests (`ready_for_review` starts it). dotfiles #347 (merged) consumes the recipes through thin wrappers and denylists `scripts/` and `tests/` in its skills sync.

## In Progress

- #11 (`docs/readme-and-handover`): `docs/intent.md` redraft, awaiting the requester's confirmation (see Next Actions).

## Next Actions

1. Requester confirms `docs/intent.md` (the 2026-09-06 decisions are drafted in; the open questions from June are answered there).
2. Decide on the one passage the translators could not resolve: `gcp-serverless-appdev/references/docs/infrastructure-2-data.md` §2.4.3, "Small-scale vector search / when Spanner integration is not needed" (原文「Spanner 統合が不要な場合」) — translated literally; the surrounding paragraph suggests the intended meaning may differ.
3. Confirm the origin of the 24 skills listed under "Origin not yet confirmed" in the README credits (set `metadata.provenance: original`, or name the upstream); `develop-web-game` ships an Apache-2.0 LICENSE.txt whose origin is unknown.
4. Before any visibility change: the public-readiness assessment (2026-09-06, kept with the dotfiles session artifacts) found no live secret but four items for a human decision — a 64-hex `SECRET_KEY` in the history of a deleted file (`build-things/scripts/generate_merch_url.py`, commit 6821832), the operator's own profile in `sibyl/`, the `the-organisation` internal CI hub in `consume-hub-actions/`, and the 24 unconfirmed origins above. The repository also has no LICENSE of its own.

## Known Risks / Blockers

- `just sync-agents` treats `skills` as additive: a changed skill is not re-copied into an agent home that already has it. After merging a change here, refresh the home copies by hand (rsync from the submodule at the bumped commit); otherwise agents keep reading the old version while the repository says otherwise.
- `bunx skills check` and `update` rewrite the store copy of any skill the CLI tracks, including forks it once installed. Do not run them before comparing a fork against its upstream; compare against a scratch clone of the upstream instead.
- CI runs `just check` on every pull request, but `just audit-consumers` (are the agent homes up to date?) can only run on the machine that hosts them; run it by hand after every submodule bump.

## Context the Next Actor Needs

- Each skill is self-contained: `<skill-name>/SKILL.md` with YAML frontmatter (`name`, `description`, optionally `disable-model-invocation`, `allowed-tools`, `argument-hint`, `metadata.upstream`); some include `references/`, `templates/`, `assets/`, `scripts/`.
- Third-party skills live outside this repository (installed with `bunx skills`, declared in dotfiles `dump/harness/skill-lock.json`). A lock-managed name reappearing here fails `just skills-lock-check` in dotfiles.
- Routing between overlapping skills was measured with pi (`pi -p --tools read --no-session … "which skill would you invoke for …"`) in a fresh session; a session that already discussed a skill keeps naming it after it is removed.
- The `cloudflare-deploy/references/` tree is vendored Cloudflare documentation and is exempt from the emoji rule.

## Relevant Files and Commands

- `README.md` — conventions, the "Maintaining" recipe table, and the generated index and credits tables (`just readme-index` regenerates them from frontmatter).
- `<skill-name>/SKILL.md` — skill definition (frontmatter + body).
- `justfile`, `scripts/`, `tests/unit/` — the tooling: `just check` before a pull request, `just compare <fork> /abs/upstream` for a fork-vs-upstream pass, `just audit-consumers` after a submodule bump.
- `writing-great-skills/` — the style reference for authoring skills.
- `git log --oneline -- <skill-name>/` — trace an individual skill's history.
- In dotfiles: `just sync-agents`, `just skills-lock-check`, `just dump-skills-lock`, the wrappers `just skills-*`, and the procedure in `docs/agents/skills-maintenance.md`.
