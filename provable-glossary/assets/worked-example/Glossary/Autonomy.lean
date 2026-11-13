import Glossary.Fairness

/-!
# Experiment 006: 方針で決まる判断と、決まらない判断

方針のもとで最善の選択肢がどれも同じ結果を与えるなら、判断は方針だけで決まる。
システムはどれを選んでも結果が同じなので、自分で実行できる。
最善の選択肢の間で結果が違うなら、方針は選び方を決めていない。
-/

namespace Glossary.Autonomy

open Fairness

/-- 方針で決まる: 最善の選択肢は、どれも同じ結果を与える。 -/
def Determined {O R : Type} (optimal : O → Prop) (outcome : O → R) : Prop :=
  ∀ p q, optimal p → optimal q → outcome p = outcome q

/-- 結果: 誰が席を得るか。 -/
def whoIsServed (p : Alloc) : Customer → Bool := fun c => (p c).isSome

theorem isSome_of_served {p : Alloc} {c : Customer} (h : Served p c) : (p c).isSome = true := by
  obtain ⟨s, hs⟩ := seat_of_served h
  simp [hs]

theorem isSome_false_of_not_served {p : Alloc} {c : Customer} (h : ¬ Served p c) :
    (p c).isSome = false := by
  unfold Served at h
  cases hc : p c with
  | none => rfl
  | some s => exact absurd (by simp [hc]) h

/-! ## 席が足りる場面 (13:00 に 2 席) -/

/-- 最善: 保護対象の A・B・C を全員振り替える。 -/
def RescuesAll (p : Alloc) : Prop := Valid p ∧ Served p .A ∧ Served p .B ∧ Served p .C

theorem who_of_rescuesAll {p : Alloc} (h : RescuesAll p) :
    whoIsServed p = fun c => decide (c ≠ .D) := by
  obtain ⟨hv, hA, hB, hC⟩ := h
  have hD : ¬ Served p .D := fun hD => d_served_costs_protected p hv hD ⟨hA, hB, hC⟩
  funext c
  cases c
  · simpa [whoIsServed] using isSome_of_served hA
  · simpa [whoIsServed] using isSome_of_served hB
  · simpa [whoIsServed] using isSome_of_served hC
  · simpa [whoIsServed] using isSome_false_of_not_served hD

/-- 席が足りる場面では、誰が席を得るかは方針だけで決まる。 -/
theorem enough_determined : Determined RescuesAll whoIsServed := by
  intro p q hp hq
  rw [who_of_rescuesAll hp, who_of_rescuesAll hq]

/-! ## 席が足りない場面 (13:00 に 1 席) -/

def ValidShort (p : Alloc) : Prop := Valid p ∧ ∀ c, p c ≠ some .s13b

/-- A と B の両方は振り替えられない。 -/
theorem short_cannot_serve_both (p : Alloc) (hv : ValidShort p) :
    ¬ (Served p .A ∧ Served p .B) := by
  intro ⟨hA, hB⟩
  obtain ⟨⟨hacc, hinj⟩, hno⟩ := hv
  obtain ⟨a, ha⟩ := seat_of_served hA
  obtain ⟨b, hb⟩ := seat_of_served hB
  cases a <;> cases b <;>
    first
    | exact absurd ha (hno _)
    | exact absurd hb (hno _)
    | exact absurd (hacc _ _ ha) (by decide)
    | exact absurd (hacc _ _ hb) (by decide)
    | exact absurd (hinj _ _ _ ha hb) (by decide)

/-- 最善: C と、A か B のどちらかを振り替える (2 人。3 人は上の定理で不可能)。 -/
def BestShort (p : Alloc) : Prop := ValidShort p ∧ Served p .C ∧ (Served p .A ∨ Served p .B)

def pickA : Alloc
  | .A => some .s13a
  | .C => some .s16a
  | _ => none

def pickB : Alloc
  | .B => some .s13a
  | .C => some .s16a
  | _ => none

theorem pickA_best : BestShort pickA := by
  refine ⟨⟨⟨?_, ?_⟩, ?_⟩, by simp [Served, pickA], Or.inl (by simp [Served, pickA])⟩
  · intro c s h; cases c <;> cases s <;> simp_all [pickA, acceptable]
  · intro c₁ c₂ s h₁ h₂; cases c₁ <;> cases c₂ <;> cases s <;> simp_all [pickA]
  · intro c; cases c <;> simp [pickA]

theorem pickB_best : BestShort pickB := by
  refine ⟨⟨⟨?_, ?_⟩, ?_⟩, by simp [Served, pickB], Or.inr (by simp [Served, pickB])⟩
  · intro c s h; cases c <;> cases s <;> simp_all [pickB, acceptable]
  · intro c₁ c₂ s h₁ h₂; cases c₁ <;> cases c₂ <;> cases s <;> simp_all [pickB]
  · intro c; cases c <;> simp [pickB]

/-- 席が足りない場面では、誰が席を得るかは方針で決まらない。 -/
theorem short_not_determined : ¬ Determined BestShort whoIsServed := by
  intro h
  have := congrFun (h pickA pickB pickA_best pickB_best) .A
  simp [whoIsServed, pickA, pickB] at this

end Glossary.Autonomy
