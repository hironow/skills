# RUBRIC — quality rubric for intent.md / handover.md

Criteria for judging the **substance** of the two files. Format (required header fields and sections) is checked against [REFERENCE.md](REFERENCE.md) §2/§3; this rubric measures whether the file is useful to the next actor and to the requester.

## How to use it (two gates)

- **Intent gate**: score I1–I5 before creating or updating `docs/intent.md`. **A single 0 means no write.** In addition, **the human must approve the draft** (a perfect score without approval still means no write).
- **Handover gate**: score H1–H6 before writing `docs/handover.md`. **Do not write unless every gate criterion (H1/H3/H5) is at 2.**
- Scores: `0 = missing / fail`, `1 = present but insufficient`, `2 = pass`. Include the scores in the report to the user (for example `I1:2 I2:1 … / H1:2 H2:2 …`).
- When in doubt, give the lower score (lenient self-scoring is how drift starts).

## Intent criteria

| # | criterion | 0 (missing) | 1 (insufficient) | 2 (pass) |
|---|---|---|---|---|
| I1 | **Provenance of the intent** | Some part was guessed by the AI without asking the human | The human was asked but a vague answer was filled in as is, or an assumption is not marked as one | Every item comes from the human's answers or explicit instructions; anything unsettled is isolated in Open Questions |
| I2 | **Goal is unambiguous** | No Goal, or only a list of means with no result | Several independent goals mixed together, or readers would interpret it differently | The **result** the requester wants reads unambiguously in one or two sentences |
| I3 | **Success criteria are verifiable** | None | Unobservable wording such as "better" or "faster" | Every item is observable and verifiable (a test, a number, the existence of an artifact) |
| I4 | **Scope boundary** | No in/out distinction | In scope only, with empty non-goals, or a boundary vague enough to stretch | Non-goals are explicit and usable as a boundary for judgement calls during the work |
| I5 | **Freshness** | No `Last updated`, or a relative date | A date exists but the intent may not reflect a change | An absolute date that matches the current work unit |

## Handover criteria

| # | criterion | 0 (missing) | 1 (insufficient) | 2 (pass) |
|---|---|---|---|---|
| H1 | **Current State is factual** (gate) | Missing, or unverified hopes ("should work") | Facts and guesses mixed without distinction | Verified facts only (test results, merge state, measurements); guesses marked as guesses |
| H2 | **Readable in two minutes** | Takes more than five minutes, or accumulated old logs | Readable but verbose, or copies content from other artifacts | Concise; detail pushed out to path/URL/ID references |
| H3 | **Next Actions are actionable** (gate) | Missing, or at the level of "continue" | A direction exists but starting needs more investigation | The next actor can **start directly** (down to commands, paths, and skill names) |
| H4 | **Risks and waits are explicit** | No Known Risks, or an implicit external wait | Items exist but lack a mitigation or the party being waited on | Every risk has a mitigation; every external wait names who, what, and since when |
| H5 | **Consistency check done** (gate) | The check (REFERENCE §5) was not run, or a finding was ignored and the file written anyway | The check ran but skipped confirming that branches and PRs exist | Compared on all five categories; no findings, or every finding has a human ruling with a trace |
| H6 | **No duplication** | Restates the intent's Goal | Copies more than a summary of what is already in a PR or ADR | The intent and other artifacts are only referenced; only handover-specific information is in the body |

Gate criteria (must be 2 at the handover gate): H1, H3, H5.

## Good and bad examples (H3 Next Actions)

- Score 0: 「1. 残りを実装する」
- Score 1: 「1. テストを直す」(which test? what is the cause?)
- Score 2: 「1. `tests/unit/test_sync.py::test_additive` の赤を直す — 原因は `ADDITIVE_DIRECTORIES` に `skills` 追加後の fixture 未更新（`scripts/sync_agents.py:142` 参照）。直したら `just ci`。」

## Good and bad examples (I3 Success Criteria)

- Score 0: (no section)
- Score 1: 「- 引き継ぎがスムーズになる」
- Score 2: 「- 新しいセッションが docs/handover.md だけを読んで、質問なしで Next Actions の1番に着手できる」

## Scoring in practice

1. Before writing the intent (workflow A), score I1–I5, fix every 0, then present the draft to the human and obtain approval. Writing without approval is forbidden regardless of the score.
2. Before writing the handover (workflow B), score H1–H6; if any gate criterion (H1/H3/H5) is below 2, fix it before presenting.
3. Handing over (workflow C) needs no scoring, but complete the checklist in REFERENCE §6 before starting work.
4. H5 is 2 only when there are no findings or every finding has a human ruling. **Ignoring or auto-fixing a finding scores 0** (and is forbidden in the first place).
