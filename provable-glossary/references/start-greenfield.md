# Starting point A: greenfield

No glossary and little or no implementation. You write the terms from a description of the business.

**The risk here**: inventing. With nothing to check against, it is easy to model a business that does not exist. The industry research (step 2, Tier 2) is the counterweight. In Tier 1, mark every business fact you assumed as an assumption in the README; when you go on to Tier 2, do step 2 first.

## What to do

1. `python3 <skill>/scripts/init_project.py <repo-dir>`. In an empty repository the repository becomes the glossary project (root layout). If it already holds a build file or a little code, the project goes into `glossary/` even though the starting point is A; use the commands `init_project.py` prints.
2. Follow the workflow in `SKILL.md` from step 0. `references/runbook.md` gives the same steps with commands and expected output.
3. If the user gave a draft glossary, even a rough list of words, write it down exactly as given first (pattern 1). A draft that fails the checker is the first finding.
4. Leave `anchors` empty: there is no implementation to point at. If an implementation is written later, add anchors then (see `start-from-code.md`, "Anchors").

## Done when

The list in `SKILL.md`, nothing more.

The worked example in `assets/worked-example/` is a greenfield project.
