"""Shared helpers: find the glossary project inside a repository and run its `just` recipes.

A project is a directory that holds `lakefile.toml` and `Glossary/Core.lean`. It is either the
repository root (root layout, with `justfile`) or a subfolder (subdir layout, with `mod.just`).
"""
import pathlib
import subprocess

SKIP_DIRS = {".git", ".lake", "node_modules", "vendor", "target", "dist", "build", ".venv", "venv",
             "__pycache__", "_apalache-out", ".next", ".idea", ".vscode", "third_party", "Pods",
             ".claude", ".githooks", "glossary-scan"}


def is_project(path: pathlib.Path) -> bool:
    return (path / "lakefile.toml").is_file() and (path / "Glossary" / "Core.lean").is_file()


def locate(path: pathlib.Path) -> pathlib.Path | None:
    """The project directory at `path` or one level below it, or None."""
    path = path.resolve()
    if is_project(path):
        return path
    for child in sorted(p for p in path.iterdir() if p.is_dir() and p.name not in SKIP_DIRS):
        if is_project(child):
            return child
    return None


def repo_root(project: pathlib.Path) -> pathlib.Path:
    """The nearest directory at or above the project that has its own `.git`; else the project."""
    for candidate in [project, *project.parents]:
        if (candidate / ".git").exists():
            # A project in a folder the outer repository ignores is not part of that repository.
            ignored = subprocess.run(["git", "check-ignore", "-q", str(project)], cwd=candidate,
                                     capture_output=True).returncode == 0
            return project if candidate != project and ignored else candidate
    return project


def just(project: pathlib.Path, recipe: str, timeout: int = 3600) -> subprocess.CompletedProcess:
    """Run one recipe of the project, whichever layout it uses."""
    justfile = project / "justfile" if (project / "justfile").is_file() else project / "mod.just"
    return subprocess.run(["just", "--justfile", str(justfile), "--working-directory", str(project), recipe],
                          capture_output=True, text=True, timeout=timeout)


def just_prefix(project: pathlib.Path) -> str:
    """How a person types the recipes, from the repository root."""
    return "just " if (project / "justfile").is_file() else f"just {project.name} "


def walk_files(root: pathlib.Path):
    """Every file under root, skipping dependency, build and tool folders."""
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if entry.name not in SKIP_DIRS and not is_project(entry):
                    stack.append(entry)
            elif entry.is_file():
                yield entry
