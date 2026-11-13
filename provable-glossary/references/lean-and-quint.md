# Writing glossaries, claims and models

## Contents

1. A glossary file
2. Claims and evidence
3. Registering a glossary
4. Quint models and scripted tests
5. Plain Lean first; mathlib only in special cases
6. Pitfalls

## 1. A glossary file

One file per glossary: `Glossary/<Domain>.lean`. Start from `assets/template/Glossary/Starter.lean`.

```lean
import Glossary.Claim

namespace Glossary.Clinic

inductive Term where
  | patient | slot | slotHold
  deriving DecidableEq, Repr

inductive Ctx where
  | booking | payment
  deriving DecidableEq, Repr

open Term

def terms : List (Entry Term Ctx) := [
  { id := patient, label := "Patient", context := .booking, gloss := "A person who books a consultation" },
  { id := slot, label := "Slot", context := .booking, gloss := "One consultation time of one doctor" },
  { id := slotHold, label := "Slot hold", context := .booking,
    gloss := "A time-limited reservation of a slot for one patient", defDeps := [patient, slot] }
]

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)
```

- List entries in the order they are defined. `defDeps` may only name earlier entries; that is how the checker rules out cycles.
- `assoc` may name any entry, including later ones.
- `label` and `gloss` are in the user's language. IDs are identifiers.
- To record a broken draft, write it as a second list and prove what is wrong with it (`assets/worked-example/Glossary/Broken.lean`).

## 2. Claims and evidence

```lean
def clinic (main invariant : String) : QuintRef :=
  { file := "Spec/clinic.qnt", main, invariant }

def claims : List (Claim Term) := [
  { about := [slot, slotHold],
    statement := "A slot is never booked by two patients",
    verdict := .proved, evidence := .holds (clinic "guarded" "exclusive") },
  { about := [slotHold],
    statement := "Can a hold be extended while payment is in progress?",
    verdict := .undecided, evidence := .question [clinic "guarded" "noOrphan"] }
]

def book : Book Term Ctx := { title := "Clinic booking", terms, claims }

theorem book_check : book.check = true := by decide
```

| Evidence | Verdict | What `just check` does |
|---|---|---|
| `.lean name prop proof` | proved | The file does not compile without the proof |
| `.leanRefutes name prop proof` | counterexample | Same, for a proof of `¬ prop` |
| `.holds ref` | proved | TLC explores every reachable state of `ref.main` and the invariant must hold |
| `.violated ref` | counterexample | The Quint simulator must find a violation without a script |
| `.question refs` | undecided | Each witness in `refs` must be violated (it shows the gap is reachable) |

- `book_check` fails when a claim mentions a term that is not in the glossary, or when its verdict does not match its evidence.
- `.question []` (no witness) is allowed. Use it for a question the models do not cover, such as a legal deadline. Prefer a witness whenever a model can show the gap.
- For a temporal property set `temporal := true` in the `QuintRef`; TLC checks it.
- Write the claim as the statement being tested, in the positive. A counterexample verdict then reads "this does not hold".
- Add a line to `Audit.lean` for every theorem cited as evidence. It prints the axioms the theorem depends on.

## 3. Registering a glossary

In `Glossary/Registry.lean`, import the file and add `<Domain>.book.view labels` to `books`. Add the import to `Glossary.lean` too. Then `just generate`. It rewrites the whole folder and removes documents that are no longer generated, so a deleted glossary leaves nothing stale behind.

## 4. Quint models and scripted tests

- One file per scene under `Spec/`. Put the shared machinery in a base module with `const` switches, and one small module per design variant:

```quint
module guarded {
  import clinic(GUARDED = true).*
}
```

- A scripted test is a `run` whose name ends in `Test`. List the module in `Spec/tests.txt` as `<file> <module>`. Use scripted tests to pin a specific trace (the counterexample from the discussion, an incident timeline).
- **A scripted test must not pass through a random choice.** If an action picks a value with `nondet`, a run that calls it is not reproducible: it passes on some seeds and fails on others. Give the action a parameter (`detectAs(real: bool)`) and pass the value explicitly in every run. The gate runs each scripted test 20 times so that such a run fails every time instead of occasionally.
- A `.violated` claim needs no script. The gate first lets the simulator look for the violation; if it finds none, TLC searches every reachable state, and the claim passes when TLC finds it (the gate then prints "found by TLC; too deep for the simulator"). Pin such a deep counterexample with a scripted test ending in `.expect`, so a reader can see the trace.

### Liveness: "it is eventually resolved"

An invariant says nothing bad is ever reached. "Every commitment is eventually resolved" is a different kind of claim: a temporal property, checked by TLC over infinite runs. It always needs a fairness assumption, because a run in which nobody ever acts is allowed and resolves nothing. Write the assumption as the left side of an implication, so the claim states what it relies on.

```quint
module liveness {
  var state: str   // "Waiting" until the commitment is resolved, then "Done"
  var up: bool     // false while the system is stopped

  action init = all { state' = "Waiting", up' = true }
  action stop = all { up, up' = false, state' = state }
  action recover = all { not(up), up' = true, state' = state }
  action resolve = all { up, state == "Waiting", state' = "Done", up' = up }
  action step = any { stop, recover, resolve }

  val vars = (state, up)   // every state variable, in a tuple
  temporal resolves = always(state == "Waiting" implies eventually(state == "Done"))

  // resolve is enabled only while the system runs, and stop can interrupt it again and again:
  // weak fairness is not enough for it, strong fairness is. recover stays enabled while stopped.
  temporal fairStrong = strongFair(resolve, vars) and weakFair(recover, vars)
  temporal fairWeak = weakFair(resolve, vars) and weakFair(recover, vars)
  temporal Liveness = fairStrong implies resolves         // holds
  temporal LivenessWeak = fairWeak implies resolves       // violated: stop, recover, stop, ...
}
```

- `weakFair(a, vars)`: if `a` stays enabled forever, it is eventually taken. Enough for an action nothing else can disable, such as `recover` while stopped.
- `strongFair(a, vars)`: if `a` is enabled again and again, it is eventually taken. Needed when another action (a stop) can disable it each time before it runs.
- Without any fairness, `resolves` is violated too: nothing forces `resolve` to be taken at all. That counterexample says nothing about the design; add the assumption instead of reporting it.
- An assumption about the world, such as "recovery eventually happens", is also fairness (`weakFair(recover, vars)` above). Drop it and the claim becomes "if the stop never ends, nothing is resolved", which is often worth recording as a counterexample of its own.
- Cite it with `temporal := true` in the `QuintRef`, for example `{ file := "Spec/liveness.qnt", main := "liveness", invariant := "Liveness", temporal := true }`. The gate runs TLC with `--temporal` for both `.holds` and `.violated`. The cinema example is `Spec/obligation.qnt` (`Liveness`, `LivenessGivenRecovery`).

## 5. Plain Lean first; mathlib only in special cases

Projects use plain Lean 4 (core and `Std`) with no external packages. mathlib is a heavy dependency: several GB of download and build cache per project, a slower gate, and a version to keep in step with the toolchain. The glossaries this method produces are finite and concrete, and their theorems rarely need a library. So the default is: **do not add mathlib.**

### Proving carefully without a library

With no library to lean on, the risk moves from "the proof is long" to "the statement is not what you meant". Guard against that.

- **Write the statement first, in the domain's terms, and read it back.** A theorem that is easy to prove because it says less than intended is worse than no theorem. Do not weaken a statement to get it through; if it will not go through, the claim may be false. Look for a counterexample and, if you find one, record the claim as a counterexample.
- **Keep the objects finite and explicit.** Small inductive types for parties and resources, `Bool`-valued predicates, concrete functions. Then `decide`, `cases`, and `simp` carry most proofs.
- **Quantify over the real domain, not over a list you wrote by hand.** "For every allocation `p`" is a statement about all allocations. If you instead enumerate allocations in a list and check the list, you must also prove the list is complete; otherwise the theorem is only about your list.
- **Use every hypothesis.** A theorem whose hypotheses are not needed by its proof, or whose conclusion is true of anything, says nothing. Delete it rather than count it.
- **Exhaust cases visibly.** A proof by `cases a <;> cases b <;> first | ... | ...` is fine: Lean rejects it if any case is left open. State in a comment what the cases are.
- **Assumptions go in the statement.** If a result needs "recovery eventually happens", it is a hypothesis of the theorem and a phrase in the claim, not a silent premise.
- **Check what the proof rests on.** Add the theorem to `Audit.lean`; `just lean-check` prints its axioms and rejects `sorryAx`. `propext`, `Classical.choice` and `Quot.sound` are the standard ones.
- **Prefer a general lemma once over the same argument many times.** `Glossary/Progress.lean` and `acyclic_of_rank` in `Glossary/Core.lean` are examples: short, plain Lean, reusable in any domain. From inside `namespace Glossary.<Domain>`, refer to them as `Progress.Reach`, `Progress.resolvable`, and `acyclic_of_rank` (import `Glossary.Progress` first).

Worked examples in plain Lean: `assets/worked-example/Glossary/Fairness.lean` (impossibility and existence over four parties and three resources, by case analysis), `Autonomy.lean`, `Deadline.lean`, `EmptyConcept.lean`.

### When you do not know how to prove something: read mathlib online

mathlib is the best reference for how a statement is usually phrased and proved, and it can be read without installing it.

- Search by name or by shape: Loogle (https://loogle.lean-lang.org), LeanSearch (https://leansearch.net), or the documentation index (https://leanprover-community.github.io/mathlib4_docs/).
- Read the source on GitHub (https://github.com/leanprover-community/mathlib4). The docs pages link each declaration to its source line.
- Take the **idea**: the right statement, the induction to use, the auxiliary lemma. Then restate what you need locally, as a small lemma with its own proof in plain Lean. Name the mathlib declaration you followed in a comment, so the next reader can compare.
- Check versions. A lemma's name or signature in today's mathlib may differ from what you remember, and core Lean may already have it under another name. If the web is unavailable, say so and prove the lemma from first principles.
- Do not paste large stretches of mathlib into the project. If a proof would need that, it is the special case below.

For example, to show that a relation with a strictly decreasing rank has no cycle, the mathlib notions to look up are `Relation.TransGen` and well-founded relations; the project needs only a ten-line induction on `TransGen`, which is what `acyclic_of_rank` is.

### The special case: adding mathlib

Add mathlib only when all of these hold: the claim matters to the deliverable; the proof needs real library theory (not just finite enumeration or a short induction); and reproducing the needed lemmas locally would be long or error-prone. Ask the user first if they are available, because of the download size. Record the reason in the README.

How:

1. Add to `lakefile.toml`, with the tag that matches `lean-toolchain`:

```toml
[[require]]
name = "mathlib"
scope = "leanprover-community"
rev = "v4.35.0"
```

2. Run `lake update`, then `just setup` (it fetches the prebuilt cache once mathlib is in `lake-manifest.json`). To reuse the packages of another project on the same machine that pins the same versions, start the project with `init_project.py --packages-from <that-project>`.
3. A file that imports mathlib must use the module system, or lake warns and the gate (`--wfail`) fails. Do not silence the warning:

```lean
module

public import Mathlib.Data.Fintype.Pi

@[expose] public section
```

4. Import only the modules you need. Put `set_option ... in` before the doc comment, not between the doc comment and the theorem. With mathlib at this version, `deriving Fintype` failed on plain enumerations; write the instance by hand.

What mathlib bought in a trial on the worked example: with `Fintype` instances, five theorems quantified over all allocations became `revert p; decide`, and two files shrank by about a quarter. That saving did not justify the dependency, so the example stays in plain Lean.

Never use `native_decide`, `sorry`, or new axioms, with or without mathlib. The gate rejects them.

## 6. Pitfalls

Quint:

- The first run of a new Quint version downloads its evaluator, and `quint verify` downloads Apalache, both from GitHub. An unauthenticated machine gets 60 GitHub API calls an hour; when they are used up the download fails with "Failed to fetch from GitHub". Wait for the limit to reset and run again. It is not a problem in the model.

- Parenthesise an assignment whose right side is a disjunction: `x' = (a or b)`. Without the parentheses the error points elsewhere: "Expected [a, b, c] and [a, b] to be the same" (the branches assign different variables) or "Using an action as an argument" on another line.
- `next` is a built-in name, like `assign`. Do not use it for a definition.
- A `val` cannot be declared inside an `all { ... }` action body. Compute the value in a `pure def` above the action and call it.
- `assign` is a reserved name.
- A `match` cannot mix actions and booleans across its branches. Compute the value with a pure function and use it in one action.
- `quint verify --invariants A B <path>` swallows the path. Put the path first, or use one `--invariant=` per run.
- TLC does not name which invariant broke when several are given. Check them one at a time.
- A scripted test that passes trivially proves nothing. End it with an `.expect` that states what the trace is meant to show.
- An invariant can hold for the wrong reason. If a property and the repair that is meant to establish it share the same condition, the property is true by construction and shows nothing. For every `.holds` claim about a repaired design, add a scripted test in which the repair is seen to act (the stuck loan is swept, the late result is turned into a refund request), and ask of the property: could a broken design also satisfy this?
- The simulator can miss a violation that TLC finds. Never treat "the simulator found nothing" as "holds".
- If TLC does not terminate, the state space is infinite. Look for a counter with no bound.
- Running many `quint verify --backend tlc` in parallel fails silently unless an Apalache server is running (see `references/experiments.md`).
- Even one after another, `quint verify` can fail with "Address already in use" on port 8822 when a previous run has not released the port or another project on the machine is verifying. Run it again; `scripts/truth_table.py` retries by itself.
- Do not put dozens of variants into one file; the translation to TLA+ fails. Generate one file per variant.

Lean:

- `decide` on a large case space may need `set_option maxRecDepth <n> in` before the theorem.
- `decide` fails on propositions with no `Decidable` instance. Make predicates `Bool`-valued, or give the instance: for a proposition, `instance : Decidable (P x) := by unfold P; infer_instance`; for a predicate such as `def Resolved (s : St) : Prop := s ≠ .owed`, `instance : DecidablePred Resolved := fun s => by unfold Resolved; infer_instance`.
- Lemma names differ between core Lean versions and mathlib; check before relying on one.
- A term ID must not be a Lean keyword. `recall`, `open`, `end`, `import`, `section`, `example`, `instance`, `theorem`, `variable`, `from`, `at`, `in`, `do`, `where`, `with`, `then`, `else` and the like give "unexpected token ...; expected ']'" inside `about := [...]`, followed by misleading `decide` failures. Name the term `toolRecall`, not `recall`.
- When a file has a second enumeration beside `Term` (the code's states, copied for a proof), its case names can clash with term IDs once both are opened. Open them locally: `open Term in` before a definition, or a `section` with its own `open`.
- A theorem about a table or a type that you copied from the code by hand is evidence about the copy. Word the claim that way ("in the transcription of the transition table, …") and anchor the term to the code so that a change there is noticed.
- The gate builds with `--wfail`, so linter warnings fail it. A common one: `simp [x]` where `x` is not needed is reported as an unused simp argument. Remove the argument.
- Write quantities as `Nat` directly. With `abbrev Amount := Nat`, `omega` reports "No usable constraints found" on hypotheses and goals stated in `Amount` (seen with Lean 4.35.0).

Shell:

- Some environments rewrite shell commands with a hook (for example adding a prefix to `git` or `cat`) and then refuse the call with a message that shows the rewritten command. This is a two-step handshake, not a block: send one new call whose command is exactly the rewritten string from the message, with nothing else in that turn. Sending your original command again is refused again. If the refusal has any other reason, do not retry; write down what you could not run and carry on with the rest.
- Send a shell call that may be rewritten alone in its turn. When one call in a turn is rewritten, the other tool calls sent with it are refused too and must be sent again.
- `python3 <script>` and `just <recipe>` are rarely rewritten. Prefer them, and read files with the file-reading tool instead of `cat`.
