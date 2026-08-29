from __future__ import annotations

from pathlib import Path

from asgard_harness import checks_ownership
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index, parse_index
from asgard_harness.ownership_document import load_ownership, parse_ownership
from asgard_harness.selfcheck import duplicate_row, set_cell
from asgard_harness.workspace import Workspace

OWNER_COLUMN = 1
VERIFICATION_COLUMN = 3
PROCEDURE_COLUMN = 4


def _subjects(check) -> list[str]:
    return [finding.subject for finding in check.findings]


def test_owner_enumeration_passes_on_a_clean_table(mini: Workspace):
    assert checks_ownership.check_owner_enumeration(load_ownership(mini.ownership_path)).status is CheckStatus.PASSED


def test_owner_enumeration_fires_on_a_sentence(mini: Workspace):
    set_cell(mini.ownership_path, "Racking and cabling", OWNER_COLUMN, "whoever is nearest")
    check = checks_ownership.check_owner_enumeration(load_ownership(mini.ownership_path))
    assert _subjects(check) == ["Racking and cabling"]


def test_owner_enumeration_skips_without_a_stated_enumeration():
    ownership = parse_ownership("no tables here\n", Path("o.md"))
    assert checks_ownership.check_owner_enumeration(ownership).status is CheckStatus.SKIPPED


def test_one_owner_passes_and_reports_the_delegated_exemption(mini: Workspace):
    check = checks_ownership.check_one_owner(load_ownership(mini.ownership_path))
    assert check.status is CheckStatus.PASSED
    assert check.note == "1 Delegated row(s) exempt"


def test_one_owner_fires_and_picks_no_winner(mini: Workspace):
    duplicate_row(mini.ownership_path, "Racking and cabling", {OWNER_COLUMN: "`Ansible`"})
    check = checks_ownership.check_one_owner(load_ownership(mini.ownership_path))
    assert _subjects(check) == ["Racking and cabling"]
    assert "does not pick a winner" in check.findings[0].detail


def test_one_owner_tolerates_a_repeated_row_with_the_same_owner(mini: Workspace):
    duplicate_row(mini.ownership_path, "Racking and cabling", {})
    assert checks_ownership.check_one_owner(load_ownership(mini.ownership_path)).status is CheckStatus.PASSED


def test_verification_present_fires_on_an_empty_cell(mini: Workspace):
    set_cell(mini.ownership_path, "Racking and cabling", VERIFICATION_COLUMN, "")
    check = checks_ownership.check_verification_present(load_ownership(mini.ownership_path))
    assert _subjects(check) == ["Racking and cabling"]


def test_verification_present_covers_delegated_rows_too(mini: Workspace):
    set_cell(mini.ownership_path, "Component version pins", VERIFICATION_COLUMN, "")
    check = checks_ownership.check_verification_present(load_ownership(mini.ownership_path))
    assert _subjects(check) == ["Component version pins"]


def test_procedure_coverage_passes_on_a_clean_table(mini: Workspace):
    check = checks_ownership.check_procedure_coverage(load_ownership(mini.ownership_path), load_index(mini.index_path))
    assert check.status is CheckStatus.PASSED


def test_procedure_coverage_fires_on_an_unknown_key(mini: Workspace):
    set_cell(mini.ownership_path, "Racking and cabling", PROCEDURE_COLUMN, "`PROC-NOPE`")
    check = checks_ownership.check_procedure_coverage(load_ownership(mini.ownership_path), load_index(mini.index_path))
    assert _subjects(check) == ["Racking and cabling"]
    assert "do not exist" in check.findings[0].detail


def test_procedure_coverage_fires_on_zero_keys(mini: Workspace):
    set_cell(mini.ownership_path, "Racking and cabling", PROCEDURE_COLUMN, "to be decided")
    check = checks_ownership.check_procedure_coverage(load_ownership(mini.ownership_path), load_index(mini.index_path))
    assert "zero is not permitted" in check.findings[0].detail


def test_procedure_coverage_skips_without_an_index(mini: Workspace):
    empty = parse_index("", Path("i.md"))
    assert checks_ownership.check_procedure_coverage(load_ownership(mini.ownership_path), empty).status is (
        CheckStatus.SKIPPED
    )


def test_unowned_defect_is_reported_as_unimplementable_not_as_a_pass(mini: Workspace):
    check = checks_ownership.unowned_defect_status(load_ownership(mini.ownership_path))
    assert check.status is CheckStatus.SKIPPED
    assert "not mechanically decidable" in check.note
