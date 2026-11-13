"""Read the machine lines that the gate-verified generated documents carry.

The stop scene is declared in the glossary (`stopScene` on each book, `role` on terms) and verified
by `just check` (stop-check, `Glossary/StopScene.lean`). `just generate` writes, for each glossary,
machine-readable lines into `docs/generated/roles.md`:

    <!-- stop-scene: ok; modelled -->
    <!-- stop-scene: todo; <the problems stop-check reports> -->
    <!-- roles-tagged: 7 -->

`docs/generated/questions.md` carries, for each glossary, the questions and their basis, verified by
`just check` (question-check, `Glossary/Questions.lean`):

    <!-- questions: 11; with-counterexample: 5; outside-model: 6 -->
    <!-- industry: classified: 11; researched: 9 -->

This module reads those lines and nothing else. It never judges by whether a word appears in a
model, a README or any other file. Used by scripts/status.py and evals/grade.py.
"""

import re

STOP_LINE = re.compile(r"^<!-- stop-scene: (ok|todo); (.*) -->$", re.MULTILINE)
TAGGED_LINE = re.compile(r"^<!-- roles-tagged: (\d+) -->$", re.MULTILINE)
MISSING = "docs/generated/roles.md has no stop-scene line: declare stopScene in each glossary, tag the roles on its terms, and run `just generate`"


def stop_scene(roles_md: str) -> tuple[bool, str]:
    """(declared and verified, note). True only if every glossary's line says ok."""
    lines = STOP_LINE.findall(roles_md)
    if not lines:
        return False, MISSING
    todo = [detail for state, detail in lines if state == "todo"]
    if todo:
        return False, "; ".join(todo)
    return True, "; ".join(detail for _, detail in lines)


def roles_tagged(roles_md: str) -> int:
    """The largest number of distinct shared roles tagged on the terms of one glossary."""
    return max((int(n) for n in TAGGED_LINE.findall(roles_md)), default=0)


QUESTIONS_LINE = re.compile(
    r"^<!-- questions: (\d+); with-counterexample: (\d+); outside-model: (\d+) -->$",
    re.MULTILINE,
)


def question_counts(questions_md: str) -> tuple[int, int] | None:
    """(questions, questions backed by a counterexample) over all glossaries, or None without lines."""
    lines = QUESTIONS_LINE.findall(questions_md)
    if not lines:
        return None
    return sum(int(q) for q, _, _ in lines), sum(int(w) for _, w, _ in lines)


INDUSTRY_LINE = re.compile(r"^<!-- industry: classified: (\d+); researched: (\d+) -->$", re.MULTILINE)


def industry_counts(questions_md: str) -> tuple[int, int] | None:
    """(classified, researched) questions over all glossaries, or None without lines."""
    lines = INDUSTRY_LINE.findall(questions_md)
    if not lines:
        return None
    return sum(int(c) for c, _ in lines), sum(int(r) for _, r in lines)


def industry_complete(questions_md: str) -> tuple[bool, str]:
    """Every question is classified, and at least half were actually researched (Tier 2)."""
    counts = question_counts(questions_md)
    industry = industry_counts(questions_md)
    if counts is None or industry is None:
        return False, "no question or industry counts in docs/generated/questions.md"
    total, _ = counts
    classified, researched = industry
    ok = total > 0 and classified == total and 2 * researched >= total
    return ok, f"{classified} of {total} questions classified, {researched} researched"
