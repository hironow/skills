# Runbook: the workflow as commands

The same workflow as `SKILL.md`, written as commands with the output you should see. Follow it top to bottom. When a step does not behave as described, stop and fix that step before going on; do not skip ahead.

`<skill>` is the folder of this skill. `J` stands for the command prefix of the project: `just` in the root layout, `just glossary` in the subdir layout. `status.py` prints the right one.

At any moment, this tells you what is done and what comes next:

```sh
python3 <skill>/scripts/status.py <repo-dir>
```

## Tier 1: required

The step numbers here are the runbook's own. Each heading names the workflow step of `SKILL.md` it carries out.

### 1. Find the starting point (before workflow step 0)

```sh
python3 <skill>/scripts/detect_start.py <repo-dir>
```

You should see `starting point: A`, `B` or `C` and the playbook to read. Read that playbook now. It adds steps to this runbook; it does not replace it.

### 2. Create the project (workflow step 1)

```sh
python3 <skill>/scripts/init_project.py <repo-dir>
J generate
J check
```

You should see, at the end of `J check`, lines beginning with `ok` and no line beginning with `FAIL` or `error`. The first `J check` can take a few minutes on a machine that has not built Lean or downloaded the model checker before; afterwards it takes well under a minute.

Now set the language of the generated documents, before you forget: in `Glossary/Registry.lean`, change the one line `def labels : Labels := Labels.en` to the user's language (`Labels.ja` for Japanese), then run `J generate`.

If it fails here, the tools are missing or too old. Check `elan --version`, `bun --version`, `java -version`, `just --version` (1.39 or newer), `rg --version`. Fix the tool; do not edit the `justfile`.

### 3. Fill the role table (workflow step 0)

Copy the role table from `SKILL.md` into the README and fill the third column for this domain. Write "none" for a role that does not exist. Do not go on until every row is filled or says "none".

### 4. Write the glossary file (workflow step 3)

Create `Glossary/<Domain>.lean`. Start from this skeleton and replace the terms.

```lean
import Glossary.Claim

namespace Glossary.Rooms

inductive Term where
  | member | slot | slotHold | payment | booking | emergencyStop
  deriving DecidableEq, Repr

inductive Ctx where
  | booking | payment | operations
  deriving DecidableEq, Repr

open Term

def terms : List (Entry Term Ctx) := [
  { id := member, label := "会員", context := .booking, gloss := "会議室を借りる利用者" },
  { id := slot, label := "時間枠", context := .booking, gloss := "1 つの会議室の、1 つの時間帯" },
  { id := slotHold, label := "仮押さえ", context := .booking,
    gloss := "会員が時間枠を期限つきで確保している状態", defDeps := [member, slot] },
  { id := payment, label := "決済", context := .payment,
    gloss := "外部の決済会社が行う支払い。結果は遅れて届き、止められない", defDeps := [member] },
  { id := booking, label := "予約確定", context := .booking,
    gloss := "決済が成功し、時間枠が会員のものになった状態", defDeps := [member, slot, payment] },
  { id := emergencyStop, label := "受付停止", context := .operations,
    gloss := "システムが自律的に、新しい仮押さえと決済の開始を止めること", defDeps := [slotHold, payment] }
]

theorem terms_wellFormed : WellFormed terms := check_sound _ (by decide)

def claims : List (Claim Term) := [
  { about := [member, slot, slotHold, booking],
    statement := "用語集は、ID が一意で、参照先が存在し、定義が循環していない",
    verdict := .proved,
    evidence := .lean "Glossary.Rooms.terms_wellFormed" (WellFormed terms) terms_wellFormed }
]

def book : Book Term Ctx := { title := "会議室の予約", terms, claims }

theorem book_check : book.check = true := by decide

end Glossary.Rooms
```

Rules that the build enforces, so you will see an error if you break them:

- Every name after `id :=`, in `defDeps` and in `about` is one of the cases of `Term`.
- A term appears in the list after every term in its `defDeps`.
- `verdict` matches `evidence`: `.lean` and `.holds` are `.proved`; `.leanRefutes` and `.violated` are `.counterexample`; `.question` is `.undecided`.
- Indentation matters inside `{ ... }`: every line of an entry or a claim is indented further than its opening brace. A line that starts at the brace's column gives "unexpected identifier; expected '}'".

### 5. Register it (workflow step 3)

Three edits, then build.

1. `Glossary.lean`: add `import Glossary.Rooms`.
2. `Glossary/Registry.lean`: add `import Glossary.Rooms`; in `books`, add `Rooms.book.view labels`; set `labels` to the user's language (`Labels.ja` for Japanese).
3. `Audit.lean`: add `#print axioms Glossary.Rooms.terms_wellFormed` and `#print axioms Glossary.Rooms.book_check`.

```sh
J generate
J check
```

You should see your terms in `docs/generated/glossary.md`. If the build says `check ... = true` could not be decided, the list breaks one of the three rules above: read the message, it names the theorem.

### 6. Model the emergency stop (workflow step 4)

**Starting point A:** copy `Spec/starter.qnt` to `Spec/<domain>.qnt` and rename the roles to the domain's words (the starter is the stop scene in the shared roles). Keep the two modules `naive` and `guarded`.

**Starting points B and C with an implementation:** do not start from the starter's naive design. The first design you model is the code as it is, one action per function that changes state, as `references/start-from-code.md` step B5 describes. Use the starter only to see the shape of a model and of its claims. The rest of this step is the same. Then check it by hand before touching the glossary:

```sh
bunx @informalsystems/quint@$(cat quint-version) typecheck Spec/<domain>.qnt
bunx @informalsystems/quint@$(cat quint-version) test --main=naive Spec/<domain>.qnt
```

`typecheck` prints nothing when the file is fine; any output is an error. `test` should print `ok doubleEntitlementTest` (or your renamed test). In the subdir layout, run these two `bunx` commands inside the project folder (`glossary/`), and run every `just` command from the repository root (`just glossary check`); `just` typed inside `glossary/` finds the root justfile and reports that the recipe does not exist.

Add the claims to the glossary file. For starting point A, copy the four from `Glossary/Starter.lean` (naive exclusivity violated, guarded exclusivity holds, guarded orphan violated, and the question) and change the file name, the terms in `about`, and the statements. For B and C, write claims of the same four kinds about your own modules: what the code as it is breaks, what a proposal keeps, what a proposal newly breaks, and the question that remains. Add the test line to `Spec/tests.txt`: `Spec/<domain>.qnt naive`.

```sh
J generate
J check
```

You should see `ok  violated  naive.exclusive`, `ok  holds  guarded.exclusive (N distinct states found)` and `ok  violated  guarded.noOrphan`. A line ending in `(found by TLC; too deep for the simulator)` is also a pass: the counterexample exists but needs many steps.

- `FAIL holds ...`: the property is false. Read the trace printed above the line. Either the design is wrong (good: record it as a counterexample instead) or the property says more than you meant.
- `FAIL violated ...: no counterexample found by the simulator or by TLC`: the property holds in every reachable state. Either the design is safe here (change the claim to `.holds`) or the model does not allow the behaviour you had in mind (compare the actions with the rules or the code).

### 7. Remove the starter (workflow step 1)

Delete `Glossary/Starter.lean` and `Spec/starter.qnt`. Remove their lines from `Glossary.lean`, `Glossary/Registry.lean`, `Audit.lean` and `Spec/tests.txt`. Run `J generate` and `J check`.

### 8. Go deeper where the role table says so (workflow step 4)

For each role that is not "none", read its pattern in `references/patterns.md` and add the model and the claims. Do them in this order and run `J check` after each: pattern 3 (gaps in the rules), pattern 5 (stages of the confirmation), pattern 7 (who resolves a cancelled entitlement), pattern 8 (deadline), pattern 9 (who decides). Skip pattern 6 unless the industry actually reallocates.

After each pattern, ask of every point the design could not settle: who in the business decides this? Add it as an `.undecided` claim with a `.question`.

### 9. Write README and findings (workflow step 8)

Follow `references/documents.md`. The documents live in the project folder: `README.md` and `docs/` at the top in the root layout, `glossary/README.md` and `glossary/docs/` in the subdir layout. Leave the repository's own README as it is and add one line to it that points to the glossary (unless the user asked that no existing file be changed; then only say where the glossary is). Then:

```sh
J check
python3 <skill>/scripts/check_protection.py <repo-dir>
python3 <skill>/scripts/status.py <repo-dir>
```

You should see `J check` end without `FAIL`, every line of `check_protection.py` beginning with `ok`, and every Tier 1 line of `status.py` marked `[done]`.

## Tier 2: expected

### 10. Compare the questions with industry practice (workflow steps 2 and 6)

Read `references/industry-check.md`. Search for how real operators answer each question in `docs/generated/questions.md`, open the primary source for anything a conclusion rests on, and write `docs/business-gaps.md`. If you cannot search the web, say so in the README and leave this step out; do not write industry facts from memory.

## Tier 3: optional

### 11. Control experiment (workflow step 5)

Read `references/experiments.md`. The three scripts do the mechanical parts. If you skip it, write in `docs/findings.md` that no comparison with a control was made and therefore nothing in the documents may be called a discovery of the formal method.

### 12. Policy draft (workflow step 7)

Pattern 11 in `references/patterns.md`.

## When something goes wrong

| What you see | What to do |
|---|---|
| The hook refuses an edit under `docs/generated/` | Correct. Edit `Glossary/*.lean` and run `J generate` |
| `generated-check: docs/generated does not match` | Run `J generate` |
| `anchor-check: ... no longer occurs in ...` | The code changed. Update the anchor, and check whether the definition still holds |
| `migration-check: ... has status ''` | Fill that row of `migration/mapping.tsv` |
| `Failed to fetch from GitHub` | The hourly download limit. Wait and run again |
| `Address already in use` | Another model check is running. Run again |
| `omega could not prove the goal` with a type alias for numbers | Use `Nat` directly |
| A scripted test passes sometimes and fails sometimes | It passes through a random choice. Give the action a parameter |
| A shell call is refused with "a hook changed this call's input" and shows a rewritten command | Send exactly that rewritten command as the next call, alone. See "Shell" in `references/lean-and-quint.md` |
| You cannot run shell commands at all | Do not write the deliverable from imagination. Report which command you could not run and stop |
| You are tempted to weaken a property, delete a failing claim, or edit the `justfile` to get a green gate | Stop. A failing check is information. Record what it shows |
