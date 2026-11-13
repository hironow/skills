"""Check that a project protects its generated documents.

Runs the edit-blocking hook against sample tool calls, then tampers with docs/generated in three
ways (edit a file, add a file, remove a file) and confirms that `just generated-check` rejects each.
It restores the documents with `just generate` afterwards.

usage: python3 check_protection.py <repo-or-project-dir>
"""

import json
import pathlib
import subprocess
import sys

from glossary_project import just, locate, repo_root

project = locate(pathlib.Path(sys.argv[1]))
if project is None:
    sys.exit(f"check_protection: no provable-glossary project found at {sys.argv[1]}")
root = repo_root(project)  # the hook lives at the repository root
hook = root / ".claude" / "hooks" / "protect_generated.py"
gen = project / "docs" / "generated"
G = str(gen.relative_to(root))


def hook_exit(call):
    return subprocess.run(
        ["python3", "-I", str(hook)],
        input=json.dumps(call),
        capture_output=True,
        text=True,
    ).returncode


def gate_exit():
    return just(project, "generated-check").returncode


def regenerate():
    if just(project, "generate").returncode != 0:
        sys.exit("check_protection: `generate` failed")


cases = [
    (
        "Edit a generated document",
        {"tool_name": "Edit", "tool_input": {"file_path": f"{root}/{G}/glossary.md"}},
        2,
    ),
    (
        "Write a new file into the generated folder",
        {"tool_name": "Write", "tool_input": {"file_path": f"{G}/new.md"}},
        2,
    ),
    (
        "Edit an authored document",
        {"tool_name": "Edit", "tool_input": {"file_path": f"{root}/docs/findings.md"}},
        0,
    ),
    (
        "Bash append",
        {"tool_name": "Bash", "tool_input": {"command": f"echo x >> {G}/summary.md"}},
        2,
    ),
    (
        "Bash sed -i",
        {
            "tool_name": "Bash",
            "tool_input": {"command": f"sed -i '' s/a/b/ {G}/glossary.md"},
        },
        2,
    ),
    (
        "Bash rm",
        {"tool_name": "Bash", "tool_input": {"command": f"rm {G}/questions.md"}},
        2,
    ),
    (
        "Bash just generate",
        {"tool_name": "Bash", "tool_input": {"command": "just generate && just check"}},
        0,
    ),
    (
        "Bash read only",
        {"tool_name": "Bash", "tool_input": {"command": f"cat {G}/summary.md | head"}},
        0,
    ),
    (
        "Bash text with a comparison and the folder name only",
        {"tool_name": "Bash", "tool_input": {"command": f"python3 -c 'print(1 > 0, \"{G}/summary.md\")'"}},
        0,
    ),
    (
        "Bash redirect elsewhere, then read a generated document",
        {"tool_name": "Bash", "tool_input": {"command": f"echo ok > /tmp/x.txt; cat {G}/summary.md"}},
        0,
    ),
    ("Bash overwrite", {"tool_name": "Bash", "tool_input": {"command": f"echo x > {G}/summary.md"}}, 2),
    ("Bash tee after a pipe", {"tool_name": "Bash", "tool_input": {"command": f"echo x | tee {G}/summary.md"}}, 2),
]
failed = 0
for name, call, want in cases:
    got = hook_exit(call)
    failed += got != want
    print(f"hook  {'ok ' if got == want else 'NG '} {name}: exit {got} (expected {want})")

regenerate()
checks = []
checks.append(("untouched", gate_exit(), 0))
p = gen / "summary.md"
p.write_text(p.read_text() + "a line added by hand\n")
checks.append(("content edited", gate_exit(), 1))
regenerate()
(gen / "notes.md").write_text("a file written by hand\n")
checks.append(("file added", gate_exit(), 1))
(gen / "notes.md").unlink()
(gen / "questions.md").unlink()
checks.append(("file removed", gate_exit(), 1))
regenerate()
checks.append(("after regenerating", gate_exit(), 0))
for name, got, want in checks:
    failed += got != want
    print(f"gate  {'ok ' if got == want else 'NG '} {name}: exit {got} (expected {want})")
sys.exit(1 if failed else 0)
