# RUBRIC — quality rubric for decision records (ADR/PDR)

Criteria for judging the **substance** of a decision record. Format (required header fields and sections) is checked against [REFERENCE.md](REFERENCE.md) §2/§4; this rubric measures whether what is written can stand up to an approval decision.

## How to use it (two gates)

- **Filing gate**: score every criterion before a record's filing (workflow A) is complete. **A single 0 means the filing is not complete** (fix it before posting an approval request to Slack, too).
- **Settling gate**: score again before changing `status` to `Accepted` or `Rejected`. **Do not settle unless every gate criterion (marked "gate") is at 2.**
- Scores: `0 = missing / fail`, `1 = present but insufficient`, `2 = pass`. Include the scores in the report to the user (for example `R1:2 R2:2 R3:1 …`).

## Criteria

| # | criterion | 0 (missing) | 1 (insufficient) | 2 (pass) |
|---|---|---|---|---|
| R1 | **Header completeness** | A required field is missing, or there is an author but no `author-slack` | All fields present but a rule is broken (duplicate number, file name mismatch, ID not in `<@U` form) | Every field follows REFERENCE §2; the author is mapped to `<@U…>` |
| R2 | **Context is factual** | No background | Opinions or wishes ("we'd like to", "seems better") mixed into the facts, or the conclusion written first | Why a decision is needed now is stated only in verifiable facts (a gap between implementation and spec, an incident, the source of a request) |
| R3 | **Decision is unambiguous** (gate) | The Decision section is empty (not even the Proposed placeholder) | Hedges such as "preferably", "basically", "in principle" (with no exception defined), or several independent decisions mixed without numbers | Once settled: a single unambiguous MUST/SHALL statement; multiple decisions numbered D1, D2, …. While Proposed: the placeholder "（Proposed。確定後に MUST 文で記述。）" |
| R4 | **Options are complete, rejections reasoned** (gate) | Only one option (the conclusion restated), or no section | Several options but no rejection reasons and no comparison axes (benefits/costs); a PDR written to steer toward one option | Two or more realistic options, each with benefits and costs; once settled, every rejected option has a reason; PDRs present options neutrally |
| R5 | **Consequences are honest** | No section, or Positive only | Negative empty or perfunctory ("none in particular"); Positive/Negative/Neutral not distinguished | The cost of the chosen option (effort, risk, operational burden) is concrete, and the three categories are explicit |
| R6 | **Plain-language explanation** | A PDR without the section | Jargon left unexplained; the gist cannot be understood without reading the body | A non-engineer can read just this section and understand what is being decided and why (mandatory for PDRs, recommended for ADRs; an ADR that omits it scores at most 1) |
| R7 | **Readability (Japanese-first)** | The body is mostly English | English technical terms without a Japanese gloss on first use; sentences too long for a non-engineer to follow | Japanese-first, terms glossed on first use (for example「supersede（置き換え）」), short sentences |
| R8 | **Traceability** (gate) | Not registered in the queue, or a supersede without `supersedes:` | `related` effectively empty; a reversal whose `## 反転記録 (Reversal)` is still `none`; queue row and header disagree | Queue, README index, supersession chain, and reversal record all consistent; links to related open questions, gaps, and other records |
| R9 | **The pending-decision section is actionable** | Missing while Proposed | Option checkboxes only, with no follow-up actions, or no decision-maker/date fields | Options, decision-maker and date fields, and a follow-up action per option, so the approver can fill it in on the spot |
| R10 | **Cross-DR consistency** (gate) | The consistency check (REFERENCE §10) was not run, or a finding was ignored and the record filed or settled without consultation | The check covered only the `related` neighbourhood, not a full scan; or a finding was handled without involving the people behind the conflicting record | Compared against every DR on all five categories. No findings, or every finding went through a Slack consultation with the people involved, a human ruled, and the trace (thread, commit) exists |

Gate criteria (must be 2 at the settling gate): R3, R4, R8, R10.

## Good and bad examples (R3 Decision)

- Score 0: 「（あとで書く）」
- Score 1: 「エラーレスポンスはなるべく統一フォーマットにする」(a hedge, no force)
- Score 2: 「D1. エラーレスポンスは `{error:{code,message}, meta}` 形式に統一しなければならない（MUST）。D2. HTTP ステータスは仕様の8系統に従う（MUST）。」

## Good and bad examples (R4 Options)

- Score 0: 「A) 統一する」(no alternative: a report after the fact, not a decision)
- Score 1: 「A) 統一する B) 現状維持」(no comparison axes, no rejection reason)
- Score 2: 「A) envelope 統一 — 利点: 契約テスト基準が定まる／コスト: フロント同時修正。B) 現状維持 — 利点: 工数ゼロ／却下: 152 件の契約テスト失敗の判定基準が定まらないため却下。」

## Scoring in practice

1. Before completing a filing (workflow A) — and before posting an approval request to Slack — score R1–R10 and fix every 0 before continuing.
2. Right before the status change in an update (workflow B), score again; if any gate criterion (R3/R4/R8/R10) is below 2, stop the settlement and report what is missing to the user.
3. For a supersede or reversal (workflow C), apply the same gates to the new record (R8 includes the consistency of the supersession chain).
4. R10 is 2 only when there are no findings or every finding has been ruled on after a Slack consultation with the people involved. A finding handled without consultation scores 0.
5. When in doubt, give the lower score (lenient self-scoring is how drift starts).
