# Starting point C: migrating a glossary that people maintain

A glossary document already exists, usually with an implementation. You move it into the checked glossary without losing a term, then make the checked glossary the source of truth.

**The risks here**

- *Losing a term.* People rely on the old document. A term that silently disappears breaks trust in the new one. The migration check (below) fails until every old term is accounted for.
- *Two sources of truth.* If the old document stays editable, the two drift. The last step retires it.
- *Overwriting people's wording.* The old definitions carry decisions. Change a definition only for a reason you can state, and keep the old wording in the record.

Work with the people who maintain the glossary if they are available: the retire/keep decisions in step C4 are theirs.

The example used below is `assets/example-roomdesk/docs/GLOSSARY.md` on top of the code in `assets/example-roomdesk/`.

## Steps

### C1. Install beside the code

As in `start-from-code.md` step B1. Do not edit or move the old glossary yet.

### C2. Import the old glossary

```sh
python3 <skill>/scripts/import_glossary.py <path-to-old-glossary> --project <repo-dir>/glossary --emit-lean
```

It reads Markdown tables, Markdown lists, headings with paragraphs, definition lists, simple YAML, JSON, CSV and TSV. If it recognises no entries, convert the document to a Markdown table with the columns Term and Definition and run it again.

It writes:

| File | What it is | Do you edit it? |
|---|---|---|
| `migration/legacy.tsv` | The old glossary, one row per entry | No. It is the record of the starting point |
| `migration/mapping.tsv` | One row per old entry, with empty status. A term the old glossary defines twice has two rows, the second marked `(2)` | Yes, in step C4 |
| `migration/report.md` | What a program can notice | No. Read it |
| `Glossary/Legacy.lean` | The old glossary as a Lean list, with a checked statement of whether it passes the checker | No |

Add `import Glossary.Legacy` to `Glossary.lean` and `#print axioms Glossary.Legacy.draft_check` to `Audit.lean`, as the script says.

### C3. Read the report

For the example the report says:

```
- Terms with nearly the same name: 1        仮押さえ / 仮押え
- Terms with no definition: 1               返金
- Circular definitions: 2                   会員 → 予約 → 会員
                                            予約 → 仮押さえ → 予約
- Terms that neither mention nor are mentioned by another term: 1
```

`Legacy.lean` holds the old glossary and the statements about it that Lean has checked:

- `draft_check : check draft = false`: as written, the old glossary is rejected by the checker.
- `draft_cycle_1`, `draft_cycle_2`, …: one theorem per circular definition, `¬ Acyclic (DefDep draft)`, with the terms named in its comment.

They are the first claims of the new glossary (pattern 1). Copy this shape; the proofs already exist, so the evidence only names them:

```lean
{ about := [member, reservation, slotHold],
  statement := "移行前の用語集は、そのままで検査を通る",
  verdict := .counterexample,
  evidence := .leanRefutes "Glossary.Legacy.draft_check"
    (check Legacy.draft = true) (by rw [Legacy.draft_check]; decide) },
{ about := [member, reservation],
  statement := "移行前の用語集は、定義が循環していない (会員 → 予約 → 会員)",
  verdict := .counterexample,
  evidence := .leanRefutes "Glossary.Legacy.draft_cycle_1"
    (Acyclic (DefDep Legacy.draft)) Legacy.draft_cycle_1 },
```

The old glossary's terms have IDs like `t01` in `Legacy.lean` (the importer cannot name them). The `about` list uses the IDs of the new glossary.

To state more than "the old glossary fails the checker", use the other patterns as usual. A term the old glossary uses in two senses is an overloaded term (pattern 2): write the two readings as functions over a small type that you copy by hand from the code's states, prove that no single predicate agrees with both, and say in the README that the copied type does not follow the code by itself (anchor the term to the code's declaration so that a change there is noticed).

The script finds mentions by looking for one term's name inside another's definition. It cannot tell a definitional dependency from an association. "会員: 予約を行う利用者" mentions `予約` but does not need it to be understood. Sorting those out is how most cycles are repaired.

### C4. Write the new glossary and fill the mapping, term by term

Write `Glossary/<Domain>.lean`. For each row of `migration/mapping.tsv`, decide one of two things and write it down.

| Decision | status | target | Example |
|---|---|---|---|
| The term continues, perhaps renamed or redefined | `mapped` | the term ID in the new glossary | `仮押さえ	mapped	slotHold` |
| The term is dropped | `retired` | the reason, in the user's language | `回数券	retired	実装にも規約にもなく、運営に確認したところ 2024 年に廃止` |

A term the old glossary defines twice has two rows (`料金` and `料金 (2)`). Decide each: if the two definitions describe one thing, map both rows to the same term and record the conflict as an undecided claim; if they describe two things, map the second row to a new term with its own name.

Two old terms may map to one new term (`仮押え	mapped	slotHold`): that is how a spelling variant is merged. If the two spellings carry different definitions (in the example `仮押さえ` lasts "until the booking is confirmed" and `仮押え` "before payment"), do not choose silently: map both to the one term, define it from what the code does, and add an undecided claim that quotes both old definitions and asks which was meant. One old term may need two new terms (an overloaded term): map it to the one that keeps the name and mention the other in its definition.

Rules:

- **Never retire a term because it is inconvenient.** Retire it when it is a duplicate, when the business confirms it is gone, or when it was never a term (a heading that the importer picked up). If you cannot ask, map it and add an undecided claim: "Is 回数券 still offered?".
- **Keep the old wording unless it is wrong.** When you change a definition, the reason goes into a claim or into `docs/findings.md`.
- **Check each definition against the code.** In the example the old glossary says a hold lasts 15 minutes and the code says `HoldDuration = 10 * time.Minute`. Do not pick one. Record the conflict as an undecided claim with both sources, and anchor the term to the code line.
- Add anchors as in `start-from-code.md` step B4 if there is an implementation. Run `scan_terms.py` too: names in the code that the old glossary never mentions are terms the glossary was missing.

`just glossary migration-check` tells you what is left:

```
migration-check: 'reservation' is mapped to 'reservaton', which is not a term ID
migration-check: '返金' has status ''; use mapped or retired
```

### C5. Continue with the workflow

Steps 2 and 4 to 8 of the workflow are unchanged. If there is an implementation, model the code as it is (`start-from-code.md` step B5).

### C6. Switch the source of truth

Do this last, when `just glossary check` passes. Until then the old document stays as it was.

If you can ask the user or the people who maintain the glossary, ask before switching. If you cannot, a request to "migrate" the glossary covers the switch: do it as its own commit, separate from everything else, so that it can be reverted alone, and say in the README that the maintainers have not confirmed it.

1. Replace the body of the old glossary document with a short notice, in the user's language, that points to the generated documents:

```markdown
# roomdesk 用語集

この用語集は `glossary/Glossary/*.lean` に移りました。読むための一覧は
[glossary/docs/generated/glossary.md](../glossary/docs/generated/glossary.md) にあります。
用語を変えるときは、`glossary/Glossary/` を直して `just glossary generate` を実行します。
移行の記録は `glossary/migration/` にあります。
```

   Keep the file at its old path so existing links still work. Its history stays in git.
2. Keep `migration/` in the repository. It is the audit trail, and `migration-check` keeps guarding it.
3. Add to the repository's contribution notes (README, AGENTS.md, or wherever the team looks) how to change a term now.

If the team wants to keep editing the old document, do not switch. Say in the README that the migration stopped before the switch and that there are two sources until it is done.

## Done when

The list in `SKILL.md`, the list in `start-from-code.md` if there is an implementation, and:

- [ ] `migration-check` passes: every old term is mapped or retired with a reason.
- [ ] The claim about the old glossary (pattern 1) is in the new glossary with its Lean evidence.
- [ ] Every conflict between the old glossary and the code is a claim.
- [ ] The old document points to the generated one, or the README says why it does not yet.
