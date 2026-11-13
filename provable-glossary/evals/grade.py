"""Grade one run of the provable-glossary evals. Writes grading.json into the run directory.

The checks look at outcomes, not at the skill's own file layout, so a run without the skill can
pass them with differently named files. Checks that only make sense for the skill's layout are
marked "[layout]".

usage: python3 -I grade.py <run-dir>     (the directory that contains outputs/)
"""

import json
import pathlib
import re
import subprocess
import sys

run_dir = pathlib.Path(sys.argv[1]).resolve()
out = run_dir / "outputs"
# The grader runs from the skill (evals/grade.py) or from a copy in a workspace folder beside the skill.
HERE = pathlib.Path(__file__).resolve().parent
TEMPLATE = next(
    (
        candidate
        for candidate in (
            HERE.parent / "assets" / "template",
            HERE.parent / "provable-glossary" / "assets" / "template",
        )
        if candidate.is_dir()
    ),
    HERE.parent / "assets" / "template",
)
# The stop scene and the roles are read from the gate-verified docs/generated/roles.md, by the
# same code status.py uses. Nothing is judged by whether a word appears in a file.
sys.path.insert(0, str(TEMPLATE.parent.parent / "scripts"))
from shared_files import shared_changes  # noqa: E402
from generated_lines import (  # noqa: E402
    book_titles,
    control,
    holds_count,
    industry_complete,
    question_counts,
    roles_tagged,
    stop_scene,
)

GEN = "docs/" + "generated"
SKIP = {
    ".lake",
    ".git",
    "node_modules",
    "_apalache-out",
    "gen",
    "answers",
    "readings",
    "artifacts",
    "runs",
}
results = []


def add(text, passed, evidence):
    results.append(
        {"text": text, "passed": bool(passed), "evidence": str(evidence)[:400]}
    )


def sh(cmd, timeout=1800):
    try:
        r = subprocess.run(
            cmd, cwd=out, capture_output=True, text=True, timeout=timeout
        )
        return r.returncode, (r.stdout + r.stderr)
    except (
        Exception
    ) as err:  # a missing tool or a timeout is a failed check, not a crash
        return 999, repr(err)


def files(suffix):
    return [
        p
        for p in out.rglob(f"*{suffix}")
        if p.is_file() and not (SKIP & set(p.relative_to(out).parts))
    ]


def text_of(paths):
    return "\n".join(p.read_text(errors="replace") for p in paths)


def strip_lean_comments(src):
    src = re.sub(r"/-.*?-/", "", src, flags=re.DOTALL)
    return re.sub(r"--[^\n]*", "", src)


JA = re.compile(r"[ぁ-んァ-ヶ]")
lean, qnt, md = files(".lean"), files(".qnt"), files(".md")
authored_md = [
    p for p in md if GEN not in str(p.relative_to(out)) and p.name != "RUN_NOTES.md"
]
docs = text_of(authored_md)
all_text = text_of(md)

# 1. one command checks everything
if (out / "justfile").is_file():
    gate, (rc, log) = "just check", sh(["just", "check"])
else:
    scripts = [p for p in out.glob("*.sh")]
    if scripts:
        gate, (rc, log) = f"./{scripts[0].name}", sh(["bash", scripts[0].name])
    else:
        gate, (rc, log) = "none", (999, "no single entry point (no justfile, no *.sh)")
add(
    "One command runs every check and exits 0",
    rc == 0,
    f"{gate}: exit {rc}; {log[-160:]}",
)

# 2. Lean glossary and Quint models exist
add(
    "Has a Lean formalization and at least one Quint model",
    lean and qnt,
    f"{len(lean)} .lean, {len(qnt)} .qnt",
)

# 3. no sorry / axiom in code (comments ignored)
bad = [
    str(p.relative_to(out))
    for p in lean
    if re.search(
        r"\b(sorry|native_decide)\b|^\s*axiom\b",
        strip_lean_comments(p.read_text(errors="replace")),
        re.MULTILINE,
    )
]
add(
    "No sorry, native_decide or axiom in the Lean code",
    lean and not bad,
    bad or "clean",
)

# 4. at least one "holds" result, checked by the gate. The gate runs TLC on every .holds claim;
#    item 17 confirms the justfile is the template's, so the gate is the one that does this.
summary_md = (
    (out / GEN / "summary.md").read_text(errors="replace")
    if (out / GEN / "summary.md").is_file()
    else ""
)
holds = holds_count(summary_md)
add(
    "At least one 'holds' result is backed by the gate's exhaustive check (docs/generated/summary.md, and the gate exits 0)",
    bool(holds) and rc == 0,
    f"{holds} holds claims; gate exit {rc}" if holds is not None else "no evidence counts in docs/generated/summary.md",
)

# 5. the stop scene is declared in the glossary and the gate verifies it. A run without the skill
#    has no such declaration and fails this item by construction.
roles_md = (
    (out / GEN / "roles.md").read_text(errors="replace")
    if (out / GEN / "roles.md").is_file()
    else ""
)
stop_ok, stop_note = stop_scene(roles_md)
add(
    "The stop scene is declared in the glossary and the gate verifies it (docs/generated/roles.md, and the gate exits 0)",
    stop_ok and rc == 0,
    f"{stop_note}; gate exit {rc}",
)

# 6 and 7. questions for the business, read from the gate-verified docs/generated/questions.md.
#    question-check makes every question rest on counterexamples or say why no model shows it.
questions_md = (
    (out / GEN / "questions.md").read_text(errors="replace")
    if (out / GEN / "questions.md").is_file()
    else ""
)
counts = question_counts(questions_md)
total_q, witnessed_q = counts if counts else (0, 0)
add(
    "At least 8 questions for the business (docs/generated/questions.md)",
    total_q >= 8,
    f"{total_q} questions" if counts else "no question counts in docs/generated/questions.md",
)
add(
    "Every question states its basis, and at least one is backed by a counterexample (docs/generated/questions.md, and the gate exits 0)",
    witnessed_q >= 1 and rc == 0,
    f"{witnessed_q} of {total_q} backed by a counterexample; gate exit {rc}",
)

# 8. industry comparison with sources
urls = set(re.findall(r"https?://[^\s)>\]|]+", docs))
add(
    "The documents compare the questions with industry practice and cite at least 5 distinct source URLs",
    len(urls) >= 5,
    f"{len(urls)} URLs in authored documents",
)

# 9. questions classified against industry practice: every question carries its classification in
#    the glossary, at least half were researched, and the gate passes (question-check).
industry_ok, industry_note = industry_complete(questions_md)
add(
    "Each open question is classified against industry practice in the glossary, at least half researched (docs/generated/questions.md, and the gate exits 0)",
    industry_ok and rc == 0,
    f"{industry_note}; gate exit {rc}",
)

# 10. generated documents are separate and regenerable
gen_files = (
    sorted(p.name for p in (out / GEN).glob("*.md")) if (out / GEN).is_dir() else []
)
rc_gen, _ = (
    sh(["just", "generated-check"]) if (out / "justfile").is_file() else (999, "")
)
add(
    "Documents derived from the formalization are generated by a command and kept apart from authored ones",
    bool(gen_files) and rc_gen == 0,
    f"{GEN}: {gen_files}; regeneration check exit {rc_gen}",
)

# 11. hand edits to generated documents are rejected
tampered = False
if gen_files and rc_gen == 0:
    target = out / GEN / gen_files[0]
    original = target.read_bytes()
    target.write_bytes(original + b"hand edit\n")
    rc_t, _ = sh(["just", "generated-check"])
    target.write_bytes(original)
    tampered = rc_t != 0
hook = out / ".claude" / "hooks" / "protect_generated.py"
blocked = False
if hook.is_file():
    call = json.dumps(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": str(out / GEN / "glossary.md")},
        }
    )
    blocked = (
        subprocess.run(
            ["python3", "-I", str(hook)], input=call, capture_output=True, text=True
        ).returncode
        == 2
    )
add(
    "A hand edit to a generated document is rejected by the gate, and an edit hook blocks it beforehand",
    tampered and blocked,
    f"gate rejects tampering: {tampered}; hook blocks edit: {blocked}",
)

# 12. three verdicts
summary = (
    (out / GEN / "summary.md").read_text(errors="replace")
    if (out / GEN / "summary.md").is_file()
    else ""
)
nums = re.findall(
    r"\|\s*(?:合計|Total)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|",
    summary,
)
add(
    "Claims are counted by verdict (proved, counterexample, undecided), each at least 1",
    bool(nums) and all(int(x) >= 1 for x in nums[0][2:]),
    nums or "no machine-made count of claims by verdict",
)

# 13. control experiment: declared in Glossary/Registry.lean and verified by the gate (control-check:
#     for .run, some experiments/<name>/protocol.md was committed before result.md).
# 14. (limits and model sizes) is left to a reader: no check reads the meaning of prose.
declared = control(summary_md)
add(
    "The control experiment is declared run (preregistration verified by the gate) or skipped with a reason (docs/generated/summary.md, and the gate exits 0)",
    declared is not None and declared[0] in ("run", "skipped") and rc == 0,
    f"control {declared[0] if declared else 'not declared'}; gate exit {rc}",
)

# 15. documents are in the user's language
add(
    "The authored documents are in Japanese",
    len(JA.findall(docs)) > 500,
    f"{len(JA.findall(docs))} kana characters",
)

# 16. role mapping: the shared roles are tagged on terms in the glossary. The generated role table
#     lists every role, and an untagged role shows as none.
tagged = roles_tagged(roles_md)
add(
    "Terms are tagged with the shared roles: at least three roles (docs/generated/roles.md)",
    tagged >= 3,
    f"{tagged} roles tagged",
)

# 17. [layout] shared machinery untouched, starter removed


changed = shared_changes(out, TEMPLATE)
titles = book_titles(summary_md)
add(
    "[layout] Shared machinery is unchanged from the template and the starter glossary is removed",
    not changed and bool(titles) and "Starter" not in titles,
    changed or f"identical; glossaries: {titles}",
)

passed = sum(r["passed"] for r in results)
(run_dir / "grading.json").write_text(
    json.dumps(
        {
            "expectations": results,
            "summary": {
                "passed": passed,
                "failed": len(results) - passed,
                "total": len(results),
                "pass_rate": round(passed / len(results), 3),
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n"
)
print(f"{run_dir.parent.name}/{run_dir.name}: {passed}/{len(results)}")
for r in results:
    print(
        ("  ok  " if r["passed"] else "  NG  ")
        + r["text"]
        + "  ["
        + r["evidence"][:90]
        + "]"
    )
