"""The scripts print ✅ and ❌; a console that cannot encode them must not
crash them.

A Japanese Windows console writes cp932, which has neither character, so a
clean `just audit` used to die with UnicodeEncodeError. PYTHONIOENCODING=cp932
gives the child that same stdout on every OS, so CI on Linux reproduces it.
"""

import os
import subprocess
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
NOT_A_SKILL = 2  # compare.py exits 2 for a directory without SKILL.md


def _run(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        env={**os.environ, "PYTHONIOENCODING": "cp932"},
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def _skill(root: Path, name: str) -> None:
    (root / name).mkdir()
    (root / name / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: Does {name}.\n---\n", encoding="utf-8"
    )


def test_audit_reports_on_a_cp932_console(tmp_path: Path) -> None:
    result = _run("audit.py", "--skills-dir", str(tmp_path))
    assert "Traceback" not in result.stderr
    assert "✅ audit: 0 skills, 0 finding(s)" in result.stdout
    assert result.returncode == 0


def test_readme_index_reports_on_a_cp932_console(tmp_path: Path) -> None:
    _skill(tmp_path, "alpha")
    readme = tmp_path / "README.md"
    readme.write_text(
        "# skills\n\n<!-- skills-index:start -->\n<!-- skills-index:end -->\n\n"
        "<!-- credits:start -->\n<!-- credits:end -->\n",
        encoding="utf-8",
    )
    result = _run(
        "readme_index.py", "--skills-dir", str(tmp_path), "--readme", str(readme)
    )
    assert "Traceback" not in result.stderr
    assert "✅ regenerated tables" in result.stdout
    assert result.returncode == 0


def test_compare_reports_on_a_cp932_console(tmp_path: Path) -> None:
    result = _run("compare.py", str(tmp_path))
    assert "Traceback" not in result.stderr
    assert "❌ not a skill directory" in result.stdout
    assert result.returncode == NOT_A_SKILL
