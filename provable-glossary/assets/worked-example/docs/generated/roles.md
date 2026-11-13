<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 役割と停止の場面

共通の役割を、各用語に付けた役割から一覧にする。停止の場面について各用語集が宣言したことも載せる。宣言は `just check` (stop-check) が確かめる。

## 注文

<!-- stop-scene: ok; in book 映画館のチケット販売 -->
<!-- roles-tagged: 2 -->

停止の場面: 次の用語集で検査モデルにした: 映画館のチケット販売

| 役割 | 用語 |
|---|---|
| 資源 (Resource) | なし |
| 仮確保 (Hold) | なし |
| 外部の確認 (External confirmation) | 支払い |
| 権利 (Entitlement) | 発送 |
| 停止 (Stop) | なし |
| 計画停止 (Planned stop) | なし |
| 期限 (Deadline) | なし |
| 代わりの経路 (Fallback channel) | なし |
| 供給の取り消し (Supply cancellation) | なし |
| 振替 (Reallocation) | なし |

## 映画館のチケット販売

<!-- stop-scene: ok; modelled -->
<!-- roles-tagged: 10 -->

停止の場面: 検査モデルにした。支える主張を下に載せる。

| 役割 | 用語 |
|---|---|
| 資源 (Resource) | 座席 |
| 仮確保 (Hold) | 仮確保 |
| 外部の確認 (External confirmation) | 決済 |
| 権利 (Entitlement) | 入場権 |
| 停止 (Stop) | 緊急メンテナンス |
| 計画停止 (Planned stop) | 通常メンテナンス |
| 期限 (Deadline) | 履行期限 |
| 代わりの経路 (Fallback channel) | 窓口発券 |
| 供給の取り消し (Supply cancellation) | 上映中止 |
| 振替 (Reallocation) | 振替 |

### 停止についての主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 反例あり | 素朴な設計 (発券は支払い済みかどうかだけを見る) で、同じ座席の入場権は高々 1 つ | 入場権, 座席, 緊急メンテナンス | Quint 反例: `Spec/emergency_sale.qnt` `v0_naive.seatExclusive` |
| 未決定 | 緊急メンテナンスが上映開始まで続いたとき、発券保留取引をどう解決するか (時間はモデルの外) | 決済済み・発券保留取引, 上映回, 緊急メンテナンス | 業務側への質問 |
| 反例あり | 引き継ぎを入れた設計で、解決の操作が公平に実行されるなら、履行義務はいつか必ず解決する | 履行義務, 引き継ぎ, 緊急メンテナンス | Quint + TLC 反例: `Spec/obligation.qnt` `ob3_handoff.Liveness` |
| 証明済み | 同じ設計で、さらに復旧がいつか必ず来るなら、履行義務はいつか必ず解決する | 履行義務, 引き継ぎ, 緊急メンテナンス | Quint + TLC 全状態: `Spec/obligation.qnt` `ob3_handoff.LivenessGivenRecovery` |
| 未決定 | 緊急メンテナンスが終わらないとき、空席があっても販売は履行義務を決済に引き継げるか | 引き継ぎ, 緊急メンテナンス, 振替 | 業務側への質問。空白を示す反例: `Spec/obligation.qnt` `ob3_handoff.Liveness` |
| 反例あり | オンライン発券だけの設計で、履行期限を過ぎて観られなかった顧客はいない | 履行期限, 目的の喪失, 緊急メンテナンス | Quint 反例: `Spec/deadline.qnt` `online_only.goalNotLostToTime` |
| 証明済み | 「遮断中は発券しない」「履行期限までに発券する」「遮断が履行期限まで続く」は同時に成り立たない | 遮断完了, 履行期限, 緊急メンテナンス | Lean: `Glossary.Deadline.rules_conflict` |
| 未決定 | 緊急メンテナンス中の窓口発券を認めるか。認めなければ顧客の目的を守れず、認めれば遮断中に発券が起きる | 窓口発券, 緊急メンテナンス, 目的の喪失 | 業務側への質問。空白を示す反例: `Spec/deadline.qnt` `online_only.goalNotLostToTime`, `Spec/deadline.qnt` `box_office.noTicketWhileBlocked` |
| 証明済み | 停止時の規則の案では、流出した情報だけで入場する人はなく、決済済みで開始時刻に来た購入者は断られず、入場も返金もされない取引は残らない | 入場権, 決済済み・発券保留取引, 窓口発券, 返金, 緊急メンテナンス | Quint + TLC 全状態: `Spec/outage_policy.qnt` `draft.Safety` |

