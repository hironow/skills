"""Decide which starting point a repository is in. Run this first.

usage: python3 detect_start.py <repo-dir>

  A  greenfield   no glossary and little or no implementation -> references/start-greenfield.md
  B  from code    an implementation exists, no glossary       -> references/start-from-code.md
  C  migration    a glossary people maintain already exists   -> references/start-migrate.md

The script only counts files and looks for glossary-like documents. It prints the evidence so
you can overrule it: if it is wrong, say which starting point you chose and why in the README.
"""
import json
import pathlib
import re
import sys


# The sibling modules live beside this script; `python3 -I` leaves this folder off the path.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from glossary_project import locate, walk_files
from import_glossary import parse_glossary

CODE_SUFFIXES = {".go", ".rs", ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".rb", ".cs", ".php",
                 ".swift", ".scala", ".ex", ".exs", ".sql", ".proto", ".graphql"}
GLOSSARY_NAME = re.compile(r"glossar|ubiquitous|terminolog|domain[-_ ]?language|用語|語彙|^terms\.", re.I)
GLOSSARY_SUFFIXES = {".md", ".markdown", ".yaml", ".yml", ".json", ".csv", ".tsv", ".txt", ".adoc", ".rst"}


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    repo = pathlib.Path(sys.argv[1]).resolve()
    project = locate(repo) if repo.is_dir() else None
    code_files, code_lines, glossaries = 0, 0, []
    if repo.is_dir():
        for path in walk_files(repo):
            if path.suffix in CODE_SUFFIXES:
                code_files += 1
                try:
                    code_lines += sum(1 for _ in path.open(errors="replace"))
                except OSError:
                    pass
            elif path.suffix.lower() in GLOSSARY_SUFFIXES and GLOSSARY_NAME.search(path.name):
                try:
                    entries = parse_glossary(path)
                except Exception:  # an unreadable candidate is simply not a glossary
                    entries = []
                if len(entries) >= 3:
                    glossaries.append((str(path.relative_to(repo)), len(entries)))
    has_code = code_files >= 3 or code_lines >= 200
    if glossaries:
        start, playbook = "C", "references/start-migrate.md"
        reason = "a glossary document with at least 3 entries exists"
    elif has_code:
        start, playbook = "B", "references/start-from-code.md"
        reason = "an implementation exists and no glossary document was found"
    else:
        start, playbook = "A", "references/start-greenfield.md"
        reason = "no glossary document and little or no implementation"
    print(f"starting point: {start} ({reason})")
    print(f"read next:      {playbook}")
    print(f"code:           {code_files} source files, {code_lines} lines")
    print("glossary files: " + (", ".join(f"{name} ({n} entries)" for name, n in glossaries) or "none found"))
    if project:
        print(f"note:           a provable-glossary project already exists at {project}; run status.py on it instead")
    if start == "C" and not has_code:
        print("note:           no implementation found; skip the code anchors in the migration playbook")
    print(json.dumps({"start": start, "code_files": code_files, "code_lines": code_lines,
                      "glossaries": glossaries, "project": str(project) if project else None}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
