---
name: intent-handover-governance
description: docs/intent.md（なぜ今やるか＝人間の意図）と docs/handover.md（どこまで進み・次に何をするか）の2ファイルで開発の継続性を統治する。intent は人間が確定させ AI は推測で書かない。handover は毎セッション末に更新し2分で読める形を保つ。更新前に intent ⇄ handover ⇄ リポジトリ実状態の整合検査を必ず行い、乖離の裁定は人間に委ねる。Use when the user mentions intent.md, handover.md, 引き継ぎ, ハンドオーバー, 意図の記録・確認, セッション終了・作業再開, work unit の開始/切替, 「なぜ今やるか」「どこまで進んだか」の記録, or wants session continuity captured in docs.
---

# Intent / Handover Governance（intent × handover × ルーブリック × 整合検査）

**中心は2ファイルを「作る・更新する・引き継ぐ」こと**。2ファイルは独立していて
合体しない — 当てはまる方だけを使う。

| ファイル | 答える問い | 所有者 | 更新タイミング |
|---|---|---|---|
| `docs/intent.md` | **なぜ今**この作業をするのか | **人間**（AI は書記係） | work unit の開始時・意図が変わったとき |
| `docs/handover.md` | **どこまで**進み、**次に何**をするか | セッション（AI/人間どちらも） | 毎セッション末・大きな区切り |

- **作る** = work unit 開始時に intent を確定させる／初回の handover を書く
- **更新する** = 意図が変わったら intent を、セッション末に handover を更新
- **引き継ぐ** = セッション開始時に両ファイルを読み、実状態と突き合わせて再開

## 絶対ルール（違反したら作業を止めてユーザーに確認）

1. **intent は人間の意図の写し・推測禁止**: goal / success criteria / scope /
   non-goals / constraints / deadline / rollback 条件のどれかが曖昧なら、
   **止めて人間に聞く**。人間の確認なしに `docs/intent.md` を新規作成・更新しない。
   隙間を仮定で埋めない（[REFERENCE.md](REFERENCE.md) §2 の確認質問リスト）。
2. **handover は draft → 提示 → 確認 → 書込み**: いきなり上書きしない。既存
   handover がある場合は「何が変わるか」を要約してから上書きする。
3. **重複禁止・参照主義**: handover に intent の再掲禁止（パス参照する）。
   PR / ADR / issue / commit / plan に既にある内容はリンクや ID で参照し、
   本文へコピーしない。
4. **日付は絶対表記**（ISO 8601）。「昨日」「来週」等の相対日付は書いた瞬間から
   腐るので禁止。
5. **履歴はファイル内に持たない**: 旧版は git history が持つ。リポジトリが
   これらを gitignore 運用している場合のみ dated backup
   （`docs/handover-YYYY-MM-DD-<slug>.md`）で退避する。commit するか gitignore かは
   リポジトリの方針に従い、初回に確認する（[REFERENCE.md](REFERENCE.md) §4）。
6. **ルーブリックゲート**: 書込み前に [RUBRIC.md](RUBRIC.md) で採点。intent ゲートは
   0 点観点ゼロ＋人間確認済みが条件、handover ゲートは★観点（H1/H3/H5）すべて 2 が
   条件。採点結果はユーザーに報告。
7. **整合検査必須・裁定は人間**: 作る・更新する・引き継ぐ前に必ず
   intent ⇄ handover ⇄ リポジトリ実状態を照合し、**意図乖離・重複・幽霊参照・
   鮮度切れ・実行不能**（[REFERENCE.md](REFERENCE.md) §5 の5分類）を検査する。
   **意図乖離を検出したら AI が intent を直して整合させるのは禁止** — 実作業を
   意図に合わせるか、意図の方が変わったのかは人間が決める。
8. **秘匿情報は redact・名前は捏造しない**: API キー・パスワード・PII は書込み前に
   除去。`Requester` / `Updated by` は確実に分かる場合のみ実名、不明なら
   セッション ID を使う。

## ワークフロー

### A. intent を作る / 更新する（work unit 開始・意図の変化時）
1. 既存 `docs/intent.md` の有無を確認。あれば読み、今回の作業が現 intent の
   範囲内かを判定（範囲内なら更新不要 — そのまま作業へ）。
2. 曖昧点を人間に質問して確定させる（絶対ルール1。質問リストは
   [REFERENCE.md](REFERENCE.md) §2）。
3. [templates/intent.md](templates/intent.md) で draft を作成し、
   [RUBRIC.md](RUBRIC.md) の **intent ゲート**で採点（0 があれば直す）。
4. draft を人間に提示し、**承認を得てから**書き込む。
5. 実装詳細の変化では更新しない — 更新するのは「依頼者の意図」が変わったときだけ。

### B. handover を更新する（セッション末・大きな区切り）
1. セッションの成果・進行中・次手を会話とリポジトリ実状態（branch / PR / テスト
   結果）から集める。
2. **整合検査**（絶対ルール7・[REFERENCE.md](REFERENCE.md) §5）。intent との乖離を
   検出したら停止して人間に確認。
3. [templates/handover.md](templates/handover.md) で draft を作成。intent と重複する
   記述は参照に置換（絶対ルール3）。
4. [RUBRIC.md](RUBRIC.md) の **handover ゲート**で採点（★ = H1/H3/H5 が 2 未満なら
   直す）。
5. draft を提示し、確認を得てから書き込む（絶対ルール2）。

### C. 引き継いで再開する（セッション開始）
1. `docs/intent.md` と `docs/handover.md` を読む（無ければ無いと報告し、必要なら
   A から始める）。
2. **鮮度と実在の確認**: handover の branch / PR / ファイル / コマンドが現存するか、
   `Last updated` からリポジトリに大きな変化がないかを検証
   （[REFERENCE.md](REFERENCE.md) §6 のチェックリスト）。
3. 乖離があれば人間に報告してから作業に入る。なければ `Next Actions` の先頭から
   再開する。

### D. 棚卸し（stale 検出）
1. `Last updated` が古い・完了済みの項目が `In Progress` に残置・`Open Questions`
   が未解決のまま放置 — を検出して報告。
2. intent が現状と噛み合っていない疑いは人間に確認（AI が書き換えない）。

## このスキルが守備範囲にしないもの

- 決定の記録（why we decided X）→ ADR/PDR（`decision-record-governance` skill）。
  intent の「なぜ今」とは別物 — 決定が発生したら ADR/PDR に書き、intent /
  handover からは ID で参照する。
- 現状仕様の記述 → `docs/*.md`（docs-discipline に従う）。
- 一時的な agent 間 handoff（temp-dir 行き・リポジトリに残さないもの）。
