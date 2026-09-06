# REFERENCE — intent.md / handover.md in detail

The operating rules for `docs/intent.md` and `docs/handover.md`, two of the four document kinds (and four questions) in docs-discipline.

## Contents

1. [Terms and when to use which](#1-terms-and-when-to-use-which)
2. [intent.md](#2-intentmd)
3. [handover.md](#3-handovermd)
4. [Storage and history](#4-storage-and-history)
5. [The five categories of the consistency check](#5-the-five-categories-of-the-consistency-check-detection-is-mandatory-the-ruling-is-human)
6. [Resume checklist](#6-resume-checklist-workflow-c)

## 1. Terms and when to use which

- **intent**: the record in which the requester — a human — has settled *why this work is being done now*. One per work unit (a coherent piece of work: an issue, a PR, a campaign, …). **Owned by the human** — the AI listens and transcribes; it never invents content.
- **handover**: the record of where things stand, optimised so that the next actor (a new agent, a colleague, your future self) **can read it in two minutes and resume**. Owned by the session.
- **Which one**: starting a work unit whose intent is not obvious → intent. Work that continues across sessions → handover. Either or both (never merged). The handover **references** the intent; it does not restate it.

## 2. intent.md

### Required header

| field | rule |
|---|---|
| `Last updated` | ISO 8601 (YYYY-MM-DD) |
| `Requester` | The requester's real name or role. **Only when certain; never fabricated** |
| `Work unit` | A short identifier (issue ID, PR, campaign name, …) |

### Required sections

- `## Goal` — the result the requester wants, in one or two sentences.
- `## Success Criteria` — a bullet list of observable, verifiable conditions.
- `## Scope` (`### In scope` / `### Out of scope (Non-goals)`) — explicit boundaries.
- `## Constraints` — technical, deadline, budget, and compliance constraints.
- `## Open Questions` — undecided items to resolve before implementation (checkboxes).

### Questions to settle before creating or updating (STOP and ask the human if any is unclear)

1. What has to be true for the work to be "done" (goal, success criteria)?
2. How far does it go, and what is excluded (scope, non-goals)?
3. Which conditions cannot move (constraints, deadline)?
4. Which components are affected?
5. How is it rolled back if it fails (rollback conditions)?

### When to update

- Update **when the requester's intent changes** (scope grows, the goal changes, a constraint is added).
- Do not update for implementation detail or progress (that is the handover's job).
- Updates, like creation, are written **only after the human confirms**.

## 3. handover.md

### Required header

| field | rule |
|---|---|
| `Last updated` | ISO 8601 with time and time zone (for example `2026-07-02 18:30 (JST)`) |
| `Updated by` | A human's real name (only when certain) or the AI session ID. Never fabricated |

### Required sections

- `## Current State` — what is done, in one paragraph. **Verified facts only** (tests passed, merged, …; never "probably works").
- `## In Progress` — work under way, with branch names, PR links, and issue IDs.
- `## Next Actions` — numbered, **concrete** next steps, at a granularity the next actor can start on directly (name the skill or command if there is one).
- `## Known Risks / Blockers` — risks with their mitigations. **Anything waiting on someone else goes here without fail** (an implicit wait is the most dangerous kind).
- `## Context the Next Actor Needs` — non-obvious traps, quirks of the environment, external dependencies.
- `## Relevant Files and Commands` — `path — why it matters` / `command — what it does`.

### Length and style

- **Readable in two minutes.** When it grows, move detail into other artifacts and replace it with references.
- Both humans and agents read it. Use code references (`path:line`).
- Never restate the intent — write `see docs/intent.md`.

### When to update

- At the end of a meaningful working session (per session, not per commit).
- Before an interruption, a handover, or a long absence.

## 4. Storage and history

1. **The default is to commit to the repository** (it travels with the code). Some repositories keep these files gitignored (local only) — **check `.gitignore` the first time**, and ask the user if the policy is not clear from it.
2. Older versions are **not kept inside the file**. With the commit policy, git history is the history.
3. In a gitignored repository, when the work unit switches and the handover is rewritten, the old version may be parked as `docs/handover-YYYY-MM-DD-<slug>.md` (confirm that glob is ignored). Same for the intent (`docs/intent-YYYY-MM-DD-<slug>.md`).
4. Secrets (API keys, tokens, PII) are redacted before writing, whether the file is committed or local.

## 5. The five categories of the consistency check (detection is mandatory, the ruling is human)

Before creating, updating, or handing over, compare intent ⇄ handover ⇄ the repository's actual state.
**On any finding, stop, report, and continue only after a human ruling.**

| category | definition | example |
|---|---|---|
| **Intent drift** | The actual work (or the handover's account of it) cannot coexist with the intent's scope, non-goals, or constraints | The intent says "refactor only, no behaviour change" and the handover's Current State reports a new feature |
| **Duplication** | The handover restates something already in the intent, a PR, an ADR, or an issue | The Goal copied verbatim; the same change list as the PR description |
| **Stale reference** | A branch, PR, file, or command named in the file does not exist or is already gone | A merged and deleted branch still under In Progress; a renamed file path |
| **Staleness** | Current State disagrees with the repository's actual state | "tests red" when they are now green; main moved far after the handover was written |
| **Unactionable** | Next Actions are too abstract for the next actor to start on directly | Items like "continue", "polish it up" |

### Procedure

1. Read both `docs/intent.md` and `docs/handover.md` (if only one exists, say so).
2. Confirm that the named branches, PRs, and files exist (`git branch` / `gh pr view` / file existence checks).
3. Compare the claims in Current State (test results, merge state) with what you can measure.
4. Check every statement in the handover against the intent's scope and non-goals (intent drift).
5. No findings: say so in the score report and continue. **Any finding: report in the form below and hold the write (or the resume) until a human rules.**

### Report format

The report is in the user's language (Japanese by default):

```
intent/handover 整合検査: {n} 件検出

1. [{分類}] {該当箇所の要約}
   - 記載: {ファイルの記述の引用}
   - 実状態: {観測した事実}
   - 解消の選択肢:
     a) {例: intent の scope を人間が更新する（意図の方が変わった場合）}
     b) {例: 作業を intent の範囲内に戻す}
     c) {例: handover の記述を実測に合わせて修正する}
```

**The AI must not choose how to resolve intent drift** (absolute rule 7). In particular, "rewrite the intent to match the actual work" happens only with the human's explicit approval.

## 6. Resume checklist (workflow C)

- [ ] Read `docs/intent.md` (or reported that it does not exist)
- [ ] Read `docs/handover.md` (same)
- [ ] Checked `Last updated` and used `git log` to see what moved on main and the branches since then
- [ ] Confirmed that the In Progress branches and PRs exist
- [ ] Confirmed that the first Next Action is still valid
- [ ] Checked the intent's Open Questions for unresolved blockers
- [ ] Reported any gap or doubt to the human before starting work
