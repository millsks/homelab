from __future__ import annotations

from pathlib import Path

from asgard_harness.epics import load_stories, parse_stories
from asgard_harness.index_document import load_index, parse_index
from asgard_harness.ownership_document import load_ownership, parse_ownership
from asgard_harness.workspace import Workspace


def test_index_parses_every_declared_structure(mini: Workspace):
    index = load_index(mini.index_path)
    assert [entry.key for entry in index.entries] == ["PROC-ONE", "PROC-TWO-A", "PROC-TWO-B", "PROC-MANUAL"]
    assert index.legal_statuses == {"planned", "incomplete", "complete", "manual-by-decision"}
    assert index.provenance_commit == "abc1234"
    assert index.retired_keys == frozenset()
    assert index.totals.figures["Entries in this Index"] == 4
    assert index.totals.per_layer == {"l0-physical": 2, "l1-hypervisor": 2}
    assert index.exceptions[0].keys == ("PROC-TWO-A", "PROC-TWO-B")
    assert index.alert_sources[0].registering_story == "1.1"


def test_index_entry_lookup_and_key_set(mini: Workspace):
    index = load_index(mini.index_path)
    assert index.entry("PROC-ONE") is not None
    assert index.entry("PROC-NOPE") is None
    assert "PROC-MANUAL" in index.keys


def test_manual_row_lookup_and_yes_no_reading(mini: Workspace):
    index = load_index(mini.index_path)
    assert index.manual_row("PROC-MANUAL") is not None
    assert index.manual_row("PROC-NOPE") is None
    assert index.manual_row("PROC-MANUAL").human_form_written is True
    assert index.manual_row("PROC-TWO-A").human_form_written is False


def test_manual_row_reports_an_uncheckable_cell():
    text = (
        "## Deliberately manual work\n\n"
        "| Key | Story | Why no Automation | Verification | Human form written? | Provisional? |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| `PROC-X` | 1.1 | because | a read | maybe | No |\n"
    )
    index = parse_index(text, Path("PROCEDURE-INDEX.md"))
    assert index.manual_rows[0].human_form_written is None


def test_manual_literal_recognised(mini: Workspace):
    index = load_index(mini.index_path)
    assert index.entry("PROC-TWO-A").is_manual_literal is True
    assert index.entry("PROC-ONE").is_manual_literal is False


def test_retired_keys_are_read_from_the_document():
    index = parse_index("**Retired keys:** `PROC-OLD`, `PROC-OLDER`.\n", Path("i.md"))
    assert index.retired_keys == {"PROC-OLD", "PROC-OLDER"}


def test_missing_index_yields_an_empty_index(tmp_path: Path):
    index = load_index(tmp_path / "absent.md")
    assert index.entries == ()
    assert index.provenance_commit is None


def test_ownership_parses_rows_and_enumeration(mini: Workspace):
    ownership = load_ownership(mini.ownership_path)
    assert len(ownership.rows) == 4
    assert ownership.legal_owners == {"Ansible", "Runbook", "docs/ record", "Delegated"}
    host_os = next(row for row in ownership.rows if row.resource_class == "Host OS configuration")
    assert host_os.procedures == ("PROC-ONE", "PROC-TWO-B")
    assert host_os.layer == "L0 — Physical"
    assert host_os.is_delegated is False


def test_delegated_row_names_no_procedure_and_is_flagged(mini: Workspace):
    ownership = load_ownership(mini.ownership_path)
    pins = next(row for row in ownership.rows if row.resource_class == "Component version pins")
    assert pins.is_delegated is True
    assert pins.procedures == ()


def test_normalised_class_collapses_whitespace_and_case():
    ownership = parse_ownership(
        "| Resource class | Owner | Declaring mechanism | Verification | Procedure | Notes |\n"
        "| --- | --- | --- | --- | --- | --- |\n"
        "| **A   Class** | `Ansible` | x | y | `PROC-A` | |\n",
        Path("o.md"),
    )
    assert ownership.rows[0].normalised_class == "a class"


def test_missing_ownership_yields_an_empty_table(tmp_path: Path):
    ownership = load_ownership(tmp_path / "absent.md")
    assert ownership.rows == ()
    assert ownership.legal_owners == frozenset()


def test_stories_are_read_from_headings(mini: Workspace):
    stories = load_stories(mini.epics_path)
    assert [story.number for story in stories] == ["1.1", "1.2", "1.3"]
    assert stories[0].title == "One"
    assert stories[0].line == 3


def test_missing_epics_yields_no_stories(tmp_path: Path):
    assert load_stories(tmp_path / "absent.md") == []


def test_epic_headings_are_not_stories():
    stories = parse_stories("### Epic 1: Not a story\n### Story 2.1: Yes\n")
    assert [(story.number, story.title) for story in stories] == [("2.1", "Yes")]
