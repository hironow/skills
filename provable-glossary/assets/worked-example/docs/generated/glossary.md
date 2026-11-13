<!-- 生成物。`just generate` が `Glossary/*.lean` から作る。手で編集しない。 -->

# 用語と主張

## 注文

### 用語

| 用語 | ID | 文脈 | 定義 | 定義依存 | 関連 |
|---|---|---|---|---|---|
| 顧客 | `customer` | sales | 商品を買う主体 |  | 注文 |
| 取引 | `transaction` | sales | 対価と引き換えに権利を渡す商業上の活動 |  |  |
| 注文 | `order` | sales | 顧客が商品を購入するために作成する取引 | 顧客, 取引 | 顧客 |
| 支払い | `payment` | sales | 顧客が注文の代金を払うこと | 顧客, 注文 |  |
| 与信 | `authorization` | sales | カード会社が注文の代金の枠を押さえること。期限があり、お金はまだ動かない | 支払い |  |
| 売上確定 | `capture` | sales | 与信した代金の請求を事業者が確定すること | 与信 |  |
| 発送 | `shipment` | sales | 注文の商品を顧客に送り出すこと | 顧客, 注文 |  |
| キャンセル | `cancellation` | sales | 注文を取りやめること | 注文 |  |
| 確定注文 | `confirmedOrder` | sales | 支払いが完了しており、かつ支払いが未完了の注文 (議論の例のまま) | 注文, 支払い |  |

### 主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 反例あり | 草稿の用語集 (注文と取引が互いを定義に使う) は定義依存が非循環である | 注文, 取引 | Lean (否定を証明): `Glossary.Broken.draft_is_cyclic` |
| 証明済み | 修正した用語集は、ID が一意で、参照先が存在し、定義依存が非循環である | 注文, 顧客, 取引 | Lean: `Glossary.Broken.repaired_wellFormed` |
| 証明済み | 確定注文は空である: どんな注文の型と支払いの意味でも、定義を満たす注文は存在しない | 確定注文 | Lean: `Glossary.EmptyConcept.confirmedOrder_empty` |
| 証明済み | 到達できるどの状態でも、発送かキャンセルができるか、終端である (議論が挙げた網羅性) | 注文, 発送, キャンセル | Quint + TLC 全状態: `Spec/order_coverage.qnt` `order_coverage.discussionCoverage` |
| 反例あり | 到達できるどの状態でも、すべての操作について許可か禁止かが決まっている | 注文, 支払い, 発送, キャンセル | Quint 反例: `Spec/order_coverage.qnt` `order_coverage.everyOpDecided` |
| 未決定 | 支払い済みで発送前の注文はキャンセルできるか | 注文, 支払い, キャンセル | 業務側への質問。空白を示す反例: `Spec/order_coverage.qnt` `order_coverage.paidCancelDecided` |
| 証明済み | 「支払い済み」を 1 つの述語にすると、与信の意味と売上確定の意味の両方には合わせられない | 支払い, 与信, 売上確定 | Lean: `Glossary.PaidStages.paid_is_not_one_notion` |
| 証明済み | 与信で発送し、発送と同時に売上を確定するなら、発送した注文の代金は回収できる | 注文, 与信, 売上確定, 発送 | Quint + TLC 全状態: `Spec/payment_stages.qnt` `capture_at_ship.shippedIsCollectible` |
| 反例あり | 与信で発送し、売上の確定を後に回しても、発送した注文の代金は回収できる | 注文, 与信, 売上確定, 発送 | Quint 反例: `Spec/payment_stages.qnt` `capture_after_ship.shippedIsCollectible` |
| 未決定 | 支払い済みの注文をもう一度支払えるか | 注文, 支払い | 業務側への質問。空白を示す反例: `Spec/order_coverage.qnt` `order_coverage.paidPayDecided` |

## 映画館のチケット販売

### 用語

| 用語 | ID | 文脈 | 定義 | 定義依存 | 関連 |
|---|---|---|---|---|---|
| 顧客 | `customer` | sales | チケットを買う、または買った主体 |  | 仮確保, 決済, 入場権 |
| 上映回 | `screening` | sales | ある作品を、ある日時に、あるスクリーンで上映する 1 回 |  |  |
| 座席 | `seat` | sales | 上映回の中で 1 人が座る場所 | 上映回 |  |
| 仮確保 | `seatHold` | sales | 顧客が決済を終えるまで、座席を他の顧客に売らないでおく取り置き | 顧客, 座席 |  |
| 決済 | `payment` | payment | 顧客が外部の決済サービスを通じて代金を支払うこと。結果は成功・失敗・不明のどれか | 顧客 |  |
| 返金 | `refund` | payment | 成功した決済の代金を顧客に戻すこと | 決済 |  |
| 入場権 | `admission` | ticketing | 顧客が、ある上映回のある座席で鑑賞できる権利 (チケット) | 顧客, 座席 |  |
| 販売経路 | `salesChannel` | operations | 仮確保・決済開始・発券を受け付ける入口 |  |  |
| 通常メンテナンス | `plannedMaintenance` | operations | 新しい仮確保を止め、処理中の取引が片付いてから販売経路を止める作業 | 販売経路 |  |
| 脆弱性 | `vulnerability` | operations | 悪用されると取引や入場権の信頼性を損なう欠陥 |  |  |
| 緊急メンテナンス | `emergencyMaintenance` | operations | 脆弱性を検知して、処理中の取引を待たずに自動で販売経路を止めること | 脆弱性, 販売経路 |  |
| 停止指令 | `cutoffOrder` | operations | 緊急メンテナンスで販売経路を止めると決めた時点。経路はまだ動いている | 緊急メンテナンス |  |
| 遮断完了 | `cutoffApplied` | operations | すべての販売経路が実際に止まった時点 | 停止指令 |  |
| 販売成立 | `saleEstablished` | sales | 未決定: 決済が成功した時点か、入場権を発行した時点か | 決済, 入場権 |  |
| 決済済み・発券保留取引 | `paidPendingIssuance` | sales | 決済は成功したが入場権がまだない取引。仮確保を保ったまま、発券か返金で解決する | 決済, 入場権, 仮確保, 返金 |  |
| 振替 | `rebooking` | sales | 中止になった上映回の入場権を、別の上映回の入場権に替えること | 入場権, 上映回 |  |
| 保護対象 | `protectedCustomer` | sales | 映画館側の事情で上映回が中止になった既存購入者 | 顧客, 入場権, 上映回 |  |
| 回復可能性 | `recoverability` | sales | いまの割当てを延長して、保護対象の全員を振り替えられること | 振替, 保護対象 |  |
| 回復可能性の喪失 | `recoverabilityLoss` | sales | 有効な確定によって回復可能性が失われること | 回復可能性 |  |
| 公平性 | `fairness` | sales | 未決定: 顧客の希望が衝突したとき、誰を優先するかの方針 | 顧客 |  |
| 上映中止 | `screeningCancellation` | operations | 設備故障など映画館側の事情で、上映回を取りやめること | 上映回 |  |
| 履行義務 | `obligation` | sales | 入場権を発行した顧客に対して、鑑賞させるか、振替か返金で埋め合わせる義務 | 入場権, 顧客, 振替, 返金 |  |
| 解決責任者 | `resolutionOwner` | operations | 未解決の履行義務を、解決するまで引き受ける文脈 | 履行義務 |  |
| 権限 | `authority` | operations | ある解決の操作を実行してよいという許可。返金の権限は決済の文脈だけが持つ | 履行義務, 返金 |  |
| 引き継ぎ | `handoff` | operations | 解決責任者が、権限を持つ別の文脈に履行義務を渡すこと | 解決責任者, 権限 |  |
| 進行可能性 | `progressability` | operations | 未解決の履行義務に、責任者が実行できる解決の道が残っていること | 履行義務, 解決責任者, 権限 |  |
| 履行期限 | `fulfillmentDeadline` | sales | それを過ぎると顧客の目的が果たせなくなる時刻。上映開始 | 履行義務, 上映回 |  |
| 目的の喪失 | `goalLoss` | sales | 履行期限を過ぎて、顧客が観られなかったこと。返金で解決しても残る | 履行期限 |  |
| 窓口発券 | `boxOfficeIssue` | ticketing | 販売経路を通さずに入場権を発行すること | 入場権, 販売経路 |  |
| 方針で決まる判断 | `determinedDecision` | sales | 採用した方針のもとで、最善の割当てがどれも同じ顧客に席を渡す判断。システムが自分で実行できる | 公平性, 回復可能性 |  |
| 人への委譲 | `escalation` | operations | 方針で決まらない判断を、権限を持つ人に渡すこと | 方針で決まる判断, 権限 |  |

### 主張

| 判定 | 主張 | 用語 | 証拠 |
|---|---|---|---|
| 反例あり | 素朴な設計 (発券は支払い済みかどうかだけを見る) で、同じ座席の入場権は高々 1 つ | 入場権, 座席, 緊急メンテナンス | Quint 反例: `Spec/emergency_sale.qnt` `v0_naive.seatExclusive` |
| 反例あり | 発券時に仮確保を確かめる設計で、支払い済み・未発券の取引は座席を保ったまま追跡されている | 決済, 入場権, 仮確保 | Quint 反例: `Spec/emergency_sale.qnt` `v1_guarded.paidIsTracked` |
| 証明済み | 決済済み・発券保留取引を入れた設計で、座席の排他性・決済後の取引保全・遮断完了後に発券なし・通常メンテナンス中に未解決の決済なし、がすべて成り立つ | 決済済み・発券保留取引, 入場権, 座席, 通常メンテナンス, 遮断完了 | Quint + TLC 全状態: `Spec/emergency_sale.qnt` `v2_pending_issuance.Safety` |
| 未決定 | 販売成立は決済成功の時点か、発券の時点か。決済成功とするなら、遮断完了後にも販売が成立する | 販売成立, 遮断完了, 決済 | 業務側への質問。空白を示す反例: `Spec/emergency_sale.qnt` `v2_pending_issuance.noPaymentWhileBlocked` |
| 未決定 | 遮断中に返金してよいか (モデルは許している) | 返金, 遮断完了, 決済済み・発券保留取引 | 業務側への質問。モデルで示せない理由: 決済の競合のモデル (Spec/emergency_sale.qnt) は遮断中の返金を許している。許すか禁じるかで性質は破れないので、どちらが正しいかを示す反例はない |
| 未決定 | 緊急メンテナンスが上映開始まで続いたとき、発券保留取引をどう解決するか (時間はモデルの外) | 決済済み・発券保留取引, 上映回, 緊急メンテナンス | 業務側への質問。モデルで示せない理由: 決済の競合のモデルは時刻を持たない。期限のモデル (Spec/deadline.qnt) は解決の手段ごとの帰結を示すが、どれを選ぶかは業務の方針である |
| 未決定 | 緊急メンテナンスの前に発行した入場権は、脆弱性の影響を調べ終えるまで有効か (モデルの外) | 入場権, 脆弱性 | 業務側への質問。モデルで示せない理由: 脆弱性の影響の調査と、発行済みの入場権の有効性は、どの検査モデルにも状態として書いていない |
| 未決定 | 販売の文脈と決済の文脈が定義の上で互いに依存している。顧客をどの文脈が持つか | 顧客, 決済, 仮確保 | 業務側への質問。モデルで示せない理由: 用語集の定義依存 (Lean) から出た問いで、状態遷移の反例ではない。文脈の分け方は設計と組織の判断である |
| 証明済み | 4 人全員の希望を満たす割当ては存在しない | 振替, 顧客, 座席 | Lean: `Glossary.Fairness.not_all_four` |
| 証明済み | 保護対象の A・B・C は全員振り替えられる | 振替, 保護対象 | Lean: `Glossary.Fairness.abc_possible` |
| 証明済み | A・B・C を全員振り替えるなら、C は必ず 16:00 になる | 回復可能性 | Lean: `Glossary.Fairness.c_must_take_16` |
| 証明済み | C が 13:00 の席を取ると、A と B の両方は振り替えられない | 回復可能性の喪失 | Lean: `Glossary.Fairness.c_at_13_costs` |
| 証明済み | 新規購入の D に席を渡すと、A・B・C の全員は振り替えられない | 回復可能性の喪失, 保護対象 | Lean: `Glossary.Fairness.d_served_costs_protected` |
| 反例あり | 先着順で、確定した割当ては回復可能性を保つ | 回復可能性, 公平性 | Quint 反例: `Spec/rebooking.qnt` `fcfs.noAvoidableLoss` |
| 証明済み | 回復可能性を守る方針で、席の排他性と回復可能性が常に成り立つ | 回復可能性, 座席 | Quint + TLC 全状態: `Spec/rebooking.qnt` `preserving.Safety` |
| 証明済み | 回復可能性を守る方針で、振替がまだの保護対象には確定できる席が必ず残っている | 回復可能性, 保護対象 | Quint + TLC 全状態: `Spec/rebooking.qnt` `preserving.rescueNeverStuck` |
| 証明済み | 回復可能性を守る方針の代償: 新規購入の D は席を得られない | 公平性, 顧客 | Quint + TLC 全状態: `Spec/rebooking.qnt` `preserving.dNeverServed` |
| 未決定 | 公平性としてどの方針を採るか (先着順, 既存購入者優先, 最大履行人数, 選択肢の少ない顧客優先) | 公平性 | 業務側への質問。空白を示す反例: `Spec/rebooking.qnt` `fcfs.noAvoidableLoss` |
| 未決定 | 取引の確認が終わっていない保護対象のために、席を保留するか (モデルの外) | 公平性, 保護対象, 決済 | 業務側への質問。モデルで示せない理由: 振替のモデル (Spec/rebooking.qnt) は、取引の確認の途中という状態を持たない |
| 未決定 | 割当ての優先順位を決め、変える権限は誰にあるか | 公平性 | 業務側への質問。モデルで示せない理由: 権限の割り当ては組織の決めごとで、どの検査モデルの状態にもない |
| 反例あり | 購入完了を終点とみなす設計で、中止になった上映回の入場権は履行義務として数えられている | 履行義務, 上映中止, 入場権 | Quint 反例: `Spec/obligation.qnt` `ob0_no_obligation.cancelledIsOwed` |
| 反例あり | 履行義務を作るだけの設計で、未解決の履行義務には解決責任者がいる | 履行義務, 解決責任者 | Quint 反例: `Spec/obligation.qnt` `ob1_no_owner.owedHasOwner` |
| 反例あり | 責任者を割り当てるだけの設計で、未解決の履行義務には責任者が実行できる解決の道がある | 解決責任者, 権限, 進行可能性 | Quint 反例: `Spec/obligation.qnt` `ob2_no_authority.owedCanProgress` |
| 証明済み | 引き継ぎを入れた設計で、中止の入場権は履行義務になり、責任者がいて、解決の道がある | 履行義務, 解決責任者, 権限, 引き継ぎ, 進行可能性 | Quint + TLC 全状態: `Spec/obligation.qnt` `ob3_handoff.Safety` |
| 証明済み | 未解決の状態から必ず残量の減る一歩を踏めるなら、どの状態からも解決済みに到達できる (状態と操作が何であっても) | 進行可能性, 履行義務 | Lean: `Glossary.Progress.resolvable` |
| 反例あり | 引き継ぎを入れた設計で、解決の操作が公平に実行されるなら、履行義務はいつか必ず解決する | 履行義務, 引き継ぎ, 緊急メンテナンス | Quint + TLC 反例: `Spec/obligation.qnt` `ob3_handoff.Liveness` |
| 証明済み | 同じ設計で、さらに復旧がいつか必ず来るなら、履行義務はいつか必ず解決する | 履行義務, 引き継ぎ, 緊急メンテナンス | Quint + TLC 全状態: `Spec/obligation.qnt` `ob3_handoff.LivenessGivenRecovery` |
| 未決定 | 緊急メンテナンスが終わらないとき、空席があっても販売は履行義務を決済に引き継げるか | 引き継ぎ, 緊急メンテナンス, 振替 | 業務側への質問。空白を示す反例: `Spec/obligation.qnt` `ob3_handoff.Liveness` |
| 証明済み | オンライン発券だけの設計でも、未解決の取引には常に先へ進む道がある (最終的な解決) | 決済済み・発券保留取引, 進行可能性 | Quint + TLC 全状態: `Spec/deadline.qnt` `online_only.owedCanProgress` |
| 反例あり | オンライン発券だけの設計で、履行期限を過ぎて観られなかった顧客はいない | 履行期限, 目的の喪失, 緊急メンテナンス | Quint 反例: `Spec/deadline.qnt` `online_only.goalNotLostToTime` |
| 証明済み | 窓口発券を認める設計で、システムが最後の機会を見送らないなら、履行期限を過ぎて観られなかった顧客はいない | 窓口発券, 履行期限, 目的の喪失 | Quint + TLC 全状態: `Spec/deadline.qnt` `box_office.goalNotLostToTime` |
| 反例あり | 窓口発券を認める設計で、遮断完了後に発券は起きない | 窓口発券, 遮断完了, 入場権 | Quint 反例: `Spec/deadline.qnt` `box_office.noTicketWhileBlocked` |
| 証明済み | 「遮断中は発券しない」「履行期限までに発券する」「遮断が履行期限まで続く」は同時に成り立たない | 遮断完了, 履行期限, 緊急メンテナンス | Lean: `Glossary.Deadline.rules_conflict` |
| 未決定 | 緊急メンテナンス中の窓口発券を認めるか。認めなければ顧客の目的を守れず、認めれば遮断中に発券が起きる | 窓口発券, 緊急メンテナンス, 目的の喪失 | 業務側への質問。空白を示す反例: `Spec/deadline.qnt` `online_only.goalNotLostToTime`, `Spec/deadline.qnt` `box_office.noTicketWhileBlocked` |
| 証明済み | 席が足りる場面 (13:00 に 2 席) では、誰が席を得るかは方針だけで決まる | 方針で決まる判断, 保護対象 | Lean: `Glossary.Autonomy.enough_determined` |
| 証明済み | 席が足りない場面 (13:00 に 1 席) では、誰が席を得るかは方針で決まらない | 方針で決まる判断, 人への委譲 | Lean: `Glossary.Autonomy.short_not_determined` |
| 証明済み | 席が足りる場面で、システムは方針で決まらない選択を 1 つもしない | 方針で決まる判断 | Quint + TLC 全状態: `Spec/autonomy.qnt` `enough_auto.noArbitraryChoice` |
| 証明済み | 席が足りる場面で、人に決定を求めることはない | 人への委譲 | Quint + TLC 全状態: `Spec/autonomy.qnt` `enough_escalate.humanNeverAsked` |
| 反例あり | 席が足りない場面で、人に委ねない設計のシステムは、方針で決まらない選択をしない | 方針で決まる判断, 公平性 | Quint 反例: `Spec/autonomy.qnt` `short_auto.noArbitraryChoice` |
| 証明済み | 席が足りない場面で、人に委ねる設計は、席の排他性と方針を保ち、行き詰まらない | 人への委譲, 方針で決まる判断, 座席 | Quint + TLC 全状態: `Spec/autonomy.qnt` `short_escalate.Safety` |
| 証明済み | 同じ設計で、システムは方針で決まらない選択を自分ではしない | 人への委譲, 方針で決まる判断 | Quint + TLC 全状態: `Spec/autonomy.qnt` `short_escalate.noArbitraryChoice` |
| 反例あり | 席が足りない場面で、人に決定を求めずに済む | 人への委譲 | Quint 反例: `Spec/autonomy.qnt` `short_escalate.humanNeverAsked` |
| 証明済み | 席が足りない場面でも、新規購入の D を断ることは方針だけで決まる | 方針で決まる判断, 顧客 | Quint + TLC 全状態: `Spec/autonomy.qnt` `short_escalate.dNeverServed` |
| 未決定 | 方針で決まらない選択 (A か B か) を誰が決めるか。あるいは、方針に順位付けの規則を足すか | 人への委譲, 権限, 公平性 | 業務側への質問。空白を示す反例: `Spec/autonomy.qnt` `short_escalate.humanNeverAsked` |
| 証明済み | 停止時の規則の案では、流出した情報だけで入場する人はなく、決済済みで開始時刻に来た購入者は断られず、入場も返金もされない取引は残らない | 入場権, 決済済み・発券保留取引, 窓口発券, 返金, 緊急メンテナンス | Quint + TLC 全状態: `Spec/outage_policy.qnt` `draft.Safety` |
| 反例あり | 公表された案内を単純化した扱い (券は有効のまま、氏名を告げれば通す) で、流出した情報だけで入場する人はいない | 入場権, 脆弱性 | Quint 反例: `Spec/outage_policy.qnt` `as_reported.noImpostor` |
| 反例あり | 案から「会場は購入者の一覧で決済済みの客を通す」を外しても、決済済みで開始時刻に来た購入者は断られない | 窓口発券, 決済済み・発券保留取引 | Quint 反例: `Spec/outage_policy.qnt` `without_venue_issue.noLockout` |
| 反例あり | 案から「流出後は本人確認に切り替える」を外しても、流出した情報だけで入場する人はいない | 入場権, 脆弱性 | Quint 反例: `Spec/outage_policy.qnt` `without_identity_check.noImpostor` |
| 反例あり | 案に「氏名を告げるだけの客を通す」を足しても、流出した情報だけで入場する人はいない | 入場権, 脆弱性 | Quint 反例: `Spec/outage_policy.qnt` `with_name_only.noImpostor` |
| 反例あり | 案から「入場できなかった決済済みの客に申し出なしで返金する」を外しても、入場も返金もされない取引は残らない | 返金, 決済済み・発券保留取引 | Quint 反例: `Spec/outage_policy.qnt` `without_auto_refund.noLimbo` |
| 証明済み | 流出した券をすべて無効にすれば、流出した情報だけで入場する人はいない | 入場権, 脆弱性 | Quint + TLC 全状態: `Spec/outage_policy.qnt` `invalidate_all.noImpostor` |
| 反例あり | 流出した券をすべて無効にしても、決済済みで開始時刻に来た購入者は断られない | 入場権, 脆弱性 | Quint 反例: `Spec/outage_policy.qnt` `invalidate_all.noLockout` |

