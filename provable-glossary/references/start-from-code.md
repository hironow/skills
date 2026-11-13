# Starting point B: an implementation exists, no glossary

You derive the glossary from the code, then check the design the code implements.

**The risks here**

- *A glossary that drifts from the code.* Words in a document and names in the code part ways within weeks. Anchors (below) make the gate fail when that happens.
- *A model that flatters the code.* It is tempting to model what the code should do. Model what it does, including what looks like a bug; the counterexample is the finding.
- *Missing a name.* The scanner makes sure every declared name is at least looked at.

The example used below is `assets/example-roomdesk/`, a small Go service that rents meeting rooms.

## Steps

### B1. Install beside the code

```sh
python3 <skill>/scripts/init_project.py <repo-dir>
```

The repository already holds files, so the project goes into `<repo-dir>/glossary/` and the root `justfile` gets the line `mod glossary`. From the repository root the commands are `just glossary generate` and `just glossary check`. Existing `.claude/settings.json` is merged, not replaced. If the repository already manages git hooks, the script prints one line to add to them; add it. Otherwise it creates `.githooks/pre-commit` and sets the repository's `core.hooksPath` to `.githooks`, which changes the repository's git configuration; tell the user.

Do not move, rename or reformat the existing code. This work reads the implementation; it does not change it. If you find a bug, record it as a claim and tell the user.

### B2. Scan the names

```sh
python3 <skill>/scripts/scan_terms.py <repo-dir>
```

It writes three tables into `<repo-dir>/glossary-scan/`. They are scratch material; `init_project.py` already added that folder to `.gitignore`.

- `words.tsv`: read from the top. The frequent words are your term candidates.
- `states.tsv`: read all of it. Each row is a group of constants that looks like the states of something. In the example:

```
Status  StatusHeld, StatusPaying, StatusBooked, StatusExpired, StatusCancelled, StatusRefunded
```

  Every such group becomes a state machine in a Quint model, and each state usually becomes a term. A group of error constants (`ErrSlotTaken`, …) is not a state machine: each error is a guard of some operation, and belongs in the model as that guard.
- `identifiers.tsv`: the anchor column is ready to paste (step B4). The `other_uses` column counts how often the name appears elsewhere in the scanned code. It is a rough count: it cannot tell a real use from an import or a re-export, and entry points that only outside callers use show 0. Use it for constants. For each limit or duration the code declares, open its few uses and check that something actually reads it; a limit that nothing reads is a rule that nothing enforces.

### B3. Read the code and decide the roles

The scanner counts words; it does not understand them. Open the files where the top words occur and answer, for each role in the `SKILL.md` table, "which name in the code is this?".

| Role | In the example | Found in |
|---|---|---|
| Resource | `Slot` | `internal/booking/reservation.go` |
| Hold | `Reservation` with `StatusHeld`, `HoldDuration` | `reservation.go`, `hold.go` |
| External confirmation | `PaymentEvent` arriving at `HandlePaymentWebhook` | `payment.go` |
| Entitlement | `Reservation` with `StatusBooked` | `payment.go` |
| Emergency stop | `EmergencyStop` | `stop.go` |
| Supply cancellation | `CloseSlot` | `payment.go` |
| Deadline, fallback channel, planned stop, reallocation | none in the code | |

Write "none in the code" where the code has no such thing. A role the business has but the code lacks is itself a question for the business. Record the roles as `role := some .<role>` on the terms when you write the glossary; leave a role untagged where the code has nothing, and `docs/generated/roles.md` shows it as none.

While reading, write down three kinds of observation. They become claims in step 4 of the workflow.

1. **One thing, two names.** The example says `Reservation` in the types and "booking" in the package name and the mail (`SendBookingConfirmed`). Ask which word the business uses; record the other as a synonym in the definition.
2. **One name, two things.** `Reservation` is a hold while `HELD` and an entitlement while `BOOKED`. These are two terms (pattern 2, overloaded terms).
3. **A guard that is missing.** `HandlePaymentWebhook` sets `StatusBooked` without looking at the current status or the stop. Do not fix it. Model it.

### B4. Write the glossary with anchors

Write `glossary/Glossary/<Domain>.lean` as in `references/lean-and-quint.md`. Give every term that exists in the code at least one anchor: the file, a `#`, and a piece of text that must occur in that file. Paste them from `identifiers.tsv`.

```lean
{ id := slotHold, label := "仮押さえ", context := .booking,
  gloss := "会員が時間枠を 10 分間だけ確保している状態。コード上は Reservation の状態 HELD",
  defDeps := [member, slot],
  anchors := ["internal/booking/reservation.go#StatusHeld",
              "internal/booking/reservation.go#const HoldDuration",
              "internal/booking/hold.go#func (s *Service) PlaceHold"] },
```

Rules for anchors:

- The path starts at the repository root, not at `glossary/`.
- The text is short and specific: a declaration (`type Slot struct`, `func (s *Service) PlaceHold`, `CREATE TABLE slots`) or a constant name. Not a whole line with arguments, which changes too often, and not a common word, which matches by accident.
- Pinning a value is the exception, and a good one: when a definition quotes a value the code fixes, anchor on the assignment itself (`HoldDuration = 10 * time.Minute`). The gate then fails when the value changes, which is exactly when the definition must be reread.
- When a definition rests on something the code does not do, say so with a negative anchor, `!path#text`: it passes while the text is absent. In the example nothing ever assigns the refunded status, so the term `返金済み` carries `"!internal/booking/payment.go#= StatusRefunded"`. The day someone adds that assignment the gate fails and the definition gets revisited. Keep the text narrow (an assignment, a call), or it will match a declaration or a comment.
- A term the business has but the code does not gets no anchor and a definition that says so. `just glossary anchor-check` prints how many anchors resolve.
- `just glossary check` now fails when someone renames `PlaceHold` or deletes the file. That is the point: the person who renames it updates the glossary in the same change.

Put values the code fixes into the definition with their source ("10 分。`HoldDuration`"). Values are where documents go stale first.

### B5. Model what the code does

Follow step 4 of the workflow, with one difference: the first design you model is the code as it is, not a naive design you made up.

- One Quint action per function that changes state. Name the action after the function and say so in a comment:

```quint
// HandlePaymentWebhook (internal/booking/payment.go): sets BOOKED on success.
// It checks neither the current status nor the emergency stop.
action paymentSucceeds(r: str): bool = all {
  status.get(r) != "none",
  status' = status.set(r, "BOOKED"),
  ...
}
```

- Copy the guards exactly. If the function has no guard, the action has none.
- Include time-driven jobs (`ExpireHolds`) and staff operations (`CloseSlot`, `Lift`) as actions.
- State the properties the business would expect (pattern 4: exclusivity, preservation, meaning of the stop) and let the checker find which ones the code breaks. To see every property against every design at once, use `scripts/truth_table.py` (it retries a busy model checker, which a hand-written loop does not).
- Then repair in the model, one step at a time, as in the workflow. The repaired designs are proposals; say in the claim which design is the code's and which are proposals ("In the code as it is, …" / "With the guard added, …").
- Record in `docs/findings.md`, under limits, what the model leaves out of the code (persistence, retries, concurrency inside a function, anything you did not read).

A counterexample found in a model of the code is a hypothesis about the code until someone confirms it. Write the trace as a test the team can run or read against the code, and say that it was not executed against the implementation unless you executed it.

### B6. Continue with the workflow

Steps 5 to 8 are unchanged. The README and `docs/` of this work go into the project folder (`glossary/README.md`, `glossary/docs/`); the repository's own README stays, with one added line that points to the glossary. If the user asked that existing files not be changed at all, leave the README alone too and say in your final message where the glossary is. In `glossary/README.md`, state that the starting point was B and list the code that was read (folders, commit).

## Done when

The list in `SKILL.md`, and:

- [ ] Every term that exists in the code has an anchor, and `anchor-check` passes.
- [ ] Every group in `states.tsv` is either modelled or listed as left out, with the reason.
- [ ] Claims about the code say "in the code as it is"; proposals are marked as proposals.
- [ ] No file of the existing implementation was changed.
