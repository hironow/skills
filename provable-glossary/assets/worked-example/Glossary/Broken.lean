import Glossary.Core

/-!
# 実験 1: 壊れた用語集は検査で落ちる (Red)

議論に出てきた「注文 → 取引 → 注文」の例。検査が落ちること、
そして本当に循環していること (誤検知でないこと) を示す。
-/

namespace Glossary.Broken

inductive Term where
  | order | customer | transaction
  deriving DecidableEq, Repr

inductive Ctx where
  | sales
  deriving DecidableEq, Repr

open Term

def draftCustomer : Entry Term Ctx :=
  { id := customer, context := .sales, gloss := "注文を行う主体", defDeps := [order] }

def draftTransaction : Entry Term Ctx :=
  { id := transaction, context := .sales, gloss := "注文によって成立する商業上の活動",
    defDeps := [order] }

def draftOrder : Entry Term Ctx :=
  { id := order, context := .sales, gloss := "顧客が商品を購入するために作成する取引",
    defDeps := [customer, transaction] }

/-- 議論の草稿のまま。注文と取引が互いの定義に必要。 -/
def draft : List (Entry Term Ctx) := [draftCustomer, draftTransaction, draftOrder]

theorem draft_rejected : check draft = false := by decide

/-- 誤検知ではない: 注文 → 取引 → 注文 という道がある。 -/
theorem draft_is_cyclic : ¬ Acyclic (DefDep draft) := by
  intro h
  apply h order
  refine .tail (.single (b := transaction) ?_) ?_
  · exact ⟨draftOrder, .tail _ (.tail _ (.head _)), rfl, by decide⟩
  · exact ⟨draftTransaction, .tail _ (.head _), rfl, by decide⟩

/-- 行き先のない参照: 「取引」を使うが、定義した項目がない。 -/
def dangling : List (Entry Term Ctx) := [
  { id := order, context := .sales, gloss := "顧客が作成する取引", defDeps := [transaction] }
]

theorem dangling_rejected : check dangling = false := by decide

/-- 同じ ID を 2 回定義している。 -/
def duplicated : List (Entry Term Ctx) := [
  { id := order, context := .sales, gloss := "購入の申し込み" },
  { id := order, context := .sales, gloss := "配送の指示" }
]

theorem duplicated_rejected : check duplicated = false := by decide

/-- 修正版。顧客と取引を、注文を使わずに定義する。
「顧客は注文を行う」は定義依存ではなく関連として残す (循環してよい)。 -/
def repaired : List (Entry Term Ctx) := [
  { id := customer, context := .sales, gloss := "商品を買う主体", assoc := [order] },
  { id := transaction, context := .sales, gloss := "対価と引き換えに権利を渡す商業上の活動" },
  { id := order, context := .sales, gloss := "顧客が商品を購入するために作成する取引",
    defDeps := [customer, transaction], assoc := [customer] }
]

theorem repaired_wellFormed : WellFormed repaired := check_sound _ (by decide)

end Glossary.Broken
