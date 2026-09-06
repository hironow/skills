---
name: intent-handover-governance
description: Govern development continuity with two files — docs/intent.md (why we are doing this now, the human's intent) and docs/handover.md (how far we got and what comes next). The intent is settled by a human and never guessed by the AI; the handover is updated at the end of every session and kept readable in two minutes. Before any update, check intent ⇄ handover ⇄ the repository's actual state for drift, and leave the ruling on any gap to a human. Use when the user mentions intent.md, handover.md, 引き継ぎ（ハンドオーバー）, 意図の記録・確認, セッション終了・作業再開, starting or switching a work unit, or wants session continuity captured in docs.
license: MIT
metadata:
  provenance: original
---

# Intent / Handover Governance (intent × handover × rubric × consistency check)

**The core job is to create, update, and hand over two files.** The two files are independent and are never merged — use whichever applies.

| file | question it answers | owner | when it changes |
|---|---|---|---|
| `docs/intent.md` | **Why now** — why this work is being done | **A human** (the AI only takes dictation) | When a work unit starts, or when the intent changes |
| `docs/handover.md` | **How far** we got and **what comes next** | The session (AI or human) | At the end of every session, and at major milestones |

- **Create** = settle the intent when a work unit starts; write the first handover
- **Update** = update the intent when the intent changes; update the handover at the end of a session
- **Hand over** = at the start of a session, read both files, compare them with the actual state, and resume

## Absolute rules (stop and ask the user on any violation)

1. **The intent is a transcript of the human's intent; guessing is forbidden**: if any of goal / success criteria / scope / non-goals / constraints / deadline / rollback conditions is unclear, **stop and ask the human**. Never create or update `docs/intent.md` without the human's confirmation. Do not fill gaps with assumptions (the question list in [REFERENCE.md](REFERENCE.md) §2).
2. **The handover goes draft → present → confirm → write**: never overwrite outright. When a handover already exists, summarise what will change before overwriting it.
3. **No duplication; reference instead**: never restate the intent in the handover (refer to the path). Anything already in a PR, ADR, issue, commit, or plan is referenced by link or ID, not copied into the body.
4. **Dates are absolute** (ISO 8601). Relative dates such as "yesterday" or "next week" rot the moment they are written and are forbidden.
5. **No history inside the file**: older versions live in git history. Only when the repository keeps these files gitignored, park the old version as a dated backup (`docs/handover-YYYY-MM-DD-<slug>.md`). Whether to commit or gitignore follows the repository's policy; confirm it the first time ([REFERENCE.md](REFERENCE.md) §4).
6. **Rubric gate**: score with [RUBRIC.md](RUBRIC.md) before writing. The intent gate requires no criterion at 0 plus human confirmation; the handover gate requires every gate criterion (H1/H3/H5) at 2. Report the scores to the user.
7. **The consistency check is mandatory; the ruling is human**: before creating, updating, or handing over, always compare intent ⇄ handover ⇄ the repository's actual state and check for **intent drift, duplication, stale references, staleness, and unactionable items** (the five categories in [REFERENCE.md](REFERENCE.md) §5). **When intent drift is found, the AI must not edit the intent to make things consistent** — whether the work is brought back in line with the intent, or the intent itself has changed, is the human's call.
8. **Redact secrets; never invent names**: remove API keys, passwords, and PII before writing. Use a real name in `Requester` / `Updated by` only when it is certain; otherwise use the session ID.

## Workflow

### A. Create or update the intent (work unit starts, or the intent changes)
1. Check whether `docs/intent.md` exists. If it does, read it and judge whether this work falls within the current intent (if so, no update is needed — go straight to the work).
2. Ask the human about anything unclear and settle it (absolute rule 1; the question list is in [REFERENCE.md](REFERENCE.md) §2).
3. Draft from [templates/intent.md](templates/intent.md) and score with the **intent gate** in [RUBRIC.md](RUBRIC.md); fix anything at 0.
4. Present the draft to the human and **write it only after approval**.
5. Do not update for changes in implementation detail — update only when the requester's intent changes.

### B. Update the handover (end of session, major milestone)
1. Gather the session's results, work in progress, and next steps from the conversation and the repository's actual state (branches, PRs, test results).
2. **Consistency check** (absolute rule 7, [REFERENCE.md](REFERENCE.md) §5). On intent drift, stop and ask the human.
3. Draft from [templates/handover.md](templates/handover.md); replace anything that duplicates the intent with a reference (absolute rule 3).
4. Score with the **handover gate** in [RUBRIC.md](RUBRIC.md); fix any gate criterion (H1/H3/H5) below 2.
5. Present the draft and write it only after confirmation (absolute rule 2).

### C. Hand over and resume (start of session)
1. Read `docs/intent.md` and `docs/handover.md` (if either is missing, say so, and start from A if needed).
2. **Verify freshness and existence**: check that the branches, PRs, files, and commands named in the handover still exist, and that the repository has not moved far since `Last updated` (the checklist in [REFERENCE.md](REFERENCE.md) §6).
3. Report any gap to the human before starting work. If there is none, resume from the top of `Next Actions`.

### D. Inventory (stale detection)
1. Detect and report: an old `Last updated`, completed items still under `In Progress`, and `Open Questions` left unresolved.
2. If the intent seems out of step with reality, ask the human (the AI does not rewrite it).

## Out of scope for this skill

- Recording decisions (why we decided X) → ADR/PDR (the `decision-record-governance` skill). That is different from the intent's "why now" — when a decision happens, write it as an ADR/PDR and reference it by ID from the intent or handover.
- Describing the current specification → `docs/*.md` (follow docs-discipline).
- Temporary agent-to-agent handoffs (things that go to a temp dir and never into the repository).
