import Glossary.Claim
import Glossary.Fairness
import Glossary.Progress
import Glossary.Deadline
import Glossary.Autonomy

/-! # 用語集 B: 映画館のチケット販売 (実験 4〜5) -/

namespace Glossary.Cinema

inductive Term where
  | customer | screening | seat | seatHold | payment | refund | admission
  | salesChannel | plannedMaintenance | vulnerability | emergencyMaintenance
  | cutoffOrder | cutoffApplied | saleEstablished
  -- 実験 4 で見つけた概念
  | paidPendingIssuance
  -- 実験 5 で見つけた概念
  | rebooking | protectedCustomer | recoverability | recoverabilityLoss | fairness
  -- Take 2〜4 (要約からの再構成) で見つけた概念
  | screeningCancellation | obligation | resolutionOwner | authority | handoff | progressability
  | fulfillmentDeadline | goalLoss | boxOfficeIssue
  -- Experiment 006 で見つけた概念
  | determinedDecision | escalation
  deriving DecidableEq, Repr

inductive Ctx where
  | sales | payment | ticketing | operations
  deriving DecidableEq, Repr

open Term

/-- 実験の前からあった用語。 -/
def baseTerms : List (Entry Term Ctx) := [
  { id := customer, label := "顧客", context := .sales,
    gloss := "チケットを買う、または買った主体",
    assoc := [seatHold, payment, admission] },
  { id := screening, label := "上映回", context := .sales,
    gloss := "ある作品を、ある日時に、あるスクリーンで上映する 1 回" },
  { id := seat, label := "座席", role := some .resource, context := .sales,
    gloss := "上映回の中で 1 人が座る場所", defDeps := [screening] },
  { id := seatHold, label := "仮確保", role := some .hold, context := .sales,
    gloss := "顧客が決済を終えるまで、座席を他の顧客に売らないでおく取り置き",
    defDeps := [customer, seat] },
  { id := payment, label := "決済", role := some .externalConfirmation, context := .payment,
    gloss := "顧客が外部の決済サービスを通じて代金を支払うこと。結果は成功・失敗・不明のどれか",
    defDeps := [customer] },
  { id := refund, label := "返金", context := .payment,
    gloss := "成功した決済の代金を顧客に戻すこと", defDeps := [payment] },
  { id := admission, label := "入場権", role := some .entitlement, context := .ticketing,
    gloss := "顧客が、ある上映回のある座席で鑑賞できる権利 (チケット)",
    defDeps := [customer, seat] },
  { id := salesChannel, label := "販売経路", context := .operations,
    gloss := "仮確保・決済開始・発券を受け付ける入口" },
  { id := plannedMaintenance, label := "通常メンテナンス", role := some .plannedStop, context := .operations,
    gloss := "新しい仮確保を止め、処理中の取引が片付いてから販売経路を止める作業",
    defDeps := [salesChannel] },
  { id := vulnerability, label := "脆弱性", context := .operations,
    gloss := "悪用されると取引や入場権の信頼性を損なう欠陥" },
  { id := emergencyMaintenance, label := "緊急メンテナンス", role := some .stop, context := .operations,
    gloss := "脆弱性を検知して、処理中の取引を待たずに自動で販売経路を止めること",
    defDeps := [vulnerability, salesChannel] },
  { id := cutoffOrder, label := "停止指令", context := .operations,
    gloss := "緊急メンテナンスで販売経路を止めると決めた時点。経路はまだ動いている",
    defDeps := [emergencyMaintenance] },
  { id := cutoffApplied, label := "遮断完了", context := .operations,
    gloss := "すべての販売経路が実際に止まった時点", defDeps := [cutoffOrder] },
  { id := saleEstablished, label := "販売成立", context := .sales,
    gloss := "未決定: 決済が成功した時点か、入場権を発行した時点か",
    defDeps := [payment, admission] }
]

/-- 実験 4 で見つけた概念。 -/
def pendingIssuanceEntry : Entry Term Ctx :=
  { id := paidPendingIssuance, label := "決済済み・発券保留取引", context := .sales,
    gloss := "決済は成功したが入場権がまだない取引。仮確保を保ったまま、発券か返金で解決する",
    defDeps := [payment, admission, seatHold, refund] }

/-- 実験 5 で見つけた概念。 -/
def rebookingEntries : List (Entry Term Ctx) := [
  { id := rebooking, label := "振替", role := some .reallocation, context := .sales,
    gloss := "中止になった上映回の入場権を、別の上映回の入場権に替えること",
    defDeps := [admission, screening] },
  { id := protectedCustomer, label := "保護対象", context := .sales,
    gloss := "映画館側の事情で上映回が中止になった既存購入者",
    defDeps := [customer, admission, screening] },
  { id := recoverability, label := "回復可能性", context := .sales,
    gloss := "いまの割当てを延長して、保護対象の全員を振り替えられること",
    defDeps := [rebooking, protectedCustomer] },
  { id := recoverabilityLoss, label := "回復可能性の喪失", context := .sales,
    gloss := "有効な確定によって回復可能性が失われること", defDeps := [recoverability] },
  { id := fairness, label := "公平性", context := .sales,
    gloss := "未決定: 顧客の希望が衝突したとき、誰を優先するかの方針", defDeps := [customer] }
]

/-- Take 2〜4 で見つけた概念。 -/
def obligationEntries : List (Entry Term Ctx) := [
  { id := screeningCancellation, label := "上映中止", role := some .supplyCancellation, context := .operations,
    gloss := "設備故障など映画館側の事情で、上映回を取りやめること", defDeps := [screening] },
  { id := obligation, label := "履行義務", context := .sales,
    gloss := "入場権を発行した顧客に対して、鑑賞させるか、振替か返金で埋め合わせる義務",
    defDeps := [admission, customer, rebooking, refund] },
  { id := resolutionOwner, label := "解決責任者", context := .operations,
    gloss := "未解決の履行義務を、解決するまで引き受ける文脈", defDeps := [obligation] },
  { id := authority, label := "権限", context := .operations,
    gloss := "ある解決の操作を実行してよいという許可。返金の権限は決済の文脈だけが持つ",
    defDeps := [obligation, refund] },
  { id := handoff, label := "引き継ぎ", context := .operations,
    gloss := "解決責任者が、権限を持つ別の文脈に履行義務を渡すこと",
    defDeps := [resolutionOwner, authority] },
  { id := progressability, label := "進行可能性", context := .operations,
    gloss := "未解決の履行義務に、責任者が実行できる解決の道が残っていること",
    defDeps := [obligation, resolutionOwner, authority] },
  { id := fulfillmentDeadline, label := "履行期限", role := some .deadline, context := .sales,
    gloss := "それを過ぎると顧客の目的が果たせなくなる時刻。上映開始",
    defDeps := [obligation, screening] },
  { id := goalLoss, label := "目的の喪失", context := .sales,
    gloss := "履行期限を過ぎて、顧客が観られなかったこと。返金で解決しても残る",
    defDeps := [fulfillmentDeadline] },
  { id := boxOfficeIssue, label := "窓口発券", role := some .fallbackChannel, context := .ticketing,
    gloss := "販売経路を通さずに入場権を発行すること", defDeps := [admission, salesChannel] }
]

/-- Experiment 006 で見つけた概念。 -/
def autonomyEntries : List (Entry Term Ctx) := [
  { id := determinedDecision, label := "方針で決まる判断", context := .sales,
    gloss := "採用した方針のもとで、最善の割当てがどれも同じ顧客に席を渡す判断。システムが自分で実行できる",
    defDeps := [fairness, recoverability] },
  { id := escalation, label := "人への委譲", context := .operations,
    gloss := "方針で決まらない判断を、権限を持つ人に渡すこと",
    defDeps := [determinedDecision, authority] }
]

def terms : List (Entry Term Ctx) :=
  baseTerms ++ [pendingIssuanceEntry] ++ rebookingEntries ++ obligationEntries ++ autonomyEntries

theorem baseTerms_check : check baseTerms = true := by decide

/-- 見つけた概念の追加は、追加の保存定理 (`check_add`) で正当化できる。 -/
theorem pendingIssuance_added : check (baseTerms ++ [pendingIssuanceEntry]) = true :=
  check_add baseTerms pendingIssuanceEntry baseTerms_check (by decide) (by decide) (by decide)

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)

/-- 発見: 販売と決済の文脈は、定義の上で互いに依存している (文脈間の循環)。 -/
theorem sales_payment_depend_on_each_other :
    (Ctx.sales, Ctx.payment) ∈ contextEdges terms ∧ (Ctx.payment, Ctx.sales) ∈ contextEdges terms := by
  decide

def sale (main invariant : String) : QuintRef :=
  { file := "Spec/emergency_sale.qnt", main, invariant }

def rebook (main invariant : String) : QuintRef :=
  { file := "Spec/rebooking.qnt", main, invariant }

def duty (main invariant : String) : QuintRef :=
  { file := "Spec/obligation.qnt", main, invariant }

def dutyLive (main property : String) : QuintRef :=
  { file := "Spec/obligation.qnt", main, invariant := property, temporal := true }

def due (main invariant : String) : QuintRef :=
  { file := "Spec/deadline.qnt", main, invariant }

def auto (main invariant : String) : QuintRef :=
  { file := "Spec/autonomy.qnt", main, invariant }

def outage (main invariant : String) : QuintRef :=
  { file := "Spec/outage_policy.qnt", main, invariant }

open Fairness in
def claims : List (Claim Term) := [
  -- 実験 4: 決済成功と緊急メンテナンスの競合
  { about := [admission, seat, emergencyMaintenance],
    statement := "素朴な設計 (発券は支払い済みかどうかだけを見る) で、同じ座席の入場権は高々 1 つ",
    verdict := .counterexample, evidence := .violated (sale "v0_naive" "seatExclusive") },
  { about := [payment, admission, seatHold],
    statement := "発券時に仮確保を確かめる設計で、支払い済み・未発券の取引は座席を保ったまま追跡されている",
    verdict := .counterexample, evidence := .violated (sale "v1_guarded" "paidIsTracked") },
  { about := [paidPendingIssuance, admission, seat, plannedMaintenance, cutoffApplied],
    statement := "決済済み・発券保留取引を入れた設計で、座席の排他性・決済後の取引保全・遮断完了後に発券なし・通常メンテナンス中に未解決の決済なし、がすべて成り立つ",
    verdict := .proved, evidence := .holds (sale "v2_pending_issuance" "Safety") },
  { about := [saleEstablished, cutoffApplied, payment],
    statement := "販売成立は決済成功の時点か、発券の時点か。決済成功とするなら、遮断完了後にも販売が成立する",
    verdict := .undecided,
    evidence := .question [sale "v2_pending_issuance" "noPaymentWhileBlocked"],
    industry := some (.answered "決済の完了で売買が成立し、発券は成立したあとの履行として扱われている") },
  { about := [refund, cutoffApplied, paidPendingIssuance],
    statement := "遮断中に返金してよいか (モデルは許している)",
    verdict := .undecided, evidence := .questionOutsideModel
      "決済の競合のモデル (Spec/emergency_sale.qnt) は遮断中の返金を許している。許すか禁じるかで性質は破れないので、どちらが正しいかを示す反例はない",
    industry := some (.gap "停止中の返金を事前に決めて公開している事業者が、調べた範囲で見つからない") },
  { about := [paidPendingIssuance, screening, emergencyMaintenance],
    statement := "緊急メンテナンスが上映開始まで続いたとき、発券保留取引をどう解決するか (時間はモデルの外)",
    verdict := .undecided, evidence := .questionOutsideModel
      "決済の競合のモデルは時刻を持たない。期限のモデル (Spec/deadline.qnt) は解決の手段ごとの帰結を示すが、どれを選ぶかは業務の方針である",
    industry := some (.gap "事故のたびに、購入完了の通知を見せて入場させるなどの対応を現場で決めている") },
  { about := [admission, vulnerability],
    statement := "緊急メンテナンスの前に発行した入場権は、脆弱性の影響を調べ終えるまで有効か (モデルの外)",
    verdict := .undecided, evidence := .questionOutsideModel
      "脆弱性の影響の調査と、発行済みの入場権の有効性は、どの検査モデルにも状態として書いていない",
    industry := some (.gap "有効のままが暗黙の既定で、無効にする基準を定めた規約が見つからない") },
  { about := [customer, payment, seatHold],
    statement := "販売の文脈と決済の文脈が定義の上で互いに依存している。顧客をどの文脈が持つか",
    verdict := .undecided, evidence := .questionOutsideModel
      "用語集の定義依存 (Lean) から出た問いで、状態遷移の反例ではない。文脈の分け方は設計と組織の判断である",
    industry := some (.answered "カード番号は決済の側、本人の情報は販売の側が持つのが普通である") },
  -- 実験 5: 公平性
  { about := [rebooking, customer, seat],
    statement := "4 人全員の希望を満たす割当ては存在しない",
    verdict := .proved,
    evidence := .lean "Glossary.Fairness.not_all_four"
      (∀ p, Valid p → ¬ ∀ c, Served p c) not_all_four },
  { about := [rebooking, protectedCustomer],
    statement := "保護対象の A・B・C は全員振り替えられる",
    verdict := .proved,
    evidence := .lean "Glossary.Fairness.abc_possible"
      (Valid rescue ∧ Served rescue .A ∧ Served rescue .B ∧ Served rescue .C) abc_possible },
  { about := [recoverability],
    statement := "A・B・C を全員振り替えるなら、C は必ず 16:00 になる",
    verdict := .proved,
    evidence := .lean "Glossary.Fairness.c_must_take_16"
      (∀ p, Valid p → Served p .A → Served p .B → Served p .C → p .C = some .s16a)
      c_must_take_16 },
  { about := [recoverabilityLoss],
    statement := "C が 13:00 の席を取ると、A と B の両方は振り替えられない",
    verdict := .proved,
    evidence := .lean "Glossary.Fairness.c_at_13_costs"
      (∀ p, Valid p → (p .C = some .s13a ∨ p .C = some .s13b) → ¬ (Served p .A ∧ Served p .B))
      c_at_13_costs },
  { about := [recoverabilityLoss, protectedCustomer],
    statement := "新規購入の D に席を渡すと、A・B・C の全員は振り替えられない",
    verdict := .proved,
    evidence := .lean "Glossary.Fairness.d_served_costs_protected"
      (∀ p, Valid p → Served p .D → ¬ (Served p .A ∧ Served p .B ∧ Served p .C))
      d_served_costs_protected },
  { about := [recoverability, fairness],
    statement := "先着順で、確定した割当ては回復可能性を保つ",
    verdict := .counterexample, evidence := .violated (rebook "fcfs" "noAvoidableLoss") },
  { about := [recoverability, seat],
    statement := "回復可能性を守る方針で、席の排他性と回復可能性が常に成り立つ",
    verdict := .proved, evidence := .holds (rebook "preserving" "Safety") },
  { about := [recoverability, protectedCustomer],
    statement := "回復可能性を守る方針で、振替がまだの保護対象には確定できる席が必ず残っている",
    verdict := .proved, evidence := .holds (rebook "preserving" "rescueNeverStuck") },
  { about := [fairness, customer],
    statement := "回復可能性を守る方針の代償: 新規購入の D は席を得られない",
    verdict := .proved, evidence := .holds (rebook "preserving" "dNeverServed") },
  { about := [fairness],
    statement := "公平性としてどの方針を採るか (先着順, 既存購入者優先, 最大履行人数, 選択肢の少ない顧客優先)",
    verdict := .undecided, evidence := .question [rebook "fcfs" "noAvoidableLoss"],
    industry := some (.notAsked "調べた範囲の国内の映画館では、上映中止のときは払い戻しだけで、振替がない") },
  { about := [fairness, protectedCustomer, payment],
    statement := "取引の確認が終わっていない保護対象のために、席を保留するか (モデルの外)",
    verdict := .undecided, evidence := .questionOutsideModel
      "振替のモデル (Spec/rebooking.qnt) は、取引の確認の途中という状態を持たない",
    industry := some (.notAsked "振替がないので、振替のために席を保留する場面がない") },
  { about := [fairness],
    statement := "割当ての優先順位を決め、変える権限は誰にあるか",
    verdict := .undecided, evidence := .questionOutsideModel
      "権限の割り当ては組織の決めごとで、どの検査モデルの状態にもない",
    industry := some (.notAsked "振替がないので、割当ての優先順位を決める場面がない") },
  -- Take 2 (要約からの再構成): 履行義務
  { about := [obligation, screeningCancellation, admission],
    statement := "購入完了を終点とみなす設計で、中止になった上映回の入場権は履行義務として数えられている",
    verdict := .counterexample, evidence := .violated (duty "ob0_no_obligation" "cancelledIsOwed") },
  -- Take 3 (要約からの再構成): 責任・権限・進行可能性
  { about := [obligation, resolutionOwner],
    statement := "履行義務を作るだけの設計で、未解決の履行義務には解決責任者がいる",
    verdict := .counterexample, evidence := .violated (duty "ob1_no_owner" "owedHasOwner") },
  { about := [resolutionOwner, authority, progressability],
    statement := "責任者を割り当てるだけの設計で、未解決の履行義務には責任者が実行できる解決の道がある",
    verdict := .counterexample, evidence := .violated (duty "ob2_no_authority" "owedCanProgress") },
  { about := [obligation, resolutionOwner, authority, handoff, progressability],
    statement := "引き継ぎを入れた設計で、中止の入場権は履行義務になり、責任者がいて、解決の道がある",
    verdict := .proved, evidence := .holds (duty "ob3_handoff" "Safety") },
  { about := [progressability, obligation],
    statement := "未解決の状態から必ず残量の減る一歩を踏めるなら、どの状態からも解決済みに到達できる (状態と操作が何であっても)",
    verdict := .proved,
    evidence := .lean "Glossary.Progress.resolvable"
      (∀ (S : Type) (step : S → S → Prop) (resolved : S → Prop) (μ : S → Nat),
        (∀ s, ¬ resolved s → ∃ t, step s t ∧ μ t < μ s) →
        ∀ s, ∃ t, Progress.Reach step s t ∧ resolved t)
      (fun _ step resolved μ h => Progress.resolvable step resolved μ h) },
  { about := [obligation, handoff, emergencyMaintenance],
    statement := "引き継ぎを入れた設計で、解決の操作が公平に実行されるなら、履行義務はいつか必ず解決する",
    verdict := .counterexample, evidence := .violated (dutyLive "ob3_handoff" "Liveness") },
  { about := [obligation, handoff, emergencyMaintenance],
    statement := "同じ設計で、さらに復旧がいつか必ず来るなら、履行義務はいつか必ず解決する",
    verdict := .proved, evidence := .holds (dutyLive "ob3_handoff" "LivenessGivenRecovery") },
  { about := [handoff, emergencyMaintenance, rebooking],
    statement := "緊急メンテナンスが終わらないとき、空席があっても販売は履行義務を決済に引き継げるか",
    verdict := .undecided, evidence := .question [dutyLive "ob3_handoff" "Liveness"],
    industry := some (.gap "引き継ぎを定めた規約がなく、実際には返金で終わっている") },
  -- Take 4 (要約からの再構成): 時間制約
  { about := [paidPendingIssuance, progressability],
    statement := "オンライン発券だけの設計でも、未解決の取引には常に先へ進む道がある (最終的な解決)",
    verdict := .proved, evidence := .holds (due "online_only" "owedCanProgress") },
  { about := [fulfillmentDeadline, goalLoss, emergencyMaintenance],
    statement := "オンライン発券だけの設計で、履行期限を過ぎて観られなかった顧客はいない",
    verdict := .counterexample, evidence := .violated (due "online_only" "goalNotLostToTime") },
  { about := [boxOfficeIssue, fulfillmentDeadline, goalLoss],
    statement := "窓口発券を認める設計で、システムが最後の機会を見送らないなら、履行期限を過ぎて観られなかった顧客はいない",
    verdict := .proved, evidence := .holds (due "box_office" "goalNotLostToTime") },
  { about := [boxOfficeIssue, cutoffApplied, admission],
    statement := "窓口発券を認める設計で、遮断完了後に発券は起きない",
    verdict := .counterexample, evidence := .violated (due "box_office" "noTicketWhileBlocked") },
  { about := [cutoffApplied, fulfillmentDeadline, emergencyMaintenance],
    statement := "「遮断中は発券しない」「履行期限までに発券する」「遮断が履行期限まで続く」は同時に成り立たない",
    verdict := .proved,
    evidence := .lean "Glossary.Deadline.rules_conflict"
      (∀ (deadline : Nat) (blocked : Nat → Prop) (issuedAt : Option Nat),
        (∀ t, issuedAt = some t → ¬ blocked t) →
        (∃ t, t < deadline ∧ issuedAt = some t) →
        (∀ t, t < deadline → blocked t) → False)
      Deadline.rules_conflict },
  { about := [boxOfficeIssue, emergencyMaintenance, goalLoss],
    statement := "緊急メンテナンス中の窓口発券を認めるか。認めなければ顧客の目的を守れず、認めれば遮断中に発券が起きる",
    verdict := .undecided,
    evidence := .question [due "online_only" "goalNotLostToTime", due "box_office" "noTicketWhileBlocked"],
    industry := some (.answered "停止中も会場で入場や発券を続けるのが、業界の普通の対応である") },
  -- Experiment 006: 自律と人の判断の境界
  { about := [determinedDecision, protectedCustomer],
    statement := "席が足りる場面 (13:00 に 2 席) では、誰が席を得るかは方針だけで決まる",
    verdict := .proved,
    evidence := .lean "Glossary.Autonomy.enough_determined"
      (Autonomy.Determined Autonomy.RescuesAll Autonomy.whoIsServed) Autonomy.enough_determined },
  { about := [determinedDecision, escalation],
    statement := "席が足りない場面 (13:00 に 1 席) では、誰が席を得るかは方針で決まらない",
    verdict := .proved,
    evidence := .lean "Glossary.Autonomy.short_not_determined"
      (¬ Autonomy.Determined Autonomy.BestShort Autonomy.whoIsServed)
      Autonomy.short_not_determined },
  { about := [determinedDecision],
    statement := "席が足りる場面で、システムは方針で決まらない選択を 1 つもしない",
    verdict := .proved, evidence := .holds (auto "enough_auto" "noArbitraryChoice") },
  { about := [escalation],
    statement := "席が足りる場面で、人に決定を求めることはない",
    verdict := .proved, evidence := .holds (auto "enough_escalate" "humanNeverAsked") },
  { about := [determinedDecision, fairness],
    statement := "席が足りない場面で、人に委ねない設計のシステムは、方針で決まらない選択をしない",
    verdict := .counterexample, evidence := .violated (auto "short_auto" "noArbitraryChoice") },
  { about := [escalation, determinedDecision, seat],
    statement := "席が足りない場面で、人に委ねる設計は、席の排他性と方針を保ち、行き詰まらない",
    verdict := .proved, evidence := .holds (auto "short_escalate" "Safety") },
  { about := [escalation, determinedDecision],
    statement := "同じ設計で、システムは方針で決まらない選択を自分ではしない",
    verdict := .proved, evidence := .holds (auto "short_escalate" "noArbitraryChoice") },
  { about := [escalation],
    statement := "席が足りない場面で、人に決定を求めずに済む",
    verdict := .counterexample, evidence := .violated (auto "short_escalate" "humanNeverAsked") },
  { about := [determinedDecision, customer],
    statement := "席が足りない場面でも、新規購入の D を断ることは方針だけで決まる",
    verdict := .proved, evidence := .holds (auto "short_escalate" "dNeverServed") },
  { about := [escalation, authority, fairness],
    statement := "方針で決まらない選択 (A か B か) を誰が決めるか。あるいは、方針に順位付けの規則を足すか",
    verdict := .undecided, evidence := .question [auto "short_escalate" "humanNeverAsked"],
    industry := some (.notAsked "振替がないので、方針で決まらない割当ての選択が生じない") },
  -- 停止時の規則の案
  { about := [admission, paidPendingIssuance, boxOfficeIssue, refund, emergencyMaintenance],
    statement := "停止時の規則の案では、流出した情報だけで入場する人はなく、決済済みで開始時刻に来た購入者は断られず、入場も返金もされない取引は残らない",
    verdict := .proved, evidence := .holds (outage "draft" "Safety") },
  { about := [admission, vulnerability],
    statement := "公表された案内を単純化した扱い (券は有効のまま、氏名を告げれば通す) で、流出した情報だけで入場する人はいない",
    verdict := .counterexample, evidence := .violated (outage "as_reported" "noImpostor") },
  { about := [boxOfficeIssue, paidPendingIssuance],
    statement := "案から「会場は購入者の一覧で決済済みの客を通す」を外しても、決済済みで開始時刻に来た購入者は断られない",
    verdict := .counterexample, evidence := .violated (outage "without_venue_issue" "noLockout") },
  { about := [admission, vulnerability],
    statement := "案から「流出後は本人確認に切り替える」を外しても、流出した情報だけで入場する人はいない",
    verdict := .counterexample, evidence := .violated (outage "without_identity_check" "noImpostor") },
  { about := [admission, vulnerability],
    statement := "案に「氏名を告げるだけの客を通す」を足しても、流出した情報だけで入場する人はいない",
    verdict := .counterexample, evidence := .violated (outage "with_name_only" "noImpostor") },
  { about := [refund, paidPendingIssuance],
    statement := "案から「入場できなかった決済済みの客に申し出なしで返金する」を外しても、入場も返金もされない取引は残らない",
    verdict := .counterexample, evidence := .violated (outage "without_auto_refund" "noLimbo") },
  { about := [admission, vulnerability],
    statement := "流出した券をすべて無効にすれば、流出した情報だけで入場する人はいない",
    verdict := .proved, evidence := .holds (outage "invalidate_all" "noImpostor") },
  { about := [admission, vulnerability],
    statement := "流出した券をすべて無効にしても、決済済みで開始時刻に来た購入者は断られない",
    verdict := .counterexample, evidence := .violated (outage "invalidate_all" "noLockout") }
]

def book : Book Term Ctx := { title := "映画館のチケット販売", terms, claims, stopScene := .modelled }

theorem book_check : book.check = true := by decide

end Glossary.Cinema
