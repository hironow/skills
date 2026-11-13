The source of truth is `Glossary/*.lean` (terms and claims) and `Spec/*.qnt` (models).
Run the `check` recipe before saying anything is done: `just check`, or `just <folder> check` when this project sits in a folder of a larger repository.

Authored by you: `Glossary/*.lean`, `Spec/*.qnt`, `Spec/tests.txt`, `README.md`, `docs/*.md`, `experiments/`.
Generated, never edited: `docs/generated/*.md`. To change them, edit `Glossary/*.lean` and run the `generate` recipe.
A hook refuses edits to `docs/generated/`, and `just check` fails when it does not match the glossaries.

Same for every domain, do not edit: `Glossary/Core.lean`, `Glossary/Claim.lean`, `Glossary/Render.lean`,
`Glossary/Progress.lean`, `Main.lean`, `justfile`, `.claude/hooks/`, `.githooks/`.
