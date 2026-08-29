"""The harness against the real repository.

The unit suite proves each detector fires against a synthetic document. This suite proves it fires
against *these* documents, which is the claim that actually matters: a detector that only works on
a fixture is a detector that has never met the Index.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from asgard_harness.audit import EXPECTED_AUDIT_SKIPS, run_audit, run_convergence, run_drift
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index
from asgard_harness.ownership_document import load_ownership
from asgard_harness.selfcheck import FIXTURES, Fixture, run_fixture, run_self_check
from asgard_harness.workspace import Workspace

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def epics_commit(repo_workspace: Workspace) -> str | None:
    return repo_workspace.git_commit_for(repo_workspace.epics_path)


def test_the_repository_audits_clean(repo_workspace: Workspace):
    report = run_audit(repo_workspace)
    assert report.exit_code == 0, report.render()


def test_the_audit_reports_what_it_checked_not_only_that_it_passed(repo_workspace: Workspace):
    report = run_audit(repo_workspace)
    examined = {check.name: check.examined for check in report.results}
    assert examined["Status enumeration"] == len(load_index(repo_workspace.index_path).entries)
    assert examined["Verification named per class"] == len(load_ownership(repo_workspace.ownership_path).rows)
    assert all(check.note for check in report.results if check.status is CheckStatus.SKIPPED)


def test_every_skipped_check_says_why(repo_workspace: Workspace):
    for check in run_audit(repo_workspace).results:
        if check.status is CheckStatus.SKIPPED:
            assert len(check.note) > 20, check.name


def test_exactly_the_documented_checks_are_skipped(repo_workspace: Workspace):
    """A SKIP does not fail the gate, so a detector degrading to SKIP would go unnoticed.

    Pinning the set turns any new silent degradation — a shallow clone silencing the provenance
    check, a template that stopped being found — into a test failure rather than a green run with
    one fewer rule enforced.
    """
    report = run_audit(repo_workspace)
    skipped = {check.name for check in report.results if check.status is CheckStatus.SKIPPED}
    assert skipped == EXPECTED_AUDIT_SKIPS


def test_a_shallow_checkout_degrading_provenance_to_skip_is_detectable(repo_workspace: Workspace):
    """The mechanism the assertion above guards against, made concrete."""
    report = run_audit(repo_workspace, resolve_commit=lambda _ws: None)
    skipped = {check.name for check in report.results if check.status is CheckStatus.SKIPPED}
    assert skipped == EXPECTED_AUDIT_SKIPS | {"Provenance of the story list"}
    assert report.exit_code == 0, "a SKIP does not fail the gate — which is exactly why the set is pinned"


def test_the_audit_touches_no_managed_system(repo_workspace: Workspace, monkeypatch):
    """The gate must stay a pure reader: the Runbook's preconditions promise no credentials."""
    import asgard_harness.convergence as convergence_module

    def forbidden(argv, cwd):
        raise AssertionError(f"run_audit shelled out to {argv!r}; the merge gate must not reach infrastructure")

    monkeypatch.setattr(convergence_module, "run_command", forbidden)
    assert run_audit(repo_workspace).exit_code == 0


def test_the_convergence_suite_is_not_in_the_gate():
    import inspect

    from asgard_harness import audit as audit_module

    assert "check_convergence_suite" not in inspect.getsource(audit_module.run_audit)
    assert "check_convergence_suite" in inspect.getsource(audit_module.run_convergence)


@pytest.mark.parametrize("fixture", FIXTURES, ids=lambda f: f.defect)
def test_each_defect_class_fires_on_its_own_bad_fixture(
    repo_workspace: Workspace, fixture: Fixture, epics_commit: str | None
):
    outcome = run_fixture(repo_workspace, fixture, epics_commit)
    assert not outcome.error, outcome.error
    assert outcome.exit_code != 0, f"{fixture.name} did not make the audit fail"
    assert outcome.subjects, f"{fixture.name} fired no {fixture.defect} finding"


def test_the_self_check_passes_and_leaves_the_working_tree_clean(repo_root: Path, repo_workspace: Workspace):
    before = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"], capture_output=True, text=True, check=True
    ).stdout
    report = run_self_check(repo_workspace)
    after = subprocess.run(
        ["git", "-C", str(repo_root), "status", "--porcelain"], capture_output=True, text=True, check=True
    ).stdout
    assert report.exit_code == 0, report.render()
    assert before == after


def test_drift_detection_is_registered_and_reports_zero_targets(repo_workspace: Workspace):
    report = run_drift(repo_workspace)
    assert report.exit_code == 0
    assert report.results[0].status is CheckStatus.SKIPPED

    index = load_index(repo_workspace.index_path)
    registered = {source.source for source in index.alert_sources}
    assert any("drift" in source for source in registered), "the drift detector must register as an alert source"
    assert all(source.wired_by == "13.5" for source in index.alert_sources)


def test_the_convergence_harness_procedure_is_complete(repo_workspace: Workspace):
    entry = load_index(repo_workspace.index_path).entry("PROC-CONVERGENCE-HARNESS")
    assert entry is not None
    assert entry.status == "complete"
    assert repo_workspace.declared_exists(entry.runbook)
    assert repo_workspace.declared_exists(entry.automation)


def test_convergence_run_is_scheduled_and_reports_zero_targets(repo_workspace: Workspace):
    report = run_convergence(repo_workspace)
    assert report.exit_code == 0
    assert report.results[0].status is CheckStatus.SKIPPED
    assert "repository tooling" in report.results[0].note


def test_every_fixture_names_a_non_empty_subject(repo_workspace: Workspace, epics_commit: str | None):
    """Replaces a test that looped one fixture and asserted `all()` over a possibly-empty list."""
    for fixture in FIXTURES:
        if fixture.requires_git and epics_commit is None:
            continue
        outcome = run_fixture(repo_workspace, fixture, epics_commit)
        assert outcome.subjects, fixture.name
        assert all(subject.strip() for subject in outcome.subjects), fixture.name
