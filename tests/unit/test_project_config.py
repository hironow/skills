"""Guard the maintenance tooling's public-PyPI project and committed lock.

The previous checks enforced the Flatt route from dotfiles ADR 0028. This
emergency cutover does not amend that Accepted ADR; its successor needs a
separate decision. Public provenance and age are not malware certification.
"""

import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_declares_public_pypi_as_the_only_default() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert project["tool"]["uv"]["index"] == [
        {"name": "pypi", "url": "https://pypi.org/simple/", "default": True}
    ]


def test_lock_references_only_public_pypi_artifacts() -> None:
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert "pypi.flatt.tech" not in lock
    for package in tomllib.loads(lock)["package"]:
        registry = package["source"].get("registry")
        if registry:
            assert registry == "https://pypi.org/simple/"
        for artifact in (
            [package["sdist"]] if "sdist" in package else []
        ) + package.get("wheels", []):
            if "url" in artifact:
                assert artifact["url"].startswith("https://files.pythonhosted.org/")


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
