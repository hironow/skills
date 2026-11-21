---
name: decision-record-governance
description: Govern active engineering and operational rules using code-SSOT, mechanical checks, provable-glossary, and a structured rules registry (docs/rules.toml) instead of standalone ADR/PDR markdown files. Triages every proposed decision at entry, checks proposed rules against the rules registry for contradiction, duplication, misreading, false relation, and mistaken relationship, and requires durable human consultation and ruling on any conflict. Use when the user mentions ADR, PDR, decision record, rules registry, docs/rules.toml, 決定記録, ルール一覧, 意思決定の起票・更新・例外追加・廃止, ルールの矛盾・整合性チェック, or wants to manage architecture or operational rules.
license: MIT
metadata:
  provenance: original
---

# Decision & Rule Governance (Code-SSOT × Rules Registry × Human Ruling)

**The core job is to keep active rules verifiable and non-contradictory without accumulating stale `docs/adr/` prose.** Machine-verifiable invariants belong in code, tests, lint/CI checks, or `provable-glossary`. Only non-codable operational policies and named exceptions live in `docs/rules.toml`. Pending proposals live in GitHub Draft PRs or Issues — never in a separate markdown queue.

## 0. Triage — where does this decision belong?

Evaluate in order and stop at the first match. Never create a `docs/adr/` or `docs/pdr/` file.

1. **Ephemeral implementation detail or discoverable from code/config** → put the rationale in the **PR description**. Create no rule entry.
2. **Mechanically verifiable invariant or domain state machine** → encode it in **code + test / lint / CI check** or **`provable-glossary`** (`glossary/Glossary/*.lean`, `glossary/Spec/*.qnt`). If an operational summary is needed in `docs/rules.toml`, add one short `[[rule]]` with `enforced_by` and `state = "enforced"`.
3. **Named exception to an existing rule** (tool name, version, deadline, repo scope) → **PR editing `docs/rules.toml`** (`exceptions` + an exception `[[rule]]` with `expires` if time-boxed). The human ruling comment on the PR is the `consultation_url`.
4. **Long-lived cross-cutting policy that code cannot express** → **PR adding or updating a `[[rule]]` in `docs/rules.toml`** with a stable ID and human ruling.

When unsure between destinations, ask the user; do not invent a record file.

## Absolute rules (stop and ask the user on any violation)

1. **No standalone `docs/adr/` or `docs/pdr/` files**: active rules live in code/`provable-glossary` or `docs/rules.toml`; pending proposals live in GitHub Draft PRs/Issues.
2. **Stable contacts are mandatory**: every rule in `docs/rules.toml` must carry `author_contact` and, before settlement, `decision_maker_contact` (prefer GitHub `@handle`; Slack `<@UXXXXXXXX>` where used). **Never fabricate a handle** (see [REFERENCE.md](REFERENCE.md) §4).
3. **Stable IDs and durable retirement**: a rule `id` (`<area>.<kebab-case>`) is never renamed or reused. Updating an active rule's text or exceptions happens in place via PR with a new human ruling (`decided_date`, `consultation_url`). Retiring a rule moves the entry to `docs/rules-retired.toml` (never auto-loaded by agents).
4. **Rubric gate**: score every proposed rule change with [RUBRIC.md](RUBRIC.md) before opening for review (no criterion at 0) and before merge/settlement (every gate criterion R1/R3/R5/R7 at 2). Report the scores to the user.
5. **Consistency check, consultation with the people involved, and a human ruling**: before proposing, amending, or retiring a rule, compare it against every active rule in `docs/rules.toml` (and matching `enforced_by` checks) for contradiction, duplication, misreading, false relation, and mistaken relationship ([REFERENCE.md](REFERENCE.md) §6). On any finding, stop, report it, and consult the conflicting rule's `decision_maker_contact` and `author_contact` in a durable venue. **A human decides how to resolve it. The AI resolving, patching, or ignoring a contradiction is forbidden.**
6. **Outward-facing posts require confirmation**: before the first GitHub, Slack, or external post, confirm venue and wording with the user. A chat ruling counts only once copied to a stable URL recorded in `consultation_url`.

## Workflow

### A. Propose a rule or exception (Draft PR)

1. Run **Step 0 Triage**; confirm the decision belongs in `docs/rules.toml` (if it belongs in code/lint/`provable-glossary`, implement the check directly).
2. Draft the `[[rule]]` entry in `docs/rules.toml` from [templates/rules.toml](templates/rules.toml) with a new immutable `id` (`<area>.<kebab-case>`).
3. Confirm `author_contact` (absolute rule 2).
4. Run the **consistency check** against all active rules in `docs/rules.toml` ([REFERENCE.md](REFERENCE.md) §6). On any finding, stop and run durable consultation.
5. Score with the **filing gate** in [RUBRIC.md](RUBRIC.md); fix any 0.
6. Open a Draft PR with the rationale, rejected options, and rubric scores in the PR body.

### B. Settle / merge a rule change

1. Verify an explicit human ruling in the confirmed durable venue (PR comment, issue, or confirmed thread). If ambiguous or missing, ask the `decision_maker_contact`.
2. Re-run the **consistency check** against `docs/rules.toml`. Never settle while a finding is unresolved.
3. Fill in `decision_maker_contact`, `decided_date`, `consultation_url`, and (if mechanically checked) `enforced_by` and `state = "enforced"`.
4. Score with the **settling gate** in [RUBRIC.md](RUBRIC.md); if any gate criterion is below 2, stop and report.
5. Run the repository's registry validation tests (unique IDs, existing `enforced_by` paths, valid `exceptions` references, non-empty contacts and `consultation_url`).

### C. Amend, reverse, or retire an active rule

1. **Consulting the existing rule's `decision_maker_contact` and `author_contact` is mandatory** for any semantic change, reversal, or retirement.
2. For an amendment or exception change, edit the `[[rule]]` in place keeping the same `id`, and update `decided_date` and `consultation_url` to the new ruling.
3. For retirement, move the `[[rule]]` entry to `docs/rules-retired.toml` with `retired_date` and `retirement_url` (never reuse the `id`).

### D. Registry audit (periodic sweep)

1. Validate `docs/rules.toml` structurally (unique IDs, valid `enforced_by` paths, valid `exceptions` IDs, expired `expires` entries).
2. Sweep active rules by `area` for contradiction or duplication ([REFERENCE.md](REFERENCE.md) §6). On any finding, start durable consultation — never resolve unilaterally.
3. Flag any `approved` rule that can now be promoted to `enforced` via lint, test, or `provable-glossary`.

Detailed schema, contacts, message templates, and consistency-check categories: [REFERENCE.md](REFERENCE.md). Quality rubric: [RUBRIC.md](RUBRIC.md).
