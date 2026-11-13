/-!
# Take 4: 3 つのルールは同時に成り立たない

- 遮断中は発券しない (Take 1 の性質)。
- 履行期限までに発券する (顧客の目的を守る)。
- 緊急メンテナンスの遮断が履行期限まで続く (起こりうる環境)。
-/

namespace Glossary.Deadline

theorem rules_conflict (deadline : Nat) (blocked : Nat → Prop) (issuedAt : Option Nat)
    (noIssueWhileBlocked : ∀ t, issuedAt = some t → ¬ blocked t)
    (goalKept : ∃ t, t < deadline ∧ issuedAt = some t)
    (outage : ∀ t, t < deadline → blocked t) : False := by
  obtain ⟨t, hlt, hissued⟩ := goalKept
  exact noIssueWhileBlocked t hissued (outage t hlt)

end Glossary.Deadline
