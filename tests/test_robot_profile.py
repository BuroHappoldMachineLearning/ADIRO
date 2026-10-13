"""The ROBOT report profile (config/robot_report_profile.txt)."""
from pathlib import Path

PROFILE = Path(__file__).resolve().parent.parent / "config" / "robot_report_profile.txt"


def rules():
    return [line.split("\t") for line in PROFILE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_every_line_is_a_level_and_a_rule_in_strict_tsv():
    # The format takes no comments, so a malformed line would fail the ROBOT run; AGENTS.md explains the choices instead.
    for fields in rules():
        assert len(fields) == 2 and fields[0] in ("ERROR", "WARN", "INFO") and fields[1].isidentifier(), fields


def test_missing_superclass_is_not_run():
    # ADIRO's modules have root classes by design (and external stubs are not ours to classify): the OBO rule only
    # produced a standing list nobody acts on. See AGENTS.md before adding it back.
    assert "missing_superclass" not in [rule for _, rule in rules()]


def test_missing_definition_is_not_run_either():
    # ADIRO's definition vocabulary is rdfs:comment, not the OBO IAO:0000115 that this rule looks for (AGENTS.md).
    assert "missing_definition" not in [rule for _, rule in rules()]
