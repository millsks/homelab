"""Every address-plan detector, in both directions.

A check tested only on bad input is satisfied by a check that fires on everything, so each detector
here has a fixture that must fire and an assertion that the clean miniature plan does not.
"""

from __future__ import annotations

from pathlib import Path

from asgard_harness import checks_address_plan
from asgard_harness.address_plan_document import (
    load_address_plan,
    parse_address,
    parse_address_plan,
    parse_network,
)
from asgard_harness.findings import CheckResult, CheckStatus
from asgard_harness.selfcheck import delete_row, duplicate_row, set_cell
from asgard_harness.workspace import Workspace

SEGMENT_ANCHOR = "## Segments"
RANGE_ANCHOR = "## Address ranges"
ALLOCATION_ANCHOR = "## Allocations"

ADDRESS_COLUMN = 0
SEGMENT_COLUMN = 1
HOLDS_COLUMN = 2
KIND_COLUMN = 3
GATEWAY_COLUMN = 3
ISOLATED_COLUMN = 4
RANGE_FIRST_COLUMN = 2
RANGE_LAST_COLUMN = 3
RANGE_TYPE_COLUMN = 4

EMPTY = parse_address_plan("nothing here\n", Path("ADDRESS-PLAN.md"))


def _subjects(check: CheckResult) -> list[str]:
    return [finding.subject for finding in check.findings]


def _plan(mini: Workspace):
    return load_address_plan(mini.address_plan_path)


# --- Parsing --------------------------------------------------------------------------------------


def test_an_unparseable_address_is_none_rather_than_an_exception():
    assert parse_address("192.168.86.300") is None
    assert parse_address("") is None
    assert parse_address("192.168.86.11") is not None


def test_a_host_bit_set_is_not_a_network():
    assert parse_network("192.168.86.1/24") is None
    assert parse_network("192.168.86.0/24") is not None


def test_the_plan_reads_its_own_enumerations_out_of_the_document(mini: Workspace):
    plan = _plan(mini)
    assert plan.legal_kinds == {"node", "gateway", "appliance"}
    assert [segment.name for segment in plan.segments] == ["data", "membership"]
    assert len(plan.allocations) == 5


def test_a_missing_plan_yields_an_empty_one_rather_than_raising(tmp_path: Path):
    plan = load_address_plan(tmp_path / "ADDRESS-PLAN.md")
    assert plan.segments == ()
    assert plan.allocations == ()


def test_an_isolated_segment_declares_no_gateway(mini: Workspace):
    membership = _plan(mini).segment("membership")
    assert membership is not None
    assert membership.is_isolated is True
    assert membership.declares_gateway is False


def test_a_range_type_that_is_neither_allocatable_nor_a_pool_counts_as_reserved(mini: Workspace):
    set_cell(mini.address_plan_path, "data-hosts", RANGE_TYPE_COLUMN, "`allocatible`", anchor=RANGE_ANCHOR)
    entry = next(entry for entry in _plan(mini).ranges if entry.name == "data-hosts")
    assert entry.is_reserved, "a misspelled type must make the check stricter, never silent"


# --- Collisions -----------------------------------------------------------------------------------


def test_collisions_pass_on_the_clean_plan(mini: Workspace):
    assert checks_address_plan.check_collisions(_plan(mini)).status is CheckStatus.PASSED


def test_a_collision_names_both_claimants_and_picks_neither(mini: Workspace):
    duplicate_row(mini.address_plan_path, "10.0.0.2", {HOLDS_COLUMN: "`impostor`"}, anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_collisions(_plan(mini))
    assert _subjects(check) == ["10.0.0.2 on segment data"]
    assert "node-a" in check.findings[0].detail
    assert "impostor" in check.findings[0].detail
    assert "picks neither" in check.findings[0].detail


def test_the_same_address_on_two_segments_is_not_a_collision(mini: Workspace):
    set_cell(mini.address_plan_path, "10.9.9.2", ADDRESS_COLUMN, "`10.0.0.2`", anchor=ALLOCATION_ANCHOR)
    assert checks_address_plan.check_collisions(_plan(mini)).status is CheckStatus.PASSED


def test_collisions_skip_on_an_empty_plan():
    assert checks_address_plan.check_collisions(EMPTY).status is CheckStatus.SKIPPED


# --- The DHCP pool --------------------------------------------------------------------------------


def test_statics_outside_the_pool_pass_and_the_pool_is_reported(mini: Workspace):
    check = checks_address_plan.check_dhcp_pool(_plan(mini))
    assert check.status is CheckStatus.PASSED
    assert "data-dhcp" in check.note


def test_a_static_inside_the_pool_names_the_address_and_the_pool(mini: Workspace):
    set_cell(mini.address_plan_path, "10.0.0.2", ADDRESS_COLUMN, "`10.0.0.5`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_dhcp_pool(_plan(mini))
    assert _subjects(check) == ["10.0.0.5 (node-a)"]
    assert "data-dhcp" in check.findings[0].detail


def test_the_pool_check_skips_when_no_pool_is_declared(mini: Workspace):
    set_cell(mini.address_plan_path, "data-dhcp", RANGE_TYPE_COLUMN, "`reserved`", anchor=RANGE_ANCHOR)
    assert checks_address_plan.check_dhcp_pool(_plan(mini)).status is CheckStatus.SKIPPED


# --- Reservations ---------------------------------------------------------------------------------


def test_reservations_pass_on_the_clean_plan(mini: Workspace):
    check = checks_address_plan.check_reservations(_plan(mini))
    assert check.status is CheckStatus.PASSED
    assert "reserved range(s) held" in check.note


def test_consuming_a_growth_reservation_names_the_reservation(mini: Workspace):
    set_cell(mini.address_plan_path, "10.0.0.2", ADDRESS_COLUMN, "`10.0.0.4`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_reservations(_plan(mini))
    assert _subjects(check) == ["10.0.0.4 (node-a)"]
    assert "data-growth" in check.findings[0].detail


def test_reservations_skip_on_an_empty_plan():
    assert checks_address_plan.check_reservations(EMPTY).status is CheckStatus.SKIPPED


# --- Node homing ----------------------------------------------------------------------------------


def test_node_homing_passes_on_the_clean_plan(mini: Workspace):
    check = checks_address_plan.check_node_homing(_plan(mini))
    assert check.status is CheckStatus.PASSED
    assert check.examined == 2


def test_a_node_on_one_segment_only_is_named(mini: Workspace):
    delete_row(mini.address_plan_path, "10.9.9.3", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_node_homing(_plan(mini))
    assert _subjects(check) == ["node-b"]
    assert "both segments or neither" in check.findings[0].detail


def test_a_node_with_two_addresses_on_one_segment_is_named(mini: Workspace):
    duplicate_row(mini.address_plan_path, "10.0.0.2", {ADDRESS_COLUMN: "`10.0.0.3`"}, anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_node_homing(_plan(mini))
    assert "node-a" in _subjects(check)
    assert any("carries exactly one" in finding.detail for finding in check.findings)


def test_a_node_homed_on_an_undeclared_segment_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "10.9.9.2", SEGMENT_COLUMN, "`elsewhere`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_node_homing(_plan(mini))
    details = " ".join(finding.detail for finding in check.findings)
    assert "elsewhere" in details


def test_a_non_node_on_one_segment_is_not_a_defect(mini: Workspace):
    """The membership switch is the live case: it belongs to that segment alone, by design."""
    duplicate_row(
        mini.address_plan_path,
        "10.9.9.2",
        {ADDRESS_COLUMN: "`10.9.9.1`", HOLDS_COLUMN: "`mini-switch`", KIND_COLUMN: "`appliance`"},
        anchor=ALLOCATION_ANCHOR,
    )
    assert checks_address_plan.check_node_homing(_plan(mini)).status is CheckStatus.PASSED


def test_node_homing_skips_on_an_empty_plan():
    assert checks_address_plan.check_node_homing(EMPTY).status is CheckStatus.SKIPPED


# --- Isolation ------------------------------------------------------------------------------------


def test_isolation_passes_on_the_clean_plan(mini: Workspace):
    check = checks_address_plan.check_isolated_segments(_plan(mini))
    assert check.status is CheckStatus.PASSED
    assert check.note == "1 declared isolated"


def test_a_gateway_on_the_isolated_segment_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "membership", GATEWAY_COLUMN, "`10.9.9.1`", anchor=SEGMENT_ANCHOR)
    check = checks_address_plan.check_isolated_segments(_plan(mini))
    assert _subjects(check) == ["membership"]
    assert "no route off-segment" in check.findings[0].detail


def test_a_gateway_allocation_on_the_isolated_segment_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "10.9.9.2", KIND_COLUMN, "`gateway`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_isolated_segments(_plan(mini))
    assert _subjects(check) == ["10.9.9.2 (node-a)"]


def test_an_isolated_cell_that_states_neither_yes_nor_no_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "membership", ISOLATED_COLUMN, "mostly", anchor=SEGMENT_ANCHOR)
    check = checks_address_plan.check_isolated_segments(_plan(mini))
    assert _subjects(check) == ["membership"]
    assert "neither 'yes' nor 'no'" in check.findings[0].detail


def test_a_gateway_on_a_routed_segment_is_fine(mini: Workspace):
    assert checks_address_plan.check_isolated_segments(_plan(mini)).status is CheckStatus.PASSED


def test_isolation_skips_on_an_empty_plan():
    assert checks_address_plan.check_isolated_segments(EMPTY).status is CheckStatus.SKIPPED


# --- Kinds ----------------------------------------------------------------------------------------


def test_kinds_pass_on_the_clean_plan(mini: Workspace):
    assert checks_address_plan.check_kind_enumeration(_plan(mini)).status is CheckStatus.PASSED


def test_a_kind_outside_the_closed_set_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "10.0.0.1", KIND_COLUMN, "whatever it turns out to be", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_kind_enumeration(_plan(mini))
    assert _subjects(check) == ["10.0.0.1 (mini-router)"]


def test_kinds_skip_without_a_stated_enumeration():
    plan = parse_address_plan("# Plan\n\nNo kinds table.\n", Path("ADDRESS-PLAN.md"))
    assert checks_address_plan.check_kind_enumeration(plan).status is CheckStatus.SKIPPED


# --- Range coverage -------------------------------------------------------------------------------


def test_range_coverage_passes_on_the_clean_plan(mini: Workspace):
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert check.status is CheckStatus.PASSED, [f.render() for f in check.findings]
    assert check.examined == 10


def test_a_deleted_range_leaves_a_named_gap(mini: Workspace):
    delete_row(mini.address_plan_path, "data-growth", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert _subjects(check) == ["data"]
    assert "10.0.0.4" in check.findings[0].detail


def test_a_missing_tail_range_is_named(mini: Workspace):
    delete_row(mini.address_plan_path, "data-broadcast", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert "tail of the segment" in check.findings[0].detail


def test_an_overlapping_range_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "data-growth", RANGE_FIRST_COLUMN, "`10.0.0.3`", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert "overlaps" in " ".join(finding.detail for finding in check.findings)


def test_a_backwards_range_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "data-hosts", RANGE_FIRST_COLUMN, "`10.0.0.6`", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert any("runs backwards" in finding.detail for finding in check.findings)


def test_an_unparseable_range_bound_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "data-hosts", RANGE_LAST_COLUMN, "`10.0.0.300`", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert any("do not both parse" in finding.detail for finding in check.findings)


def test_a_range_outside_its_own_segment_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "data-hosts", RANGE_FIRST_COLUMN, "`10.5.5.2`", anchor=RANGE_ANCHOR)
    set_cell(mini.address_plan_path, "data-hosts", RANGE_LAST_COLUMN, "`10.5.5.3`", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert any("is not inside segment" in finding.detail for finding in check.findings)


def test_a_segment_whose_network_is_not_a_cidr_block_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "data", 1, "`the household LAN`", anchor=SEGMENT_ANCHOR)
    check = checks_address_plan.check_range_coverage(_plan(mini))
    assert any("not a CIDR block" in finding.detail for finding in check.findings)


def test_range_coverage_skips_on_an_empty_plan():
    assert checks_address_plan.check_range_coverage(EMPTY).status is CheckStatus.SKIPPED


# --- Allocations land somewhere declared ----------------------------------------------------------


def test_declared_ranges_pass_on_the_clean_plan(mini: Workspace):
    assert checks_address_plan.check_allocations_are_declared(_plan(mini)).status is CheckStatus.PASSED


def test_an_address_that_is_not_an_address_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "10.0.0.2", ADDRESS_COLUMN, "`10.0.0.300`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_allocations_are_declared(_plan(mini))
    assert any("is not an IP address" in finding.detail for finding in check.findings)


def test_an_allocation_on_an_undeclared_segment_is_named(mini: Workspace):
    set_cell(mini.address_plan_path, "10.0.0.1", SEGMENT_COLUMN, "`storage`", anchor=ALLOCATION_ANCHOR)
    check = checks_address_plan.check_allocations_are_declared(_plan(mini))
    assert _subjects(check) == ["10.0.0.1 (mini-router)"]
    assert "does not declare" in check.findings[0].detail


def test_an_address_in_no_declared_range_is_named(mini: Workspace):
    delete_row(mini.address_plan_path, "data-edge", anchor=RANGE_ANCHOR)
    check = checks_address_plan.check_allocations_are_declared(_plan(mini))
    assert _subjects(check) == ["10.0.0.1 (mini-router)"]
    assert "nobody accounted for" in check.findings[0].detail


def test_declared_ranges_skip_on_an_empty_plan():
    assert checks_address_plan.check_allocations_are_declared(EMPTY).status is CheckStatus.SKIPPED


# --- The suite ------------------------------------------------------------------------------------


def test_the_whole_suite_passes_on_the_clean_plan(mini: Workspace):
    results = checks_address_plan.run_address_plan_checks(_plan(mini))
    assert len(results) == 8
    assert all(check.status is CheckStatus.PASSED for check in results), [
        check.render() for check in results if check.status is not CheckStatus.PASSED
    ]


def test_every_detector_reports_what_it_examined(mini: Workspace):
    for check in checks_address_plan.run_address_plan_checks(_plan(mini)):
        assert check.examined > 0, check.name
        assert check.noun
