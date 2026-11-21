"""Keep code-SSOT governance, rules registry schema, and consultation rules aligned."""

import tomllib
from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "decision-record-governance"


def text(name: str) -> str:
    return (SKILL / name).read_text(encoding="utf-8")


def test_no_standalone_adr_or_pdr_files_and_triage_comes_first() -> None:
    instructions = text("SKILL.md")
    assert "## 0. Triage" in instructions
    assert "Never create a `docs/adr/` or `docs/pdr/` file." in instructions
    assert "provable-glossary" in instructions
    assert "docs/rules.toml" in instructions
    for removed in ("adr-template.md", "pdr-template.md", "decision-queue.md"):
        assert not (SKILL / "templates" / removed).exists()


def test_github_contacts_and_blocking_rules_stay_mandatory() -> None:
    instructions = text("SKILL.md")
    assert "author_contact" in instructions
    assert "decision_maker_contact" in instructions
    assert "Never fabricate a handle" in instructions
    reference = text("REFERENCE.md")
    assert "Prefer a GitHub `@handle`" in reference
    assert "If `author_contact` is missing, block proposal" in reference
    assert "If `decision_maker_contact` is missing, block settlement" in reference


def test_conflicts_still_require_original_people_and_a_human_ruling() -> None:
    instructions = text("SKILL.md")
    assert (
        "The AI resolving, patching, or ignoring a contradiction is forbidden."
        in instructions
    )
    reference = text("REFERENCE.md").split("## 6. Consistency check", 1)[1]
    assert "`decision_maker_contact` and `author_contact`" in reference
    assert "stop immediately" in reference
    assert "human ruling is recorded" in reference


def test_chat_ruling_alone_cannot_settle_a_rule() -> None:
    instructions = text("SKILL.md")
    assert (
        "A chat ruling counts only once copied to a stable URL recorded in `consultation_url`."
        in instructions
    )
    rubric = text("RUBRIC.md")
    assert "ephemeral chat" in rubric
    assert "durable consultation and human ruling" in rubric


def test_rules_toml_template_is_valid_toml_with_required_audit_fields() -> None:
    raw = text("templates/rules.toml")
    parsed = tomllib.loads(raw)
    rules = parsed["rule"]
    assert len(rules) == 1
    rule = rules[0]
    for field in (
        "id",
        "level",
        "text",
        "scope",
        "area",
        "enforced_by",
        "state",
        "exceptions",
        "author_contact",
        "decision_maker_contact",
        "decided_date",
        "consultation_url",
    ):
        assert field in rule, f"missing field in templates/rules.toml: {field}"


def test_rubric_enforces_settling_gates() -> None:
    rubric = text("RUBRIC.md")
    assert (
        "Gate criteria (must be 2 at the settling gate): **R1, R3, R5, R7**." in rubric
    )
    assert "Creates a `docs/adr/` file" in rubric
