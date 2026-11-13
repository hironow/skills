/-!
# 実験 2: 空の概念

「確定注文とは、支払いが完了しており、かつ支払いが未完了の注文である」。
この定義を満たす注文は、注文の型や支払いの意味が何であっても 1 つも存在しない。
-/

namespace Glossary.EmptyConcept

def ConfirmedOrder {Order : Type} (Paid : Order → Prop) (o : Order) : Prop :=
  Paid o ∧ ¬ Paid o

/-- 確定注文は空。有限のモデルに限らない。 -/
theorem confirmedOrder_empty {Order : Type} (Paid : Order → Prop) :
    ¬ ∃ o, ConfirmedOrder Paid o :=
  fun ⟨_, hPaid, hNotPaid⟩ => hNotPaid hPaid

/-! ## 型を閉じると空白が消える (議論の「落とし穴」)

支払いを 2 値にすると「どちらかである」が証明できてしまい、
「決済結果が不明」という現実の状態を書けなくなる。3 値にすると証明できなくなる。 -/

theorem two_valued_hides_unknown {Order : Type} (paid : Order → Bool) :
    ∀ o, paid o = true ∨ paid o = false := by
  intro o
  cases paid o <;> simp

inductive PaymentStatus where
  | paid | unpaid | unknown
  deriving DecidableEq, Repr

theorem three_valued_keeps_unknown :
    ¬ ∀ (status : Unit → PaymentStatus) (o : Unit),
      status o = .paid ∨ status o = .unpaid := by
  intro h
  cases h (fun _ => .unknown) () <;> contradiction

/-- 修正した定義は空でない: 支払い済みの注文があるモデルが存在する。 -/
def ConfirmedOrder' {Order : Type} (status : Order → PaymentStatus) (o : Order) : Prop :=
  status o = .paid

theorem confirmedOrder'_inhabited :
    ∃ (status : Unit → PaymentStatus) (o : Unit), ConfirmedOrder' status o :=
  ⟨fun _ => .paid, (), rfl⟩

end Glossary.EmptyConcept
