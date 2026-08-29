from __future__ import annotations

from pathlib import Path

from asgard_harness import checks_index, defects
from asgard_harness.epics import Story, load_stories
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index, parse_index
from asgard_harness.selfcheck import ENTRY_ANCHOR, MANUAL_ANCHOR, delete_row, duplicate_row, replace_text, set_cell
from asgard_harness.workspace import Workspace

STATUS_COLUMN = 6
AUTOMATION_COLUMN = 5
RUNBOOK_COLUMN = 4
STORY_COLUMN = 3


def _index(workspace: Workspace):
    return load_index(workspace.index_path)


def _stories(workspace: Workspace) -> list[Story]:
    return load_stories(workspace.epics_path)


def _subjects(check) -> list[str]:
    return [finding.subject for finding in check.findings]


# --- illegal status ------------------------------------------------------------------------------


def test_status_enumeration_passes_on_a_clean_index(mini: Workspace):
    assert checks_index.check_status_enumeration(_index(mini)).status is CheckStatus.PASSED


def test_status_enumeration_fires_and_names_the_entry(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", STATUS_COLUMN, "`nearly`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_status_enumeration(_index(mini))
    assert _subjects(check) == ["PROC-ONE"]


def test_status_enumeration_skips_when_no_enumeration_is_stated():
    index = parse_index("| Key | Value |\n| --- | --- |\n", Path("i.md"))
    assert checks_index.check_status_enumeration(index).status is CheckStatus.SKIPPED


# --- incomplete Procedure ------------------------------------------------------------------------


def test_incomplete_procedure_fires_on_exactly_one_half(mini: Workspace):
    (mini.runbooks_dir / "l0-physical" / "one.md").write_text("x\n", encoding="utf-8")
    set_cell(mini.index_path, "PROC-ONE", STATUS_COLUMN, "`incomplete`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_incomplete_procedure(_index(mini), mini)
    assert _subjects(check) == ["PROC-ONE"]
    assert "ansible/l0-physical/one.yml" in check.findings[0].detail


def test_incomplete_procedure_names_the_missing_runbook_half(mini: Workspace):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    set_cell(mini.index_path, "PROC-ONE", STATUS_COLUMN, "`incomplete`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_incomplete_procedure(_index(mini), mini)
    assert "Runbook half" in check.findings[0].detail


def test_incomplete_procedure_excludes_manual_literal_entries(mini: Workspace):
    check = checks_index.check_incomplete_procedure(_index(mini), mini)
    assert check.examined == 2
    assert check.status is CheckStatus.PASSED


# --- status against the filesystem ---------------------------------------------------------------


def test_status_filesystem_fires_when_complete_but_absent(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", STATUS_COLUMN, "`complete`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_status_matches_filesystem(_index(mini), mini)
    assert _subjects(check) == ["PROC-ONE"]


def test_status_filesystem_fires_when_planned_but_present(mini: Workspace):
    (mini.runbooks_dir / "l0-physical" / "one.md").write_text("x\n", encoding="utf-8")
    check = checks_index.check_status_matches_filesystem(_index(mini), mini)
    assert _subjects(check) == ["PROC-ONE"]


def test_status_filesystem_excludes_manual_by_decision(mini: Workspace):
    check = checks_index.check_status_matches_filesystem(_index(mini), mini)
    assert check.examined == 2


def test_status_filesystem_ignores_an_illegal_status(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", STATUS_COLUMN, "`nearly`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_status_matches_filesystem(_index(mini), mini)
    assert check.examined == 1


# --- manual literal ------------------------------------------------------------------------------


def test_manual_literal_fires_without_the_status(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", AUTOMATION_COLUMN, "none — by decision", anchor=ENTRY_ANCHOR)
    check = checks_index.check_manual_literal(_index(mini))
    assert _subjects(check) == ["PROC-ONE"]
    assert "manual literal" in check.findings[0].detail


def test_manual_literal_fires_without_the_literal(mini: Workspace):
    set_cell(mini.index_path, "PROC-TWO-A", AUTOMATION_COLUMN, "`ansible/x.yml`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_manual_literal(_index(mini))
    assert _subjects(check) == ["PROC-TWO-A"]
    assert "not the literal" in check.findings[0].detail


# --- manual verification and human form ----------------------------------------------------------


def test_manual_verification_fires_on_an_empty_cell(mini: Workspace):
    set_cell(mini.index_path, "PROC-TWO-A", 3, "", anchor=MANUAL_ANCHOR)
    check = checks_index.check_manual_verification(_index(mini))
    assert _subjects(check) == ["PROC-TWO-A"]


def test_manual_verification_fires_when_the_row_is_missing(mini: Workspace):
    delete_row(mini.index_path, "PROC-TWO-A", anchor=MANUAL_ANCHOR)
    check = checks_index.check_manual_verification(_index(mini))
    assert _subjects(check) == ["PROC-TWO-A"]
    assert "no row" in check.findings[0].detail


def test_manual_human_form_fires_when_recorded_yes_but_absent(mini: Workspace):
    set_cell(mini.index_path, "PROC-TWO-A", 4, "Yes", anchor=MANUAL_ANCHOR)
    check = checks_index.check_manual_human_form(_index(mini), mini)
    assert _subjects(check) == ["PROC-TWO-A"]


def test_manual_human_form_fires_when_recorded_no_but_present(mini: Workspace):
    (mini.runbooks_dir / "l0-physical" / "two-a.md").write_text("x\n", encoding="utf-8")
    check = checks_index.check_manual_human_form(_index(mini), mini)
    assert _subjects(check) == ["PROC-TWO-A"]


def test_manual_human_form_fires_on_an_uncheckable_cell(mini: Workspace):
    set_cell(mini.index_path, "PROC-TWO-A", 4, "sort of", anchor=MANUAL_ANCHOR)
    check = checks_index.check_manual_human_form(_index(mini), mini)
    assert "states neither Yes nor No" in check.findings[0].detail


def test_manual_human_form_skips_an_entry_with_no_manual_row(mini: Workspace):
    delete_row(mini.index_path, "PROC-TWO-A", anchor=MANUAL_ANCHOR)
    assert checks_index.check_manual_human_form(_index(mini), mini).status is CheckStatus.PASSED


# --- namespace -----------------------------------------------------------------------------------


def test_duplicate_key_names_the_key(mini: Workspace):
    duplicate_row(mini.index_path, "PROC-ONE", {}, anchor=ENTRY_ANCHOR)
    check = checks_index.check_duplicate_keys(_index(mini))
    assert defects.DUPLICATE_KEY in {finding.defect for finding in check.findings}
    assert "PROC-ONE" in _subjects(check)


def test_duplicate_runbook_path_names_both_procedures(mini: Workspace):
    duplicate_row(mini.index_path, "PROC-ONE", {0: "`PROC-ONE-BIS`"}, anchor=ENTRY_ANCHOR)
    check = checks_index.check_duplicate_keys(_index(mini))
    finding = next(f for f in check.findings if f.defect == defects.DUPLICATE_RUNBOOK_PATH)
    assert "PROC-ONE-BIS" in finding.detail


def test_retired_key_reuse_names_the_entry(mini: Workspace):
    replace_text(mini.index_path, "**Retired keys:** none yet.", "**Retired keys:** `PROC-ONE`.")
    check = checks_index.check_retired_keys(_index(mini))
    assert _subjects(check) == ["PROC-ONE"]


def test_retired_keys_reports_none_recorded(mini: Workspace):
    assert checks_index.check_retired_keys(_index(mini)).note == "none recorded as retired"


# --- Index against the story list ----------------------------------------------------------------


def test_story_with_no_entry_names_the_story(mini: Workspace):
    delete_row(mini.index_path, "PROC-ONE", anchor=ENTRY_ANCHOR)
    check = checks_index.check_story_coverage(_index(mini), _stories(mini))
    assert any("story 1.1" in subject for subject in _subjects(check))


def test_entry_with_no_story_names_the_entry(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", STORY_COLUMN, "9.9", anchor=ENTRY_ANCHOR)
    check = checks_index.check_story_coverage(_index(mini), _stories(mini))
    assert defects.ENTRY_WITH_NO_STORY in {f.defect for f in check.findings}


def test_story_over_allowance_names_the_story(mini: Workspace):
    duplicate_row(
        mini.index_path,
        "PROC-ONE",
        {0: "`PROC-ONE-EXTRA`", RUNBOOK_COLUMN: "`runbooks/l0-physical/extra.md`"},
        anchor=ENTRY_ANCHOR,
    )
    check = checks_index.check_story_coverage(_index(mini), _stories(mini))
    finding = next(f for f in check.findings if f.defect == defects.STORY_OVER_ENTRY_ALLOWANCE)
    assert "not listed in the exception table" in finding.detail


def test_exception_story_with_the_wrong_keys_is_reported(mini: Workspace):
    set_cell(mini.index_path, "PROC-TWO-B", 0, "`PROC-TWO-C`", anchor=ENTRY_ANCHOR)
    check = checks_index.check_story_coverage(_index(mini), _stories(mini))
    finding = next(f for f in check.findings if f.defect == defects.STORY_OVER_ENTRY_ALLOWANCE)
    assert "exception names" in finding.detail


def test_story_coverage_skips_without_a_story_list(mini: Workspace):
    assert checks_index.check_story_coverage(_index(mini), []).status is CheckStatus.SKIPPED


# --- provenance ----------------------------------------------------------------------------------


def test_provenance_passes_when_the_commit_matches(mini: Workspace, mini_commit: str):
    check = checks_index.check_provenance(_index(mini), mini, lambda _ws: mini_commit)
    assert check.status is CheckStatus.PASSED
    assert mini_commit in check.note


def test_provenance_tolerates_differing_hash_lengths(mini: Workspace):
    check = checks_index.check_provenance(_index(mini), mini, lambda _ws: "abc1234def56789")
    assert check.status is CheckStatus.PASSED


def test_provenance_fires_when_stale(mini: Workspace):
    check = checks_index.check_provenance(_index(mini), mini, lambda _ws: "0000000")
    assert check.status is CheckStatus.FAILED
    assert "re-derive" in check.findings[0].detail


def test_provenance_skips_when_git_cannot_answer(mini: Workspace):
    assert checks_index.check_provenance(_index(mini), mini, lambda _ws: None).status is CheckStatus.SKIPPED


def test_provenance_fires_when_none_is_recorded(mini: Workspace):
    replace_text(mini.index_path, "at commit `abc1234`", "derived somehow")
    check = checks_index.check_provenance(_index(mini), mini, lambda _ws: "abc1234")
    assert "unfalsifiable" in check.findings[0].detail


def test_provenance_uses_git_when_no_resolver_is_supplied(mini: Workspace):
    assert checks_index.check_provenance(_index(mini), mini).status is CheckStatus.SKIPPED


# --- alert sources -------------------------------------------------------------------------------


def test_alert_sources_pass_when_the_stories_resolve(mini: Workspace):
    assert checks_index.check_alert_sources(_index(mini), _stories(mini)).status is CheckStatus.PASSED


def test_alert_sources_fire_on_an_unresolvable_story(mini: Workspace):
    replace_text(mini.index_path, "| `mini drift` | 1.1 | 1.3 |", "| `mini drift` | 9.9 | 1.3 |")
    check = checks_index.check_alert_sources(_index(mini), _stories(mini))
    assert _subjects(check) == ["mini drift"]


def test_alert_sources_skip_without_a_story_list(mini: Workspace):
    assert checks_index.check_alert_sources(_index(mini), []).status is CheckStatus.SKIPPED


# --- totals --------------------------------------------------------------------------------------


def test_totals_pass_on_a_clean_index(mini: Workspace):
    assert checks_index.check_totals(_index(mini), _stories(mini), mini).status is CheckStatus.PASSED


def test_totals_fire_on_a_hand_edited_figure(mini: Workspace):
    replace_text(mini.index_path, "| Entries in this Index | 4 |", "| Entries in this Index | 9 |")
    check = checks_index.check_totals(_index(mini), _stories(mini), mini)
    assert "Totals states 9, the tables give 4" in check.findings[0].detail


def test_totals_report_a_figure_nothing_recomputes(mini: Workspace):
    replace_text(mini.index_path, "| Human forms written | 1 |", "| Bananas | 3 |\n| Human forms written | 1 |")
    check = checks_index.check_totals(_index(mini), _stories(mini), mini)
    assert any(f.defect == defects.UNRECOMPUTED_TOTAL for f in check.findings)


def test_totals_report_a_missing_figure(mini: Workspace):
    replace_text(mini.index_path, "| Human forms written | 1 |\n", "")
    check = checks_index.check_totals(_index(mini), _stories(mini), mini)
    assert any("human_forms_written" in f.subject for f in check.findings)


def test_totals_fire_on_a_wrong_per_layer_count(mini: Workspace):
    replace_text(mini.index_path, "`l1-hypervisor` 2", "`l1-hypervisor` 5")
    check = checks_index.check_totals(_index(mini), _stories(mini), mini)
    assert any(f.subject == "per layer: l1-hypervisor" for f in check.findings)


def test_totals_skip_without_a_story_list(mini: Workspace):
    assert checks_index.check_totals(_index(mini), [], mini).status is CheckStatus.SKIPPED
