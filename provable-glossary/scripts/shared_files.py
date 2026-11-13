"""Find where a project's shared machinery differs from the skill's template.

The shared machinery is the same in every project and is never edited per project: every
`Glossary/*.lean` of the template except `Starter.lean` and `Registry.lean` (the rules and their
tests live there: StopScene, Questions, Control), `Main.lean`, and the `justfile` (`mod.just` in
the subdir layout). A file counts as unchanged when it equals the current template or any earlier
version of it in the skill's git history, so a project started from an older template is not
blamed for the skill's later edits. A rule file the project does not have at all came from an older
template (`Main.lean` imports the rule files, so a project missing one that its `Main.lean` needs
does not build).

`lakefile.toml` is not compared byte for byte: a project may add options or packages (the mathlib
case). What must hold is the setting: `leanOptions` turns on `linter.extra`.

Used by scripts/status.py and evals/grade.py.
"""

import pathlib
import subprocess
import tomllib

PER_PROJECT = {"Starter.lean", "Registry.lean"}


def shared_paths(template: pathlib.Path) -> list[str]:
    glossary = sorted(
        f"Glossary/{p.name}"
        for p in (template / "Glossary").glob("*.lean")
        if p.name not in PER_PROJECT
    )
    return [*glossary, "Main.lean", "justfile"]


def template_versions(template: pathlib.Path, rel: str) -> set[bytes]:
    """The current template file and every earlier version of it in the skill's git history."""
    versions = {(template / rel).read_bytes()}
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=template,
        capture_output=True,
        text=True,
        check=False,
    )
    if top.returncode != 0:  # not in a git checkout: only the current template is known
        return versions
    repo = pathlib.Path(top.stdout.strip())
    path = str((template / rel).resolve().relative_to(repo.resolve()))
    commits = subprocess.run(
        ["git", "log", "--format=%H", "--", path],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    for commit in commits.stdout.split():
        blob = subprocess.run(
            ["git", "show", f"{commit}:{path}"],
            cwd=repo,
            capture_output=True,
            check=False,
        )
        if blob.returncode == 0:
            versions.add(blob.stdout)
    return versions


def linter_extra_on(lakefile: pathlib.Path) -> bool:
    try:
        config = tomllib.loads(lakefile.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return False
    return config.get("leanOptions", {}).get("linter", {}).get("extra") is True


def shared_changes(project: pathlib.Path, template: pathlib.Path) -> list[str]:
    """The shared files that differ from every version of the template, or are missing."""
    changed = []
    for rel in shared_paths(template):
        here = project / rel
        if (
            rel == "justfile"
            and not here.is_file()
            and (project / "mod.just").is_file()
        ):
            here = project / "mod.just"
        if not here.is_file():
            if rel.startswith("Glossary/"):
                continue  # added to the template after this project started
            changed.append(rel)
            continue
        if here.read_bytes() not in template_versions(template, rel):
            changed.append(rel)
    if not linter_extra_on(project / "lakefile.toml"):
        changed.append("lakefile.toml (leanOptions must turn on linter.extra)")
    return changed
