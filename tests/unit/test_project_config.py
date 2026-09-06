"""Guards on the tooling's own uv project configuration.

dotfiles ADR 0028: every uv project resolves through the malware-scanning
Flatt Security PyPI mirror, and no committed lock falls back to raw pypi.org.
dotfiles enforces this for its own projects with a fixed project list that
cannot reach into this repository, so the same two checks live here.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_pyproject_declares_the_flatt_index_as_default() -> None:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'url = "https://pypi.flatt.tech/simple/"' in text
    assert "default = true" in text


def test_lock_never_references_raw_pypi() -> None:
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert 'registry = "https://pypi.org/simple"' not in lock
