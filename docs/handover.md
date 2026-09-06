# Handover

**Last updated:** 2026-09-06 17:20 (JST)
**Updated by:** claude (session 777ca0b0, working in hironow/dotfiles)

## Current State

44 skill directories, each with a `SKILL.md` (`sibyl` moved to hironow/skills-private and `consume-hub-actions` to the the-organisation organisation's own skills repository on 2026-09-06). `README.md` indexes them (generated tables), states the conventions (English instructions, Japanese-writing skills and user-facing templates excepted), and credits the upstream of every derived skill. All instruction text is English except those deliberate cases; no emoji markers remain in self-authored skills. The maintenance tooling lives here (`scripts/`, `tests/`, `justfile`, `.github/workflows/ci.yaml`): `just check` = ruff + mypy + tests + `audit` + `readme-check`, run by CI on every pull request; `audit` reports 0 findings at `main`.

Since 2026-09-02 (`main` 749791a → 0bf2e29, PRs #2–#13):

- Dropped `electron`, `linear`, `microsoft-foundry` (#2) and `write-a-skill` (#6, replaced by the upstream anthropics `skill-creator` installed via `bunx skills`).
- `review` and `diagnose` were reconciled with their upstream (mattpocock/skills `code-review` / `diagnosing-bugs`): the upstream improvements were ported, the fork-specific de-cruft kept, and the upstream installs removed from the agent homes. `xcodebuildmcp-cli` is the official CLI skill with one local change (`bun add -g`); its MCP-flavoured sibling was removed because no XcodeBuildMCP MCP server is configured. Each of the three records the compared upstream commit in `metadata.upstream` (#3, #4, #5).
- Five description pairs that competed for the same requests now name each other and state what they are not for (#7). The arcjet skills invoke `bunx` / `bun add` / `uv add` instead of `npx` / `npm` / `pip` (#8).
- Instructions rewritten in English: `decision-record-governance`, `intent-handover-governance`, `update-submodule-changelog` (#9); `gcp-serverless-appdev` (SKILL.md + 16 reference docs), `gcp-serverless-tf`, `sibyl`, `verification-discipline` (#10). Each rewrite passed an independent Japanese-vs-English fidelity check; two unintended generalisations found by that check were reverted before merge.
- Provenance and licenses recorded for the 22 derived skills (`license`, `metadata.provenance` / `upstream` / `upstream-license` / `changes`, upstream LICENSE copied into the skill, modification notices on the 17 bundled files that differ from upstream); `README.md` gained the generated index and credits tables (#12). Three `metadata.changes` values containing `: ` were quoted after Claude Code dropped the frontmatter of those skills (#13).

dotfiles side: submodule pointer bumped to 328c2d8 and the declared skill lock re-dumped (hironow/dotfiles #346); Claude's `skillOverrides` no longer hides `xcodebuildmcp-cli`, `create-mcp-app`, `migrate-oai-app`, `jupyter-notebook` (#345). hironow/dotfiles #347 adds the spoke `docs/agents/skills-maintenance.md` (the procedure around the recipes) and thin wrappers (`just skills-audit` etc.) that delegate into this repository's `justfile`. All eight agent homes hold byte-identical copies of every skill at 0bf2e29.

Provenance (#17, 2026-09-06): every one of the 44 skills has a traced origin. 34 derived: openai/skills 13 (incl. `develop-web-game` at `.curated`@30444ae), mattpocock/skills 13 (ten of them found only in that repository's full history because upstream renamed, deprecated, or deleted them: `zoom-out`, `writing-great-skills`, `ubiquitous-language`, `edit-article`, `qa`, `request-refactor-plan`, `design-an-interface`, `decision-mapping`, `obsidian-vault`, `to-issues`), k16shikano's gist 2 (`japanese-tech-writing`; `argument-gap-edit` from comment 6201959; Unlicense by the author's declaration), arcjet/arcjet-plugin 2, and one each from JuliusBrussee/caveman, cameroncooke/XcodeBuildMCP, microsoft/playwright-cli, vercel-labs/agent-browser. 10 original: `agents-md-triage`, `brand-legal-review`, `decision-record-governance`, `fallacy-check`, `gcp-serverless-appdev` and `gcp-serverless-tf` (generated with skill-creator from the operator's own infrastructure docs in `learned/` on 2026-03-05, three weeks before google/skills existed; no public overlap found), `intent-handover-governance`, `manager-loop` (idea credit to Matt Shumer via `metadata.inspired-by`), `update-submodule-changelog`, `verification-discipline`. Method: first-commit trace, GitHub code search per description, full-history comparison against the cloned upstreams, and a sweep of the author's gists; the tooling grew `gist:` upstreams (incl. `comment-<id>`) and `inspired-by`.

Tooling history: #14 moved the tooling here from dotfiles; #15 hardened it after an independent review (Windows shell prelude in the justfile, pytest `pythonpath` instead of a `sys.path` hack, a test pinning the Flatt PyPI index and a raw-pypi-free lock, the exact per-skill rsync for refreshing agent homes); #16 stops CI on draft pull requests (`ready_for_review` starts it). dotfiles #347 (merged) consumes the recipes through thin wrappers and denylists `scripts/` and `tests/` in its skills sync.

## In Progress

Nothing on a branch. `docs/intent.md` is Accepted (#11; the requester confirmed by directing the merge on 2026-09-06).

## Next Actions

1. Nothing is blocked on the requester for the tooling; the remaining items below are content decisions.
2. (resolved 2026-09-06) The pgvector Usage row in `gcp-serverless-appdev/references/docs/infrastructure-2-data.md` §2.4.3 now says what the requester meant: small-scale vector search, or when the vectors do not need to live in Spanner (a standalone PostgreSQL with pgvector is enough).
3. `develop-web-game` ships an Apache-2.0 LICENSE.txt whose origin is unknown (`upstream: unknown`); name the source if it ever turns up.
4. Visibility: the public-readiness blockers were resolved on 2026-09-06 (requester's decisions) — the secret-looking value in the history of a deleted file is a campaign key already present in openai/skills' public history (7fc1e3f), so it was accepted; the operator's personal profile skill moved to hironow/skills-private; the organisation-internal CI hub skill moved to that organisation's own skills repository; the remaining origin-unconfirmed skills were marked `provenance: original` after a first-commit trace and a public code search found no upstream; `LICENSE` (MIT) added. The switch to public itself is still the requester's call.

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
