import Glossary.Claim
import Glossary.Broken
import Glossary.EmptyConcept
import Glossary.PaidStages

/-! # 用語集 A: 注文 (実験 1〜3) -/

namespace Glossary.OrderBook

inductive Term where
  | customer | transaction | order | payment | authorization | capture | shipment | cancellation
  | confirmedOrder
  deriving DecidableEq, Repr

inductive Ctx where
  | sales
  deriving DecidableEq, Repr

open Term

def terms : List (Entry Term Ctx) := [
  { id := customer, label := "顧客", context := .sales, gloss := "商品を買う主体",
    assoc := [order] },
  { id := transaction, label := "取引", context := .sales,
    gloss := "対価と引き換えに権利を渡す商業上の活動" },
  { id := order, label := "注文", context := .sales,
    gloss := "顧客が商品を購入するために作成する取引",
    defDeps := [customer, transaction], assoc := [customer] },
  { id := payment, label := "支払い", role := some .externalConfirmation, context := .sales,
    gloss := "顧客が注文の代金を払うこと", defDeps := [customer, order] },
  { id := authorization, label := "与信", context := .sales,
    gloss := "カード会社が注文の代金の枠を押さえること。期限があり、お金はまだ動かない",
    defDeps := [payment] },
  { id := capture, label := "売上確定", context := .sales,
    gloss := "与信した代金の請求を事業者が確定すること", defDeps := [authorization] },
  { id := shipment, label := "発送", role := some .entitlement, context := .sales,
    gloss := "注文の商品を顧客に送り出すこと", defDeps := [customer, order] },
  { id := cancellation, label := "キャンセル", context := .sales,
    gloss := "注文を取りやめること", defDeps := [order] },
  { id := confirmedOrder, label := "確定注文", context := .sales,
    gloss := "支払いが完了しており、かつ支払いが未完了の注文 (議論の例のまま)",
    defDeps := [order, payment] }
]

def stages (main invariant : String) : QuintRef :=
  { file := "Spec/payment_stages.qnt", main, invariant }

def coverage (invariant : String) : QuintRef :=
  { file := "Spec/order_coverage.qnt", main := "order_coverage", invariant }

def claims : List (Claim Term) := [
  { about := [order, transaction],
    statement := "草稿の用語集 (注文と取引が互いを定義に使う) は定義依存が非循環である",
    verdict := .counterexample,
    evidence := .leanRefutes "Glossary.Broken.draft_is_cyclic"
      (Acyclic (DefDep Broken.draft)) Broken.draft_is_cyclic },
  { about := [order, customer, transaction],
    statement := "修正した用語集は、ID が一意で、参照先が存在し、定義依存が非循環である",
    verdict := .proved,
    evidence := .lean "Glossary.Broken.repaired_wellFormed"
      (WellFormed Broken.repaired) Broken.repaired_wellFormed },
  { about := [confirmedOrder],
    statement := "確定注文は空である: どんな注文の型と支払いの意味でも、定義を満たす注文は存在しない",
    verdict := .proved,
    evidence := .lean "Glossary.EmptyConcept.confirmedOrder_empty"
      (∀ (Order : Type) (Paid : Order → Prop), ¬ ∃ o, EmptyConcept.ConfirmedOrder Paid o)
      (fun _ Paid => EmptyConcept.confirmedOrder_empty Paid) },
  { about := [order, shipment, cancellation],
    statement := "到達できるどの状態でも、発送かキャンセルができるか、終端である (議論が挙げた網羅性)",
    verdict := .proved,
    evidence := .holds (coverage "discussionCoverage") },
  { about := [order, payment, shipment, cancellation],
    statement := "到達できるどの状態でも、すべての操作について許可か禁止かが決まっている",
    verdict := .counterexample,
    evidence := .violated (coverage "everyOpDecided") },
  { about := [order, payment, cancellation],
    statement := "支払い済みで発送前の注文はキャンセルできるか",
    verdict := .undecided,
    evidence := .question [coverage "paidCancelDecided"],
    industry := some (.gap "調べた範囲では事業者ごとに扱いがばらばらで、決まった答えがない") },
  { about := [payment, authorization, capture],
    statement := "「支払い済み」を 1 つの述語にすると、与信の意味と売上確定の意味の両方には合わせられない",
    verdict := .proved,
    evidence := .lean "Glossary.PaidStages.paid_is_not_one_notion"
      (¬ ∃ paid : PaidStages.Stage → Bool,
        (∀ s, paid s = PaidStages.atLeastAuthorized s) ∧ (∀ s, paid s = PaidStages.atLeastCaptured s))
      PaidStages.paid_is_not_one_notion },
  { about := [order, authorization, capture, shipment],
    statement := "与信で発送し、発送と同時に売上を確定するなら、発送した注文の代金は回収できる",
    verdict := .proved,
    evidence := .holds (stages "capture_at_ship" "shippedIsCollectible") },
  { about := [order, authorization, capture, shipment],
    statement := "与信で発送し、売上の確定を後に回しても、発送した注文の代金は回収できる",
    verdict := .counterexample,
    evidence := .violated (stages "capture_after_ship" "shippedIsCollectible") },
  { about := [order, payment],
    statement := "支払い済みの注文をもう一度支払えるか",
    verdict := .undecided,
    evidence := .question [coverage "paidPayDecided"],
    industry := some (.answered "カード決済では冪等キーで二重の支払いを防ぐのが標準で、現金系は手作業で返金している") }
]

-- この用語集では停止の場面を扱わない。このリポジトリの停止の場面は、映画館の用語集で検査モデルにした。
def book : Book Term Ctx := { title := "注文", terms, claims, stopScene := .inBook "映画館のチケット販売" }

theorem book_check : book.check = true := by decide

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)

end Glossary.OrderBook
