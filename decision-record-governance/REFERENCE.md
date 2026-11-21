# REFERENCE — code-SSOT rules registry and durable consultation

Detailed schema and governance rules for `docs/rules.toml`, `docs/rules-retired.toml`, stable contacts, durable consultation, and consistency checks.

## Contents

1. [Orthogonal SSOT boundaries](#1-orthogonal-ssot-boundaries)
2. [Rules registry schema (`docs/rules.toml`)](#2-rules-registry-schema-docsrulestoml)
3. [Retirement (`docs/rules-retired.toml`)](#3-retirement-docsrules-retiredtoml)
4. [Stable contact handles](#4-stable-contact-handles)
5. [Consultation message templates](#5-consultation-message-templates)
6. [Consistency check — detection is mandatory, the ruling is human](#6-consistency-check--detection-is-mandatory-the-ruling-is-human)

## 1. Orthogonal SSOT boundaries

Do not duplicate the same rule across prose and code:

| What | Source of truth | Read by agents |
| --- | --- | --- |
| Domain terms, state machines, formal invariants | Code + tests + `provable-glossary` (`glossary/Glossary/*.lean`, `glossary/Spec/*.qnt`, generated docs) | Generated docs / code anchors |
| Mechanically enforceable constraints | Lint rules, unit/integration tests, CI/Dagger checks | Hook/CI failures + optional 1-line `enforced_by` row in `docs/rules.toml` |
| Non-codable operational policies & named exceptions | `docs/rules.toml` | Only the `area` relevant to the task |
| Pending proposals & rationale ("Why") | GitHub Draft PRs / Issues and commit history | Only when investigating history |
| Retired rules | `docs/rules-retired.toml` | Never auto-loaded |

## 2. Rules registry schema (`docs/rules.toml`)

Default path: `docs/rules.toml` (template: [templates/rules.toml](templates/rules.toml)). TOML is used because it supports inline comments, is human-editable in PRs, and parses with Python 3.11+ stdlib `tomllib`.

| field | required | rule |
| --- | --- | --- |
| `id` | yes | `<area>.<kebab-case>`. Immutable once merged; never renamed or reused |
| `level` | yes | RFC 2119 keyword: `MUST`, `MUST NOT`, `SHOULD`, or `MAY` |
| `text` | yes | Unambiguous normative statement (1–3 sentences, no hedges like "basically") |
| `scope` | yes | `org`, `repo`, or `service:<name>` |
| `area` | yes | Lowercase domain tag (`deps`, `ci`, `security`, `governance`, `python`, `formal`, …) |
| `enforced_by` | yes | List of repo-relative paths or `just` recipes enforcing this rule (`[]` if review-only) |
| `state` | yes | `approved` (review/advisory) or `enforced` (CI/hook blocks merge; requires non-empty `enforced_by`) |
| `exceptions` | yes | List of exception rule IDs in `docs/rules.toml` (`[]` if none) |
| `expires` | conditional | Required for time-boxed exceptions (ISO 8601 date or concrete milestone condition) |
| `author_contact` | yes | Stable handle (`@handle` or `<@UXXXXXXXX>`) of who proposed the rule |
| `decision_maker_contact` | yes (on settlement) | Stable handle of the human who ruled on the rule |
| `decided_date` | yes (on settlement) | ISO 8601 date of the human ruling |
| `consultation_url` | yes (on settlement) | Durable URL (PR comment, issue, or discussion) recording the human ruling and rationale |

### Automated validation (implement in repo tests)

Every repository carrying `docs/rules.toml` should validate in its test suite:

1. No duplicate `id` across `docs/rules.toml` and `docs/rules-retired.toml`.
2. Every `enforced_by` file path exists in the repository; every `state = "enforced"` rule has non-empty `enforced_by`.
3. Every ID listed in `exceptions` exists in `docs/rules.toml`.
4. Every active rule has non-empty `author_contact`, `decision_maker_contact`, `decided_date`, and `consultation_url`.

## 3. Retirement (`docs/rules-retired.toml`)

When a rule is retired or fully superseded by a replacement, move its `[[rule]]` block to `docs/rules-retired.toml` and add:

- `retired_date`: ISO 8601 date of retirement
- `retirement_url`: PR/Issue URL with the human ruling
- `replaced_by`: optional list of replacement rule IDs or code/check paths

Never delete the ID from history or reuse it for a new rule.

## 4. Stable contact handles

- Prefer a GitHub `@handle` when the repository lives on GitHub. Slack `<@UXXXXXXXX>` remains valid where Slack is the confirmed venue.
- Obtain handles from existing repository records, authenticated accounts, or the user. Display names alone are insufficient.
- **If `author_contact` is missing, block proposal. If `decision_maker_contact` is missing, block settlement. Never guess or fabricate.**

## 5. Consultation message templates

Confirm venue and wording with the user before posting externally (absolute rule 6).

### Proposal / approval request

```text
:bell: ルール決裁依頼 `{id}`（area: {area} / scope: {scope}）
起票: {author_contact} ／ 決裁者: {decision_maker_contact}
■ 条文（{level}）: {text}
■ 機械検証（enforced_by）: {enforced_by または なし（レビュー運用）}
■ PR: {PR URL}
このスレッドで「Accept / 修正のうえ Accept / Reject」を返信してください。
```

### Conflict consultation (mandatory on any consistency finding)

```text
:warning: ルール整合性チェックの相談（{category}）
提案: `{new_id}`（起票: {author_contact}）
競合対象: `{existing_id}`（決裁者: {existing_decider} / 起票: {existing_author}）
■ 検出内容: {具体的な矛盾・重複・関係誤りの説明}
■ 選択肢: A) {…} / B) {…}
■ 詳細: {PR URL}
関係者の確認のうえ、人間の裁定をお願いします。
```

## 6. Consistency check — detection is mandatory, the ruling is human

### Five categories

1. **Contradiction**: two rules cannot both be satisfied.
2. **Duplication**: the same constraint is stated twice (risk of drift).
3. **Misreading**: a proposed rule quotes or narrows an existing rule inaccurately.
4. **False relation**: an `exceptions` link points to an unrelated rule.
5. **Mistaken relationship**: an exception is filed as a reversal, or a reversal is disguised as a minor edit.

### Procedure

1. Draft the proposed `[[rule]]` entry.
2. Compare it against **all active rules in `docs/rules.toml`** (O(N) for a single proposal; group by `area` for periodic full sweeps), paying special attention to matching `area`, `scope`, and `exceptions`.
3. When a match is found, open the existing rule's `consultation_url` if needed to verify intent.
4. If any of the five categories triggers, **stop immediately**, report the exact rule IDs and finding to the user, consult `decision_maker_contact` and `author_contact` in the confirmed durable venue, and proceed only after a human ruling is recorded.
