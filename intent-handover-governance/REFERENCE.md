# REFERENCE — intent.md / handover.md の詳細仕様

docs-discipline（4種のドキュメントと4つの問い）のうち、`docs/intent.md` と
`docs/handover.md` の運用ルール詳細。

## 目次

1. [用語と使い分け](#1-用語と使い分け)
2. [intent.md の仕様](#2-intentmd-の仕様)
3. [handover.md の仕様](#3-handovermd-の仕様)
4. [保存・履歴の規約](#4-保存履歴の規約)
5. [整合検査の5分類](#5-整合検査の5分類検出は必須裁定は人間)
6. [再開時チェックリスト](#6-再開時チェックリストワークフロー-c)

## 1. 用語と使い分け

- **intent**（意図）: 依頼者＝人間が「なぜ今この作業をするか」を確定させた記録。
  work unit（ひとまとまりの作業。issue / PR / キャンペーン等）に1つ。
  **人間が所有** — AI は聞き取って書記するだけで、内容を発明しない。
- **handover**（引き継ぎ）: 次の担い手（新しいエージェント・同僚・未来の自分）が
  **2分で読んで再開できる**ことに最適化した現在地の記録。セッションが所有。
- **どちらを使うか**: 意図が非自明な work unit を始める → intent。セッションを
  跨いで作業が続く → handover。両方でも片方でもよい（合体はしない）。
  handover は intent を**参照**する（再掲しない）。

## 2. intent.md の仕様

### 必須ヘッダ

| field | 規則 |
|---|---|
| `Last updated` | ISO 8601（YYYY-MM-DD） |
| `Requester` | 依頼者の実名/ロール。**確実に分かる場合のみ・捏造禁止** |
| `Work unit` | 簡潔な識別子（issue ID / PR / キャンペーン名など） |

### 必須セクション

- `## Goal` — 依頼者が求める結果を1〜2文で。
- `## Success Criteria` — 観測可能・検証可能な条件の箇条書き。
- `## Scope`（`### In scope` / `### Out of scope (Non-goals)`）— 境界を明示。
- `## Constraints` — 技術・期限・予算・コンプライアンス上の制約。
- `## Open Questions` — 実装前に解消すべき未決事項（チェックボックス）。

### 起票・更新前の確認質問（曖昧なら STOP して人間に聞く）

1. 何が達成されたら「終わり」か（goal / success criteria）
2. どこまでやるか・やらないか（scope / non-goals）
3. 動かせない条件は何か（constraints / deadline）
4. 影響するコンポーネントはどこか
5. 失敗したらどう戻すか（rollback 条件）

### 更新トリガ

- 更新するのは**依頼者の意図が変わったとき**（scope 拡大・goal 変更・制約追加）。
- 実装詳細の変化・進捗では更新しない（それは handover の仕事）。
- 更新も新規作成と同じく **人間の確認を経てから**書き込む。

## 3. handover.md の仕様

### 必須ヘッダ

| field | 規則 |
|---|---|
| `Last updated` | ISO 8601 ＋時刻＋タイムゾーン（例: `2026-07-02 18:30 (JST)`） |
| `Updated by` | 人間の実名（確実な場合のみ）または AI セッション ID。捏造禁止 |

### 必須セクション

- `## Current State` — 完了していることを1段落で。**検証済みの事実のみ**
  （テストが通った・merge された等。「たぶん動く」は書かない）。
- `## In Progress` — 進行中の作業。branch 名・PR リンク・issue ID を含める。
- `## Next Actions` — 番号付きの**具体的な**次手。次の担い手がそのまま着手できる
  粒度（呼ぶべき skill・コマンドがあれば明記）。
- `## Known Risks / Blockers` — リスクと緩和策。**「誰かの返事待ち」等の外部待ちも
  必ずここに書く**（暗黙の待ちが一番危ない）。
- `## Context the Next Actor Needs` — 非自明な罠・環境の癖・外部依存。
- `## Relevant Files and Commands` — `パス — なぜ重要か` / `コマンド — 何をするか`。

### 分量と文体

- **2分で読み切れる**こと。長くなったら詳細を他 artifact に逃がして参照に置換。
- 人間とエージェントの両方が読者。code reference（`path:line`）を活用する。
- intent の再掲禁止 — `docs/intent.md 参照` と書く。

### 更新トリガ

- 意味のある作業セッションの終わり（セッション単位。commit 単位ではない）。
- 中断・引き継ぎ・長期離脱の前。

## 4. 保存・履歴の規約

1. **既定は repo に commit**（コードと一緒に流れる）。ただしリポジトリによっては
   gitignore 運用（ローカル専用）の場合がある — **初回に `.gitignore` を確認**し、
   方針が読み取れなければユーザーに聞く。
2. 旧版は**ファイル内に残さない**。commit 運用なら git history が履歴。
3. gitignore 運用のリポジトリでは、work unit が切り替わって handover を書き直す
   ときに旧版を `docs/handover-YYYY-MM-DD-<slug>.md` へ退避してよい（同 glob が
   ignore されていることを確認）。intent も同様（`docs/intent-YYYY-MM-DD-<slug>.md`）。
4. 秘匿情報（API キー・トークン・PII）は commit 運用・ローカル運用を問わず
   書き込み前に redact する。

## 5. 整合検査の5分類（検出は必須・裁定は人間）

作る・更新する・引き継ぐ前に、intent ⇄ handover ⇄ リポジトリ実状態を照合する。
**検出したら止めて報告し、人間の裁定を得てから続行する。**

| 分類 | 定義 | 検出例 |
|---|---|---|
| **意図乖離 (intent drift)** | 実作業（または handover の記述）が intent の scope / non-goals / constraints と両立しない | intent が「リファクタのみ・挙動変更なし」なのに handover の Current State に新機能追加がある |
| **重複 (duplication)** | handover が intent・PR・ADR・issue に既にある内容を再掲している | Goal の全文コピー／PR 説明と同じ変更一覧 |
| **幽霊参照 (stale reference)** | 記載の branch / PR / ファイル / コマンドが実在しない・既に消えている | merge 済みで削除された branch が In Progress に残る／改名されたファイルパス |
| **鮮度切れ (staleness)** | Current State がリポジトリの実状態と食い違う | 「テスト赤」と書いてあるが現在は緑／handover 更新後に main が大きく進んだ |
| **実行不能 (unactionable)** | Next Actions が抽象的で、次の担い手がそのまま着手できない | 「続きをやる」「いい感じに仕上げる」だけの項目 |

### 検査手順

1. `docs/intent.md` / `docs/handover.md` の両方を読む（片方しか無ければその旨込みで）。
2. 記載の branch / PR / ファイルの実在を確認する（`git branch` / `gh pr view` /
   ファイル存在チェック）。
3. Current State の主張（テスト結果・merge 状態）を可能な範囲で実測と突き合わせる。
4. handover の各記述を intent の scope / non-goals と照合する（意図乖離の検出）。
5. 検出ゼロならその旨を採点報告に含めて先へ進む。**検出があれば下の形式で報告し、
   人間の裁定まで書込み（または再開）を保留する。**

### 報告形式

```
⚠️ intent/handover 整合検査: {n} 件検出

1. [{分類}] {該当箇所の要約}
   - 記載: {ファイルの記述の引用}
   - 実状態: {観測した事実}
   - 解消の選択肢:
     a) {例: intent の scope を人間が更新する（意図の方が変わった場合）}
     b) {例: 作業を intent の範囲内に戻す}
     c) {例: handover の記述を実測に合わせて修正する}
```

**意図乖離の解消を AI が選んではならない**（絶対ルール7）。特に「intent を実作業に
合わせて書き換える」は人間の明示承認がある場合のみ。

## 6. 再開時チェックリスト（ワークフロー C）

- [ ] `docs/intent.md` を読んだ（無ければ「無い」と報告した）
- [ ] `docs/handover.md` を読んだ（同上）
- [ ] `Last updated` を確認し、それ以降の main / branch の動きを `git log` で把握した
- [ ] In Progress の branch / PR が実在することを確認した
- [ ] Next Actions の1番が今も有効であることを確認した
- [ ] Open Questions（intent）に未解決の blocking がないか確認した
- [ ] 乖離・疑問があれば作業前に人間へ報告した
