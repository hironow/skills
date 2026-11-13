"""Decide whether a README may waive the stop scene.

A project models what happens to work in flight when the system stops (pattern 4). A domain where
nothing is in flight may instead put this line in its README:

    <!-- stop-scene: none; <one sentence on why nothing is in flight across a stop> -->

The line is a claim about the domain, so it is accepted only when the README's role table agrees:
each of the four roles that can be in flight across a stop is named in English in the first
column and mapped to none. Anything else (no reason, a role mapped to something, a role not named,
no role table) is refused, and the stop scene has to be modelled.

Used by scripts/status.py and evals/grade.py, so both apply the same rule.
"""

import re

IN_FLIGHT_ROLES = ("External confirmation", "Hold", "Entitlement", "Deadline")
WAIVER = re.compile(r"<!--\s*stop-scene:\s*none;\s*(\S[^>]{9,}?)\s*-->")
NONE = re.compile(r"(none|なし|無し)\b", re.IGNORECASE)
SEPARATOR = re.compile(r"\|?[\s:|-]+")


def table_rows(markdown: str) -> list[list[str]]:
    """The cells of every table row in the text, header rows included, separator rows left out."""
    rows = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|") or SEPARATOR.fullmatch(line):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) >= 2:
            rows.append(cells)
    return rows


def stop_waiver(readme: str) -> tuple[bool, str]:
    """(accepted, note). accepted is True only for a waiver with a reason that the role table backs."""
    line = WAIVER.search(readme)
    if not line:
        return False, "no stop-scene waiver with a reason in the README"
    rows = table_rows(readme)
    problems = []
    for role in IN_FLIGHT_ROLES:
        named = re.compile(rf"\b{re.escape(role)}\b", re.IGNORECASE)
        found = [cells for cells in rows if named.search(cells[0])]
        if not found:
            problems.append(f"{role} is not named in the role table")
        elif not all(NONE.match(cells[-1]) for cells in found):
            mapped = next(cells[-1] for cells in found if not NONE.match(cells[-1]))
            problems.append(f"{role} is mapped to '{mapped[:60]}', not none")
    if problems:
        return False, "stop-scene waiver refused: " + "; ".join(problems)
    return True, "stop scene waived: " + line.group(1)
