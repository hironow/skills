# Testing this skill

`evals.json` holds the test prompts. `grade.py` scores a greenfield run on outcomes.

Two kinds of fixture:

- `../assets/example-roomdesk/` is the small existing service (with a hand-written `docs/GLOSSARY.md`) that the playbooks quote. For a from-code run, copy it without `docs/`. A run on it shows whether the
  steps go through, but not whether the skill finds anything: the answers are in the playbooks.
- `../../evals-heldout/` (lendbox) is kept outside the skill folder and is mentioned nowhere in the
  skill's documents. Use it to test whether a run finds defects and glossary problems on its own. Its
  `PLANTED.md` lists what was planted; never copy that file into a test workspace, and tell the run to
  read only the skill folder and its own repository.

When a playbook gains an example, check that it does not quote a held-out fixture.
