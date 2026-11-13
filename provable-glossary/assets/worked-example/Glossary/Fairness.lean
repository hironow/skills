/-!
# 実験 5: 公平性 (Experiment 005)

上映回 S1 (10:00) が中止。振替に使える席は 13:00 に 2 席、16:00 に 1 席。
A・B は 13:00 だけ、C は 13:00 か 16:00、D は 13:00 の新規購入を望む。
ここで証明するのは「何が不可能で、何が可能か」。誰を優先すべきかは証明しない。
-/

namespace Glossary.Fairness

inductive Customer where
  | A | B | C | D
  deriving DecidableEq, Repr

inductive Seat where
  | s13a | s13b | s16a
  deriving DecidableEq, Repr

def acceptable : Customer → Seat → Bool
  | .C, _ => true
  | _, .s16a => false
  | _, _ => true

/-- 割当て。席をもらえない顧客は `none`。 -/
abbrev Alloc := Customer → Option Seat

/-- 有効な割当て: 受け入れ可能な席だけを渡し、1 つの席を 2 人に渡さない。 -/
def Valid (p : Alloc) : Prop :=
  (∀ c s, p c = some s → acceptable c s = true) ∧
  (∀ c₁ c₂ s, p c₁ = some s → p c₂ = some s → c₁ = c₂)

def Served (p : Alloc) (c : Customer) : Prop := p c ≠ none

theorem seat_of_served {p : Alloc} {c : Customer} (h : Served p c) : ∃ s, p c = some s := by
  unfold Served at h
  cases hc : p c with
  | none => exact absurd hc h
  | some s => exact ⟨s, rfl⟩

/-- 4 人全員の希望は満たせない。 -/
theorem not_all_four (p : Alloc) (hv : Valid p) : ¬ ∀ c, Served p c := by
  intro h
  obtain ⟨hacc, hinj⟩ := hv
  obtain ⟨a, ha⟩ := seat_of_served (h .A)
  obtain ⟨b, hb⟩ := seat_of_served (h .B)
  obtain ⟨d, hd⟩ := seat_of_served (h .D)
  cases a <;> cases b <;> cases d <;>
    first
    | exact absurd (hacc _ _ ha) (by decide)
    | exact absurd (hacc _ _ hb) (by decide)
    | exact absurd (hacc _ _ hd) (by decide)
    | exact absurd (hinj _ _ _ ha hb) (by decide)
    | exact absurd (hinj _ _ _ ha hd) (by decide)
    | exact absurd (hinj _ _ _ hb hd) (by decide)

/-- 議論が示した割当て: A・B は 13:00、C は 16:00。 -/
def rescue : Alloc
  | .A => some .s13a
  | .B => some .s13b
  | .C => some .s16a
  | .D => none

/-- 中止の影響を受けた A・B・C は全員振り替えられる。 -/
theorem abc_possible : Valid rescue ∧ Served rescue .A ∧ Served rescue .B ∧ Served rescue .C := by
  refine ⟨⟨?_, ?_⟩, by simp [Served, rescue], by simp [Served, rescue], by simp [Served, rescue]⟩
  · intro c s h
    cases c <;> cases s <;> simp_all [rescue, acceptable]
  · intro c₁ c₂ s h₁ h₂
    cases c₁ <;> cases c₂ <;> cases s <;> simp_all [rescue]

/-- A・B・C を全員振り替えるなら、C は必ず 16:00 になる。 -/
theorem c_must_take_16 (p : Alloc) (hv : Valid p)
    (hA : Served p .A) (hB : Served p .B) (hC : Served p .C) : p .C = some .s16a := by
  obtain ⟨hacc, hinj⟩ := hv
  obtain ⟨a, ha⟩ := seat_of_served hA
  obtain ⟨b, hb⟩ := seat_of_served hB
  obtain ⟨c, hc⟩ := seat_of_served hC
  cases a <;> cases b <;> cases c <;>
    first
    | exact hc
    | exact absurd (hacc _ _ ha) (by decide)
    | exact absurd (hacc _ _ hb) (by decide)
    | exact absurd (hinj _ _ _ ha hb) (by decide)
    | exact absurd (hinj _ _ _ ha hc) (by decide)
    | exact absurd (hinj _ _ _ hb hc) (by decide)

/-- 回復可能性の喪失: C が 13:00 の席を取ると、A と B の両方は振り替えられない。 -/
theorem c_at_13_costs (p : Alloc) (hv : Valid p)
    (hC : p .C = some .s13a ∨ p .C = some .s13b) : ¬ (Served p .A ∧ Served p .B) := by
  intro ⟨hA, hB⟩
  have h16 := c_must_take_16 p hv hA hB (by unfold Served; rcases hC with h | h <;> simp [h])
  rcases hC with h | h <;> simp [h] at h16

/-- 新規購入の D に席を渡すと、A・B・C の全員は振り替えられない。 -/
theorem d_served_costs_protected (p : Alloc) (hv : Valid p) (hD : Served p .D) :
    ¬ (Served p .A ∧ Served p .B ∧ Served p .C) := by
  intro ⟨hA, hB, _⟩
  obtain ⟨hacc, hinj⟩ := hv
  obtain ⟨a, ha⟩ := seat_of_served hA
  obtain ⟨b, hb⟩ := seat_of_served hB
  obtain ⟨d, hd⟩ := seat_of_served hD
  cases a <;> cases b <;> cases d <;>
    first
    | exact absurd (hacc _ _ ha) (by decide)
    | exact absurd (hacc _ _ hb) (by decide)
    | exact absurd (hacc _ _ hd) (by decide)
    | exact absurd (hinj _ _ _ ha hb) (by decide)
    | exact absurd (hinj _ _ _ ha hd) (by decide)
    | exact absurd (hinj _ _ _ hb hd) (by decide)

end Glossary.Fairness
