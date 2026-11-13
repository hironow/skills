"""Start a provable-glossary project from the template.

usage: python3 init_project.py <repo-dir> [--subdir NAME | --root] [--packages-from <project>]

Two layouts:

  root layout    the glossary project IS the repository. Used when <repo-dir> holds no code and no build manifest.
                 Commands: `just generate`, `just check`.

  subdir layout  the glossary project lives in <repo-dir>/<NAME>/ beside existing code.
                 Used automatically (NAME = glossary) when <repo-dir> already holds code or a build manifest.
                 The template's justfile becomes <NAME>/mod.just and the repository's root
                 justfile gets one line, `mod <NAME>`, so the root stays the only entry point.
                 Commands: `just <NAME> generate`, `just <NAME> check`.

What it does, in both layouts:
  - copies assets/template/ into the project directory (never over an existing Glossary/ folder)
  - installs the edit-blocking hook at the repository root (.claude/hooks/, merged into an
    existing .claude/settings.json; the previous file is kept as settings.json.bak)
  - turns on a git pre-commit hook that runs generated-check, unless the repository already
    configures hooks (then it prints the one line to add to them)
  - initialises git if the directory is not a repository

--packages-from is only for the special case where the project will add mathlib: it reuses the
downloaded Lean packages of another project on this machine that pins the same versions.
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

TEMPLATE = pathlib.Path(__file__).resolve().parent.parent / "assets" / "template"
HOOK_COMMAND = 'python3 -I "$CLAUDE_PROJECT_DIR/.claude/hooks/protect_generated.py"'
CODE_SUFFIXES = {
    ".go", ".rs", ".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".rb", ".cs", ".php",
    ".swift", ".scala", ".ex", ".exs", ".sql", ".proto", ".graphql",
}
MANIFESTS = {
    "justfile", "Justfile", "Makefile", "package.json", "go.mod", "Cargo.toml", "pyproject.toml",
    "pom.xml", "build.gradle", "build.gradle.kts", "Gemfile", "composer.json", "mix.exs",
}
SKIP_DIRS = {
    ".git", ".lake", "node_modules", "vendor", "target", "dist", "build", ".venv", "venv",
    ".claude", ".githooks",
}


def holds_an_implementation(repo: pathlib.Path) -> bool:
    """True when the directory already holds code or a build manifest. Notes and a README do not count."""
    if any((repo / name).exists() for name in MANIFESTS):
        return True
    stack = [repo]
    while stack:
        for entry in stack.pop().iterdir():
            if entry.is_symlink():
                continue
            if entry.is_dir() and entry.name not in SKIP_DIRS:
                stack.append(entry)
            elif entry.is_file() and entry.suffix in CODE_SUFFIXES:
                return True
    return False


def git(repo: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)


def install_hook(repo: pathlib.Path) -> None:
    hooks = repo / ".claude" / "hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        TEMPLATE / "dot-claude" / "hooks" / "protect_generated.py",
        hooks / "protect_generated.py",
    )
    settings_path = repo / ".claude" / "settings.json"
    settings = {}
    if settings_path.exists():
        shutil.copy2(settings_path, settings_path.with_suffix(".json.bak"))
        settings = json.loads(settings_path.read_text() or "{}")
    entries = settings.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if "protect_generated.py" not in json.dumps(entries):
        entries.append(
            {
                "matcher": "Edit|Write|NotebookEdit|Bash",
                "hooks": [{"type": "command", "command": HOOK_COMMAND}],
            }
        )
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n")


def install_pre_commit(repo: pathlib.Path, recipe: str) -> str:
    """Returns a note for the user."""
    configured = git(repo, "config", "core.hooksPath").stdout.strip()
    other = [
        name
        for name in (
            ".pre-commit-config.yaml",
            ".husky",
            "lefthook.yml",
            "lefthook.yaml",
        )
        if (repo / name).exists()
    ]
    # Setting core.hooksPath would silently stop every hook in .git/hooks (commit-msg, pre-push...),
    # so any hook already there means: leave the configuration alone and say what to add.
    hooks_dir = repo / ".git" / "hooks"
    existing = (
        sorted(
            p.name
            for p in hooks_dir.iterdir()
            if p.is_file() and not p.name.endswith(".sample")
        )
        if hooks_dir.is_dir()
        else []
    )
    if (configured and configured != ".githooks") or other or existing:
        managed = configured or ", ".join(other) or ", ".join(f".git/hooks/{n}" for n in existing)
        return (
            f"pre-commit: this repository already manages git hooks ({managed}); core.hooksPath was left as it is. "
            f"Add this command to its pre-commit hook yourself: {recipe}"
        )
    hook = repo / ".githooks" / "pre-commit"
    hook.parent.mkdir(exist_ok=True)
    line = recipe + "\n"
    if hook.exists():
        if recipe not in hook.read_text():
            hook.write_text(hook.read_text().rstrip("\n") + "\n" + line)
    else:
        hook.write_text(
            "#!/usr/bin/env bash\n# Stop a commit whose generated documents do not match the glossaries.\n"
            "set -euo pipefail\n" + line
        )
    hook.chmod(0o755)
    git(repo, "config", "core.hooksPath", ".githooks")
    return "pre-commit: enabled (.githooks/pre-commit)"


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("repo")
    layout = parser.add_mutually_exclusive_group()
    layout.add_argument(
        "--subdir",
        help="put the glossary project in this folder of an existing repository",
    )
    layout.add_argument("--root", action="store_true", help="force the root layout")
    parser.add_argument(
        "--packages-from", help="an existing project whose .lake/packages to reuse"
    )
    args = parser.parse_args()

    repo = pathlib.Path(args.repo).resolve()
    repo.mkdir(parents=True, exist_ok=True)
    if not (repo / ".git").exists():
        # A tracked folder inside another repository is not a repository of its own.
        outer = git(repo, "rev-parse", "--show-toplevel")
        if outer.returncode == 0 and git(repo, "check-ignore", "-q", str(repo)).returncode != 0:
            top = pathlib.Path(outer.stdout.strip())
            print(
                f"init_project: {repo} is a folder inside the repository {top}.\n"
                f"Pass the repository root and name the folder: init_project.py {top} --subdir {repo.relative_to(top)}",
                file=sys.stderr,
            )
            return 1
    subdir = args.subdir or ("glossary" if holds_an_implementation(repo) and not args.root else None)
    project = repo / subdir if subdir else repo
    if (project / "Glossary").exists():
        print(
            f"init_project: {project}/Glossary already exists; not overwriting",
            file=sys.stderr,
        )
        return 1
    if subdir and not args.subdir:
        print(
            f"init_project: {repo} already holds an implementation, so the glossary project goes into {subdir}/ "
            "(pass --root to put it at the top, or --subdir NAME to choose the folder)"
        )

    project.mkdir(parents=True, exist_ok=True)
    for source in sorted(TEMPLATE.iterdir()):
        if source.name in ("dot-claude", "dot-githooks"):
            continue  # installed at the repository root below
        name = ".gitignore" if source.name == "dot-gitignore" else source.name
        if subdir and name == "justfile":
            name = "mod.just"
        dest = project / name
        if dest.exists() and not dest.is_dir():
            print(f"init_project: kept the existing {dest.relative_to(repo)}")
            continue
        if source.is_dir():
            shutil.copytree(source, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(source, dest)
    (project / "docs" / "generated").mkdir(parents=True, exist_ok=True)

    if args.packages_from:
        packages = pathlib.Path(args.packages_from).resolve() / ".lake" / "packages"
        if not packages.is_dir():
            print(f"init_project: {packages} not found", file=sys.stderr)
            return 1
        (project / ".lake").mkdir(exist_ok=True)
        clone = (
            ["cp", "-Rc"]
            if sys.platform == "darwin"
            else ["cp", "-R", "--reflink=auto"]
        )
        subprocess.run(
            clone + [str(packages), str(project / ".lake" / "packages")], check=True
        )

    if not (repo / ".git").exists():
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    if subdir:
        root_just = repo / "justfile"
        line = f"mod {subdir}"
        if root_just.exists():
            if line not in root_just.read_text().splitlines():
                root_just.write_text(
                    root_just.read_text().rstrip("\n")
                    + f"\n\n# Provable glossary: `just {subdir} check`, `just {subdir} generate`\n{line}\n"
                )
        else:
            root_just.write_text(
                f"# Provable glossary: `just {subdir} check`, `just {subdir} generate`\n{line}\n"
            )
    prefix = f"just {subdir} " if subdir else "just "

    if subdir:
        # scan_terms.py writes scratch tables here; keep them out of the repository
        ignore = repo / ".gitignore"
        lines = ignore.read_text().splitlines() if ignore.exists() else []
        if "/glossary-scan/" not in lines:
            ignore.write_text("\n".join([*lines, "/glossary-scan/"]) + "\n")

    install_hook(repo)
    note = install_pre_commit(repo, prefix + "generated-check")

    print(f"init_project: created the glossary project in {project}")
    print(note)
    print(f"layout: {'subdir' if subdir else 'root'}; run commands from {repo}")
    print(f"next: {prefix}generate && {prefix}check")
    return 0


if __name__ == "__main__":
    sys.exit(main())
