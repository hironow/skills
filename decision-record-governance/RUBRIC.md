# RUBRIC — quality rubric for rules registry proposals

Measures whether a proposed `docs/rules.toml` entry (or amendment/retirement) is ready for human ruling and merge. Schema completeness is checked against [REFERENCE.md](REFERENCE.md) §2.

## Two gates

- **Filing gate** (before opening PR for review): score R1–R7; **no criterion may be 0**.
- **Settling gate** (before merge): score R1–R7 again; **every gate criterion (R1, R3, R5, R7) must be 2**.
- Report scores explicitly (for example `R1:2 R2:2 R3:2 R4:2 R5:2 R6:2 R7:2`).

## Criteria

| # | criterion | 0 (missing / fail) | 1 (insufficient) | 2 (pass) |
| --- | --- | --- | --- | --- |
| R1 | **Triage & SSOT placement** (gate) | Creates a `docs/adr/` file, or puts an ephemeral/easily-codable detail into `docs/rules.toml` without checking Step 0 | Placed in `docs/rules.toml` when a lint/test check is feasible, with no note on why it is `approved` instead of `enforced` | Passes Step 0 Triage cleanly; `enforced_by` and `state` accurately reflect mechanical enforcement |
| R2 | **Schema & stable contacts** | Missing required field, duplicate/reused `id`, or missing/fabricated `author_contact` / `decision_maker_contact` | All fields present, but `expires` missing on a time-boxed exception or `id` format off | Every field matches REFERENCE §2; verified stable handles; immutable `<area>.<kebab-case>` ID |
| R3 | **Normative clarity** (gate) | Empty `text` or no RFC 2119 `level` | Hedges ("basically", "preferably") without explicit exceptions, or multiple unrelated rules crammed into one entry | Single, unambiguous `MUST` / `MUST NOT` / `SHOULD` / `MAY` rule with explicit `scope` and `area` |
| R4 | **Rationale & rejected options in PR** | PR body states only the conclusion with no alternatives | Alternatives listed without rejection reasons or tradeoffs | PR body states concrete facts, at least two options, tradeoffs, and rejection reasons |
| R5 | **Human ruling & traceability** (gate) | Settled without `consultation_url`, `decided_date`, or explicit human ruling | Ruling occurred only in ephemeral chat and was not copied to a durable URL | Durable `consultation_url` records who ruled, what was chosen, and when; `exceptions`/`enforced_by` links resolve |
| R6 | **Plain language** | Jargon-heavy or unreadable to someone outside the author's immediate context | Understandable only by reading the full PR diff | Short, direct sentences; clear to any maintainer reading `docs/rules.toml` |
| R7 | **Consistency check & human resolution** (gate) | Consistency check skipped, or a conflict was patched/ignored by AI without consultation | Checked only a subset of `docs/rules.toml` or omitted the conflicting rule's contacts | Compared against all active rules in `docs/rules.toml` on all 5 categories; zero findings, or every finding went through durable consultation and human ruling |

Gate criteria (must be 2 at the settling gate): **R1, R3, R5, R7**.
