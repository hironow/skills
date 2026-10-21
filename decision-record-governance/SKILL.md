---
name: decision-record-governance
description: Create, update, and supersede (or reverse) decision records — ADRs for technical decisions and PDRs for product decisions — governed by decision-queue.md (the list of decisions awaiting approval) and a quality rubric. Always checks every other DR for contradiction, duplication, misreading, false relation, and mistaken relationship, and when anything is found, requires a durable consultation that involves the people behind the conflicting record so a human rules on it. Use when the user mentions ADR, PDR, decision record, decision queue, 決定記録, 意思決定の起票・更新・supersede・反転, DR の矛盾・整合性チェック, 決裁の相談・催促, or wants to manage architecture or product decisions.
license: MIT
metadata:
  provenance: original
---

# Decision Record Governance (ADR/PDR × queue × rubric × consistency check × durable consultation)

**The core job is to create, update, and supersede decision records (DR = ADR ∪ PDR).** Consultation must involve the people behind a conflicting record and leave a durable trace. GitHub is preferred when the work already lives there; Slack is optional.

- **Create** = file the record as `Proposed` and register it in the queue
- **Update** = settle the decision (`Accepted` / `Rejected` / `Deferred`), fill in the pending fields, update the README index
- **Supersede** = replace or reverse. Never edit the existing record; replace it with a new one

## Absolute rules (stop and ask the user on any violation)

1. **The decision queue is mandatory**: every ADR/PDR you file must be registered in `docs/decision-queue.md`. If the file does not exist, create it from [templates/decision-queue.md](templates/decision-queue.md). The queue is the single source of truth for undecided decisions.
2. **Stable contacts are mandatory**: any record with an author must carry `author-contact`; before settlement it must also carry `decision-maker-contact`. Keep both in the record and queue, including the decided log. Prefer GitHub `@handle`; Slack `<@UXXXXXXXX>` remains valid when that team uses Slack. If you cannot identify one, stop and ask. **Never fabricate one** (see [REFERENCE.md](REFERENCE.md) §6).
3. **Immutability**: the body of an `Accepted` or `Rejected` record is never edited. Changes and reversals are new records that supersede the old one. Do not delete queue rows; move them to the "decided" log.
4. **One decision = one record.** Numbering is append-only (four digits, zero-padded; never reuse a number or fill a gap). File name: `NNNN-kebab-title.md`.
5. **Rubric gate**: score the record with [RUBRIC.md](RUBRIC.md) before filing is complete and again before it is settled. The filing gate requires no criterion at 0; the settling gate requires every gate criterion (R3/R4/R8/R10) at 2. Report the scores to the user.
6. **Cross-DR consistency check, consultation with the people involved, and a human ruling**: before creating, updating, or superseding, compare the record against every other DR for contradiction, duplication, misreading, false relation, and mistaken relationship (the five categories in [REFERENCE.md](REFERENCE.md) §10). If even one is found, stop, report it, and consult the conflicting DR's decision-maker and author in a durable venue. A human decides how to resolve it after that consultation. The AI resolving, patching, or ignoring the finding is not an option, and neither is "proceed knowing there is a contradiction".
7. **Consultation posts are outward-facing (visible beyond this conversation)**: before the first GitHub, Slack, or other external post, confirm the venue and wording with the user. A chat ruling counts only when the involved person is present and the ruling is copied to a stable URL/reference in the confirmed durable venue before settlement.

## Workflow

### A. Create (file a record)
1. Classify: technical or architectural decision → ADR (`docs/adr/`); product, UX, or business decision → PDR (`docs/pdr/`).
2. Take the next number after the current maximum and create the record as `Proposed` from [templates/adr-template.md](templates/adr-template.md) or [templates/pdr-template.md](templates/pdr-template.md).
3. Confirm the author's stable contact handle (absolute rule 2).
4. **Cross-DR consistency check** (absolute rule 6, [REFERENCE.md](REFERENCE.md) §10). On any finding, stop, run the consultation (§10.3), and continue only after a human ruling.
5. Score with the **filing gate** in [RUBRIC.md](RUBRIC.md); fix anything at 0.
6. Add one row to the summary table in `docs/decision-queue.md` (columns in [REFERENCE.md](REFERENCE.md) §5).
7. If approval is needed, post in the confirmed durable venue and record its URL/reference in the queue (see "Durable consultation" below).

### B. Update (settle the decision)
1. Confirm the ruling: who chose what, and when. **If it is ambiguous or not yet obtained, ask the decision-maker in the confirmed consultation venue.**
2. **Re-run the cross-DR consistency check** (absolute rule 6). Never settle a record while a finding is still unresolved.
3. Fill in the record's `## 決定（記入待ち）` section: the chosen outcome, the decision-maker, the date, and that outcome's follow-up action. For `Accepted`, finalise `## Decision` as MUST statements and fill in the rejection reason for every rejected option. For `Rejected` or `Deferred`, state the disposition and reason/revisit condition unambiguously.
4. Update `status`, `decided-date`, `decision-maker`, and `decision-maker-contact` in the header.
5. Score with the **settling gate** in [RUBRIC.md](RUBRIC.md); if any gate criterion is below 2, stop and report.
6. Move the queue row to the "decided" log and update the ADR/PDR README (index and decision change log).
7. If useful, post a settlement notice in the recorded consultation thread, mentioning the author.

### C. Supersede (replace or reverse)
1. Do not edit the old record. File a new one with workflow A (the `supersedes:` header is mandatory; the consistency check in A also validates the supersession chain).
2. **Consulting the old record's decision-maker and author is mandatory.** A supersede or reversal is a deliberate contradiction of an existing `Accepted` decision, so it always goes through the durable consultation flow of absolute rule 6 ([REFERENCE.md](REFERENCE.md) §10.3).
3. The only edits to the old record are `status: Superseded` and a `superseded-by:` line. A reversal requires a `## 反転記録 (Reversal)` section in the new record.
4. Add one line to `## 決定変更ログ (Decision Change Log)` at the end of the README and register the new record in the queue.

### D. Queue maintenance (inventory)
1. Check the queue against the record files (validation rules in [REFERENCE.md](REFERENCE.md) §5).
2. **Cross-DR consistency sweep**: compare every DR against every other using the five categories of §10. On any finding, start the consultation required by absolute rule 6.
3. List items still `Proposed` past their deadline and, if needed, remind the approver in the recorded venue. Update the "last reminded" column.

## Durable consultation (the venue is optional; involving people and preserving the trace are not)

When: (1) requesting approval, (2) asking the decision-maker when the intent or choice is ambiguous, (3) reminding after a deadline — all three when needed — and **(4) consulting the people involved about a consistency-check finding — mandatory, never skipped**.
Means, in order of preference: an existing GitHub PR/issue/discussion → a new GitHub issue/discussion → Slack when the team uses it → another user-approved durable venue. Direct chat can gather the ruling only when the involved people are present; copy the exact ruling to a stable URL/reference in the confirmed durable venue before settlement and record it in the queue. When no posting tool or credential is available, prepare the message and ask the user to post it by hand; never skip the consultation itself.
Message templates, API examples, header spec, and status vocabulary: [REFERENCE.md](REFERENCE.md). Quality criteria: [RUBRIC.md](RUBRIC.md).
