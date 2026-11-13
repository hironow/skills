/-!
# 「支払い済み」は 1 つの概念ではない

業界の実務では、「支払い済み」は少なくとも 2 つの別の状態を指す。
与信済み (カード会社が枠を押さえた) と、売上確定済み (事業者が請求を確定した) である。
1 つの述語「支払い済み」が、両方の意味と同時に一致することはない。
-/

namespace Glossary.PaidStages

/-- 代金の段階。 -/
inductive Stage where
  | notPaid | authorized | captured | settled
  deriving DecidableEq, Repr

/-- 与信までは済んでいる。 -/
def atLeastAuthorized : Stage → Bool
  | .notPaid => false
  | _ => true

/-- 売上の確定までは済んでいる。 -/
def atLeastCaptured : Stage → Bool
  | .notPaid => false
  | .authorized => false
  | _ => true

/-- 「支払い済み」を 1 つの述語にすると、与信の意味と売上確定の意味の両方には合わせられない。 -/
theorem paid_is_not_one_notion :
    ¬ ∃ paid : Stage → Bool,
      (∀ s, paid s = atLeastAuthorized s) ∧ (∀ s, paid s = atLeastCaptured s) := by
  intro ⟨_, h1, h2⟩
  exact absurd ((h1 .authorized).symm.trans (h2 .authorized)) (by decide)

end Glossary.PaidStages
