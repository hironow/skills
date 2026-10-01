"""Guards on the tooling's own uv project configuration.

dotfiles ADR 0028: every uv project resolves through the malware-scanning
Flatt Security PyPI mirror, and no committed lock falls back to raw pypi.org.
dotfiles enforces this for its own projects with a fixed project list that
cannot reach into this repository, so the same two checks live here.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_declares_the_flatt_index_as_default() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'url = "https://pypi.flatt.tech/simple/"' in text
    assert "default = true" in text


def test_lock_never_references_raw_pypi() -> None:
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'registry = "https://pypi.org/simple"' not in lock


def _groups() -> dict[str, list[str]]:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    return pyproject["dependency-groups"]


def test_ruff_and_ty_are_the_lint_group_pinned_exactly() -> None:
    # dotfiles ADR 0044 / python-tooling spoke: ruff and ty pinned exactly, in
    # a group of their own so the gate can run them without the dev tools
    lint = _groups()["lint"]
    assert sorted(spec.split("==")[0] for spec in lint) == ["ruff", "ty"]
    assert all("==" in spec for spec in lint)
    assert not [s for s in _groups()["dev"] if s.startswith(("ruff", "ty"))]


def test_the_gate_runs_ruff_alone_and_ty_with_the_project() -> None:
    # ruff only parses source; ty resolves imports, so it needs the default
    # groups too (`--group`, not `--only-group`)
    justfile = (ROOT / "justfile").read_text(encoding="utf-8")
    runs = [
        ln.strip() for ln in justfile.splitlines() if ln.strip().startswith("uv run")
    ]
    ruff_lines = [ln for ln in runs if " ruff " in ln]
    ty_lines = [ln for ln in runs if " ty " in ln]
    assert ruff_lines
    assert all(
        ln.startswith("uv run --locked --only-group lint ruff ") for ln in ruff_lines
    )
    assert ty_lines == ["uv run --locked --group lint ty check"]
