---
name: decision-record-governance
description: ADR（技術決定）/ PDR（プロダクト決定）のディシジョンレコードを作成・更新・上書き（supersede/反転）し、decision-queue.md（決裁待ち一覧）と品質ルーブリックで統治する。他 DR との矛盾・重複・誤解・関連の誤謬・関係の錯誤を必ず検査し、検出時は矛盾先の関係者を巻き込む Slack 相談を必須として人間に裁定させる。Use when the user mentions ADR, PDR, decision record, decision queue, 決定記録, 意思決定の起票・更新・supersede・反転, DR の矛盾・整合性チェック, 決裁の相談・催促, or wants to manage architecture/product decisions.
---

# Decision Record Governance（ADR/PDR × Queue × ルーブリック × 整合検査 × Slack 相談）

**中心は DR（Decision Record = ADR ∪ PDR）を「作る・更新する・上書きする」こと**。Slack は相談の場 — 決裁依頼・確認・催促（必要時）と、整合検査で矛盾等を検出したときの関係者相談（必須）に使う。

- **作る** = 起票（`Proposed`）して queue に登録
- **更新する** = 決定の確定（`Accepted`/`Rejected`/`Deferred`）・記入待ちの記入・README 連動更新
- **上書きする** = supersede（置き換え）/ 反転。既存記録は編集せず新記録で置換

## 絶対ルール（違反したら作業を止めてユーザーに確認）

1. **decision queue 必須**: ADR/PDR を起票したら必ず `docs/decision-queue.md` に登録する。なければ [templates/decision-queue.md](templates/decision-queue.md) から作成。queue が「未承認決定の SSoT（唯一の正）」。
2. **作者がいる場合は Slack メンション ID 必須**: 作者（起票者）が存在する記録は、queue の行と記録ヘッダに **`<@UXXXXXXXX>` 形式の Slack メンション ID が必ず存在する**こと。不明なら登録を進めず確認する。**捏造禁止**（取得方法は [REFERENCE.md](REFERENCE.md) §6）。
3. **不変性**: `Accepted`/`Rejected` の記録本文は編集禁止。変更・反転は新記録で supersede。queue から消さず「決定済みログ」へ移す。
4. **1決定 = 1記録**。採番は append-only（4桁ゼロ詰・再利用/欠番埋め禁止）。ファイル名 `NNNN-kebab-title.md`。
5. **ルーブリックゲート**: 起票完了前・確定前に [RUBRIC.md](RUBRIC.md) で採点する。起票ゲートは 0 点観点ゼロ、確定ゲートは★観点（R3/R4/R8/R10）すべて 2 が条件。採点結果はユーザーに報告。
6. **DR 間整合検査必須・関係者相談必須・裁定は人間**: 作る・更新する・上書きする前に必ず他の全 DR と照合し、**矛盾・重複・誤解・関連の誤謬・関係の錯誤**（[REFERENCE.md](REFERENCE.md) §10 の5分類）を検査する。1件でも検出したら作業を止めて指摘し、**矛盾先 DR の関係者（決定者・作者）を巻き込んだ相談を必ず実施する**（相談場所が Slack というだけで、巻き込みが本質）。**「矛盾を承知でこのまま進める」は選択肢にしない・受け付けない。** 解消方法は相談を経て人間が決め、AI が自動で解消・修正・黙殺してはならない。
7. **Slack 投稿は外部公開**: 用途は決裁依頼・確認・催促（必要時）と、**整合検査検出時の関係者相談（必須）**。初回投稿前にチャンネルと文面をユーザーに確認する。

## ワークフロー

### A. 作る（起票）
1. 種別判定: 技術/アーキ判断 → ADR（`docs/adr/`）、プロダクト/UX/業務判断 → PDR（`docs/pdr/`）。
2. 既存の最大番号から次番号を採番し、[templates/adr-template.md](templates/adr-template.md) / [templates/pdr-template.md](templates/pdr-template.md) で `Proposed` として作成。
3. 作者の Slack メンション ID を確認（絶対ルール2）。
4. **DR 間整合検査**（絶対ルール6・[REFERENCE.md](REFERENCE.md) §10）。検出したら停止し、関係者相談（§10.3）を経て人間の裁定を得てから続行。
5. [RUBRIC.md](RUBRIC.md) の**起票ゲート**で採点（0 があれば直す）。
6. `docs/decision-queue.md` の早見表に1行追加（列構成は [REFERENCE.md](REFERENCE.md) §5）。
7. 決裁を依頼する必要があれば Slack に投稿し、スレッドを queue に記録（下記「Slack で相談する」）。

### B. 更新する（決定の確定）
1. 決裁内容（誰が・いつ・どれを選んだか）を確認。**曖昧・未取得なら Slack で決めた人に聞く**。
2. **DR 間整合検査を再実行**（絶対ルール6）。未裁定の検出が残ったまま `Accepted` 化しない。
3. 記録の `## 決定（記入待ち）` にチェック・決定者・日付を記入。`Accepted` なら `## Decision` を MUST 文で確定し、却下案の却下理由を埋める。
4. ヘッダの `status` / `decided-date` / `decision-maker` を更新。
5. [RUBRIC.md](RUBRIC.md) の**確定ゲート**で採点（★が 2 未満なら確定を止めて報告）。
6. queue の行を「決定済みログ」へ移動し、ADR/PDR の README（索引・決定変更ログ）を更新。
7. 必要があれば Slack スレッドに確定報告（作者メンション付き）。

### C. 上書きする（supersede / 反転）
1. 旧記録は本文編集せず、新記録を A の手順で起票（ヘッダ `supersedes:` 必須。A の整合検査で supersession チェーンも検証）。
2. **旧記録の決定者・作者（関係者）への Slack 相談は必須**。supersede/反転は既存の `Accepted` 決定との意図的な矛盾なので、絶対ルール6 の相談フロー（[REFERENCE.md](REFERENCE.md) §10.3）を必ず通す。
3. 旧記録は `status: Superseded` ＋ `superseded-by:` 追記のみ。反転なら新記録に `## 反転記録 (Reversal)` 必須。
4. README 末尾の `## 決定変更ログ (Decision Change Log)` に1行追記し、queue にも新記録を登録。

### D. queue のメンテ（棚卸し）
1. queue と記録ファイルの整合を検査（[REFERENCE.md](REFERENCE.md) §5 の検証ルール）。
2. **DR 間整合スイープ**: 全 DR を §10 の5分類で照合。検出したら絶対ルール6に従い関係者相談を起こす。
3. `Proposed` のまま期限超過の項目を抽出し、必要があれば Slack で決裁者に催促。「最終催促日」を更新。

## Slack で相談する（相談場所が Slack なだけ・巻き込みが本質）

使いどころ: ①決裁を依頼したい ②決定の意図・選択が曖昧で決めた人に確認したい ③期限超過の催促（①〜③は必要時）／**④整合検査で検出した矛盾等の関係者相談（必須・省略不可）**。
手段の優先順: Slack MCP ツール（ToolSearch でロード）→ `$SLACK_BOT_TOKEN` で `chat.postMessage` → `$SLACK_WEBHOOK_URL` → 文面だけ生成して手動投稿を依頼。
メッセージテンプレ・API 例・ヘッダ仕様・ステータス語彙は [REFERENCE.md](REFERENCE.md)、品質基準は [RUBRIC.md](RUBRIC.md) を参照。
