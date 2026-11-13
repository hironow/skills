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
TEMPLATE = (
    pathlib.Path(__file__).resolve().parent.parent
    / "provable-glossary"
    / "assets"
    / "template"
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

# 4. exhaustive state exploration backs at least one "holds" result
gate_sources = text_of(
    [p for p in [out / "justfile", *out.glob("*.sh")] if p.is_file()]
)
exhaustive = bool(
    re.search(
        r"quint[^\n]*\bverify\b|\bverify\b[^\n]*--backend|apalache-mc|tlc2",
        gate_sources,
    )
)
add(
    "The gate backs at least one 'holds' result with exhaustive state exploration (TLC or Apalache), not only random simulation",
    exhaustive and rc == 0,
    f"verify in gate: {exhaustive}",
)

# 5. the emergency stop is modelled and something is shown to break
models = text_of(qnt)
add(
    "The emergency stop is modelled in Quint, and the gate expects at least one property to be violated",
    bool(re.search(r"emergency|halt|stop|freeze|緊急|停止", models, re.IGNORECASE))
    and bool(
        re.search(
            r"violat|反例|counterexample|exit 1|negative", gate_sources + all_text, re.IGNORECASE
        )
    ),
    "searched models, gate and documents",
)

# 6. open questions for the business
question_files = [p for p in md if re.search(r"question|質問|未決", p.name, re.IGNORECASE)]
qtext = text_of(question_files)
q_items = len(
    re.findall(r"^\s*(?:[-*]|\d+[.)]|\|\s*(?!-)[^|\n]{8,}\|)|^#+\s*Q\d+", qtext, re.MULTILINE)
)
add(
    "At least 8 questions for the business are listed in a dedicated document",
    q_items >= 8,
    f"{[p.name for p in question_files]}: {q_items} items",
)

# 7. questions are tied to machine evidence
add(
    "Open questions are linked to machine evidence (a counterexample, an invariant or a theorem name)",
    bool(
        re.search(
            r"`[A-Za-z_][\w./]*\.(qnt|lean)`|`\w+\.\w+`|反例|counterexample|定理|invariant",
            qtext,
        )
    ),
    "searched the question document",
)

# 8. industry comparison with sources
urls = set(re.findall(r"https?://[^\s)>\]|]+", docs))
add(
    "The documents compare the questions with industry practice and cite at least 5 distinct source URLs",
    len(urls) >= 5,
    f"{len(urls)} URLs in authored documents",
)

# 9. questions classified against industry practice
add(
    "Each open question is classified against industry practice (answered / not asked here / gap, or equivalent)",
    bool(re.search(r"\|[^\n]*分類[^\n]*\|", docs) or re.search(r"答えあり|問われない|解決済み|決着済み", docs))
    and "空白" in docs,
    "searched authored documents",
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

# 13. control experiment
protocols = [p for p in md if p.name == "protocol.md"]
results_md = [p for p in md if p.name == "result.md"]
skipped = bool(
    re.search(r"対照[^\n]*(飛ばし|実行していない|行っていない|スキップ|省略)", docs)
)
add(
    "A comparison with a tool-less control was preregistered and run, or the documents say it was skipped",
    (protocols and results_md) or skipped,
    f"{len(protocols)} protocols, {len(results_md)} results, skip stated: {skipped}",
)

# 14. limits and model sizes
add(
    "The documents state limits and the size of the models",
    "限界" in docs
    and bool(re.search(r"\d+\s*状態|状態数|\d\s*人|\d\s*枠|\d\s*つ", docs)),
    "searched authored documents",
)

# 15. documents are in the user's language
add(
    "The authored documents are in Japanese",
    len(JA.findall(docs)) > 500,
    f"{len(JA.findall(docs))} kana characters",
)

# 16. role mapping, with missing roles marked
readme = (
    (out / "README.md").read_text(errors="replace")
    if (out / "README.md").is_file()
    else ""
)
role_table = re.search(r"^#+[^\n]*(役割|[Rr]ole)[^\n]*\n(.*?)(?=^#+ |\Z)", readme, re.S | re.M)
role_rows = [
    line
    for line in (role_table.group(2) if role_table else "").splitlines()
    if line.startswith("|") and not line.startswith("|-")
]
roles = max(len(role_rows) - 1, 0)  # minus the header row
none_marked = bool(re.search(r"\|\s*(なし|none)", readme))
if "p2p" in str(run_dir):
    add(
        "README maps the domain onto the shared roles and marks the roles that do not exist as none",
        roles >= 6 and none_marked,
        f"{roles} rows in the role table; none marked: {none_marked}",
    )
else:
    add(
        "README maps the domain onto the shared roles",
        roles >= 6,
        f"{roles} rows in the role table",
    )

# 17. [layout] shared machinery untouched, starter removed


def template_versions(rel):
    """Every version of a template file in the skill's history: a run is compared with the
    template it was started from, not with later edits to the template."""
    repo = TEMPLATE.parents[3]
    path = str((TEMPLATE / rel).relative_to(repo))
    commits = subprocess.run(["git", "log", "--format=%H", "--", path], cwd=repo, capture_output=True, text=True)
    versions = {(TEMPLATE / rel).read_bytes()}
    for commit in commits.stdout.split():
        blob = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=repo, capture_output=True)
        if blob.returncode == 0:
            versions.add(blob.stdout)
    return versions


changed = [
    rel
    for rel in [
        "Glossary/Core.lean",
        "Glossary/Claim.lean",
        "Glossary/Render.lean",
        "Main.lean",
        "justfile",
    ]
    if not (out / rel).is_file() or (out / rel).read_bytes() not in template_versions(rel)
]
registry = (
    (out / "Glossary/Registry.lean").read_text(errors="replace")
    if (out / "Glossary/Registry.lean").is_file()
    else ""
)
add(
    "[layout] Shared machinery is unchanged from the template and the starter glossary is removed",
    not changed and registry and "Starter" not in registry,
    changed or "identical; starter removed",
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
