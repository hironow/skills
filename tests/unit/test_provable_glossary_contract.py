"""Keep the public copy of provable-glossary usable where it is published."""

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import ModuleType

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
    assert "'justfile'" in grading


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


# Each question carries its industry classification in the glossary; `just generate` counts them
# into a machine line of docs/generated/questions.md. A business-gaps document full of 分類,
# 答えあり and 空白 counts for nothing.
WORDY_GAPS = "| 質問 | 分類 |\n|---|---|\n| 返金 | 答えあり |\n| 停止 | 空白 |\n| 振替 | 問われない |\n"


def industry_doc(total: int, classified: int, researched: int) -> str:
    return (
        questions_doc(total, 1)
        + f"<!-- industry: classified: {classified}; researched: {researched} -->\n"
    )


INDUSTRY_CASES: dict[str, tuple[str, bool]] = {
    "all-classified-mostly-researched": (industry_doc(10, 10, 7), True),
    "one-unclassified": (industry_doc(10, 9, 9), False),
    "all-marked-not-researched": (industry_doc(10, 10, 0), False),
    "less-than-half-researched": (industry_doc(10, 10, 4), False),
    "no-machine-line": (questions_doc(10, 1), False),
}


@pytest.mark.parametrize("case", sorted(INDUSTRY_CASES))
def test_grader_reads_the_industry_classification_only_from_the_counts(
    tmp_path: Path, case: str
) -> None:
    questions, accepted = INDUSTRY_CASES[case]
    run = tmp_path / "run"
    out = run / "outputs"
    write_outputs(out, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes=True)
    (out / "docs" / "business-gaps.md").write_text(WORDY_GAPS, encoding="utf-8")
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
    expectations = json.loads((run / "grading.json").read_text(encoding="utf-8"))[
        "expectations"
    ]
    assert (
        item(expectations, "classified against industry practice")["passed"] is accepted
    )


@pytest.mark.parametrize("case", sorted(INDUSTRY_CASES))
def test_status_reads_the_industry_classification_only_from_the_counts(
    tmp_path: Path, case: str
) -> None:
    questions, accepted = INDUSTRY_CASES[case]
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    write_outputs(
        project, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes=False
    )
    (project / "docs" / "business-gaps.md").write_text(WORDY_GAPS, encoding="utf-8")
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
        if "classified against industry practice" in line
    ]
    assert lines, result.stdout
    assert all(("[done]" in line) is accepted for line in lines), lines


# The summary carries machine lines: each glossary's title, the kinds of Quint evidence, and the
# control declaration (verified by control-check). Documents that say "対照実験は省略した",
# "限界" or "verify" count for nothing.
WORDY_FINDINGS = (
    "# 結果と限界\n\n対照実験は省略した。モデルは 3 状態。\n" + "限界の説明。" * 120
)
WORDY_JUSTFILE = "check:\n    @true\n\n# quint verify --backend tlc\n"


def summary_doc(
    *books: str, holds: int = 1, control: str = "<!-- control: run -->"
) -> str:
    lines = [f"<!-- book: {title} -->" for title in books]
    lines += [f"<!-- evidence: holds: {holds}; violated: 2 -->", control]
    return "# Summary\n\n" + "\n".join(lines) + "\n"


def grade_with_summary(
    tmp_path: Path, summary: str | None, gate_passes: bool
) -> list[dict]:
    run = tmp_path / "run"
    out = run / "outputs"
    write_outputs(out, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes)
    if gate_passes:
        (out / "justfile").write_text(WORDY_JUSTFILE, encoding="utf-8")
    (out / "docs" / "findings.md").write_text(WORDY_FINDINGS, encoding="utf-8")
    if summary is not None:
        (out / "docs" / "generated" / "summary.md").write_text(
            summary, encoding="utf-8"
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


@pytest.mark.parametrize(
    ("summary", "gate_passes", "accepted"),
    [
        (summary_doc("Rooms", holds=2), True, True),
        (summary_doc("Rooms", holds=0), True, False),
        (summary_doc("Rooms", holds=2), False, False),
        (None, True, False),
    ],
)
def test_grader_reads_exhaustive_holds_from_the_summary(
    tmp_path: Path, summary: str | None, gate_passes: bool, accepted: bool
) -> None:
    expectations = grade_with_summary(tmp_path, summary, gate_passes)
    assert item(expectations, "exhaustive")["passed"] is accepted


@pytest.mark.parametrize(
    ("control", "gate_passes", "accepted"),
    [
        ("<!-- control: run -->", True, True),
        ("<!-- control: skipped; no time was left after Tier 2 -->", True, True),
        ("<!-- control: undeclared -->", True, False),
        ("<!-- control: run -->", False, False),
    ],
)
def test_grader_reads_the_control_declaration_from_the_summary(
    tmp_path: Path, control: str, gate_passes: bool, accepted: bool
) -> None:
    expectations = grade_with_summary(
        tmp_path, summary_doc("Rooms", control=control), gate_passes
    )
    assert item(expectations, "control")["passed"] is accepted


def test_grader_does_not_judge_limits_by_words(tmp_path: Path) -> None:
    expectations = grade_with_summary(tmp_path, summary_doc("Rooms"), gate_passes=True)
    assert not [e for e in expectations if "limits" in e["text"].lower()]


def status_output(
    tmp_path: Path, summary: str | None, starter_file: bool = False
) -> str:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    if not starter_file:
        (project / "Glossary" / "Starter.lean").unlink()
    write_outputs(
        project, roles_doc("<!-- stop-scene: ok; modelled -->"), gate_passes=False
    )
    (project / "docs" / "findings.md").write_text("所見。" * 200, encoding="utf-8")
    if summary is not None:
        (project / "docs" / "generated" / "summary.md").write_text(
            summary, encoding="utf-8"
        )
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    return result.stdout


def status_item(output: str, topic: str) -> bool:
    lines = [line for line in output.splitlines() if topic in line and "[" in line]
    assert lines, output
    return all("[done]" in line for line in lines)


@pytest.mark.parametrize(
    ("control", "accepted"),
    [
        ("<!-- control: run -->", True),
        ("<!-- control: skipped; no time was left after Tier 2 -->", True),
        ("<!-- control: undeclared -->", False),
    ],
)
def test_status_reads_the_control_declaration(
    tmp_path: Path, control: str, accepted: bool
) -> None:
    output = status_output(tmp_path, summary_doc("Rooms", control=control))
    assert status_item(output, "control experiment") is accepted


def test_status_finds_the_domain_glossary_by_the_summary_titles(tmp_path: Path) -> None:
    assert status_item(
        status_output(tmp_path / "a", summary_doc("Rooms")), "domain glossary"
    )
    assert not status_item(
        status_output(tmp_path / "b", summary_doc("Starter")), "domain glossary"
    )
    assert not status_item(
        status_output(tmp_path / "c", summary_doc("Rooms", "Starter")),
        "starter glossary",
    )


def test_status_does_not_judge_the_findings_by_words(tmp_path: Path) -> None:
    # The findings fixture has no 限界 and no "limit": its length is all status.py may judge.
    assert status_item(
        status_output(tmp_path, summary_doc("Rooms")), "docs/findings.md"
    )


# --- Review fixes, first part: correctness and loopholes -------------------------------------

SHARED_RULE_FILES = [
    "Glossary/StopScene.lean",
    "Glossary/Questions.lean",
    "Glossary/Control.lean",
]


def load_script(name: str) -> ModuleType:
    """Import one of the skill's scripts the way it runs: from its own folder."""
    spec = importlib.util.spec_from_file_location(
        name, SKILL / "scripts" / f"{name}.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def project_copy(tmp_path: Path, edit: dict[str, str]) -> Path:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    for rel, text in edit.items():
        (project / rel).write_text(text, encoding="utf-8")
    return project


def loosened(rel: str) -> str:
    return (TEMPLATE / rel).read_text(encoding="utf-8") + "\n-- loosened by the run\n"


@pytest.mark.parametrize("rel", SHARED_RULE_FILES)
def test_shared_files_catch_an_edited_rule_file(tmp_path: Path, rel: str) -> None:
    shared = load_script("shared_files")
    project = project_copy(tmp_path, {rel: loosened(rel)})
    assert shared.shared_changes(project, TEMPLATE) == [rel]


def test_shared_files_pass_an_untouched_project(tmp_path: Path) -> None:
    shared = load_script("shared_files")
    assert shared.shared_changes(project_copy(tmp_path, {}), TEMPLATE) == []


def test_shared_files_skip_a_rule_file_added_after_the_project_started(
    tmp_path: Path,
) -> None:
    shared = load_script("shared_files")
    project = project_copy(tmp_path, {})
    (project / "Glossary" / "Control.lean").unlink()
    assert shared.shared_changes(project, TEMPLATE) == []


def test_shared_files_read_the_lakefile_setting_not_its_bytes(tmp_path: Path) -> None:
    shared = load_script("shared_files")
    lakefile = (TEMPLATE / "lakefile.toml").read_text(encoding="utf-8")
    with_mathlib = (
        lakefile + '\n[[require]]\nname = "mathlib"\nscope = "leanprover-community"\n'
    )
    assert (
        shared.shared_changes(
            project_copy(tmp_path / "a", {"lakefile.toml": with_mathlib}), TEMPLATE
        )
        == []
    )
    linter_off = lakefile.replace("linter.extra = true", "linter.extra = false")
    assert linter_off != lakefile
    changes = shared.shared_changes(
        project_copy(tmp_path / "b", {"lakefile.toml": linter_off}), TEMPLATE
    )
    assert len(changes) == 1
    assert changes[0].startswith("lakefile.toml")


def test_every_doc_names_the_rule_files_as_shared() -> None:
    agents = (TEMPLATE / "AGENTS.md").read_text(encoding="utf-8")
    skill = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    for text in (agents, skill):
        for rel in SHARED_RULE_FILES:
            assert Path(rel).name in text, rel


def test_industry_examples_give_every_class_its_note() -> None:
    for rel in ("SKILL.md", "references/lean-and-quint.md"):
        text = (SKILL / rel).read_text(encoding="utf-8")
        assert not re.search(r"`\.(notAsked|gap)`", text), rel


@pytest.mark.parametrize(
    "script", ["status.py", "detect_start.py", "check_protection.py", "scan_terms.py"]
)
def test_scripts_import_their_siblings_in_isolated_mode(
    tmp_path: Path, script: str
) -> None:
    result = subprocess.run(
        [sys.executable, "-I", str(SKILL / "scripts" / script), str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert "ModuleNotFoundError" not in result.stderr, result.stderr[-500:]


def test_init_keeps_existing_git_hooks(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    hook = repo / ".git" / "hooks" / "commit-msg"
    hook.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    hook.chmod(0o755)
    subprocess.run(
        [sys.executable, "-I", str(SKILL / "scripts" / "init_project.py"), str(repo)],
        capture_output=True,
        text=True,
        timeout=300,
        check=True,
    )
    configured = subprocess.run(
        ["git", "-C", str(repo), "config", "core.hooksPath"],
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()
    assert configured == "", "core.hooksPath would stop .git/hooks/commit-msg"


def test_status_shows_how_to_close_every_open_item(tmp_path: Path) -> None:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    todo = [line for line in result.stdout.splitlines() if "[todo]" in line]
    hows = [
        line for line in result.stdout.splitlines() if line.strip().startswith("how:")
    ]
    assert len(todo) > 1
    assert len(hows) == len(todo), result.stdout


@pytest.mark.parametrize(("edited", "accepted"), [(False, True), (True, False)])
def test_status_reports_edited_shared_machinery(
    tmp_path: Path, edited: bool, accepted: bool
) -> None:
    project = tmp_path / "project"
    shutil.copytree(TEMPLATE, project)
    if edited:
        rel = "Glossary/StopScene.lean"
        (project / rel).write_text(loosened(rel), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SKILL / "scripts" / "status.py"), str(project)],
        capture_output=True,
        text=True,
        timeout=120,
        check=True,
    )
    assert status_item(result.stdout, "shared machinery") is accepted
