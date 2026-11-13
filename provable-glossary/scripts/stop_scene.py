"""Read what the gate verified about the stop scene and the shared roles.

The stop scene is declared in the glossary (`stopScene` on each book, `role` on terms) and verified
by `just check` (stop-check, `Glossary/StopScene.lean`). `just generate` writes, for each glossary,
machine-readable lines into `docs/generated/roles.md`:

    <!-- stop-scene: ok; modelled -->
    <!-- stop-scene: todo; <the problems stop-check reports> -->
    <!-- roles-tagged: 7 -->

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
