# skills

A personal collection of agent skills: 46 skills, one directory each, with a `SKILL.md` (YAML frontmatter plus instructions) and, where useful, `references/`, `templates/`, `assets/`, or `scripts/`. They follow the [Agent Skills](https://agentskills.io/specification) layout and are read by Claude Code, pi, Codex, and Gemini. The top-level `scripts/`, `tests/`, and `docs/` directories are not skills; they hold the maintenance tooling (see [Maintaining](#maintaining)) and the repository docs.

## How this repository is used

This repository is the `skills/` submodule of [hironow/dotfiles](https://github.com/hironow/dotfiles). `just sync-agents` there copies each skill directory into the agent homes (`~/.claude*/skills`, `~/.codex/skills`, `~/.gemini/skills`, `~/.agents/skills`; pi reads `~/.agents/skills` directly). The copy is additive: it adds skills that are missing and never overwrites or deletes an existing one, so after changing a skill here the home copies have to be refreshed by hand (rsync) once the change is merged and the submodule pointer is bumped in dotfiles.

Third-party skills are not vendored here. They are installed with `bunx skills` and declared in `dump/harness/skill-lock.json` in dotfiles; a lock-managed name must never reappear in this repository (`just skills-lock-check` fails). The few skills here that started as a copy of an upstream skill record the compared upstream commit in `metadata.upstream` so the next comparison has a baseline.

## Conventions

- Skills are written in English. The Japanese-writing skills (`japanese-tech-writing`, `argument-gap-edit`, `fallacy-check`) are the exception and stay in Japanese.
- Anything the skill prints or fills in for a person stays in the language that person reads: `templates/`, `assets/`, Slack message bodies, user-facing report formats, and setup notices are Japanese where the teams are Japanese. Japanese trigger phrases inside a `description` are kept so the skill still fires on Japanese requests.
- `name` matches the directory name. `description` says what the skill does and when to use it, names the sibling skill when two could compete for the same request, and stays under 1024 characters.
- `disable-model-invocation: true` marks skills that are only run when the user invokes them by name.
- No emoji in instruction text; markers are words (for example "(gate)", "Score 0/1/2").
- Commands follow the operator's tooling rules: `uv` for Python, `bun` / `bunx` for Node, `just` as the task runner.
- Style reference for writing a skill: [`writing-great-skills`](writing-great-skills/SKILL.md). Creating or iterating on a skill with test cases is delegated to the upstream anthropics `skill-creator`, installed via `bunx skills`.

## Changing a skill

1. Branch, edit, and run `just check` (see [Maintaining](#maintaining)). After adding, removing, or re-sourcing a skill, run `just readme-index` and commit the regenerated tables with the change.
2. Open a pull request here (`main` is not pushed to directly); CI runs the same `just check`; pull requests are squash-merged.
3. Bump the `skills` submodule pointer in dotfiles and refresh the home copies (`just audit-consumers` shows which homes still hold an older copy).
4. When a skill overlaps with an installed third-party skill, compare the two (`just compare <fork> <upstream-clone>`, then an independent reader) and keep one, or make the two descriptions mutually exclusive.

## Maintaining

The tooling lives in `scripts/` and is stdlib-only, so a plain `python3 scripts/audit.py` works in any clone; `uv sync` adds the dev tools (pytest, ruff, mypy) the `just` recipes use.

| recipe | what it does |
|---|---|
| `just check` | the local gate CI runs: `lint` + `test` + `audit` + `readme-check` |
| `just audit` | structural audit of every skill: frontmatter (`name` = directory, `description` ≤ 1024 chars, parseable YAML), relative links and `#anchors`, balanced code fences, emoji markers, the language rule, and the provenance contract (`metadata.provenance` / `upstream` / `upstream-license` / `changes`, bundled LICENSE) |
| `just audit-consumers` | the audit plus a byte comparison against every agent home that holds a copy, and dangling-symlink detection; depends on the machine, so it is not part of `check` |
| `just readme-index` / `just readme-check` | regenerate the generated blocks below from frontmatter / fail if they are stale |
| `just compare <dir>...` | quantitative comparison of skill versions (fork first, then upstream copies): sizes, description length, tooling-rule violations, body diff |
| `just test`, `just lint`, `just fmt` | the tooling's own unit tests, ruff + mypy (strict), ruff format |

The procedure around these recipes (judging a fork against its upstream, retiring a skill from the agent homes, the provenance contract in detail) is documented in dotfiles as `docs/agents/skills-maintenance.md`.

## Skills

Generated from each skill's frontmatter by `just readme-index`; do not edit by hand.

<!-- skills-index:start -->
| skill | what it does | notes |
|---|---|---|
| [`add-guard-protection`](add-guard-protection/SKILL.md) | Protect code paths that have no incoming HTTP request — AI agent tool calls, agent loops, MCP tool handlers, background jobs, queue worke… | fork of arcjet/arcjet-plugin |
| [`add-request-protection`](add-request-protection/SKILL.md) | Protect a server-side HTTP route or endpoint — API route, form handler, auth endpoint, webhook — with Arcjet, covering rate limiting, bot… | fork of arcjet/arcjet-plugin |
| [`agents-md-triage`](agents-md-triage/SKILL.md) | Audit AGENTS.md / CLAUDE.md / GEMINI.md and their spoke files (docs/agents/* etc.), classify every line as discoverable / task-specific /… |  |
| [`argument-gap-edit`](argument-gap-edit/SKILL.md) | 書籍原稿で、無理筋な議論、段落間に埋めがたいギャップ、理論や引用の見せびらかし、段落単位の割り込みを検出し、論理単位ごとに再配置・削除・橋渡しする編集を行う。 |  |
| [`brand-legal-review`](brand-legal-review/SKILL.md) | This skill should be used when the user asks to "legal review", "policy review", "review AI policy", "法務レビュー", "ポリシーチェック", or needs brand… |  |
| [`caveman`](caveman/SKILL.md) | Ultra-compressed communication mode: drops filler, articles, and pleasantries while keeping full technical accuracy. | fork of JuliusBrussee/caveman |
| [`cloudflare-deploy`](cloudflare-deploy/SKILL.md) | Deploy applications and infrastructure to Cloudflare using Workers, Pages, and related platform services. | fork of openai/skills |
| [`consume-hub-actions`](consume-hub-actions/SKILL.md) | How consumer repos in the the-organisation org use the shared CI hub (the-organisation/.github composite actions) on the heterogeneous self-hosted runner p… |  |
| [`decision-mapping`](decision-mapping/SKILL.md) | Turn a loose idea into a sequenced map of investigation tickets, then drive them to resolution one at a time. | user-invoked |
| [`decision-record-governance`](decision-record-governance/SKILL.md) | Create, update, and supersede (or reverse) decision records — ADRs for technical decisions and PDRs for product decisions — governed by d… |  |
| [`design-an-interface`](design-an-interface/SKILL.md) | Generate multiple radically different interface designs for a module using parallel sub-agents. |  |
| [`develop-web-game`](develop-web-game/SKILL.md) | Use when building or iterating on a web game (HTML/JS) and a reliable development + testing loop is needed: implement small changes, run… | derived (origin unknown) |
| [`diagnose`](diagnose/SKILL.md) | Disciplined diagnosis loop for hard bugs and performance regressions - build a feedback loop, reproduce and minimise, hypothesise, instru… | fork of mattpocock/skills |
| [`dogfood`](dogfood/SKILL.md) | Exploratory testing of a running web application through a real browser (agent-browser): systematically drive the UI, find functional/UX/… | fork of vercel-labs/agent-browser |
| [`edit-article`](edit-article/SKILL.md) | Edit and improve an article draft by restructuring sections, improving clarity, and tightening prose. | user-invoked |
| [`fallacy-check`](fallacy-check/SKILL.md) | 議論・主張・討論ログのテキストから、誤謬パターン（ストローマン、人身攻撃、レッテル貼り、 loaded language、衆人・権威・新しさへの訴え、誤った二分法、連続性の虚偽、前件否定、 後件肯定など）を検出してフラグする。 |  |
| [`gcp-serverless-appdev`](gcp-serverless-appdev/SKILL.md) | GCP serverless application development guide covering Cloud Run, Firestore, Cloud Tasks, Pub/Sub, Firebase Auth, Cloud Functions, Eventar… |  |
| [`gcp-serverless-tf`](gcp-serverless-tf/SKILL.md) | Generate and maintain Terraform/OpenTofu configurations for GCP serverless architectures (Cloud Run, Firestore, Cloud Tasks, Pub/Sub, Clo… |  |
| [`gh-address-comments`](gh-address-comments/SKILL.md) | Help address review/issue comments on the open GitHub PR for the current branch using gh CLI; verify gh auth first and prompt the user to… | fork of openai/skills |
| [`gh-fix-ci`](gh-fix-ci/SKILL.md) | Use when a user asks to debug or fix failing GitHub PR checks that run in GitHub Actions; use `gh` to inspect checks and logs, summarize… | fork of openai/skills |
| [`hatch-pet`](hatch-pet/SKILL.md) | Create, repair, validate, visually QA, and package Codex-compatible animated pets and pet spritesheets from character art, generated imag… | fork of openai/skills |
| [`imagegen`](imagegen/SKILL.md) | Use when the user asks to generate or edit images via the OpenAI Image API (for example: generate image, edit/inpaint/mask, background re… | fork of openai/skills |
| [`intent-handover-governance`](intent-handover-governance/SKILL.md) | Govern development continuity with two files — docs/intent.md (why we are doing this now, the human's intent) and docs/handover.md (how f… |  |
| [`japanese-tech-writing`](japanese-tech-writing/SKILL.md) | 日本語の技術文書・書籍原稿の文章規範。 |  |
| [`jupyter-notebook`](jupyter-notebook/SKILL.md) | Use when the user asks to create, scaffold, or edit Jupyter notebooks (`.ipynb`) for experiments, explorations, or tutorials; prefer the… | fork of openai/skills |
| [`manager-loop`](manager-loop/SKILL.md) | Run very long-horizon, multi-hour autonomous builds in Claude Code by splitting roles - a manager session that interviews the user, write… |  |
| [`obsidian-vault`](obsidian-vault/SKILL.md) | Search, create, and manage notes in the Obsidian vault with wikilinks and index notes. |  |
| [`openai-docs`](openai-docs/SKILL.md) | Use when the user asks how to build with OpenAI products or APIs and needs up-to-date official documentation with citations (for example:… | fork of openai/skills |
| [`playwright-cli`](playwright-cli/SKILL.md) | Automates browser interactions for web testing, form filling, screenshots, and data extraction. | fork of microsoft/playwright-cli |
| [`qa`](qa/SKILL.md) | Interactive QA session where user reports bugs or issues conversationally, and the agent files GitHub issues. |  |
| [`request-refactor-plan`](request-refactor-plan/SKILL.md) | Create a detailed refactor plan with tiny commits via user interview, then file it as a GitHub issue. |  |
| [`review`](review/SKILL.md) | Review the changes since a fixed point (commit, branch, tag, or merge-base) on two separate axes, Standards and Spec, using parallel sub-… | fork of mattpocock/skills |
| [`screenshot`](screenshot/SKILL.md) | Use when the user explicitly asks for a desktop or system screenshot (full screen, specific app or window, or a pixel region), or when to… | fork of openai/skills |
| [`security-best-practices`](security-best-practices/SKILL.md) | Perform language and framework specific security best-practice reviews and suggest improvements. | fork of openai/skills |
| [`security-ownership-map`](security-ownership-map/SKILL.md) | Analyze git repositories to build a security ownership topology (people-to-file), compute bus factor and sensitive-code ownership, and ex… | fork of openai/skills |
| [`security-threat-model`](security-threat-model/SKILL.md) | Repository-grounded threat modeling that enumerates trust boundaries, assets, attacker capabilities, abuse paths, and mitigations, and wr… | fork of openai/skills |
| [`sibyl`](sibyl/SKILL.md) | the operator's standing self-governance gates. |  |
| [`to-issues`](to-issues/SKILL.md) | Break a plan, spec, or PRD into independently-grabbable issues on the project issue tracker using tracer-bullet vertical slices. | user-invoked |
| [`to-prd`](to-prd/SKILL.md) | Turn the current conversation into a PRD and publish it to the project issue tracker — no interview, just synthesis of what you've alread… | user-invoked, fork of mattpocock/skills |
| [`ubiquitous-language`](ubiquitous-language/SKILL.md) | Extract a DDD-style ubiquitous language glossary from the current conversation, flagging ambiguities and proposing canonical terms. | user-invoked |
| [`update-submodule-changelog`](update-submodule-changelog/SKILL.md) | Update docs/changelogs.md after submodules under protocols/*, payments/*, or gcloud/* change. |  |
| [`verification-discipline`](verification-discipline/SKILL.md) | How to not fool yourself (or be fooled) when verifying work — yours, a reviewer's, a subagent's, or a checker's. |  |
| [`writing-great-skills`](writing-great-skills/SKILL.md) | Reference for writing and editing skills well — the vocabulary and principles that make a skill predictable. | user-invoked |
| [`xcodebuildmcp-cli`](xcodebuildmcp-cli/SKILL.md) | Official skill for the XcodeBuildMCP CLI. | fork of cameroncooke/XcodeBuildMCP |
| [`yeet`](yeet/SKILL.md) | Use only when the user explicitly asks to stage, commit, push, and open a GitHub pull request in one flow using the GitHub CLI (`gh`). | fork of openai/skills |
| [`zoom-out`](zoom-out/SKILL.md) | Tell the agent to zoom out and give broader context or a higher-level perspective. | user-invoked |
<!-- skills-index:end -->

## Credits

Skills that started from someone else's work keep that work's license file in their directory and record the compared upstream revision, its license, and what changed here in frontmatter (`metadata.provenance`, `metadata.upstream`, `metadata.upstream-license`, `metadata.changes`). Files that differ from the upstream revision carry a modification notice at the top. This block is generated from that frontmatter.

<!-- credits:start -->
| skill | upstream | upstream license | what changed here |
|---|---|---|---|
| [`add-guard-protection`](add-guard-protection/SKILL.md) | [arcjet/arcjet-plugin](https://github.com/arcjet/arcjet-plugin/tree/2c95022/plugins/arcjet/skills/add-guard-protection) | Apache-2.0 | description made mutually exclusive with add-request-protection; bunx / bun add / uv add instead of npx / npm install / pip install; content predates the current upstream layout |
| [`add-request-protection`](add-request-protection/SKILL.md) | [arcjet/arcjet-plugin](https://github.com/arcjet/arcjet-plugin/tree/2c95022/plugins/arcjet/skills/protect-route) | Apache-2.0 | description made mutually exclusive with add-guard-protection; bunx instead of npx; content predates the current upstream layout, where the skill is now named protect-route |
| [`caveman`](caveman/SKILL.md) | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman/tree/5184b3d/skills/caveman) | MIT | SKILL.md rewritten and de-crufted; only the skill is vendored, not the caveman tooling |
| [`cloudflare-deploy`](cloudflare-deploy/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/cloudflare-deploy) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; the bundled reference docs are unchanged |
| [`develop-web-game`](develop-web-game/SKILL.md) | unknown | Apache-2.0 | origin not found among the known upstream repositories; ships the Apache-2.0 LICENSE.txt it came with; SKILL.md edited in the 2026-09-02 prompt audit |
| [`diagnose`](diagnose/SKILL.md) | [mattpocock/skills](https://github.com/mattpocock/skills/tree/3cca18b/skills/engineering/diagnosing-bugs) | MIT | from diagnosing-bugs: de-crufted, then Redact / loop completion gate / Minimise ported back; glossary grounding instead of CONTEXT.md; guarded architecture hand-off |
| [`dogfood`](dogfood/SKILL.md) | [vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser/tree/4726ece/skill-data/dogfood) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; references and templates unchanged |
| [`gh-address-comments`](gh-address-comments/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/gh-address-comments) | Apache-2.0 | unchanged apart from frontmatter; kept as the single copy for gh comment triage |
| [`gh-fix-ci`](gh-fix-ci/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/gh-fix-ci) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit and the description now points the-organisation repos at consume-hub-actions first |
| [`hatch-pet`](hatch-pet/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/hatch-pet) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; assets and scripts unchanged |
| [`imagegen`](imagegen/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.system/imagegen) | Apache-2.0 | SKILL.md, references, agents/openai.yaml and scripts/image_gen.py edited in the 2026-09-02 prompt audit (from the .system/imagegen skill) |
| [`jupyter-notebook`](jupyter-notebook/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/jupyter-notebook) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; templates and scripts unchanged |
| [`openai-docs`](openai-docs/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/openai-docs) | Apache-2.0 | SKILL.md and agents/openai.yaml edited in the 2026-09-02 prompt audit |
| [`playwright-cli`](playwright-cli/SKILL.md) | [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli/tree/655530f/skills/playwright-cli) | Apache-2.0 | SKILL.md and the bundled references edited in the 2026-09-02 prompt audit |
| [`review`](review/SKILL.md) | [mattpocock/skills](https://github.com/mattpocock/skills/tree/3cca18b/skills/engineering/code-review) | MIT | from code-review: PRD vocabulary, harness-neutral spawn wording, ask-the-user fallback for the issue tracker, trimmed description; the sub-agent word budgets were ported back |
| [`screenshot`](screenshot/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/screenshot) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; scripts unchanged |
| [`security-best-practices`](security-best-practices/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/security-best-practices) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; references unchanged |
| [`security-ownership-map`](security-ownership-map/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/security-ownership-map) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; scripts unchanged |
| [`security-threat-model`](security-threat-model/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/security-threat-model) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit; references/prompt-template.md gained the closing code fence the upstream file lacks |
| [`to-prd`](to-prd/SKILL.md) | [mattpocock/skills](https://github.com/mattpocock/skills/tree/3cca18b/skills/engineering/to-spec) | MIT | renamed from to-spec: the artifact is a PRD published to the project tracker; lightly edited |
| [`xcodebuildmcp-cli`](xcodebuildmcp-cli/SKILL.md) | [cameroncooke/XcodeBuildMCP](https://github.com/cameroncooke/XcodeBuildMCP/tree/e6ef59b/skills/xcodebuildmcp-cli) | MIT | bun add -g instead of npm install -g; otherwise identical to the official CLI skill |
| [`yeet`](yeet/SKILL.md) | [openai/skills](https://github.com/openai/skills/tree/49f948f/skills/.curated/yeet) | Apache-2.0 | SKILL.md edited in the 2026-09-02 prompt audit |

Origin not yet confirmed (no upstream found; confirm before publishing): `agents-md-triage`, `argument-gap-edit`, `brand-legal-review`, `consume-hub-actions`, `decision-mapping`, `decision-record-governance`, `design-an-interface`, `edit-article`, `fallacy-check`, `gcp-serverless-appdev`, `gcp-serverless-tf`, `intent-handover-governance`, `japanese-tech-writing`, `manager-loop`, `obsidian-vault`, `qa`, `request-refactor-plan`, `sibyl`, `to-issues`, `ubiquitous-language`, `update-submodule-changelog`, `verification-discipline`, `writing-great-skills`, `zoom-out`

Original (confirmed): none
<!-- credits:end -->

## Repository docs

- `docs/intent.md` — why this repository exists and what is in and out of scope (owned by the requester).
- `docs/handover.md` — where things stand and what comes next.
