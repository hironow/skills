"""Keep the public copy of provable-glossary usable where it is published."""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2] / "provable-glossary"
TEMPLATE = SKILL / "assets" / "template"
LINK = re.compile(r"\]\(([^)\s]+)\)")
FENCE = re.compile(r"```.*?```", re.DOTALL)
# The shared files the grader compares with the template, minus the justfile:
# a run directory with a justfile would make the grader run the whole gate.
SHARED = [
    "Glossary/Core.lean",
    "Glossary/Claim.lean",
    "Glossary/Render.lean",
    "Main.lean",
]


def broken_links(markdown: Path) -> list[str]:
    text = FENCE.sub("", markdown.read_text(encoding="utf-8"))
    broken = []
    for target in LINK.findall(text):
        if re.match(r"[a-z]+:", target) or target.startswith("#"):
            continue
        if not (markdown.parent / target.split("#", 1)[0]).exists():
            broken.append(f"{markdown.relative_to(SKILL)} -> {target}")
    return broken


def test_every_relative_link_in_the_skill_resolves() -> None:
    broken = [link for md in sorted(SKILL.rglob("*.md")) for link in broken_links(md)]
    assert broken == []


def test_worked_example_says_it_is_for_reading_and_where_to_start() -> None:
    readme = (SKILL / "assets" / "worked-example" / "README.md").read_text(
        encoding="utf-8"
    )
    head = readme.split("\n## ", 1)[0]
    assert "../template/" in head
    assert "../../scripts/init_project.py" in head


@pytest.mark.parametrize("placement", ["in-skill", "sibling-workspace"])
def test_grader_finds_the_template_wherever_it_runs(
    tmp_path: Path, placement: str
) -> None:
    if placement == "in-skill":
        grader = SKILL / "evals" / "grade.py"
    else:
        workspace = tmp_path / "skills" / "provable-glossary-workspace"
        workspace.mkdir(parents=True)
        shutil.copytree(
            TEMPLATE, tmp_path / "skills" / "provable-glossary" / "assets" / "template"
        )
        grader = workspace / "grade.py"
        shutil.copy(SKILL / "evals" / "grade.py", grader)
    run = tmp_path / "run"
    for rel in SHARED:
        (run / "outputs" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE / rel, run / "outputs" / rel)

    result = subprocess.run(
        [sys.executable, "-I", str(grader), str(run)],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr[-2000:]
    grading = (run / "grading.json").read_text(encoding="utf-8")
    assert "['justfile']" in grading
