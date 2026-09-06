# REFERENCE — decision records, the decision queue, and Slack integration

Detailed rules for decision-record governance: Nygard-style ADRs made strict (immutable records, supersession, reversal records).

## Contents

1. [Terms](#1-terms)
2. [Required header fields](#2-required-header-fields-every-field-mandatory-no-blanks)
3. [Status vocabulary and lifecycle](#3-status-vocabulary-and-lifecycle-no-other-words-transitions-are-one-way)
4. [Required sections](#4-required-sections)
5. [The decision queue file](#5-the-decision-queue-file)
6. [Slack mention IDs](#6-slack-mention-ids)
7. [Slack message templates](#7-slack-message-templates)
8. [Posting with the Slack API](#8-posting-with-the-slack-api-when-slack_bot_token-is-available)
9. [README updates](#9-readme-updates-on-settlement-and-supersede)
10. [Cross-DR consistency check](#10-cross-dr-consistency-check--detection-is-mandatory-the-ruling-is-human)

## 1. Terms

- **ADR** (Architecture Decision Record): a technical, design, or architecture decision. Lives in `docs/adr/`. Decided by engineers or architects.
- **PDR** (Product Decision Record): a product, UX, or business-rule decision. Lives in `docs/pdr/`. Decided by product, operations, or business owners.
- **Decision queue**: the markdown list of undecided (`Proposed`) records awaiting approval (default path `docs/decision-queue.md`). The single source of truth for who decides what by when, and for the Slack thread state.
- **Supersede**: replace an existing decision with a new record. The old record is kept, never deleted.
- **Reversal**: a supersede whose conclusion is effectively the opposite of the old decision. A reversal section is mandatory.

## 2. Required header fields (every field mandatory, no blanks)

| field | rule |
|---|---|
| `id` | `ADR-NNNN` / `PDR-NNNN` (four digits, zero-padded, sequential; never reused, duplicated, or back-filled) |
| `title` | A noun or verb phrase that identifies the decision unambiguously. Matches the file name `NNNN-kebab-title.md` |
| `status` | One of the status words in §3 only |
| `date` | Filing date (ISO 8601) |
| `decided-date` | Date the record became Accepted or Rejected. `—` while Proposed |
| `decision-maker` | Real name or role. Mandatory once Accepted (`TBD` is allowed while Proposed) |
| `author` | Who filed the record. If present, `author-slack` is mandatory |
| `author-slack` | The author's Slack mention ID (`<@UXXXXXXXX>`). **Never blank or omitted while there is an author** |
| `supersedes` | ID of the record this one replaces, or `none` |
| `superseded-by` | ID of the record that replaced this one, or `none` |
| `related` | Cross-references to related open questions, gap IDs, or other decision records |

## 3. Status vocabulary and lifecycle (no other words; transitions are one-way)

```
Proposed ──▶ Accepted ──▶ Superseded   (replaced by a successor record)
        │            └──▶ Deprecated   (retired, no successor)
        ├──▶ Rejected
        └──▶ Deferred ──▶ Proposed     (only when re-filed)
```

- `Accepted → Proposed` is forbidden. Change means a new record plus supersede.
- Every transition leaves a date and an actor (`decided-date` plus the commit).

## 4. Required sections

- `## Context` — the background and why a decision is needed now (facts only).
- `## Decision` — the single settled statement, unambiguous, in MUST/SHALL form. Number multiple decisions D1, D2, …. While Proposed, write the placeholder "（Proposed。確定後に MUST 文で記述。）".
- `## Options Considered` — every option, chosen and rejected, each rejected one with its reason.
- `## Consequences` — explicit `Positive` / `Negative` / `Neutral`.
- `## 反転記録 (Reversal)` — mandatory only for a reversal supersede; otherwise `none`.
- `## やさしい説明` — a plain-language explanation for non-engineers (mandatory for PDRs, recommended for ADRs). The gist must be clear without jargon.
- `## 決定（記入待ち）` — mandatory while Proposed: option checkboxes, decision-maker and date fields, and the follow-up actions per option.

Record bodies are written primarily in Japanese (the templates are Japanese). Give a Japanese gloss for every English technical term on first use.

## 5. The decision queue file

- Default path: `docs/decision-queue.md` (confirm with the user if the repository differs).
- Structure: (1) how to use, (2) the summary table of records awaiting approval, (3) the decided log. Template: [templates/decision-queue.md](templates/decision-queue.md).
- Required columns of the summary table: `ID` / `何を決める（ひとことで）` / `種別` / `作者` / `作者 Slack` / `決める人` / `決裁者 Slack` / `期限` / `状態` / `Slack スレッド` / `最終催促日` / `備考` / `元ファイル`. `備考` (notes) holds consistency-check rulings (§10.3) and anything else worth noting.
- **Validation rules (check on every registration and update)**:
  1. Every row with a value in `作者` (author) has a mention ID starting with `<@U` in `作者 Slack`.
  2. The queue row and the record header agree (`status`, `author-slack`, and so on).
  3. No record that is no longer `Proposed` remains in the summary table (move it to the decided log).
  4. Every row in the summary table has an existing record file.
- When moving a row to the decided log, add `決定日` (decided date), `決定者` (decision-maker), and `結論` (Accepted/Rejected/Deferred plus a summary).

## 6. Slack mention IDs

- The form is `<@UXXXXXXXX>` (member ID). Display names and `@name` strings do not produce a mention and are not acceptable.
- How to obtain one, in order:
  1. Ask the user directly (Slack profile → "Copy member ID").
  2. With `$SLACK_BOT_TOKEN`, look it up with `users.lookupByEmail`:
     `curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" "https://slack.com/api/users.lookupByEmail?email=<email>"`
  3. Reuse the same person's ID from the existing queue, records, or git log.
- **If it cannot be found, block the registration and ask the user. Guessing or fabricating is forbidden.**

## 7. Slack message templates

> Slack is where you ask, request, and remind the decision-maker and the author. Approval requests, reminders, and settlement notices are posted when needed; **consulting the people involved about a consistency-check finding is mandatory** (template in §10.3). Creating, updating, and superseding records always happens in the markdown files in the repository — a Slack message is supporting evidence for a decision, never the source of truth.

The message bodies below are in Japanese because that is the language of the teams that read them; keep them as they are.

### Filing notice (approval request)
```
:bell: 決裁依頼 {ID}「{title}」
起票: {author-slack} ／ 決裁者: {decider-slack} ／ 期限: {YYYY-MM-DD}
■ 要点（やさしい説明）: {1〜2文}
■ 選択肢: A) {…} / B) {…}（推奨: {…}）
■ 詳細: {記録ファイルへのリンク（リポジトリ URL があれば blob リンク）}
このスレッドで「Accept / 修正のうえ Accept / Reject / Deferred」を返信してください。
```

### Reminder
```
:alarm_clock: リマインド {ID}「{title}」（期限 {YYYY-MM-DD}{超過 n 日}）
{decider-slack} 決裁をお願いします。選択肢と詳細は上記（または {リンク}）。
```

### Settlement notice
```
:white_check_mark: 決定 {ID}「{title}」→ {Accepted/Rejected/Deferred}
決定者: {decision-maker} ／ 決定日: {YYYY-MM-DD}
結論: {Decision の要約 1〜2 文}
{author-slack} 後続アクション: {決定後にやること}
```

### Supersede / reversal notice
```
:arrows_counterclockwise: 決定の置換 {新ID} が {旧ID} を supersede（{反転あり/なし}）
理由: {要約} ／ 詳細: {リンク}
```

## 8. Posting with the Slack API (when `$SLACK_BOT_TOKEN` is available)

```bash
# Post to a channel (record the returned ts in the queue as the thread ID)
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel": "{#channel or C…ID}", "text": "{template body}"}'

# Reply in the thread (reminders, settlement notices)
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel": "{C…}", "thread_ts": "{ts recorded in the queue}", "text": "{body}"}'
```

- On success, confirm `ok: true` and record `ts` in the queue's `Slack スレッド` column as `{channel}/{ts}`.
- On `ok: false`, report the error (`channel_not_found`, `not_in_channel`, …) to the user and resolve the cause before retrying.
- Keep `<@U…>` as plain text in the body (do not escape it) so the mention works.

## 9. README updates (on settlement and supersede)

- Add the new record to the index in `docs/adr/README.md` / `docs/pdr/README.md`.
- On supersede or reversal, append one line to `## 決定変更ログ (Decision Change Log)` at the end of the README in the form
  `YYYY-MM-DD: {旧ID}「A」→ {新ID}「B」（理由）`.

## 10. Cross-DR consistency check — detection is mandatory, the ruling is human

**Before creating, updating, or superseding any ADR/PDR**, compare the record against every other DR (ADR ∪ PDR).
**If even one finding comes up, stop, report it, and run the consultation with the people behind the conflicting DR (§10.3). A human decides the resolution after that consultation.**

### 10.1 The five categories

| category | definition | example |
|---|---|---|
| **Contradiction** | The record's Decision cannot coexist with the Decision of an existing `Accepted` record (without declaring `supersedes`) | ADR-0031 forbids cross-aggregate transactions outside an allowlist, and the new ADR permits one outside the allowlist with a MUST |
| **Duplication** | An existing record already covers the same decision (a "one decision = one record" violation, a risk of double approval; includes numbering collisions) | An ADR and a PDR on the same question side by side; two records both numbered `0024` |
| **Misreading** | Another DR is quoted, summarised, or relied on incorrectly | The Context says "ADR-0027 permits X" when 0027 actually forbids X |
| **False relation** | A DR, open question, or gap listed in `related` is actually unrelated, or an obviously related record is missing from `related` | A new ADR on transaction boundaries does not list ADR-0031 in `related` |
| **Mistaken relationship** | The supersession chain or the kind of relationship between records is wrong | A "supplement" declared as `supersedes`; a reversal filed as a plain supersede without a reversal section; `supersedes` and the old record's `superseded-by` do not match |

### 10.2 Procedure

1. **Scan everything**: list the title and header (`status` / `supersedes` / `superseded-by` / `related`) of every file in `docs/adr/` and `docs/pdr/` (grep is fine).
2. **Shortlist candidates**: search the existing records for the new record's keywords and area (transactions, API, encryption keys, approval flow, …).
3. **Read and compare**: read the full text of every candidate and of every record the new one lists in `related` / `supersedes`, and compare on all five categories. Check quotations and premises against the source text (misreading).
4. **Validate the chain**: check that supersession links are bidirectional (`supersedes` ⇄ `superseded-by`) and consistent with status (for example, `Superseded` with no successor) (mistaken relationship).
5. **No findings**: say so in the score report and continue. **Any finding**: report as in 10.3 and halt the affected step (completing the filing, moving to Accepted, settling the supersede) until a human rules.

### 10.3 Reporting findings and consulting the people involved (mandatory)

For each finding, first report to the user in this form (the report is in the user's language, Japanese by default):

```
DR 間整合検査: {n} 件検出（対象: {ID}「{title}」）

1. [{分類}] {相手の ID・status}
   - 該当箇所: {対象側の引用} ⇔ {相手側の引用}
   - なぜ問題か: {1〜2文。事実のみ}
   - 関係者: {相手 DR の decision-maker / author と Slack メンション ID}
   - 解消の選択肢:
     a) {例: 本記録に supersedes: {相手 ID} を宣言し反転記録を書く}
     b) {例: 本記録の該当 Decision を修正/撤回する}
     c) {例: 相手記録側の supersede を別途起票する（本件は保留）}
```

Then follow this flow **without exception or shortcut**:

1. **Identify the people involved**: the `decision-maker` and `author` of the conflicting DR, and their Slack mention IDs (§6 if unknown; if still unknown, ask the user).
2. **Consultation is mandatory**: proceeding without consulting them is **forbidden**. **Never offer "proceed knowing there is a contradiction" as an option, and do not accept it if asked** — make that request itself a topic of the consultation. Slack is only the venue; the point is to involve the people behind the original decision.
3. **Open a consultation thread on Slack** (means in §8; template below): post the finding and the options with the people mentioned, and record the thread in the queue's notes column. If Slack is unavailable, generate the message and ask the user to hold the consultation (**skipping the consultation itself is not allowed**).
4. **Ruling**: the humans (the people involved plus the approver) choose among a/b/c and so on. The AI does not decide. If you recommend, recommend one option, with reasons, neutrally.
5. **Trace**: record the ruling in the record's `related` / `## Context`, the queue's notes column, and the commit message:
   「{分類} を {誰} が {日付} に {選択肢} と裁定（相談スレッド: {channel}/{ts}）」.

Consultation message template (Japanese, as posted):
```
:warning: DR 整合相談 — {対象ID}「{title}」が {相手ID}「{相手title}」と {分類} の疑い
{関係者メンション} 元の決定に関わった方の確認・相談が必要です（このスレッドで）。
■ 該当箇所: {対象側引用} ⇔ {相手側引用}
■ なぜ問題か: {1〜2文}
■ 解消の選択肢: a) {…} b) {…} c) {…}
裁定が出るまで {対象ID} の起票完了/確定/supersede は保留します。
```
