"""Keep the public copy of provable-glossary usable where it is published."""

import json
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


# A domain with nothing in flight across a stop records that in its README instead of
# modelling a stop scene. The marker is machine-readable; the reason is required.
NO_STOP = "<!-- stop-scene: none; approvals are read-only reports and nothing is sent outside -->"
NO_STOP_WITHOUT_REASON = "<!-- stop-scene: none -->"
QUIET_MODEL = "module report {\n  var count: int\n  action init = count' = 0\n  action step = count' = count + 1\n}\n"


def graded_stop_item(tmp_path: Path, readme: str) -> dict:
    run = tmp_path / "run"
    for rel in SHARED:
        (run / "outputs" / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE / rel, run / "outputs" / rel)
    (run / "outputs" / "Spec").mkdir(exist_ok=True)
    (run / "outputs" / "Spec" / "report.qnt").write_text(QUIET_MODEL, encoding="utf-8")
    (run / "outputs" / "README.md").write_text(
        f"# Reports\n\n{readme}\n", encoding="utf-8"
    )
    subprocess.run(
        [sys.executable, "-I", str(SKILL / "evals" / "grade.py"), str(run)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    expectations = json.loads((run / "grading.json").read_text(encoding="utf-8"))[
        "expectations"
    ]
    return next(e for e in expectations if "stop" in e["text"].lower())


def test_grader_accepts_a_recorded_reason_for_no_stop_scene(tmp_path: Path) -> None:
    assert graded_stop_item(tmp_path, NO_STOP)["passed"]


def test_grader_rejects_no_stop_scene_without_a_reason(tmp_path: Path) -> None:
    assert not graded_stop_item(tmp_path, NO_STOP_WITHOUT_REASON)["passed"]


def test_status_counts_a_recorded_reason_as_the_stop_item_done(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    (project / "Spec" / "report.qnt").write_text(QUIET_MODEL, encoding="utf-8")
    (project / "README.md").write_text(f"# Reports\n\n{NO_STOP}\n", encoding="utf-8")

    # As SKILL.md runs it: without -I, so it imports its sibling modules.
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )

    stop_lines = [
        line
        for line in result.stdout.splitlines()
        if "stop" in line.lower() and "[" in line
    ]
    assert stop_lines
    assert all("[done]" in line for line in stop_lines), stop_lines


def test_skill_requires_the_stop_scene_only_when_something_is_in_flight() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    description = skill.split("\n---", 1)[0]
    assert "can stop itself autonomously" not in description
    assert "stop-scene: none;" in skill
    assert "stop-scene: none;" in (SKILL / "references" / "patterns.md").read_text(
        encoding="utf-8"
    )


def quint_blocks(markdown: str) -> list[str]:
    return re.findall(r"```quint\n(.*?)```", markdown, re.DOTALL)


def test_liveness_guide_shows_a_complete_temporal_property() -> None:
    guide = (SKILL / "references" / "lean-and-quint.md").read_text(encoding="utf-8")
    examples = [
        b
        for b in quint_blocks(guide)
        if "temporal" in b and "weakFair(" in b and "eventually(" in b
    ]
    assert examples, "no Quint example of a liveness property with fairness"
    assert "strongFair(" in guide
    assert "temporal := true" in guide


def test_skill_says_how_to_map_a_domain_with_no_scarce_resource() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    patterns = (SKILL / "references" / "patterns.md").read_text(encoding="utf-8")
    assert "no scarce resource" in skill
    assert "at most one execution" in patterns
