"""Show how far a provable-glossary project has come and what to do next.

usage: python3 status.py <repo-or-project-dir> [--run-check]

Looks only at files (and, with --run-check, runs the gate). It prints one line per item, marked
done or todo, grouped in three tiers, and ends with the next action. Run it whenever you are
unsure what remains. The tiers:

  Tier 1  required  a checked glossary, the stop scene declared and verified, questions, README and findings,
                    and the control declared (.skipped "<reason>" unless one was run)
  Tier 2  expected  the comparison with industry practice
  Tier 3  optional  a control experiment (control := .run) and a policy draft

Each line states its own threshold. Hints name the step of SKILL.md's workflow ("workflow step N").
"""
import pathlib
import re
import sys


# The sibling modules live beside this script; `python3 -I` leaves this folder off the path.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from detect_start import CODE_SUFFIXES
from glossary_project import just, just_prefix, locate, repo_root, walk_files
from shared_files import shared_changes  # noqa: E402
from generated_lines import book_titles, control, stop_waived_everywhere, industry_complete, roles_tagged, stop_scene

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

    titles = book_titles(read(project / "docs" / "generated" / "summary.md"))
    domain_registered = any(title != "Starter" for title in titles)
    starter_gone = "Starter" not in titles and not (project / "Glossary" / "Starter.lean").exists()
    item(1, domain_registered, "a domain glossary is registered in Glossary/Registry.lean",
         "write Glossary/<Domain>.lean and add it to Registry.lean and Glossary.lean")
    item(1, starter_gone, "the starter glossary and Spec/starter.qnt are removed",
         "delete Glossary/Starter.lean, Spec/starter.qnt and their lines in Glossary.lean, Audit.lean, Spec/tests.txt, Registry.lean")
    template = pathlib.Path(__file__).resolve().parent.parent / "assets" / "template"
    differs = shared_changes(project, template)
    item(1, not differs, "the shared machinery matches the skill's template" + (f" (differs: {', '.join(differs)})" if differs else ""),
         "restore these files from the template; fix the glossary or the model instead. If the skill was updated after "
         "this project started, a file can differ from the current template without having been edited: say so in the README")

    summary = read(project / "docs" / "generated" / "summary.md")
    total = re.findall(r"\|\s*(?:合計|Total)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|", summary)
    terms, claims, proved, counter, undecided = (int(x) for x in total[0]) if total else (0, 0, 0, 0, 0)
    item(1, terms >= 8 and domain_registered, f"at least 8 terms ({terms} now)", "add the terms the scenes need")
    roles_md = read(project / "docs" / "generated" / "roles.md")
    waived = stop_waived_everywhere(roles_md)
    item(1, proved >= 1 and (counter >= 1 or waived),
         f"claims with evidence: at least 1 proved and, unless the stop scene is waived, 1 counterexample "
         f"({proved} proved, {counter} counterexample now)",
         "follow pattern 4 in references/patterns.md: naive design, counterexample, repair")
    item(1, undecided >= 3, f"at least 3 open questions recorded as undecided claims ({undecided} now)",
         "turn what the design cannot settle into `.question` claims")

    stop_ok, stop_note = stop_scene(roles_md)
    item(1, stop_ok, "the stop scene is declared in the glossary and verified (docs/generated/roles.md)",
         "declare stopScene in the book (.modelled after pattern 4, or .waived \"<reason>\" if nothing is in flight), "
         f"then `{prefix}generate`. Now: " + stop_note)
    tagged = roles_tagged(roles_md)
    item(1, tagged >= 1, f"terms are tagged with the shared roles: at least 1, and every term that plays one ({tagged} roles tagged now)",
         "add role := some .<role> to the terms that play one; do not invent a term for a role. See SKILL.md, \"Map the domain onto shared roles\"")

    # In the root layout the repository is the glossary project itself, so there is no separate implementation.
    has_code = project != repo and sum(1 for p in walk_files(repo) if p.suffix in CODE_SUFFIXES) >= 3
    anchors = read(project / "docs" / "generated" / "anchors.md")
    anchor_rows = len([l for l in anchors.splitlines() if l.startswith("| ") and "`" in l])
    if has_code:
        item(1, anchor_rows >= 5, f"terms are anchored to the implementation: at least 5 anchors ({anchor_rows} now)",
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

    findings = read(project / "docs" / "findings.md")
    item(1, len(findings) > 500, f"docs/findings.md is written: more than 500 characters ({len(findings)} now; a reader checks the limits and model sizes)",
         "see references/documents.md")

    gaps = read(project / "docs" / "business-gaps.md")
    industry_ok, industry_note = industry_complete(read(project / "docs" / "generated" / "questions.md"))
    item(2, industry_ok, f"every question is classified against industry practice in the glossary ({industry_note})",
         "give each question industry := some (.answered/.notAsked/.gap \"<what was found>\") or some .notResearched; "
         "research at least half. See references/industry-check.md")
    item(2, len(set(URL.findall(gaps))) >= 3, f"docs/business-gaps.md compares the questions with industry practice: "
         f"at least 3 source URLs ({len(set(URL.findall(gaps)))} now)", "workflow step 6; see references/industry-check.md")

    declared = control(read(project / "docs" / "generated" / "summary.md"))
    item(1, declared is not None and declared[0] in ("run", "skipped"),
         f"the control experiment is declared ({declared[0] if declared else 'no declaration'}; `{prefix}check` verifies it)",
         "set control := .skipped \"<reason>\" in Glossary/Registry.lean if you stop before Tier 3 (workflow step 5), "
         f"then `{prefix}generate`")
    policy = list((project / "docs").glob("*policy*.md"))
    item(3, declared is not None and declared[0] == "run",
         "a control experiment ran: control := .run, and control-check finds a protocol committed before its result",
         "workflow step 5; see references/experiments.md")
    item(3, policy, "a policy draft for a gap exists beside its check results", "workflow step 7; pattern 11")

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
        # Every open item, in tier order: one that cannot be closed here (a file the environment
        # refuses to write) must not hide the rest.
        print("NEXT, in this order:")
        for tier, text, hint in todo:
            print(f"  (tier {tier}) {text}\n      how: {hint}")
    else:
        print(f"NEXT: nothing left on this list. Run `{prefix}check` and scripts/check_protection.py, then finish the documents.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
