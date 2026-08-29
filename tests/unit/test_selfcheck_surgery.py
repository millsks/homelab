"""The self-check's own document surgery, and the shape of its fixture list.

A fixture that quietly stops targeting anything would turn the self-check into the thing it exists
to prevent, so the surgery helpers raise rather than no-op, and that is tested here.
"""

from __future__ import annotations

import pytest

from asgard_harness import defects, selfcheck
from asgard_harness.convergence import RunResult
from asgard_harness.findings import CheckStatus, Finding
from asgard_harness.index_document import load_index
from asgard_harness.workspace import TOOL_ROOTS, Workspace


def test_set_cell_replaces_only_the_named_column(mini: Workspace):
    selfcheck.set_cell(mini.index_path, "PROC-ONE", 6, "`complete`", anchor=selfcheck.ENTRY_ANCHOR)
    entry = load_index(mini.index_path).entry("PROC-ONE")
    assert entry.status == "complete"
    assert entry.title == "One"


def test_set_cell_disambiguates_by_anchor(mini: Workspace):
    selfcheck.set_cell(mini.index_path, "PROC-TWO-A", 3, "a new verification", anchor=selfcheck.MANUAL_ANCHOR)
    index = load_index(mini.index_path)
    assert index.manual_row("PROC-TWO-A").verification == "a new verification"
    assert index.entry("PROC-TWO-A").story == "1.2"


def test_set_cell_raises_on_a_missing_row(mini: Workspace):
    with pytest.raises(selfcheck.FixtureError, match="no table row"):
        selfcheck.set_cell(mini.index_path, "PROC-NOPE", 1, "x")


def test_set_cell_raises_on_a_missing_anchor(mini: Workspace):
    with pytest.raises(selfcheck.FixtureError, match="anchor"):
        selfcheck.set_cell(mini.index_path, "PROC-ONE", 1, "x", anchor="## Nowhere")


def test_set_cell_raises_on_a_missing_column(mini: Workspace):
    with pytest.raises(selfcheck.FixtureError, match="cannot set column"):
        selfcheck.set_cell(mini.index_path, "PROC-ONE", 99, "x", anchor=selfcheck.ENTRY_ANCHOR)


def test_duplicate_row_inserts_a_modified_copy(mini: Workspace):
    selfcheck.duplicate_row(mini.index_path, "PROC-ONE", {0: "`PROC-ONE-BIS`"}, anchor=selfcheck.ENTRY_ANCHOR)
    keys = [entry.key for entry in load_index(mini.index_path).entries]
    assert keys[:2] == ["PROC-ONE", "PROC-ONE-BIS"]


def test_duplicate_row_ignores_an_out_of_range_column(mini: Workspace):
    selfcheck.duplicate_row(mini.index_path, "PROC-ONE", {99: "x"}, anchor=selfcheck.ENTRY_ANCHOR)
    assert len(load_index(mini.index_path).entries) == 5


def test_delete_row_removes_it(mini: Workspace):
    selfcheck.delete_row(mini.index_path, "PROC-ONE", anchor=selfcheck.ENTRY_ANCHOR)
    assert load_index(mini.index_path).entry("PROC-ONE") is None


def test_replace_text_raises_when_the_literal_is_gone(mini: Workspace):
    with pytest.raises(selfcheck.FixtureError, match="targets nothing"):
        selfcheck.replace_text(mini.index_path, "not present anywhere", "x")


def test_every_defect_class_the_harness_defines_has_a_fixture():
    covered = {fixture.defect for fixture in selfcheck.FIXTURES}
    # Exempt ONLY because they are proven by the runner fixtures in CONVERGENCE_FIXTURES and
    # _drift_runner_fixtures instead of by a document mutation: each is a decision about a
    # check-mode run, and no edit to a Markdown table can provoke one. The self-check exercises
    # every one of them; test_every_convergence_defect_is_proven_by_a_runner_fixture pins that, so
    # this exemption is a routing decision rather than a gap.
    exempt = {
        defects.SELF_CHECK_DID_NOT_FIRE,
        defects.AUTOMATION_NOT_CONVERGED,
        defects.AUTOMATION_NOT_IDEMPOTENT,
        defects.AUTOMATION_CHECK_FAILED,
        defects.AUTOMATION_NO_CHECK_MODE,
        defects.CHECK_MODE_DIFF_NOT_EMPTY,
    }
    declared = {
        value
        for name, value in vars(defects).items()
        if name.isupper() and isinstance(value, str) and not name.startswith("_")
    }
    assert declared - exempt - covered == set()


def test_fixture_names_and_defects_are_unique():
    assert len({fixture.name for fixture in selfcheck.FIXTURES}) == len(selfcheck.FIXTURES)
    assert len({fixture.defect for fixture in selfcheck.FIXTURES}) == len(selfcheck.FIXTURES)


def test_copy_workspace_reproduces_the_documents(mini: Workspace, tmp_path):
    copy = selfcheck.copy_workspace(mini, tmp_path / "copy")
    assert copy.index_path.is_file()
    assert copy.ownership_path.is_file()
    assert copy.epics_path.is_file()
    assert copy.template_path.is_file()


def test_a_fixture_that_cannot_apply_is_reported_not_silently_passed(mini: Workspace):
    broken = selfcheck.Fixture(
        name="targets nothing",
        defect=defects.ILLEGAL_STATUS_VALUE,
        apply=lambda ws: selfcheck.set_cell(ws.index_path, "PROC-ABSENT", 1, "x"),
    )
    outcome = selfcheck.run_fixture(mini, broken, "abc1234")
    assert outcome.fired is False
    assert "no table row" in outcome.error


def test_a_fixture_that_fires_is_recorded_with_its_subject(mini: Workspace):
    fixture = selfcheck.Fixture(
        name="illegal status",
        defect=defects.ILLEGAL_STATUS_VALUE,
        apply=lambda ws: selfcheck.set_cell(ws.index_path, "PROC-ONE", 6, "`nearly`", anchor=selfcheck.ENTRY_ANCHOR),
    )
    outcome = selfcheck.run_fixture(mini, fixture, "abc1234")
    assert outcome.fired is True
    assert outcome.subjects == ("PROC-ONE",)


def test_a_failing_baseline_stops_the_self_check(mini: Workspace):
    selfcheck.set_cell(mini.index_path, "PROC-ONE", 6, "`nearly`", anchor=selfcheck.ENTRY_ANCHOR)
    report = selfcheck.run_self_check(mini)
    assert report.exit_code == 1
    assert len(report.results) == 1
    assert "the baseline audit already fails" in report.findings[0].detail


# --- The self-check's OWN failure path -----------------------------------------------------------
#
# These are the tests two surviving mutations exposed. `run_self_check`'s "this fixture did not
# fire" branch and `_expect`'s mismatch branch are the entire mechanism by which the harness proves
# it can fail — and neither was executed by any test, so both could be deleted while the suite
# stayed green. A self-check that has silently lost the ability to report a dud fixture is exactly
# the "gate that cannot fail" this project has now shipped four times.


def test_a_fixture_that_changes_nothing_is_reported_as_a_failure(mini: Workspace, monkeypatch):
    """The no-op fixture: mutates nothing, raises nothing, provokes nothing."""
    dud = selfcheck.Fixture(name="changes nothing at all", defect=defects.ILLEGAL_STATUS_VALUE, apply=lambda ws: None)
    monkeypatch.setattr(selfcheck, "FIXTURES", (dud,))
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")

    report = selfcheck.run_self_check(mini)

    assert report.exit_code == 1, "a fixture that provokes nothing must fail the self-check"
    duds = [f for f in report.findings if f.defect == defects.SELF_CHECK_DID_NOT_FIRE]
    assert [f.subject for f in duds] == [defects.ILLEGAL_STATUS_VALUE]
    assert "a passing self-check is a failure" in duds[0].detail


def test_the_self_check_reports_one_result_per_fixture_plus_baseline_and_runners(mini: Workspace, monkeypatch):
    """Pins the check count, so a fixture silently vanishing from FIXTURES is caught."""
    dud = selfcheck.Fixture(name="changes nothing at all", defect=defects.ILLEGAL_STATUS_VALUE, apply=lambda ws: None)
    monkeypatch.setattr(selfcheck, "FIXTURES", (dud,))
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: "abc1234")

    report = selfcheck.run_self_check(mini)
    runner_count = len(selfcheck.CONVERGENCE_FIXTURES) + 5
    assert len(report.results) == 1 + 1 + runner_count


def test_the_real_fixture_list_is_fully_reported(repo_workspace: Workspace):
    """Against the real repository, every fixture produces exactly one result."""
    expected = 1 + len(selfcheck.FIXTURES) + len(selfcheck.CONVERGENCE_FIXTURES) + 5
    assert len(selfcheck.run_self_check(repo_workspace).results) == expected


@pytest.mark.parametrize(
    ("findings", "fires", "should_pass"),
    [
        ([], False, True),
        ([], True, False),
        ([Finding(defect="d", subject="s", detail="t")], True, True),
        ([Finding(defect="d", subject="s", detail="t")], False, False),
    ],
)
def test_expect_drives_both_directions_of_its_guard(findings, fires, should_pass):
    check = selfcheck._expect(findings, fires=fires, name="fixture", defect="")
    assert (check.status is CheckStatus.PASSED) is should_pass


def test_expect_rejects_a_fixture_that_fires_with_the_wrong_defect_class():
    check = selfcheck._expect(
        [Finding(defect="something-else", subject="s", detail="t")],
        fires=True,
        name="fixture",
        defect="the-required-one",
    )
    assert check.status is CheckStatus.FAILED
    assert "rather than the required" in check.findings[0].detail


def test_expect_explains_a_fixture_that_fired_when_it_should_not():
    check = selfcheck._expect([Finding(defect="d", subject="s", detail="t")], fires=False, name="f", defect="")
    assert "fired on a known-good fixture" in check.findings[0].detail


def test_a_scripted_runner_asked_for_too_many_runs_errors_rather_than_reading_clean():
    runner = selfcheck._scripted((RunResult(),))
    assert runner().errored is False
    assert runner().errored is True


def test_the_provenance_fixture_skips_when_git_cannot_answer(mini: Workspace, monkeypatch):
    """#14: it must never pass by comparing the document against a hash the document supplied."""
    monkeypatch.setattr(Workspace, "git_commit_for", lambda self, path: None)
    provenance = next(f for f in selfcheck.FIXTURES if f.requires_git)
    monkeypatch.setattr(selfcheck, "FIXTURES", (provenance,))

    report = selfcheck.run_self_check(mini)

    fixture_result = next(r for r in report.results if r.name.startswith("Fixture —"))
    assert fixture_result.status is CheckStatus.SKIPPED
    assert "git could not name the commit" in fixture_result.note
    assert report.exit_code == 0


def test_only_the_provenance_fixture_depends_on_git():
    assert [f.defect for f in selfcheck.FIXTURES if f.requires_git] == [defects.STALE_PROVENANCE]


def test_copy_set_covers_every_path_a_detector_reads(repo_workspace: Workspace):
    """#7: a detector reading outside the copy set sees an empty workspace in every fixture."""
    roots = {
        repo_workspace.relative(repo_workspace.index_path),
        repo_workspace.relative(repo_workspace.ownership_path),
        repo_workspace.relative(repo_workspace.address_plan_path),
        repo_workspace.relative(repo_workspace.epics_path),
        repo_workspace.relative(repo_workspace.runbooks_dir),
        repo_workspace.relative(repo_workspace.template_path),
        "pixi.toml",
        *TOOL_ROOTS,
    }
    for root in roots:
        assert any(root == c or root.startswith(f"{c}/") for c in selfcheck.COPIED_PATHS), root


def test_the_copy_excludes_python_bytecode(repo_workspace: Workspace, tmp_path):
    copy = selfcheck.copy_workspace(repo_workspace, tmp_path / "copy")
    assert (copy.root / "src" / "asgard_harness" / "audit.py").is_file()
    assert list(copy.root.rglob("__pycache__")) == []


def test_every_convergence_defect_is_proven_by_a_runner_fixture():
    """The exemptions above are only legitimate if the runner fixtures really do cover them."""
    proven = {f.expect_defect for f in selfcheck.CONVERGENCE_FIXTURES if f.expect_defect}
    assert proven == {
        defects.AUTOMATION_NOT_CONVERGED,
        defects.AUTOMATION_NOT_IDEMPOTENT,
        defects.AUTOMATION_CHECK_FAILED,
    }
    results = selfcheck._runner_fixtures()
    assert all(r.status is CheckStatus.PASSED for r in results)
    assert any("no known check mode" in r.name for r in results)
    assert any("drift rejects a non-empty" in r.name for r in results)
