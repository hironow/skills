"""Show how far a provable-glossary project has come and what to do next.

usage: python3 status.py <repo-or-project-dir> [--run-check]

Looks only at files (and, with --run-check, runs the gate). It prints one line per item, marked
done or todo, grouped in three tiers, and ends with the next action. Run it whenever you are
unsure what remains. The tiers:

  Tier 1  required  a checked glossary, the stop scene (or a recorded reason there is none), questions, README and findings
  Tier 2  expected  the comparison with industry practice
  Tier 3  optional  a control experiment and a policy draft (say so in the documents if skipped)
"""
import pathlib
import re
import sys

from detect_start import CODE_SUFFIXES
from glossary_project import just, just_prefix, locate, repo_root, walk_files
from stop_waiver import IN_FLIGHT_ROLES, stop_waiver

URL = re.compile(r"https?://[^\s)>\]|]+")


def read(path: pathlib.Path) -> str:
    return path.read_text(errors="replace") if path.is_file() else ""


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    start = pathlib.Path(args[0]).resolve()
    project = locate(start)
    if project is None:
        print("status: no provable-glossary project here yet.")
        print("NEXT: run detect_start.py on the repository, then init_project.py")
        return 0
    repo = repo_root(project)
    prefix = just_prefix(project)
    items = []  # (tier, done, text, hint)

    def item(tier, done, text, hint=""):
        items.append((tier, bool(done), text, hint))

    registry = read(project / "Glossary" / "Registry.lean")
    domain_registered = bool(re.search(r"\.book\.view", registry.replace("Starter.book.view", "")))
    starter_gone = "Starter" not in registry and not (project / "Glossary" / "Starter.lean").exists()
    item(1, domain_registered, "a domain glossary is registered in Glossary/Registry.lean",
         "write Glossary/<Domain>.lean and add it to Registry.lean and Glossary.lean")
    item(1, starter_gone, "the starter glossary and Spec/starter.qnt are removed",
         "delete Glossary/Starter.lean, Spec/starter.qnt and their lines in Glossary.lean, Audit.lean, Spec/tests.txt, Registry.lean")

    summary = read(project / "docs" / "generated" / "summary.md")
    total = re.findall(r"\|\s*(?:合計|Total)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", summary)
    terms, claims, proved, counter, undecided = (int(x) for x in total[0]) if total else (0, 0, 0, 0, 0)
    item(1, terms >= 8 and domain_registered, f"at least 8 terms ({terms} now)", "add the terms the scenes need")
    item(1, proved >= 1 and counter >= 1, f"claims with evidence: {proved} proved, {counter} counterexample",
         "follow pattern 4 in references/patterns.md: naive design, counterexample, repair")
    item(1, undecided >= 3, f"at least 3 open questions recorded as undecided claims ({undecided} now)",
         "turn what the design cannot settle into `.question` claims")

    specs = "\n".join(read(p) for p in (project / "Spec").glob("*.qnt") if p.name != "starter.qnt")
    waived, waiver_note = stop_waiver(read(project / "README.md"))
    item(1, waived or re.search(r"emergency|halt|stop|freeze|lockdown|shutdown|suspend|kill.?switch|緊急|停止|遮断|ロックダウン", specs, re.I),
         "the stop scene is modelled in Spec/, or the README waives it and its role table agrees",
         "write the stop scene (pattern 4). Waive it only if the role table maps "
         + ", ".join(IN_FLIGHT_ROLES) + " to none; " + waiver_note)

    # In the root layout the repository is the glossary project itself, so there is no separate implementation.
    has_code = project != repo and sum(1 for p in walk_files(repo) if p.suffix in CODE_SUFFIXES) >= 3
    anchors = read(project / "docs" / "generated" / "anchors.md")
    anchor_rows = len([l for l in anchors.splitlines() if l.startswith("| ") and "`" in l])
    if has_code:
        item(1, anchor_rows >= 5, f"terms are anchored to the implementation ({anchor_rows} anchors now)",
             "give each term that exists in the code an `anchors := [\"path#text\"]` entry; see references/start-from-code.md")
    legacy = project / "migration" / "legacy.tsv"
    if legacy.is_file():
        mapping = {}
        for line in read(project / "migration" / "mapping.tsv").splitlines()[1:]:
            cells = line.split("\t")
            if cells and cells[0]:
                mapping[cells[0]] = cells[1] if len(cells) > 1 else ""
        legacy_terms = [l.split("\t")[0] for l in read(legacy).splitlines()[1:] if l.strip()]
        open_rows = [t for t in dict.fromkeys(legacy_terms) if mapping.get(t, "") not in ("mapped", "retired")]
        item(1, not open_rows, f"every legacy term is mapped or retired ({len(open_rows)} still open)",
             "fill in migration/mapping.tsv; see references/start-migrate.md")

    readme = read(project / "README.md") or read(repo / "README.md")
    item(1, re.search(r"^#+[^\n]*(役割|[Rr]ole)", readme, re.M), "README has the role table",
         "see references/documents.md")
    findings = read(project / "docs" / "findings.md")
    item(1, len(findings) > 500 and re.search(r"限界|[Ll]imit", findings), "docs/findings.md states findings and limits",
         "see references/documents.md")

    gaps = read(project / "docs" / "business-gaps.md")
    item(2, len(set(URL.findall(gaps))) >= 3, f"docs/business-gaps.md compares the questions with industry practice "
         f"({len(set(URL.findall(gaps)))} source URLs now)", "step 6; see references/industry-check.md")

    experiments = project / "experiments"
    ran = any(experiments.glob("*/protocol.md")) and any(experiments.glob("*/result.md"))
    skipped = re.search(r"対照[^\n]*(飛ばし|実行して(い)?ない|行って(い)?ない|実施して(い)?ない|未実施|スキップ|省略|見送)|control[^\n]*(skipped|not run)", findings + readme, re.I)
    item(3, ran or skipped, "a control experiment ran, or the documents say it was skipped",
         "step 5; see references/experiments.md")
    policy = list((project / "docs").glob("*policy*.md"))
    item(3, policy, "a policy draft for a gap exists beside its check results", "step 7; pattern 11")

    if "--run-check" in sys.argv:
        done = just(project, "check")
        item(1, done.returncode == 0, f"`{prefix}check` exits 0", (done.stdout + done.stderr)[-400:])

    print(f"project: {project}   (commands: {prefix}check, {prefix}generate)")
    for tier, label in ((1, "Tier 1 (required)"), (2, "Tier 2 (expected)"), (3, "Tier 3 (optional)")):
        print(label)
        for t, done, text, _ in items:
            if t == tier:
                print(f"  [{'done' if done else 'todo'}] {text}")
    todo = [(t, text, hint) for t, done, text, hint in items if not done]
    if todo:
        tier, text, hint = todo[0]
        print(f"NEXT (tier {tier}): {text}\n      how: {hint}")
    else:
        print(f"NEXT: nothing left on this list. Run `{prefix}check` and scripts/check_protection.py, then finish the documents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
