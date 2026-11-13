"""Shared helpers for the experiment scripts: run Quint at the project's pinned version.

The project pins Quint in the file `quint-version` and runs it through bunx, as the justfile does.
Set QUINT to use an installed binary instead (for example QUINT=quint).
"""
import os
import pathlib
import re
import shlex
import subprocess
import time


def quint_command(project: pathlib.Path) -> list[str]:
    override = os.environ.get("QUINT")
    if override:
        return shlex.split(override)
    pinned = project / "quint-version"
    if not pinned.is_file():
        raise SystemExit(f"{project} has no quint-version file. Pass the glossary project folder "
                         "(the one that holds lakefile.toml and quint-version), or set QUINT.")
    version = pinned.read_text().strip()
    return ["bunx", f"@informalsystems/quint@{version}"]


def run_quint(project: pathlib.Path, args: list[str], timeout: int = 900) -> tuple[int, str]:
    """Run Quint. Retries when Apalache's port is still held by another run."""
    for attempt in range(6):
        done = subprocess.run(quint_command(project) + args, cwd=project, capture_output=True,
                              text=True, timeout=timeout)
        text = done.stdout + done.stderr
        if "Address already in use" not in text and "Failed to fetch from GitHub" not in text:
            return done.returncode, text
        time.sleep(5 * (attempt + 1))
    return done.returncode, text


def module_span(source: str, module: str) -> tuple[int, int]:
    """Offsets of the opening brace and the matching closing brace of `module <name> { ... }`."""
    found = re.search(rf"^\s*module\s+{re.escape(module)}\s*\{{", source, re.M)
    if not found:
        raise ValueError(f"module {module} not found")
    depth, i = 0, found.end() - 1
    while i < len(source):
        if source.startswith("//", i):
            i = source.find("\n", i)
            if i < 0:
                break
            continue
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                return found.end() - 1, i
        i += 1
    raise ValueError(f"module {module}: no matching closing brace")
