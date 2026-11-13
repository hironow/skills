# Document outlines

Write for a reader who was not there: conclusion first, short sentences, plain words, in the user's language. The reader has the repository, not this skill: do not link to files of the skill (`references/patterns.md` and the like). Name a pattern in words ("the emergency-stop scene") and link only to files inside the repository. Use tables and lists; one idea per paragraph. For counts and lists (terms, claims, open questions) link to `docs/generated/`; numbers copied into prose go stale.

The examples are `README.md` and `docs/` under `assets/worked-example/`.

## README.md

1. What this is (two or three lines). The three verdicts. Link to `docs/generated/summary.md` for counts.
2. The role table: link `docs/generated/roles.md` (generated from the roles tagged on terms) and say in words what it cannot: a role that exists only in another form, or a mapping that needs a note. Do not copy the table.
3. What was learned (five points at most).
4. Reading order.
5. Usage: `just setup`, `just check`, `just generate` (in the subdir layout: `just glossary setup`, `just glossary check`, `just glossary generate`).
6. What is written and what is generated, and the three mechanisms that protect the generated documents.
7. Layout: glossaries and proofs, models, experiment records.
8. Limits.

## docs/findings.md

1. Overall conclusions.
2. One section per pattern used: what was found, as bullets. A table where designs were compared in stages.
3. One section per control experiment, with one bolded conclusion each.
4. The table of questions for the business: number, question, industry status.
5. Limits: model sizes, properties not checked, bias of the comparisons, reliability of the research, no implementation.

## docs/business-gaps.md

1. Conclusions (five at most).
2. How it was researched and how reliable it is. Which points you verified yourself.
3. The classes are in `docs/generated/questions.md`, generated from the glossary; link it, do not copy the table. Here, give for each question the evidence behind its class: what the operators do, and the sources.
4. One section per class: what the answered questions teach, the questions not asked, the gaps.
5. The gap formal methods cannot close.
6. The table of business decisions: decision, customer value, role of formal methods.
7. Main sources.

## docs/<name>-policy.md

1. What this is, and that nobody who knows the business has reviewed it.
2. The clauses.
3. What was checked: the properties, and the variants × properties table.
4. The incident timeline applied to the draft: moment, what happened, published handling, the draft.
5. Limits.

## AGENTS.md

A short guide for whoever works here next: where the source of truth is, the one gate, what is authored and what is generated. The template ships one; extend it with the domain's document names.
