# Scene patterns

Use only the patterns whose roles exist in the domain. Each entry gives the question, the properties to protect, how to proceed, and the example file. Example paths are relative to `assets/worked-example/`. Do not copy the example: rewrite it in the domain's words.

## Contents

1. Glossary well-formedness
2. Empty concepts and overloaded terms
3. Specification gaps
4. A stop versus work in progress (whenever anything is in flight)
5. Stages of the external confirmation
6. Supply cancellation and reallocation
7. Obligations, responsibility, authority
8. Deadline and fallback channel
9. Autonomy and the human boundary
10. Timed guarantee
11. Stop policy

Keep models small. Start with one resource and two parties. Add more only after counterexamples stop appearing, and confirm once that a larger size does not change the conclusion.

---

## 1. Glossary well-formedness

- **Question**: Do the definitions go round in circles? Does every reference exist?
- **How**: Write the draft as given and let the checker reject it. Prove the cycle in Lean. Prove that the repaired version passes. Move statements like "a customer places orders" from definitional dependencies to associations (`assoc`).
- **Claims**: "The draft glossary has acyclic definitions" (counterexample). "The repaired glossary is well-formed" (proved).
- **Example**: `Glossary/Broken.lean`, `Glossary/OrderBook.lean`

## 2. Empty concepts and overloaded terms

- **Question**: Is there a term whose definition nothing can satisfy? Does one word name several different states?
- **How (empty)**: State the definition as a proposition and prove that no object satisfies it in any model.
- **How (overloaded)**: Write two candidate meanings as functions and prove that no single predicate agrees with both. Overloading usually shows up only after industry research ("paid" turned out to mean authorized, captured, or settled).
- **Example**: `Glossary/EmptyConcept.lean`, `Glossary/PaidStages.lean`

## 3. Specification gaps

- **Question**: Do the written business rules decide every operation in every reachable state?
- **How**: Copy the rules into a table that returns allowed, forbidden, or unspecified. Leave unwritten combinations unspecified; do not fill them by guessing. Show with a counterexample that an unspecified combination is reachable, and make each one a question.
- **Pitfall**: The weak coverage property "some operation is possible, or the state is terminal" holds even when gaps exist. Strengthen it to "every operation is decided".
- **A state nothing leads to.** When the code or the rules name a state that no operation ever sets (a `REFUNDED` status with no code path to it), no model can witness it. Record it as a question with `.question []` and put the evidence (where you looked) in the term's definition.
- **Example**: `Spec/order_coverage.qnt`

## 4. A stop versus work in progress

The central pattern. Write it whenever anything is in flight when the system stops, whatever stops it: an emergency stop the system takes on its own, a person, or a dependency that fails. If nothing is in flight, do not invent the scene; put `<!-- stop-scene: none; <reason> -->` in the README instead (see SKILL.md).

- **Question**: When the system stops accepting work, what happens to transactions that hold a resource, wait for an external confirmation, or wait for issuance?
- **Properties**:
  - Exclusivity: at most one party is entitled to a resource. In a domain with no scarce resource, use at most one execution of each external effect instead: a request resent after recovery must not pay, ship or notify twice. Give each request an identity the outside party can recognise, and reconcile with it after the stop rather than resending blindly.
  - Preservation: a transaction whose external confirmation succeeded is always tracked in a state that leads to issuance or to a refund.
  - Meaning of the stop: once the stop is complete, no new entitlement is issued.
  - Planned stop: it waits for work in progress, so no confirmation is left unresolved during it.
- **Write preservation as a property of the state, not as "already resolved".** An invariant is checked in every reachable state, including the state just before a resolving action is taken. "Nothing is left unresolved" is therefore violated in every design. State instead that the transaction is in a tracked state from which a resolving action is enabled ("there is a next step from here"), or that it is in one of the named tracked states. "It is eventually resolved" is a temporal property (pattern 7).
- **How**: Compare three designs.
  1. Naive: issuance looks only at "confirmation succeeded". After a hold expires, another party takes the resource and both get entitlements.
  2. Guard issuance on the hold. Double issuance disappears, but a transaction remains that is confirmed and has neither an entitlement nor the resource.
  3. Introduce a new concept, "confirmed, issuance pending". Once confirmation starts, the hold does not expire, and a refund can resolve it.
- **The question that always appears**: When is the sale "complete": at the external confirmation or at issuance? The confirmation cannot be stopped, so choosing it means sales complete after the stop.
- **Example**: `Spec/emergency_sale.qnt`. A minimal version in the shared roles is `assets/template/Spec/starter.qnt`.

## 5. Stages of the external confirmation

- **Question**: Is the confirmation one step, or does it have intermediate stages (a reserved amount, for instance) that expire?
- **How**: Put the stages and their expiry in the state. Compare two orders of "hand over the goods" and "finalise the confirmation". Finalising at hand-over keeps the amount collectible; finalising later lets the intermediate stage expire.
- **Example**: `Spec/payment_stages.qnt`

## 6. Supply cancellation and reallocation

Use only if the industry actually reallocates. Check in step 2.

- **Question**: When cancelled entitlements are honoured with other resources, can everyone be served? Does serving in arrival order lose someone who could have been served?
- **How**: Prove impossibility (more parties than resources) and existence (this allocation serves everyone) in Lean. With a handful of parties and resources, case analysis on the concrete types is enough in plain Lean. Show with a counterexample that first-come-first-served loses the "everyone can still be served" state using only valid steps. A policy that protects that state shuts out new customers; record that cost as a claim.
- **Left to the business**: which policy is fair. The proofs do not choose.
- **Example**: `Glossary/Fairness.lean`, `Spec/rebooking.qnt`

## 7. Obligations, responsibility, authority

- **Question**: If supply is cancelled after the entitlement was issued, whose job is it? Does that owner have the authority to resolve it?
- **How**: Compare in stages: no obligation is created (nobody's job) → an obligation is created (no owner) → an owner is assigned (lacks authority) → a hand-off is added.
- **Liveness**: "the obligation is eventually resolved" is a temporal property. It fails if the emergency stop never ends. It holds once you assume "recovery eventually happens". Write the assumption into the claim.
- **General theorem**: if every unresolved state has a step that strictly decreases a measure, a resolved state is reachable. `Glossary/Progress.lean` works for any domain and ships in the template.
- **Example**: `Spec/obligation.qnt`, `Glossary/Progress.lean`

## 8. Deadline and fallback channel

- **Question**: If the emergency stop lasts until the deadline, is the customer's purpose still met?
- **How**: Prove in Lean that these three cannot all hold: no issuance during the stop, issuance before the deadline, the stop lasts until the deadline. Allowing a fallback channel meets the purpose but issues during the stop. Make the choice a question.
- **Example**: `Glossary/Deadline.lean`, `Spec/deadline.qnt`

## 9. Autonomy and the human boundary

- **Question**: Which decisions may the system make alone, and which go to a person?
- **Definition**: A decision is determined by policy when every best choice under the policy gives the same outcome. The system may execute it. Otherwise the policy does not say how to choose.
- **How**: Prove "determined" for the scene with enough resources and "not determined" for the scene without. Show with a counterexample that a design that never escalates picks arbitrarily. A design that escalates settles the determined part itself and hands over only the rest.
- **For the emergency stop**: stopping may be automatic (it can be undone). Resuming, and anything irreversible, is a human decision.
- **Example**: `Glossary/Autonomy.lean`, `Spec/autonomy.qnt`

## 10. Timed guarantee

- **Question**: Under which settings can the operator promise "once you start confirming, the resource is yours"?
- **How**: Advance time in ticks. Make the hold length, the extension at confirmation start, the confirmation's maximum delay, and the stop's maximum length parameters. Check the whole grid of settings with TLC and tabulate the results. Read the condition off the table, then confirm it outside the grid and with more parties.
- **Condition found in the example**: the extension must be at least the confirmation's maximum delay; if hold clocks keep running during a stop, add the stop's maximum length. Re-acquiring a lost resource does not help the guarantee, and the base hold length does not matter.
- **Pitfall**: a counter with no upper bound makes the state space infinite and TLC never finishes. Bound every number.
- **Example**: `experiments/scale-003/timed_sale.qnt`, `experiments/scale-003/truth_table.py`, `experiments/guarantee-007/`

## 11. Stop policy

For step 7: closing a gap the industry has not answered.

- **How**:
  1. Write the rules as clauses: what stops and what does not, clocks, confirmed-but-not-issued transactions, entitlements already issued, refunds, who decides.
  2. Map each rule to one switch in the model.
  3. Choose about three properties. The example uses no impostor, no lockout, no limbo.
  4. Show the draft keeps every property in all states. Show that each variant with one rule removed breaks a property.
  5. Compare the naive answers with each other (keeping leaked tickets valid and invalidating them all each break a different property).
  6. Replay a real incident's timeline as a `run`, and tabulate what the draft would have settled at each moment.
- **Limits to state**: the model is built to fit the rules, so "removing a rule breaks a property" partly follows from how it was built. About a real incident, say that the model simplifies the published wording and makes no claim about what happened on site.
- **Example**: `Spec/outage_policy.qnt`
