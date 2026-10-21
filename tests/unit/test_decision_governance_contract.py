"""Keep approved consultation and trace requirements aligned across the skill."""

from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[2] / "decision-record-governance"


def text(name: str) -> str:
    return (SKILL / name).read_text(encoding="utf-8")


def test_github_is_preferred_without_requiring_slack() -> None:
    instructions = text("SKILL.md")
    assert "GitHub is preferred" in instructions
    assert "Slack is optional" in instructions
    for document in (instructions, text("REFERENCE.md")):
        assert "ask the user to post it by hand" in document
        assert "never skip the consultation itself" in document
    reference = text("REFERENCE.md")
    assert "Prefer a GitHub `@handle`" in reference
    assert "If the author contact cannot be found, block registration" in reference
    assert (
        "If the decision-maker contact cannot be found, block settlement" in reference
    )


def test_conflicts_still_require_original_people_and_a_human_ruling() -> None:
    reference = text("REFERENCE.md").split("### 10.3", 1)[1]
    assert "`decision-maker` and `author` of the conflicting DR" in reference
    assert "Consultation is mandatory" in reference
    assert "The AI does not decide" in reference
    assert "Open a durable consultation thread" in reference
    assert "stable URL/reference" in reference


def test_chat_ruling_alone_cannot_settle_a_record() -> None:
    instructions = text("SKILL.md")
    assert "involved person is present" in instructions
    assert "before settlement" in instructions
    reference = text("REFERENCE.md")
    assert "copy that ruling to a stable URL/reference" in reference
    assert "the chat alone is not the durable record" in reference


@pytest.mark.parametrize("name", ["adr-template.md", "pdr-template.md"])
def test_templates_keep_contacts_trace_and_disposition_actions(name: str) -> None:
    template = text(f"templates/{name}")
    lines = template.splitlines()
    assert "- **status**: Proposed" in lines
    for field in ("author-contact", "decision-maker-contact", "consultation-trace"):
        assert f"- **{field}**:" in template
    assert "author-slack" not in template
    assert "Rejectedの理由" in template
    assert "Deferredの再検討条件" in template
    assert "Reject時のアクション" in template
    assert "Deferred時のアクション" in template


def test_decided_log_retains_people_and_consultation_evidence() -> None:
    queue = text("templates/decision-queue.md")
    meaning = next(
        line for line in queue.splitlines() if line.startswith("> **状態の意味**")
    )
    for word in ("`Accepted`", "`Rejected`", "`Deferred`", "supersede", "再検討条件"):
        assert word in meaning
    assert "新しい `Proposed` 記録を起票" in meaning
    assert "記録本文を書き換えず" not in meaning  # immutability is per-outcome now
    decided = queue.split("## 2. 決定済みログ", 1)[1]
    heading = next(line for line in decided.splitlines() if line.startswith("| ID |"))
    for column in ("作者", "作者連絡先", "決定者", "決裁者連絡先", "相談記録", "備考"):
        assert f"| {column} |" in heading
    assert "必要に応じて" in decided  # settlement notices stay conditional (SKILL B7)
    assert (
        "相談記録での確定報告とセットで行う" not in decided
    )  # unconditional old wording


def test_rejected_and_deferred_records_have_explicit_settlement_gates() -> None:
    rubric = text("RUBRIC.md")
    assert "`Accepted`, `Rejected`, or `Deferred`" in rubric
    assert "Rejected: no option adopted plus reason" in rubric
    assert "Deferred: explicit revisit condition" in rubric
    assert "durable consultation with the people involved" in rubric
