"""Unit tests for scripts/compare.py (fork vs upstream quantitative pass).

The comparison is deterministic and cheap: per-version size (lines, words,
estimated tokens, description length), frontmatter sanity, tooling-rule
violations in the body, and pairwise SKILL.md diff sizes. It is the first
step of the fork-dedup playbook, before any judge model reads the files.
"""

from pathlib import Path

import pytest
from compare import diff_lines, main, metrics


def _skill(root: Path, name: str, body: str, desc: str = "Use when asked.") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {desc}\n---\n{body}", encoding="utf-8"
    )
    return d


def test_metrics_reports_sizes_and_frontmatter(tmp_path: Path) -> None:
    words = ["One", "two", "three", "four", "five"]
    body = "# Fork\n\n" + " ".join(words) + ".\n"
    d = _skill(tmp_path, "fork", body)
    m = metrics(d)
    assert m["name==dir"] is True
    # `lines` spans the whole file (frontmatter included); `words(body)` counts
    # the heading word too, but not the `#` marker
    frontmatter_lines = 4
    assert m["lines"] == frontmatter_lines + len(body.splitlines())
    assert m["words(body)"] == len(words) + 1
    assert m["desc_chars"] == len("Use when asked.")
    assert m["violations"] == {}


def test_metrics_flags_tooling_violations_only_in_commands(tmp_path: Path) -> None:
    body = (
        "# F\n\nRun `npm install foo` then `pip install bar`.\n"
        "Please make sure the tests pass.\n"
    )
    m = metrics(_skill(tmp_path, "fork", body))
    assert m["violations"] == {"npm": 1, "pip/poetry": 1}


def test_diff_lines_counts_changed_lines(tmp_path: Path) -> None:
    a_lines = ["line one", "line two"]
    b_lines = ["line one", "line changed", "line added"]
    a = _skill(tmp_path, "a", "# A\n\n" + "\n".join(a_lines) + "\n")
    b = _skill(tmp_path, "b", "# A\n\n" + "\n".join(b_lines) + "\n")
    assert diff_lines(a, b) == len(set(a_lines) ^ set(b_lines))


def test_main_prints_a_table_for_every_version(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    a = _skill(tmp_path, "fork", "# A\n\nbody\n")
    b = _skill(tmp_path, "upstream", "# A\n\nbody more\n")
    assert main([str(a), str(b)]) == 0
    out = capsys.readouterr().out
    assert "fork" in out
    assert "upstream" in out
    assert "diff lines" in out
