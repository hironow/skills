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
        # The workspace sits beside the whole skill (evals/README.md), not beside the template alone.
        shutil.copytree(
            SKILL,
            tmp_path / "skills" / "provable-glossary",
            ignore=shutil.ignore_patterns("worked-example", "__pycache__"),
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
# modelling a stop scene. The waiver is a claim about the domain, so it must agree with the
# role table: the four roles that can be in flight across a stop are named and mapped to none.
NO_STOP = "<!-- stop-scene: none; the site only reads a nightly import and promises nothing to anyone outside -->"
NO_STOP_WITHOUT_REASON = "<!-- stop-scene: none -->"
QUIET_MODEL = "module report {\n  var count: int\n  action init = count' = 0\n  action step = count' = count + 1\n}\n"


def role_table(**mapped: str) -> str:
    rows = {
        "External confirmation": "none",
        "Hold": "none (nothing is reserved)",
        "Entitlement": "なし",
        "Deadline": "none",
    }
    rows.update({name.replace("_", " "): value for name, value in mapped.items()})
    body = "\n".join(f"| 役割 ({name}) | {value} |" for name, value in rows.items())
    return f"## 役割の表\n\n| 役割 | この題材では |\n|---|---|\n{body}\n"


JAPANESE_ONLY_TABLE = (
    "## 役割の表\n\n| 役割 | この題材では |\n|---|---|\n"
    "| 外部の確認 | なし |\n| 仮確保 | なし |\n| 権利 | なし |\n| 期限 | なし |\n"
)

WAIVER_CASES = {
    "consistent": (role_table() + "\n" + NO_STOP, True),
    "no-reason": (role_table() + "\n" + NO_STOP_WITHOUT_REASON, False),
    "confirmation-exists": (
        role_table(External_confirmation="会計システムの支払い完了通知")
        + "\n"
        + NO_STOP,
        False,
    ),
    "deadline-exists": (
        role_table(Deadline="承認ごとに 3 営業日") + "\n" + NO_STOP,
        False,
    ),
    "roles-not-named": (JAPANESE_ONLY_TABLE + "\n" + NO_STOP, False),
    "no-role-table": (NO_STOP, False),
}


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


def status_stop_done(tmp_path: Path, readme: str) -> bool:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    (project / "Spec" / "report.qnt").write_text(QUIET_MODEL, encoding="utf-8")
    (project / "README.md").write_text(f"# Reports\n\n{readme}\n", encoding="utf-8")
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
    assert stop_lines, result.stdout
    return all("[done]" in line for line in stop_lines)


@pytest.mark.parametrize("case", sorted(WAIVER_CASES))
def test_grader_accepts_a_stop_waiver_only_when_the_role_table_agrees(
    tmp_path: Path, case: str
) -> None:
    readme, accepted = WAIVER_CASES[case]
    assert graded_stop_item(tmp_path, readme)["passed"] is accepted


@pytest.mark.parametrize("case", sorted(WAIVER_CASES))
def test_status_accepts_a_stop_waiver_only_when_the_role_table_agrees(
    tmp_path: Path, case: str
) -> None:
    readme, accepted = WAIVER_CASES[case]
    assert status_stop_done(tmp_path, readme) is accepted


def test_skill_requires_the_stop_scene_only_when_something_is_in_flight() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    description = skill.split("\n---", 1)[0]
    assert "can stop itself autonomously" not in description
    assert "stop-scene: none;" in skill
    assert "stop-scene: none;" in (SKILL / "references" / "patterns.md").read_text(
        encoding="utf-8"
    )
    runbook = (SKILL / "references" / "runbook.md").read_text(encoding="utf-8")
    assert "stop-scene: none;" in runbook
    assert "External confirmation" in skill.split("stop-scene: none;", 1)[1][:1500]


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


def test_worked_example_holds_no_records_of_testing_the_skill() -> None:
    # Records of evaluating the skill name test domains and their expected answers. A run reads
    # the example's experiments as models to copy, so those records would leak into later tests.
    experiments = SKILL / "assets" / "worked-example" / "experiments"
    assert (
        sorted(p.name for p in experiments.iterdir() if p.name.startswith("skill-"))
        == []
    )


def test_a_role_that_exists_in_another_form_is_not_none(tmp_path: Path) -> None:
    readme = role_table(
        Hold="none as such; each approval step waits up to 3 business days"
    )
    readme += "\n" + NO_STOP
    assert not graded_stop_item(tmp_path, readme)["passed"]
