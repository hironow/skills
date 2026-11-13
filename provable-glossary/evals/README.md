# Testing this skill

`evals.json` holds the test prompts. No check judges by whether a word appears in a file: the stop scene and the roles are read from the gate-verified `docs/generated/roles.md`, the questions and their industry classes from `docs/generated/questions.md`, and the evidence counts and the control declaration from `docs/generated/summary.md`, so a run without the skill fails those items by construction. Whether the documents state the limits and the model sizes is prose that no check can read: a reader judges it, and the grader has no item for it. `grade.py` scores a greenfield run on outcomes:
`python3 -I evals/grade.py <run-dir>`, where `<run-dir>` holds the run's `outputs/`. It also runs from a copy in a
workspace folder beside the skill (`<skills>/provable-glossary-workspace/grade.py`), and finds the template either way.

The grader's numbers are expectations for the prompts in `evals.json`, not rules of the skill: at least 8 questions, at least 5 source URLs, at least one question backed by a counterexample, at least 3 roles tagged. `scripts/status.py` keeps lower floors that every project can meet (a small domain, or one where nothing is in flight); raising them to the grader's numbers would invite padding, since a question or a role tag costs one line.

Two kinds of fixture:

- `../assets/example-roomdesk/` is the small existing service (with a hand-written `docs/GLOSSARY.md`) that the playbooks quote. For a from-code run, copy it without `docs/`. A run on it shows whether the
  steps go through, but not whether the skill finds anything: the answers are in the playbooks.
- `../../evals-heldout/` (lendbox) is kept outside the skill folder and is mentioned nowhere in the
  skill's documents. Use it to test whether a run finds defects and glossary problems on its own. Its
  `PLANTED.md` lists what was planted; never copy that file into a test workspace, and tell the run to
  read only the skill folder and its own repository.

When a playbook gains an example, check that it does not quote a held-out fixture.
