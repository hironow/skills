---
name: provable-glossary
description: Turn a business glossary (the DDD ubiquitous language) into a repository where every claim about the terms is proved in Lean or model-checked in Quint, every open decision is recorded as a question for the business, and those questions are compared with industry practice to find gaps. Use it to design or review the business rules of a system, including what happens to work in flight when it stops (emergency maintenance, kill switch, circuit breaker, outage); to formalize a glossary or domain model; to find gaps or contradictions in a specification; to derive a glossary from an existing codebase and keep it tied to the code; or to migrate a hand-maintained glossary into a checked one without losing a term. Demanding work, best run by a highly capable model. Use it even when the skill is not named, for requests such as provable glossary, formalize the ubiquitous language, verify a design with Quint or Lean, questions for the domain expert, 証明可能な用語集, 用語集の形式化, 仕様の空白, 緊急停止の設計検証, 業務側への質問.
license: MIT
metadata:
  provenance: original
---

# Provable glossary

Build one repository in which a business glossary is the starting point of a machine-checked specification.

What the repository holds:

- **Terms and claims** in Lean. Each claim carries one piece of evidence and one of three verdicts: proved, counterexample, undecided.
- **State-machine models** in Quint. They supply the evidence: an exhaustive check or a counterexample.
- **Generated documents**: terms, claims, open questions, counts. A program writes them from the glossary. Nobody edits them.
- **Analysis documents**: findings and limits, the comparison with industry practice, a draft policy.
- **One gate**, `just check`: proofs, model checks, and the freshness of the generated documents.

`assets/worked-example/` is a complete instance: a cinema that sells tickets online, with emergency maintenance cutting in. For a new domain, **the layout and the checking machinery stay the same; only the terms, the models, and the analysis change.**

## Which model should run this

This is demanding work. It asks for proofs in Lean, state-machine models in Quint, judgment about what a business rule leaves open, web research that separates confirmed facts from hearsay, and the discipline to report a failed check instead of hiding it. Tell the user plainly which of these applies before starting.

| Model class | Recommendation | What happened in tests |
|---|---|---|
| The most capable models | Recommended. All three tiers, all three starting points | Two new greenfield domains: all three tiers, including a control experiment and a checked policy draft |
| Mid-range models | Suitable for Tier 1 and Tier 2 on all three starting points. Have a stronger model or a person review the claims before relying on them. Leave Tier 3 out unless there is time to spare | On a codebase and an old glossary that this skill's documents never mention: every defect planted in the code and every problem planted in the glossary was found, in about twenty minutes each, without touching the existing code. Tier 3 was skipped and reported as skipped |
| Small, fast models | Not recommended as the only author, and not for reading an implementation or migrating a glossary. Usable for Tier 1 and a light Tier 2 on a greenfield design by following `references/runbook.md`; have the result reviewed | Greenfield, unaided on the second attempt: ten terms, four designs compared step by step, an honest account of what was not modelled. The first attempt stopped at an environment hurdle that the runbook now explains. Results varied a lot between the two attempts |

These rows rest on a handful of runs: one or two per cell, on small systems. Treat them as a starting expectation, not a measurement. In none of the runs did a weaker model invent results; it did less, and said so.

Whatever the model, the gate protects against the worst outcome: a claim without evidence does not build, and `just check` does not pass on a wrong proof. What the gate cannot catch is a model that proves less than it says, or a question that should have been asked and was not. Those need capability, which is why the recommendation matters.

If you are running this and find that you cannot make a step work after two honest attempts, stop at the last passing state, say in the README which tier was reached and what blocked you, and hand over. A smaller, finished deliverable is worth more than a larger one that was forced through.

## Start here: three starting points

The work begins differently depending on what already exists. Find out before anything else:

```sh
python3 <skill>/scripts/detect_start.py <repo-dir>
```

| Starting point | What exists | Main difficulty | Read |
|---|---|---|---|
| **A. Greenfield** | No glossary, little or no code | Not inventing a business that does not exist | `references/start-greenfield.md` |
| **B. From code** | An implementation, no glossary | Keeping the glossary true to the code as the code changes | `references/start-from-code.md` |
| **C. Migration** | A glossary people maintain, usually with code | Losing no term, and ending with one source of truth | `references/start-migrate.md` |

The playbook for your starting point adds steps to the workflow below; everything else is shared. B and C install the project in a `glossary/` folder beside the existing code and never change that code.

Two aids for working step by step:

- `references/runbook.md` is the workflow as commands, with the output to expect and what to do when it differs. Follow it if you are unsure how to carry out a step.
- `python3 <skill>/scripts/status.py <repo-dir>` shows what is done and names the next action. Run it whenever you lose track.
- When a command is refused or a check fails in a way you do not recognise, look it up in the table "When something goes wrong" at the end of `references/runbook.md` before trying anything else. It covers the common ones, including shell calls that an environment rewrites and then refuses.

The deliverable has three tiers. Finish a tier before starting the next, and say in the README which tier was reached.

| Tier | Content | Workflow steps |
|---|---|---|
| 1. Required | A checked glossary with roles tagged and the stop scene declared and verified, the open questions, README and findings | 0, 1, 3, 4, 8 |
| 2. Expected | The questions compared with industry practice | 2, 6 |
| 3. Optional | A control experiment and a policy draft. If skipped, the documents say so | 5, 7 |

## Language

This skill is written in English. Write the deliverable in the user's language: glossary definitions, claim statements, comments in the files you author, and every document. Pick the language of the generated documents with `Labels` in `Glossary/Registry.lean` (`Labels.en` and `Labels.ja` exist; add another by copying one). Leave the shared files as they are.

## What this method does and does not give you

The work behind this skill measured formal methods against tool-less models reading the same material. Those results shape the workflow, so know them before you start.

- Finding gaps, judging whether a design satisfies a property, and deriving the condition under which it does: a model that only reads did all of these about as well. **What formal methods added was assurance**: an answer of "holds" backed by a check of every reachable state.
- **A formal model only raises questions about what was written into it.** The largest business gap in the worked example was found by researching the industry, not by the model. So research the industry early (step 2) and again in depth (step 6).
- The part that is cleanest mathematically is not always the part customers care about. The example proves fairness theorems about rebooking, and then finds that cinemas do not rebook at all.

So do not promise discoveries. Promise two things: what has been decided is on record and machine-checked, and what has not been decided is on record as a question.

## Map the domain onto shared roles

Look for these roles in any domain and tag each term that plays one in the glossary: `role := some .externalConfirmation`. The role table is generated from the tags (`docs/generated/roles.md`): a role no term carries shows as none. Do not invent a term to fill a role.

Some domains have no scarce resource: an approval workflow, a money transfer, a report. Do not invent one. Look instead for what must happen at most once (a payment, a notification, an entitlement issued) and for what waits with a deadline (an approval step instead of a hold). Leave the resource untagged and explain the mapping in the README, as in "Resource: none as such; each approved request may be paid at most once". Pattern 4 then protects "at most one execution" in place of exclusivity.

| Role (`role := some .…`) | Meaning | Cinema example |
|---|---|---|
| Resource (`.resource`) | Limited; cannot be given to two parties at once | Seat |
| Hold (`.hold`) | A time-limited reservation of the resource | Seat hold |
| External confirmation (`.externalConfirmation`) | Happens outside the system, cannot be stopped, arrives late | Payment result |
| Entitlement (`.entitlement`) | The hard-to-revoke thing handed to the customer | Admission right (ticket) |
| Stop (`.stop`) | The system stops accepting work: on its own (emergency), by a person, or because something it depends on fails | Emergency maintenance |
| Planned stop (`.plannedStop`) | Announced; waits for work in progress | Scheduled maintenance |
| Deadline (`.deadline`) | A fixed time after which the entitlement is worthless | Showtime |
| Fallback channel (`.fallbackChannel`) | A human or on-site path that works during a stop | Box office |
| Supply cancellation (`.supplyCancellation`) | The operator can no longer honour an entitlement | Cancelled screening |
| Reallocation (`.reallocation`) | Honouring it with a different resource | Rebooking to another screening |

**Commitments in flight across a stop.** Almost every system can be stopped, for whatever reason. What matters is what is half done at that moment: an external confirmation still to arrive, a hold that will expire, an entitlement promised but not yet issued, a deadline that keeps running. These keep moving while the system stands still, and the questions they raise (grant or return, who, by when) have the same shape in every domain. Model this scene whenever anything is in flight (pattern 4 in `references/patterns.md`, which gives one pattern per role).

Declare the scene on each book of the glossary, in `stopScene`. `just check` (stop-check, `Glossary/StopScene.lean`) verifies the declaration against the roles and the claims, and never against words in files:

| Declaration | Accepted when |
|---|---|
| `stopScene := .modelled` | A term has `role := some .stop`, and the claims about it include a counterexample (a design that breaks), a proved result (a design that holds), and at least one Quint check |
| `stopScene := .waived "<reason>"` | Nothing is in flight: no term has the role `externalConfirmation`, `hold`, `entitlement` or `deadline`, and the reason is a real sentence |
| `stopScene := .inBook "<title>"` | Another registered book with that title declares `.modelled` |

Until a book declares one of these, `just check` fails. A waiver cannot hide the hard part: if anything can be in flight, a role says so and the waiver is refused. What the gate cannot see is a term left untagged on purpose; the generated role table shows it as none, so a reader can.

## Workflow

Work in order. End each step with `just check` passing and a commit in a clear unit.

### 0. Take in the domain

You can start once you know three things. Ask if they are missing; if the user left the choice to you, choose and record the choice in the README.

1. What is handed to whom, through which steps.
2. A draft glossary or a description of the business. With only a description, draft the glossary yourself.
3. What is in flight when the system stops (external confirmations, holds, entitlements not yet issued, running deadlines), what can stop it (on its own, by a person, a failing dependency), and what a stop stops (new work only, or work in progress too). Ask even when the user did not mention stopping.

Tag the roles on the terms when you write the glossary (step 3); the generated `docs/generated/roles.md` is the role table. The README links to it and explains any mapping that needs words.

### 1. Lay the foundation

```sh
python3 <skill>/scripts/init_project.py <repo-dir>
```

In an empty directory the repository becomes the glossary project (commands: `just generate`, `just check`). In a repository that already holds files, the project goes into `glossary/` and the root `justfile` gains the line `mod glossary` (commands: `just glossary generate`, `just glossary check`). The script prints which layout it used and the next command.

The project uses plain Lean with no external packages, so there is nothing to download. Do not add mathlib by default; see "Plain Lean first" in `references/lean-and-quint.md` for when it is justified and how to borrow from it without depending on it.

The checks pass at this point on a starter glossary written in the shared roles (`Glossary/Starter.lean`, `Spec/starter.qnt`). Read both: they show one claim of each kind. Delete them once your own glossary is registered.

Requirements: elan, bun (it runs Quint at the pinned version; or set `QUINT` to an installed binary), Java, just 1.39 or newer, ripgrep, Python 3.

**Use the newest stable versions.** The template pins the versions it was last tested with: Lean in `lean-toolchain`, Quint in `quint-version`. Before writing anything, look up the newest stable release of each (not a release candidate) and, if it is newer, put it into those two files and run `just check` on the starter. If the starter passes, keep the new versions. If it fails and the cause is not quick to fix, go back to the pinned versions and say so in the README. Never edit the `justfile` to change a version.

### 2. Research the industry, lightly

Before modelling, send one or two research subagents (do it inline if you cannot spawn any, or if a report fails to come back) to learn how operators in this domain handle holds, cancellations, refunds and outages in their terms, and what happened in recent incidents. See `references/industry-check.md`.

The aim is to choose which scenes to model. Do not go deep on something the industry does not do. Prefer scenes where operators are visibly improvising.

### 3. Write the glossary

Write the terms and claims in `Glossary/<Domain>.lean` and register the book in `Glossary/Registry.lean`. See `references/lean-and-quint.md`.

- A term has an ID, a label, a context, a definition, definitional dependencies (no cycles allowed) and associations (cycles allowed).
- If the draft fails the checker, that is the first finding. Keep the failing draft, prove that it is circular, and add the repaired version.
- Look for empty concepts (no object can satisfy the definition) and overloaded terms (one word, several states). Both have short proofs.

### 4. Model the scenes and attach evidence

Pick the patterns in `references/patterns.md` that fit the role table and write them in `Spec/*.qnt`. Each pattern runs the same way:

1. Write the naive design and show, with a counterexample, that a wanted property breaks.
2. Repair the design one step at a time. Record as claims the counterexample that disappeared and any new one that appeared.
3. Add to the glossary every concept the repair needed.
4. Turn what the design cannot settle into an undecided claim: a question for the business, with the counterexample that shows the gap. A question no model can show gets `.questionOutsideModel "<reason>"` instead; `just check` (question-check) refuses a question with neither.

For the stop scene (pattern 4), put the stop term in the `about` of its counterexample and of the claim that holds, then declare `stopScene := .modelled` on the book.

Every claim needs evidence. "Proved" means a Lean proof or an exhaustive TLC check; "counterexample" means a Lean proof of the negation or a counterexample Quint finds. `just check` runs every claim from the glossary; there is no separate list to maintain.

### 5. Compare with a control

Check what the formal work added by giving the same material to tool-less models. See `references/experiments.md`. Run at least one experiment; the verification experiment (guess whether variants of a model satisfy a property) is the best first choice.

- Write the procedure, the scoring, your prediction, and the decision rule, and commit them before running.
- Verify every "violated" answer by replaying the control's trace in Quint.
- Report missed predictions and retracted claims as they are.

Skipping this step leaves unsupported statements such as "the model found this" in the documents. If time does not allow it, say that it was skipped and which statements are therefore unverified.

Declare the outcome in `Glossary/Registry.lean`: `def control : Control := .run` once an `experiments/<name>/` has `protocol.md` committed before `result.md`, or `.skipped "<reason>"`. `just check` (control-check) verifies the declaration; for `.run` it checks the order of the two commits in git.

### 6. Compare the questions with industry practice

Group the questions in `docs/generated/questions.md` by area and send research subagents in parallel. See `references/industry-check.md`. Classify each question, and record the class on the question in the glossary (`industry := some (.answered "<what was found>")`, `some (.notAsked "<what was found>")`, `some (.gap "<what was found>")`, or `some .notResearched`; every class but the last needs its note):

- **Answered**: the industry has a settled answer. If the model contradicted reality, fix the glossary and the model.
- **Not asked**: the industry does not do this at all.
- **Gap**: no settled answer, and customers are affected. These are the candidates.

Then look for business options that none of the questions touched. For each gap, state the customer value and, separately, whether formal methods help. Verify yourself, from primary sources, every fact a conclusion rests on.

### 7. Draft a policy for a gap, and check it

Where rules can close a gap (usually the handling of a stop), write them as numbered clauses. Model the draft, show that the wanted properties hold in every state, and show that removing any one rule breaks a property. If the research found a real incident, replay its timeline against the draft. See pattern 11 in `references/patterns.md`.

### 8. Write the documents

Write the README, `docs/findings.md`, `docs/business-gaps.md`, and the policy document following `references/documents.md`. Point to the generated documents for counts and lists; do not copy numbers into prose.

## What you write and what is generated

| Kind | Location | Written by |
|---|---|---|
| Glossaries and proofs, with the code anchors of each term | `Glossary/*.lean` | You |
| Models | `Spec/*.qnt`, `Spec/tests.txt` | You |
| Analysis documents | `README.md`, `docs/*.md` | You |
| Experiment records | `experiments/<name>/` | You. Control answers are run records; never rewrite them |
| Migration record (starting point C) | `migration/legacy.tsv`, `report.md` | `import_glossary.py`, once. Not edited |
| Migration mapping (starting point C) | `migration/mapping.tsv` | You |
| The existing implementation (B and C) | wherever it is | Nobody in this work. It is read, not changed |
| Generated documents | `docs/generated/*.md` | Only `just generate` |
| Shared machinery | Every `Glossary/*.lean` except `Registry.lean` and your own glossary files: `Core.lean`, `Claim.lean`, `Render.lean`, `Progress.lean`, and the rules `StopScene.lean`, `Questions.lean`, `Control.lean`. Also `Main.lean`, `justfile` (`mod.just` in the subdir layout), `.claude/hooks/`, `.githooks/`, and the `linter.extra` setting in `lakefile.toml` | Nobody. Same for every domain. `status.py` and the evaluation compare them with the template; when a check fails, fix the glossary or the model, never the rule |

The generated documents are a copy of what the glossary claims right now. Editing one by hand makes the document disagree with what was checked, which defeats the point of the repository. To change their content, edit `Glossary/*.lean` and run `just generate`.

Three mechanisms protect them. They come with the template; keep all three.

1. **`just check`** (`generated-check`) regenerates the documents and compares. It rejects edited files, added files, and removed files. This is the actual guarantee. The same gate also runs `anchor-check` (every term's code anchor still resolves) and `migration-check` (every legacy term is accounted for), so the glossary cannot quietly detach from the code or drop an old term.
2. **A Claude Code hook** (`.claude/hooks/protect_generated.py`) refuses Edit and Write calls on `docs/generated/` and shell commands that rewrite it, before they run.
3. **A git pre-commit hook** (`.githooks/pre-commit`, enabled by `init_project.py`) stops a commit that is out of step.

When the hook stops you, it is working as intended. Do not look for a way around it; change the glossary.

To confirm the protection works in a project, run `python3 <skill>/scripts/check_protection.py <project-root>`. It feeds sample tool calls to the hook, tampers with `docs/generated/` three ways, checks that the gate rejects each, and restores the documents.

## Honesty rules

- No verdict without evidence. Say "not checked" for what was not checked.
- Write predictions before running, and report the ones that missed.
- Before writing "the formal model found X", check whether a control can do the same. If it can, write "confirmed", not "found".
- State the size of every model (resources, parties, state count) next to its result.
- Separate facts you confirmed from primary sources from second-hand findings.
- Say so when a draft has not been reviewed by anyone who knows the business.

## Done when

- [ ] `just check` exits 0, and `status.py` shows every Tier 1 item done.
- [ ] The extra items of the playbook for your starting point are done.
- [ ] The README names the starting point (A, B or C) and the tier reached.
- [ ] Every claim has evidence; there is no `sorry` and no extra axiom. No external Lean package was added without a recorded reason.
- [ ] No theorem is vacuous: each one uses its hypotheses and says what its claim says.
- [ ] `docs/generated/` matches the glossaries, and `scripts/check_protection.py` passes.
- [ ] The starter glossary and model are gone.
- [ ] Every book declares `stopScene`, and `docs/generated/roles.md` shows `stop-scene: ok`.
- [ ] The README links the generated role table and says what was learned, and the limits.
- [ ] Every question carries its industry class in the glossary, and at least half were researched (`docs/generated/questions.md`).
- [ ] `control` in `Glossary/Registry.lean` is `.run` (control-check passes) or `.skipped "<reason>"`, and the documents say the same.
- [ ] A policy draft, if written, sits beside its check results and its limits.

## Reference files

| File | Read it when |
|---|---|
| `references/start-greenfield.md`, `start-from-code.md`, `start-migrate.md` | First, according to `detect_start.py` |
| `references/runbook.md` | Whenever you want the exact commands and the expected output |
| `references/patterns.md` | Steps 4 and 7: the scene patterns and which example file shows each |
| `references/lean-and-quint.md` | Steps 3 and 4: writing glossaries and claims, proving carefully in plain Lean, consulting mathlib online, tool pitfalls |
| `references/experiments.md` | Step 5: control experiments and the scripts to start from |
| `references/industry-check.md` | Steps 2 and 6: briefing researchers, classifying, verifying |
| `references/documents.md` | Step 8: document outlines |
| `scripts/detect_start.py` | Before step 0: which starting point |
| `scripts/status.py` | Any time: what is done, what is next |
| `scripts/init_project.py` | Step 1 |
| `scripts/scan_terms.py` | Starting points B and C: the names the code uses, with ready-made anchors |
| `scripts/import_glossary.py` | Starting point C: read the old glossary, report its problems, start the mapping |
| `scripts/check_protection.py` | After step 1 and before finishing: proves the generated documents are protected |
| `scripts/truth_table.py`, `scripts/replay_trace.py`, `scripts/run_control.py` | Step 5: the parts of a control experiment that are the same for every model |
| `assets/template/` | Step 1: the shared machinery and the starter |
| `assets/worked-example/` | Whenever unsure: the cinema glossaries, models, documents, and experiment records (in Japanese) |
