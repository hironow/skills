---
name: agents-md-triage
description: |
  Audit AGENTS.md / CLAUDE.md / GEMINI.md and their spoke files (docs/agents/*
  etc.), classify every line as discoverable / task-specific / always, and
  produce a staged plan to shrink the hub and extract skills. Use whenever the
  user wants agent instruction files audited, slimmed, reorganized, or
  skill-ified, or asks about context/token reduction or an instruction budget
  for those files — whether or not they say "audit".
---

# AGENTS.md Triage

Context files (AGENTS.md / CLAUDE.md / spokes) are a token tax paid
unconditionally every session. The core principle of this skill:
**writing information into the hub that an agent can discover from the repo
on its own is waste, and always-loading knowledge that only matters for
specific tasks is also waste.** Triage every line into the three classes
below and keep only `always` in the hub.

Write every report, table, and question for the user in the user's language.
Keep the three classification labels (`discoverable` / `task-specific` /
`always`), file paths, and commit messages as-is in English.

- **discoverable**: findable inside the repo without help → deletion
  candidate. Always cite the concrete source file path as evidence.
  **Open and verify the file before classifying — classification before
  verification is forbidden** ("it's probably in package.json" is not
  evidence).
- **task-specific**: not discoverable, needed only for particular tasks →
  skill-extraction candidate. Attach a proposed trigger (what request or
  situation should load it).
- **always**: not discoverable AND involved in nearly every session → stays
  in the hub. This is an **AND** condition; if either half fails, it is not
  `always`.

### Reachability: the deletion safety condition

A discoverable line is safe to delete only if, *after* deletion, a live route
still leads an agent to the information — a hub trigger-table row, an explicit
pointer, a skill trigger, or a hook's block message. If the information merely
*exists* somewhere but nothing routes to it, it behaves like task-specific, not
discoverable: relocate it behind a trigger (move-before-delete) or keep it —
do not delete. Name the surviving route in the table's Destination column.

Why: "findable in principle" is not the same as "an agent will actually find
it in the moment it's needed." Deleting a line whose only copy sits in an
unreachable file silently drops the guidance. The evidence path proves the
information is duplicated; the surviving route proves it stays reachable.

## Parameters to accept on invocation

- Target files (default: AGENTS.md, CLAUDE.md, and the full spoke set).
  In hub-and-spoke repos (sources edited, then synced to distribution
  targets), **always target the source side** — editing a distribution
  target gets overwritten by the next sync.
- Protected sections (regions that must never be touched, e.g. Ship Gate,
  Non-negotiables). Mark them `(protected)` in the classification table and
  exclude them from classification and reduction.
- Hub line budget (optional). If given, state in the Phase 1 report whether
  the projected line count fits the budget; if it does not, show the gap and
  further candidates.

## Phase 1: Audit (read-only)

Classify by semantic unit (heading, bullet, paragraph) and report with this
schema. **Do not modify any file in this phase.**

| Line range | Summary | Class | Evidence | Destination |
|------------|---------|-------|----------|-------------|

- Class is one of discoverable / task-specific / always / (protected).
- Evidence: for discoverable, the verified source file path; for
  task-specific, the proposed trigger; for always, why it is involved in
  every session.
- Destination: delete / proposed skill name / stay in hub. For every delete,
  name the surviving route that keeps the information reachable (see
  Reachability) — a delete with no surviving route is not allowed.

End with per-file "current lines → projected lines" (`wc -l` measured →
post-reduction estimate), then **stop and wait for human approval**.

Why: deletion risks information loss and classifications always contain
mistakes. Having a human adjudicate the table before execution is the
cheapest insurance. Never proceed past Phase 1 without approval.

## Phase 2: Delete (after approval)

Delete only discoverable entries whose Destination names a surviving route
(see Reachability). If a delete needs a new home for the information, land that
relocation first (move-before-delete) so no window exists where the guidance is
unreachable. Keep the deletions as a separate structural commit:

```
refactor(agents): remove discoverable context
```

Do not mix behavioral changes (edits that alter what the instructions mean)
into the same commit.

## Phase 3: Skill extraction (after approval)

One skill = one commit per task-specific item. Write the description as a
**trigger condition**, not a knowledge label — the description is the only
signal an agent has for deciding when to load the skill.

- Bad: "Knowledge about releases"
- Good: "Use when asked to do release work involving tag creation or
  CHANGELOG updates"

Remove the extracted content from the hub, leaving at most a one-line
pointer if needed.

## Phase 4: Verify

- Run 3 representative tasks before/after and report behavioral diffs —
  proof that the reduction broke nothing (i.e. the deleted information was
  truly unneeded).
- If an existing quality gate exists (`just check`, an instruction-budget
  check, etc.), run it.

## Classification examples

- "React 19 + TypeScript stack" → discoverable (evidence: package.json)
  → delete
- "Before changing the Firestore schema, run firepact's compatibility gate
  first" → task-specific (trigger: a request to change the Firestore
  schema) → extract skill
- "Commits follow Conventional Commits; separate structural from
  behavioral" → always (involved in every commit; the convention is not
  discoverable from code) → stays in hub

## Common misclassifications

- **"Important" does not mean `always`.** Important but discoverable is
  still discoverable. `always` requires both halves: not discoverable AND
  involved in nearly every session.
- Tool lists, directory layout, dependency versions are discoverable from
  package.json / justfile / ls → discoverable.
- Background and rationale for decisions: discoverable if an ADR exists
  (evidence: docs/adr/xxxx.md). If no ADR exists, propose writing one
  instead of deleting — never throw the information away.
- Rules already mechanically enforced ("make lint pass") can be treated as
  discoverable when a hook or CI blocks violations (evidence: the hook/CI
  config file). Only when no enforcement exists are they `always`
  candidates.
