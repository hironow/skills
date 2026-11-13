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


# The stop scene is declared in the glossary (stopScene on each book, roles on terms) and verified
# by the gate (stop-check). `just generate` writes one machine-readable line per glossary into
# docs/generated/roles.md; status.py and the grader read only that. Every fixture below also holds a
# Quint model full of stop words and the old README waiver line: neither may ever count.
KEYWORD_MODEL = (
    "module emergency_stop {\n  var stopped: bool\n"
    "  action init = stopped' = false\n  action emergencyStop = stopped' = true\n}\n"
)
OLD_WAIVER = "<!-- stop-scene: none; the site only reads a nightly import and promises nothing outside -->"


def roles_doc(*lines: str, tagged: int = 5) -> str:
    return (
        "# Roles\n\n## Book\n\n"
        + "\n".join(lines)
        + f"\n<!-- roles-tagged: {tagged} -->\n"
    )


STOP_CASES: dict[str, tuple[str | None, bool]] = {
    "modelled-and-verified": (roles_doc("<!-- stop-scene: ok; modelled -->"), True),
    "waived-and-verified": (
        roles_doc(
            "<!-- stop-scene: ok; waived; the site only reads a nightly import -->"
        ),
        True,
    ),
    "problem-reported": (
        roles_doc("<!-- stop-scene: todo; Book: no stop scene is declared -->"),
        False,
    ),
    "one-of-two-books-todo": (
        roles_doc(
            "<!-- stop-scene: ok; modelled -->",
            "<!-- stop-scene: todo; Orders: no stop scene is declared -->",
        ),
        False,
    ),
    "no-roles-doc": (None, False),
}


def write_outputs(out: Path, roles: str | None, gate_passes: bool) -> None:
    for rel in SHARED:
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(TEMPLATE / rel, out / rel)
    (out / "Spec").mkdir(exist_ok=True)
    (out / "Spec" / "emergency_stop.qnt").write_text(KEYWORD_MODEL, encoding="utf-8")
    (out / "README.md").write_text(f"# Project\n\n{OLD_WAIVER}\n", encoding="utf-8")
    if roles is not None:
        (out / "docs" / "generated").mkdir(parents=True, exist_ok=True)
        (out / "docs" / "generated" / "roles.md").write_text(roles, encoding="utf-8")
    if gate_passes:
        (out / "justfile").write_text("check:\n    @true\n", encoding="utf-8")


def graded(tmp_path: Path, roles: str | None, gate_passes: bool, topic: str) -> dict:
    run = tmp_path / "run"
    write_outputs(run / "outputs", roles, gate_passes)
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
    return next(e for e in expectations if topic in e["text"].lower())


def status_lines(tmp_path: Path, roles: str | None, topic: str) -> list[str]:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    write_outputs(project, roles, gate_passes=False)
    # As SKILL.md runs it: without -I, so it imports its sibling modules.
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    lines = [
        line
        for line in result.stdout.splitlines()
        if topic in line.lower() and "[" in line
    ]
    assert lines, result.stdout
    return lines


@pytest.mark.parametrize("case", sorted(STOP_CASES))
def test_grader_reads_the_stop_scene_only_from_the_verified_declaration(
    tmp_path: Path, case: str
) -> None:
    roles, accepted = STOP_CASES[case]
    item = graded(tmp_path, roles, gate_passes=True, topic="stop scene")
    assert item["passed"] is accepted, item


def test_grader_requires_the_gate_to_pass_for_the_stop_scene(tmp_path: Path) -> None:
    roles = roles_doc("<!-- stop-scene: ok; modelled -->")
    assert not graded(tmp_path, roles, gate_passes=False, topic="stop scene")["passed"]


@pytest.mark.parametrize("case", sorted(STOP_CASES))
def test_status_reads_the_stop_scene_only_from_the_verified_declaration(
    tmp_path: Path, case: str
) -> None:
    roles, accepted = STOP_CASES[case]
    lines = status_lines(tmp_path, roles, topic="stop scene")
    assert all(("[done]" in line) is accepted for line in lines), lines


@pytest.mark.parametrize(("tagged", "accepted"), [(2, False), (3, True)])
def test_role_mapping_is_read_from_the_tags_on_terms(
    tmp_path: Path, tagged: int, accepted: bool
) -> None:
    roles = roles_doc("<!-- stop-scene: ok; modelled -->", tagged=tagged)
    item = graded(tmp_path / "grade", roles, gate_passes=True, topic="tagged")
    assert item["passed"] is accepted, item
    lines = status_lines(tmp_path / "status", roles, topic="tagged")
    assert all(("[done]" in line) is accepted for line in lines), lines


def test_skill_declares_the_stop_scene_in_the_glossary() -> None:
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    description = skill.split("\n---", 1)[0]
    assert "can stop itself autonomously" not in description
    assert "stopScene" in skill
    assert "role := some" in skill
    docs = {
        name: (SKILL / "references" / name).read_text(encoding="utf-8")
        for name in ("patterns.md", "runbook.md", "documents.md")
    }
    assert "stopScene" in docs["patterns.md"]
    assert "stopScene" in docs["runbook.md"]
    for text in [skill, *docs.values()]:
        assert "stop-scene: none" not in text


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


# Every question states its basis in the glossary, and question-check verifies it. `just generate`
# writes one machine line per glossary into docs/generated/questions.md; the grader and status.py
# read only that. A question document full of the words "反例" or "定理" counts for nothing.
WORDY_QUESTIONS = (
    "# 質問\n\n- 反例 `Spec/a.qnt` の定理 invariant により、返金するか\n" * 9
)


def questions_doc(total: int, witnessed: int) -> str:
    line = f"<!-- questions: {total}; with-counterexample: {witnessed}; outside-model: {total - witnessed} -->"
    return f"# Questions\n\n## Book\n\n{line}\n"


QUESTION_CASES: dict[str, tuple[str | None, bool, bool]] = {
    # name: (questions.md, at least 8 questions, at least one backed by a counterexample)
    "enough-and-witnessed": (questions_doc(9, 4), True, True),
    "none-witnessed": (questions_doc(9, 0), True, False),
    "too-few": (questions_doc(5, 2), False, True),
    "no-machine-line": (None, False, False),
}


def graded_questions(
    tmp_path: Path, questions: str | None, gate_passes: bool
) -> list[dict]:
    run = tmp_path / "run"
    out = run / "outputs"
    write_outputs(out, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes)
    (out / "docs" / "questions.md").write_text(WORDY_QUESTIONS, encoding="utf-8")
    if questions is not None:
        (out / "docs" / "generated" / "questions.md").write_text(
            questions, encoding="utf-8"
        )
    subprocess.run(
        [sys.executable, "-I", str(SKILL / "evals" / "grade.py"), str(run)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return json.loads((run / "grading.json").read_text(encoding="utf-8"))[
        "expectations"
    ]


def item(expectations: list[dict], topic: str) -> dict:
    return next(e for e in expectations if topic in e["text"].lower())


@pytest.mark.parametrize("case", sorted(QUESTION_CASES))
def test_grader_reads_questions_only_from_the_verified_counts(
    tmp_path: Path, case: str
) -> None:
    questions, enough, witnessed = QUESTION_CASES[case]
    expectations = graded_questions(tmp_path, questions, gate_passes=True)
    assert item(expectations, "at least 8 questions")["passed"] is enough
    assert item(expectations, "backed by a counterexample")["passed"] is witnessed


def test_grader_requires_the_gate_for_the_question_basis(tmp_path: Path) -> None:
    expectations = graded_questions(tmp_path, questions_doc(9, 4), gate_passes=False)
    assert not item(expectations, "backed by a counterexample")["passed"]


@pytest.mark.parametrize("case", sorted(QUESTION_CASES))
def test_status_reads_questions_only_from_the_verified_counts(
    tmp_path: Path, case: str
) -> None:
    questions, _, witnessed = QUESTION_CASES[case]
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    write_outputs(
        project, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes=False
    )
    (project / "docs" / "questions.md").write_text(WORDY_QUESTIONS, encoding="utf-8")
    if questions is not None:
        (project / "docs" / "generated" / "questions.md").write_text(
            questions, encoding="utf-8"
        )
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    lines = [
        line
        for line in result.stdout.splitlines()
        if "backed by a counterexample" in line
    ]
    assert lines, result.stdout
    assert all(("[done]" in line) is witnessed for line in lines), lines
