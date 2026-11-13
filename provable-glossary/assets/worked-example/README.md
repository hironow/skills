# spec-ddd: 証明可能な用語集

> この実例は読むための見本である。これだけでは検査を実行できない。検査の仕組み (`Main.lean`、`justfile` など) は [../template/](../template/) にある。新しい題材は `python3 ../../scripts/init_project.py <置き場所>` で始める。下の「使い方」と「スキル」は、この実例を作った元のリポジトリでの手順である。

DDD の用語集 (Ubiquitous Language) を、機械で検査できる仕様の起点にする実験である。
題材は、EC の注文と、映画館のチケット販売 (通常メンテナンス・緊急メンテナンスとの競合) である。

用語集の正本は `Glossary/*.lean` にある。各用語は定義と参照を持ち、各主張は証拠を 1 つ持つ。
判定は 3 つある。

- **証明済み**: Lean の証明、または Quint + TLC による全状態の検査
- **反例あり**: Lean による否定の証明、または Quint が見つけた反例
- **未決定**: 業務側が決める問い

用語と主張の件数は [docs/generated/summary.md](docs/generated/summary.md) にある (用語集から生成する)。

## 役割の対応表

どの題材にも共通する役割に、この題材を当てはめたもの。
機械が確かめる版は、各用語に付けた役割から生成した [docs/generated/roles.md](docs/generated/roles.md) にある。
停止の場面の宣言 (`stopScene`) も同じ文書に載り、`just check` (stop-check) が確かめる。

| 役割 | 意味 | この題材での姿 |
|---|---|---|
| 資源 | 数に限りがあり、同じものを 2 人に渡せない | 座席 |
| 仮確保 | 期限つきで資源を押さえること | 座席の仮確保 |
| 外部の確認 | システムの外で起き、止められず、遅れて届く結果 | 決済サービスの成功・失敗 |
| 権利の発行 | 顧客に渡す、取り消しにくいもの | 入場権 (チケット) |
| 緊急停止 | システムが自律的に入る、受付の遮断 | 緊急メンテナンス |
| 計画停止 | 予告して、処理中のものを待ってから入る停止 | 通常メンテナンス |
| 期限 | 過ぎると価値がなくなる、動かせない時刻 | 上映開始 |
| 代わりの経路 | 停止中でも動く、人や現場の手段 | 劇場の窓口 |
| 供給の取り消し | 事業者の都合で、渡した権利を果たせなくなること | 上映中止 |
| 振替 | 果たせなくなった権利を、別の資源で果たすこと | 別の上映回への振替 (業界には存在しなかった) |

出発点は A (用語集も実装もない状態から) で、3 つの段階 (必須・期待・任意) をすべて行った。

## 分かったこと

1. **用語集を形式的に書くと、循環・空の概念・仕様の空白・設計の競合を機械で確かめられる。**
   議論が設計案として挙げた実験は、すべて実際に実行できた。
2. **しかし、同じことの大半は、道具を使わない現在のモデルが読むだけでできた。**
   空白の発見、設計が性質を満たすかの判定、成立条件の導出、決め忘れの防止を比べた。
   どれでも、形式手法は読解に対する上積みを示せなかった (数百状態までの小さな設計で測った)。
3. **形式手法に残った価値は保証である。** 対照の答えは当たっていたが、当たっていると言えたのは、
   全状態を検査した正解表があったからである。
4. **形式手法が出す質問は、モデルに書いたものの内側にしか生まれない。**
   出した質問 14 件を業界の現状と突き合わせると、5 件は業界が答え済みで、4 件は映画館では問う場面がなかった。
   いちばん大きな事業の空白 (日本の映画館は購入後に取り消せない) には、1 件も触れていなかった。
5. **業界に答えがなかったのは、販売が止まったときの扱いである。** 規則の案を書き、検査した。

## 読む順番

| 文書 | 中身 |
|---|---|
| [docs/findings.md](docs/findings.md) | 実験の結果と限界。まずここを読む |
| (この実例には含めていない) | 業界の現状との突き合わせと、停止時の規則の案。実在の事業者と事故に触れるため、公開の場には置かない |
| [docs/generated/glossary.md](docs/generated/glossary.md) | 用語と主張の一覧 (生成物) |
| [docs/generated/questions.md](docs/generated/questions.md) | 未決定の質問の一覧 (生成物) |
| [docs/generated/summary.md](docs/generated/summary.md) | 件数の集計 (生成物) |

## 使い方

```sh
just check      # Lean の証明、Quint の検査、文書の鮮度をすべて調べる
just generate   # 生成物 (docs/generated/) を用語集から作り直す
```

必要なもの: elan、bun、Java、just、ripgrep。
Lean の版は `lean-toolchain`、Quint の版は `quint-version` で固定する。どちらも最新の安定版を使う。
Quint は bunx がその版を取得して実行するので、導入は要らない (導入済みのものを使うなら `QUINT=quint` を指定する)。
証明は素の Lean で書いてあり、mathlib などの外部のパッケージは使わない。取得するものはない。
証明の書き方に迷ったときは、mathlib の実装をネットで読み、必要な補題だけを素の Lean で書き直す
([スキルの説明](../../references/lean-and-quint.md))。

`just check` は次の 9 つを行う。

- **lean-check**: 証明をビルドし、`sorry`・`axiom`・`native_decide` を拒否する。警告も失敗にする。警告には Lean 本体の追加の静的検査 (`linter.extra`、`lakefile.toml` で有効にした) を含む。
- **stop-check**: 各用語集の停止の場面の宣言 (`stopScene`) を、用語の役割と主張で確かめる。語の有無では判定しない。
- **question-check**: 未決定の主張 (業務側への質問) が、空白を示す反例か、モデルで示せない理由のどちらかを持つことを確かめる。
- **control-check**: 対照実験の宣言 (`Glossary/Registry.lean` の `control`) を確かめる。行ったと宣言したなら、手順書が結果より先にコミットされた実験があることを git の履歴で確かめる。
- **spec-check**: 用語集が持つ主張の一覧を出力させ、その 1 件ずつを Quint で実行する。
  「証明済み」は TLC の全状態検査、「反例あり」はシミュレータで確かめる。
- **generated-check**: 生成物を作り直して比べる。手で変えた版、足したファイル、消したファイルを拒否する。
- **anchor-check**: 用語に付けた実装との対応 (ファイルと、そこにあるべき文字列) が切れていないことを確かめる。
- **migration-check**: 既存の用語集から移行している場合に、旧用語がすべて対応づけ済みか廃止になっていることを確かめる。
- **skill-check**: スキルに同梱した写しが、このリポジトリの元のファイルと一致することを確かめる。

## 書くものと、生成されるもの

| 種類 | 置き場所 | 誰が書くか |
|---|---|---|
| 用語集と証明 | `Glossary/*.lean` | AI が書く |
| モデル | `Spec/*.qnt`, `Spec/tests.txt` | AI が書く |
| 分析の文書 | `README.md`, `docs/*.md` | AI が書く |
| 実験の記録 | `experiments/<名前>/` | AI が書く。対照の答えは実行の記録で、書き換えない |
| 生成物 | `docs/generated/*.md` | `just generate` だけが書く |

生成物は「用語集がいま何を主張しているか」の写しである。手で直すと、文書と検査された中身が食い違う。
内容を変えるには、`Glossary/*.lean` を直して `just generate` を実行する。次の 3 つがこれを守る。

1. **`just check` (generated-check)**: 保証の本体。食い違いがあれば検査が落ちる。
2. **Claude Code のフック** (`.claude/hooks/protect_generated.py`): `docs/generated/` への編集を、実行の前に止める。
3. **git の pre-commit** (`.githooks/pre-commit`): `just install-hooks` で有効にする。食い違ったままのコミットを止める。

## スキル

この成果物を、別の題材や別の業界で作るためのスキルが [skills/provable-glossary](../../SKILL.md) にある。

- どの題材でも同じ土台 (`Glossary/` の `Core.lean`, `Claim.lean`, `Render.lean`, `Progress.lean` と規則の `StopScene.lean`, `Questions.lean`, `Control.lean`、`Main.lean`, `justfile`, フック類) を
  テンプレートとして持つ。このリポジトリのファイルの写しである。
- このリポジトリの用語集、モデル、文書、実験の記録を、実例として同梱する。
- 写しは `just skill-sync` で更新し、`just check` (skill-check) が一致を確かめる。
- 新しいプロジェクトは `python3 skills/provable-glossary/scripts/init_project.py <置き場所>` で始める。
- 出発点は 3 つある。まっさら (A)、実装はあるが用語集がない (B)、人が管理する用語集を移行する (C)。
  `scripts/detect_start.py` が判定し、`scripts/status.py` が次にすることを表示する。
- B と C では、用語を実装の場所に結ぶ (`anchors`)。実装の名前が変わると `just check` が落ちる。
- C では、旧用語集の用語がすべて「対応づけ済み」か「廃止」になるまで `just check` が落ちる。

## 置き場所

### 用語集と証明 (Lean)

| パス | 中身 |
|---|---|
| `Glossary/Core.lean` | 用語集の型、検査関数 `check`、健全性 (`check_sound`) と追加の保存 (`check_add`) の定理 |
| `Glossary/Claim.lean` | 主張と証拠の型 |
| `Glossary/Render.lean` | 検査の一覧と生成物を作る。生成物の言語を切り替えられる |
| `Glossary/Registry.lean` | 対象にする用語集の登録 |
| `Glossary/OrderBook.lean` | 用語集 A: 注文 |
| `Glossary/Cinema.lean` | 用語集 B: 映画館のチケット販売 |
| `Glossary/Broken.lean` | 循環する草稿と、修正した用語集 |
| `Glossary/EmptyConcept.lean` | 空の概念 (確定注文) |
| `Glossary/PaidStages.lean` | 「支払い済み」は 1 つの概念ではない |
| `Glossary/Fairness.lean` | 振替の不可能性と存在 |
| `Glossary/Progress.lean` | 進行可能性の一般定理 |
| `Glossary/Deadline.lean` | 遮断と履行期限の衝突 |
| `Glossary/Autonomy.lean` | 方針だけで決まる判断と、決まらない判断 |
| `Main.lean` | 検査の一覧を出力し、生成物を書き出す |
| `Audit.lean` | 証明が使う公理を出力する |

### 状態遷移モデル (Quint)

| パス | 中身 |
|---|---|
| `Spec/order_coverage.qnt` | 注文の仕様の空白 |
| `Spec/payment_stages.qnt` | 与信と売上確定。発送と確定の順序 |
| `Spec/emergency_sale.qnt` | 決済成功と緊急メンテナンスの競合 (設計 3 段階) |
| `Spec/rebooking.qnt` | 上映中止の振替。先着順と、回復可能性を守る方針 |
| `Spec/obligation.qnt` | 履行義務、責任、権限、引き継ぎ |
| `Spec/deadline.qnt` | 上映開始という期限と、窓口発券 |
| `Spec/autonomy.qnt` | システムが自分で決めてよい範囲と、人に委ねる範囲 |
| `Spec/outage_policy.qnt` | 販売が止まったときの規則の案 |

### 実験の記録

どの実験も、手順と予想を先にコミットしてから実行した。各ディレクトリの `protocol.md` が手順、
`result.md` が結果である。

| パス | 問い | 結果 |
|---|---|---|
| `experiments/control-001` | 形式手法なしで、同じ空白は見つかるか | 対照は 24 件中 88〜94% を見つけた |
| `experiments/verify-002` | 設計が性質を満たすかを、道具なしで判定できるか | 対照は 3 つとも 19 問を全問正解 |
| `experiments/scale-003` | 時間と数値を入れると、対照は誤り始めるか | 対照は 3 つとも 24 問を全問正解 |
| `experiments/formal-004` | 自然言語で渡すと、対照の正確さは変わるか | 変わらなかった |
| `experiments/forward-005` | 形式的に書かせると、決め忘れは減るか | 差は示せなかった (11.0 対 11.7) |
| `experiments/derive-006` | 対照は成立条件を自力で導けるか | 12 回中 12 回、正解表と一致した |
| `experiments/guarantee-007` | 座席の保証の条件は、元の格子の外でも成り立つか | 1344 通りすべてで一致した |

対照とは、道具を使わない Claude のモデル (Fable 5.2、Opus 5.5、Sonnet 5.5) のことである。

### そのほか

| パス | 中身 |
|---|---|
| `justfile` | 検査の入口。これ 1 つだけ |

## 限界

- モデルは小さい。座席 1 つ・顧客 2〜3 人、または顧客 4 人・席 3 つである。状態数は数百までしか調べていない。
- 対照との比較は、同じ系列のモデルが書いた仕様を、同じ系列のモデルが読んでいる。人との比較はしていない。
- 業界の調査は Web の公開資料による。一次資料と二次情報が混ざっており、顧客への聞き取りはしていない。
- 停止時の規則の案は、業務を知る人にも法務にも見せていない。
- 実装はない。モデルと実装の一致は対象外である。

詳しい限界は [docs/findings.md](docs/findings.md) の末尾にある。
