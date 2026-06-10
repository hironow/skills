# REFERENCE — 決定記録・decision queue・Slack 連携の詳細仕様

Nygard 流 ADR を厳密化した決定記録ガバナンス（不変・supersede・反転記録）に基づく運用ルールの詳細。

## 目次

1. [用語](#1-用語)
2. [決定記録の必須ヘッダ](#2-決定記録の必須ヘッダ全項目必須空欄禁止)
3. [ステータス語彙とライフサイクル](#3-ステータス語彙とライフサイクルこの語彙以外禁止遷移は一方向)
4. [決定記録の必須セクション](#4-決定記録の必須セクション)
5. [Decision Queue ファイルの仕様](#5-decision-queue-ファイルの仕様)
6. [Slack メンション ID の取り扱い](#6-slack-メンション-id-の取り扱い)
7. [Slack メッセージテンプレ](#7-slack-メッセージテンプレ)
8. [Slack API 投稿の具体例](#8-slack-api-投稿の具体例slack_bot_token-がある場合)
9. [README 連動更新](#9-readme-連動更新確定supersede-時)
10. [DR 間整合検査](#10-dr-間整合検査cross-consistency-check--検出は必須裁定は人間)

## 1. 用語

- **ADR** (Architecture Decision Record): 技術・設計・アーキテクチャの決定記録。`docs/adr/`。決める人はエンジニア/アーキテクト。
- **PDR** (Product Decision Record): プロダクト・UX・業務仕様の決定記録。`docs/pdr/`。決める人はプロダクト/運用/ビジネス。
- **Decision Queue**: 未承認決定（Proposed）の決裁待ち一覧 md ファイル（既定パス: `docs/decision-queue.md`）。「誰が・何を・いつ決めるか」と Slack 連携状態の SSoT（唯一の正）。
- **supersede（置き換え）**: 既存の決定を新しい記録で置換すること。旧記録は削除せず残す。
- **reversal（反転）**: 旧決定と実質逆の結論で supersede すること。反転記録セクションが必須。

## 2. 決定記録の必須ヘッダ（全項目必須・空欄禁止）

| field | 規則 |
|---|---|
| `id` | `ADR-NNNN` / `PDR-NNNN`（4桁ゼロ詰・連番・再利用/重複/欠番埋め禁止） |
| `title` | 決定内容が一意に分かる名詞句/動詞句。ファイル名 `NNNN-kebab-title.md` と一致 |
| `status` | 下記ステータス語彙のみ |
| `date` | 起票日（ISO 8601） |
| `decided-date` | Accepted/Rejected 化した日。Proposed の間は `—` |
| `decision-maker` | 実名/ロール。Accepted では必須（Proposed は `TBD` 可） |
| `author` | 起票者。存在する場合は次の `author-slack` が必須 |
| `author-slack` | 作者の Slack メンション ID（`<@UXXXXXXXX>`）。**author がいる限り空欄・省略禁止** |
| `supersedes` | 旧記録 ID。無ければ `none` |
| `superseded-by` | 後続記録 ID。無ければ `none` |
| `related` | 関連 OQ / gap-ID / 他の決定記録への cross-ref |

## 3. ステータス語彙とライフサイクル（この語彙以外禁止・遷移は一方向）

```
Proposed ──▶ Accepted ──▶ Superseded   (後継記録に置換)
        │            └──▶ Deprecated   (廃止・後継なし)
        ├──▶ Rejected
        └──▶ Deferred ──▶ Proposed     (再起票時のみ)
```

- `Accepted → Proposed` への差し戻し禁止。変更は新規起票＋supersede。
- 各遷移に日付＋実行者を残す（`decided-date` ＋ commit）。

## 4. 決定記録の必須セクション

- `## Context` — 背景・なぜ決めるか（事実のみ）。
- `## Decision` — 唯一の確定文。MUST/SHALL で一意に。複数決定は D1/D2… と番号付与。Proposed の間は「（Proposed。確定後に MUST 文で記述。）」と書く。
- `## Options Considered` — 採用案＋却下案を全列挙し、却下理由必須。
- `## Consequences` — `Positive` / `Negative` / `Neutral` を明示。
- `## 反転記録 (Reversal)` — 反転 supersede のときのみ必須。それ以外は `none`。
- `## やさしい説明` — 非エンジニア向け（PDR 必須・ADR 推奨）。専門用語なしで要点が分かるように。
- `## 決定（記入待ち）` — Proposed のとき必須。選択肢チェックボックス＋決定者/日付欄＋決定後のアクション。

本文は日本語主体。英語専門用語は初出時に日本語の言い換えを併記する。

## 5. Decision Queue ファイルの仕様

- 既定パス: `docs/decision-queue.md`（リポジトリによって異なる場合はユーザーに確認）。
- 構成: ①使い方 ②早見表（決裁待ち） ③決定済みログ。テンプレ: [templates/decision-queue.md](templates/decision-queue.md)。
- 早見表の必須列: `ID` / `何を決める（ひとことで）` / `種別` / `作者` / `作者 Slack` / `決める人` / `決裁者 Slack` / `期限` / `状態` / `Slack スレッド` / `最終催促日` / `備考` / `元ファイル`。`備考` には整合検査の裁定結果（§10.3）や特記事項を残す。
- **検証ルール（登録・更新のたびに確認）**:
  1. `作者` 列に値がある行は `作者 Slack` 列に `<@U` で始まるメンション ID が必ずある。
  2. queue の行と決定記録ヘッダ（`status` / `author-slack` 等）が一致している。
  3. `Proposed` でない記録が早見表に残っていない（決定済みログへ移す）。
  4. 早見表の全行に対応する記録ファイルが実在する。
- 決定済みログへ移す際は `決定日` / `決定者` / `結論（Accepted/Rejected/Deferred＋要約）` を追記する。

## 6. Slack メンション ID の取り扱い

- 形式は `<@UXXXXXXXX>`（メンバー ID）。表示名や `@name` 文字列はメンションにならないため不可。
- ID の入手方法（優先順）:
  1. ユーザーに直接確認（Slack プロフィール →「メンバー ID をコピー」）。
  2. `$SLACK_BOT_TOKEN` があれば `users.lookupByEmail` で引く:
     `curl -s -H "Authorization: Bearer $SLACK_BOT_TOKEN" "https://slack.com/api/users.lookupByEmail?email=<email>"`
  3. 既存の queue・決定記録・git log から同一人物の ID を再利用。
- **見つからない場合は登録をブロックしてユーザーに確認する。推測・捏造は禁止。**

## 7. Slack メッセージテンプレ

> Slack は「決めた人・作者に聞く／依頼する／催促する」相談の場。決裁依頼・催促・確定報告は必要時に、**整合検査検出時の関係者相談は必須**（テンプレは §10.3）に使う。記録の作成・更新・上書きそのものは常にリポジトリ内の md ファイルで完結させる（Slack の発言は決定の根拠メモであって SSoT ではない）。

### 起票通知（決裁依頼）
```
:bell: 決裁依頼 {ID}「{title}」
起票: {author-slack} ／ 決裁者: {decider-slack} ／ 期限: {YYYY-MM-DD}
■ 要点（やさしい説明）: {1〜2文}
■ 選択肢: A) {…} / B) {…}（推奨: {…}）
■ 詳細: {記録ファイルへのリンク（リポジトリ URL があれば blob リンク）}
このスレッドで「Accept / 修正のうえ Accept / Reject / Deferred」を返信してください。
```

### 催促
```
:alarm_clock: リマインド {ID}「{title}」（期限 {YYYY-MM-DD}{超過 n 日}）
{decider-slack} 決裁をお願いします。選択肢と詳細は上記（または {リンク}）。
```

### 確定報告
```
:white_check_mark: 決定 {ID}「{title}」→ {Accepted/Rejected/Deferred}
決定者: {decision-maker} ／ 決定日: {YYYY-MM-DD}
結論: {Decision の要約 1〜2 文}
{author-slack} 後続アクション: {決定後にやること}
```

### supersede / 反転通知
```
:arrows_counterclockwise: 決定の置換 {新ID} が {旧ID} を supersede（{反転あり/なし}）
理由: {要約} ／ 詳細: {リンク}
```

## 8. Slack API 投稿の具体例（`$SLACK_BOT_TOKEN` がある場合）

```bash
# チャンネルへ投稿（返り値の ts をスレッド ID として queue に記録する）
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel": "{#channel または C…ID}", "text": "{テンプレ本文}"}'

# スレッドへ返信（催促・確定報告）
curl -s -X POST https://slack.com/api/chat.postMessage \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"channel": "{C…}", "thread_ts": "{queue に記録した ts}", "text": "{本文}"}'
```

- 投稿成功時は `ok: true` を確認し、`ts` を queue の `Slack スレッド` 列に `{channel}/{ts}` 形式で記録する。
- `ok: false` ならエラー（`channel_not_found` / `not_in_channel` 等）をユーザーに報告し、リトライ前に原因を解消する。
- メンションを有効にするため本文はプレーンテキストの `<@U…>` をそのまま含める（エスケープしない）。

## 9. README 連動更新（確定・supersede 時）

- `docs/adr/README.md` / `docs/pdr/README.md` の索引に新記録を追記。
- supersede/反転時は README 末尾の `## 決定変更ログ (Decision Change Log)` に
  `YYYY-MM-DD: {旧ID}「A」→ {新ID}「B」（理由）` 形式で1行追記。

## 10. DR 間整合検査（cross-consistency check）— 検出は必須・裁定は人間

ADR/PDR を**作る・更新する・上書きする前に必ず**、対象記録を他の全 DR（ADR ∪ PDR）と照合する。
**1件でも検出したら作業を止めて指摘し、矛盾先 DR の関係者を巻き込んだ相談（§10.3）を必ず実施する。解消方法は相談を経て人間が決める。AI が自動で解消・修正・黙殺してはならず、「矛盾を承知で進める」も認めない。**

### 10.1 検査の5分類

| 分類 | 定義 | 検出例 |
|---|---|---|
| **矛盾 (contradiction)** | 対象の Decision が、既存の `Accepted` 記録の Decision と両立しない（supersedes 宣言なしで） | ADR-0031 が「cross-aggregate tx 禁止（allowlist 外）」なのに、新 ADR が allowlist 外の tx を MUST で許可 |
| **重複 (duplication)** | 同じ決定対象を扱う既存記録が存在する（1決定=1記録違反・二重決裁の危険・採番重複も含む） | 同一論点の ADR と PDR が並立／`0024` が2件のような採番衝突 |
| **誤解 (misreading)** | 他 DR の内容を誤って引用・要約・前提にしている | Context に「ADR-0027 は X を許可している」と書くが、実際の 0027 は X を禁止 |
| **関連の誤謬 (false relation)** | `related` に挙げた DR/OQ/gap が実際は無関係、または明らかに関連する記録が `related` から欠落 | tx 境界の新 ADR が ADR-0031 を related に持たない |
| **関係の錯誤 (mistaken relationship)** | supersession チェーンや記録間の関係種別の誤り | 「補足」なのに `supersedes` と宣言／反転なのに反転記録なしの通常 supersede／`supersedes` と旧記録側 `superseded-by` の双方向不一致 |

### 10.2 検査手順

1. **全件走査**: `docs/adr/` と `docs/pdr/` の全ファイルのタイトル・ヘッダ（`status`/`supersedes`/`superseded-by`/`related`）を一覧化する（grep で可）。
2. **候補抽出**: 対象記録のキーワード・対象領域（例: tx、API、暗号鍵、承認フロー）で既存記録を検索し、関連候補を挙げる。
3. **精読照合**: 関連候補と、対象記録の `related`/`supersedes` に挙がっている記録は**全文を読み**、5分類それぞれで照合する。引用・前提の正誤は原文と突き合わせる（誤解の検出）。
4. **チェーン検証**: supersession の双方向リンク（`supersedes` ⇄ `superseded-by`）と status の整合（Superseded なのに後継なし等）を確認する（錯誤の検出）。
5. **検出ゼロなら**その旨を採点報告に含めて先へ進む。**検出があれば 10.3 の報告を行い、人間の裁定まで該当作業（起票完了・Accepted 化・supersede 確定）を停止する。**

### 10.3 指摘の報告と関係者相談（必須）— 「矛盾を承知で進める」は不可

検出ごとにまずユーザーへ次の形式で報告する:

```
⚠️ DR 間整合検査: {n} 件検出（対象: {ID}「{title}」）

1. [{分類}] {相手の ID・status}
   - 該当箇所: {対象側の引用} ⇔ {相手側の引用}
   - なぜ問題か: {1〜2文。事実のみ}
   - 関係者: {相手 DR の decision-maker / author と Slack メンション ID}
   - 解消の選択肢:
     a) {例: 本記録に supersedes: {相手 ID} を宣言し反転記録を書く}
     b) {例: 本記録の該当 Decision を修正/撤回する}
     c) {例: 相手記録側の supersede を別途起票する（本件は保留）}
```

そのうえで次のフローを**必ず**通す（省略・短絡は不可）:

1. **関係者の特定**: 矛盾先（相手）DR の `decision-maker`・`author` を特定し、Slack メンション ID を確認する（不明なら §6 の手順、それでも不明ならユーザーに確認）。
2. **相談必須**: 関係者を巻き込んだ相談なしに先へ進むことは**禁止**。**「矛盾を承知でこのまま進める」という選択肢は提示しない・求められても受け付けない**（その求め自体を相談の議題にする）。相談場所が Slack というだけで、本質は「元の決定の関係者を巻き込むこと」。
3. **Slack で相談スレッドを立てる**（手段は §8。下のテンプレ使用）: 検出内容＋選択肢を関係者メンション付きで投稿し、スレッドを queue の備考に記録する。Slack が一切使えない場合は相談文面を生成してユーザーに相談の実施を依頼する（**相談そのものの省略は不可**）。
4. **裁定**: 相談の結果として人間（関係者＋決裁者）が a/b/c 等から決める。AI は決めない。推奨を示すなら理由つきで1つだけ・中立に。
5. **痕跡**: 裁定結果を対象記録の `related` / `## Context`、queue の備考、commit message に記録する:
   「{分類} を {誰} が {日付} に {選択肢} と裁定（相談スレッド: {channel}/{ts}）」。

相談メッセージテンプレ:
```
:warning: DR 整合相談 — {対象ID}「{title}」が {相手ID}「{相手title}」と {分類} の疑い
{関係者メンション} 元の決定に関わった方の確認・相談が必要です（このスレッドで）。
■ 該当箇所: {対象側引用} ⇔ {相手側引用}
■ なぜ問題か: {1〜2文}
■ 解消の選択肢: a) {…} b) {…} c) {…}
裁定が出るまで {対象ID} の起票完了/確定/supersede は保留します。
```
