from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

from asgard_harness import convergence, defects
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index
from asgard_harness.selfcheck import set_cell
from asgard_harness.workspace import Workspace

ANSIBLE_RECAP = """
PLAY RECAP *********************************************************************
node-a                     : ok=6    changed=2    unreachable=0    failed=0
node-b                     : ok=6    changed=0    unreachable=0    failed=0
"""

TOFU_PLAN = """
OpenTofu will perform the following actions:

  # proxmox_vm_qemu.guest["mimir"] will be updated in-place
  ~ resource "proxmox_vm_qemu" "guest" {
"""

KUBECTL_DIFF = """
diff -u -N /tmp/live/apps_v1.Deployment.default.web
--- a
+++ b
"""


def _runner(results: list[convergence.RunResult]) -> convergence.Runner:
    stream: Iterator[convergence.RunResult] = iter(results)
    return lambda: next(stream)


def _defects(findings) -> set[str]:
    return {finding.defect for finding in findings}


# --- parsers: changes vs failure -----------------------------------------------------------------


def test_parse_ansible_check_names_only_changed_hosts():
    run = convergence.parse_ansible_check(0, ANSIBLE_RECAP)
    assert run.changed == ("node-a",)
    assert run.errored is False


def test_parse_ansible_check_on_a_clean_run():
    run = convergence.parse_ansible_check(0, "node-b : ok=6 changed=0 unreachable=0 failed=0")
    assert run.changed == ()
    assert run.errored is False


@pytest.mark.parametrize(
    ("exit_code", "meaning"),
    [(1, "error"), (2, "one or more hosts failed"), (3, "unreachable"), (4, "parse error"), (99, "unexpected")],
)
def test_a_failed_ansible_run_is_an_error_not_a_clean_run(exit_code: int, meaning: str):
    run = convergence.parse_ansible_check(exit_code, "boom", "ansible-playbook --check x.yml")
    assert run.errored is True
    assert run.changed == ()
    assert str(exit_code) in run.error
    assert meaning.split()[0] in run.error
    assert "ansible-playbook --check x.yml" in run.error


def test_parse_tofu_plan_names_resource_addresses():
    run = convergence.parse_tofu_plan(2, TOFU_PLAN)
    assert run.changed == ('proxmox_vm_qemu.guest["mimir"]',)
    assert run.errored is False


def test_parse_tofu_plan_reports_unnamed_changes():
    assert convergence.parse_tofu_plan(2, "changes ahead").changed[0].startswith("<plan reports changes")


def test_parse_tofu_plan_on_a_clean_plan():
    assert convergence.parse_tofu_plan(0, "No changes.").changed == ()


def test_an_uninitialised_tofu_module_is_an_error_not_a_clean_plan():
    run = convergence.parse_tofu_plan(1, "Error: Backend initialization required", "tofu plan -detailed-exitcode")
    assert run.errored is True
    assert run.changed == ()
    assert "exited 1" in run.error
    assert "tofu plan -detailed-exitcode" in run.error


def test_parse_kubectl_diff_names_objects():
    assert convergence.parse_kubectl_diff(1, KUBECTL_DIFF).changed == ("/tmp/live/apps_v1.Deployment.default.web",)


def test_parse_kubectl_diff_reports_unnamed_differences():
    assert convergence.parse_kubectl_diff(1, "").changed[0].startswith("<diff reports differences")


def test_parse_kubectl_diff_on_a_clean_diff():
    assert convergence.parse_kubectl_diff(0, "").changed == ()


def test_an_unreachable_cluster_is_an_error_not_an_empty_diff():
    run = convergence.parse_kubectl_diff(2, "The connection to the server was refused", "kubectl diff -k k8s/x")
    assert run.errored is True
    assert run.changed == ()
    assert "exited 2" in run.error


@pytest.mark.parametrize(
    "parse",
    [convergence.parse_ansible_check, convergence.parse_tofu_plan, convergence.parse_kubectl_diff],
)
def test_a_tool_that_could_not_be_started_is_an_error_for_every_mechanism(parse):
    run = parse(convergence.LAUNCH_FAILURE_EXIT_CODE, "could not run x: No such file", "x")
    assert run.errored is True
    assert "could not be started" in run.error


def test_a_long_output_is_truncated_but_still_reported():
    run = convergence.parse_tofu_plan(1, "E" * 5000, "tofu plan")
    assert run.errored is True
    assert len(run.error) < 1000
    assert "…" in run.error


# --- convergence and idempotence are separate claims ---------------------------------------------


def test_a_converged_idempotent_automation_produces_nothing():
    runner = _runner([convergence.RunResult(), convergence.RunResult()])
    assert convergence.check_convergence_and_idempotence("thing", runner) == []


def test_a_first_run_with_changes_is_a_convergence_defect():
    runner = _runner([convergence.RunResult(changed=("node-a",)), convergence.RunResult()])
    findings = convergence.check_convergence_and_idempotence("thing", runner)
    assert _defects(findings) == {defects.AUTOMATION_NOT_CONVERGED}
    assert "node-a" in findings[0].detail


def test_a_second_run_with_changes_is_an_idempotence_defect():
    runner = _runner([convergence.RunResult(), convergence.RunResult(changed=("node-a",))])
    findings = convergence.check_convergence_and_idempotence("thing", runner)
    assert _defects(findings) == {defects.AUTOMATION_NOT_IDEMPOTENT}


def test_both_claims_can_fail_together():
    runner = _runner([convergence.RunResult(changed=("a",)), convergence.RunResult(changed=("b",))])
    findings = convergence.check_convergence_and_idempotence("thing", runner)
    assert _defects(findings) == {defects.AUTOMATION_NOT_CONVERGED, defects.AUTOMATION_NOT_IDEMPOTENT}


def test_an_errored_first_run_fails_and_does_not_run_again():
    calls: list[int] = []

    def runner() -> convergence.RunResult:
        calls.append(1)
        return convergence.parse_tofu_plan(1, "Error", "tofu plan")

    findings = convergence.check_convergence_and_idempotence("thing", runner)
    assert _defects(findings) == {defects.AUTOMATION_CHECK_FAILED}
    assert len(calls) == 1, "a second run cannot rescue a first that never completed"
    assert "proves nothing about convergence" in findings[0].detail


def test_an_errored_second_run_is_reported():
    runner = _runner([convergence.RunResult(), convergence.parse_kubectl_diff(2, "refused", "kubectl diff")])
    findings = convergence.check_convergence_and_idempotence("thing", runner)
    assert _defects(findings) == {defects.AUTOMATION_CHECK_FAILED}


# --- drift ---------------------------------------------------------------------------------------


def test_drift_accepts_an_empty_diff():
    assert convergence.check_drift("thing", _runner([convergence.RunResult()])).status is CheckStatus.PASSED


def test_drift_rejects_a_non_empty_diff_and_names_the_items():
    check = convergence.check_drift("thing", _runner([convergence.RunResult(changed=("a", "b"))]))
    assert check.status is CheckStatus.FAILED
    assert "'a', 'b'" in check.findings[0].detail


def test_drift_rejects_an_errored_run_rather_than_reading_it_as_empty():
    check = convergence.check_drift("thing", _runner([convergence.parse_kubectl_diff(2, "refused", "kubectl diff")]))
    assert check.status is CheckStatus.FAILED
    assert check.findings[0].defect == defects.AUTOMATION_CHECK_FAILED


# --- running commands ----------------------------------------------------------------------------


def test_run_command_reports_a_missing_binary_instead_of_raising(tmp_path: Path):
    code, output = convergence.run_command(["definitely-not-a-real-binary-xyz"], tmp_path)
    assert code == convergence.LAUNCH_FAILURE_EXIT_CODE
    assert "could not run" in output


def test_run_command_captures_a_real_command(tmp_path: Path):
    code, output = convergence.run_command(["echo", "hello"], tmp_path)
    assert code == 0
    assert "hello" in output


def test_a_missing_binary_becomes_a_failing_check_end_to_end(mini: Workspace):
    target = convergence.AutomationTarget(
        key="PROC-X", layer="l0-physical", path="tofu/l0-physical/x.tf", mechanism="opentofu"
    )
    runner = convergence.build_runner(target, mini)
    assert runner is not None
    findings = convergence.check_convergence_and_idempotence(target.name, runner)
    assert _defects(findings) == {defects.AUTOMATION_CHECK_FAILED}


# --- discovery -----------------------------------------------------------------------------------


def test_discovery_finds_nothing_while_no_automation_exists(mini: Workspace):
    assert convergence.discover_targets(load_index(mini.index_path), mini) == []


def test_discovery_finds_an_automation_that_exists(mini: Workspace):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    targets = convergence.discover_targets(load_index(mini.index_path), mini)
    assert [target.key for target in targets] == ["PROC-ONE"]
    assert targets[0].mechanism == "ansible"
    assert targets[0].name == "PROC-ONE (ansible/l0-physical/one.yml)"


def test_discovery_restricts_to_the_push_based_layers(mini: Workspace):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    assert convergence.discover_targets(load_index(mini.index_path), mini, layers=["l5-workloads"]) == []


def test_discovery_excludes_repository_tooling_but_discover_all_keeps_it(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", 5, "`PROCEDURE-INDEX.md`", anchor="## The Index")
    index = load_index(mini.index_path)
    assert convergence.discover_targets(index, mini) == []
    assert [t.mechanism for t in convergence.discover_all(index, mini)] == ["repository-tooling"]


def test_the_skip_reason_names_an_excluded_repository_tooling_half(mini: Workspace):
    set_cell(mini.index_path, "PROC-ONE", 5, "`PROCEDURE-INDEX.md`", anchor="## The Index")
    check = convergence.check_convergence_suite(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.SKIPPED
    assert "PROC-ONE (PROCEDURE-INDEX.md)" in check.note
    assert "no Automation half exists on disk" not in check.note


def test_the_skip_reason_is_accurate_when_nothing_at_all_exists(mini: Workspace):
    check = convergence.check_convergence_suite(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.SKIPPED
    assert "no Automation half exists on disk" in check.note


def test_drift_suite_skips_rather_than_passing_over_nothing(mini: Workspace):
    check = convergence.check_drift_suite(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.SKIPPED
    assert "registered as an alert source" in check.note


# --- run_targets ---------------------------------------------------------------------------------


def test_a_target_with_no_check_mode_is_named_and_not_counted_as_run():
    target = convergence.AutomationTarget(key="PROC-X", layer="l0-physical", path="weird/x", mechanism="unknown")
    findings, ran = convergence.run_targets([target], lambda _t: None, convergence.check_convergence_and_idempotence)
    assert ran == 0
    assert _defects(findings) == {defects.AUTOMATION_NO_CHECK_MODE}
    assert "must not be counted as converged" in findings[0].detail


def test_run_targets_runs_what_it_can():
    target = convergence.AutomationTarget(key="PROC-X", layer="l0-physical", path="a/x", mechanism="ansible")
    findings, ran = convergence.run_targets(
        [target],
        lambda _t: _runner([convergence.RunResult(), convergence.RunResult()]),
        convergence.check_convergence_and_idempotence,
    )
    assert (findings, ran) == ([], 1)


def test_the_suite_reports_a_target_it_could_not_run(mini: Workspace, monkeypatch):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    monkeypatch.setattr(convergence, "build_runner", lambda target, workspace: None)
    check = convergence.check_convergence_suite(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.FAILED
    assert check.examined == 0
    assert "1 target(s) had no runnable check mode" in check.note


# --- the suites over a real discovered target ----------------------------------------------------


def test_suites_fail_on_a_changing_target(mini: Workspace, monkeypatch):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    monkeypatch.setattr(convergence, "run_command", lambda argv, cwd: (0, ANSIBLE_RECAP))
    index = load_index(mini.index_path)
    assert convergence.check_convergence_suite(index, mini).status is CheckStatus.FAILED
    assert convergence.check_drift_suite(index, mini).status is CheckStatus.FAILED


def test_suites_fail_on_an_errored_target_rather_than_passing(mini: Workspace, monkeypatch):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    monkeypatch.setattr(convergence, "run_command", lambda argv, cwd: (3, "UNREACHABLE"))
    index = load_index(mini.index_path)
    for check in (
        convergence.check_convergence_suite(index, mini),
        convergence.check_drift_suite(index, mini),
    ):
        assert check.status is CheckStatus.FAILED
        assert check.findings[0].defect == defects.AUTOMATION_CHECK_FAILED


def test_suites_pass_when_the_target_is_clean(mini: Workspace, monkeypatch):
    (mini.root / "ansible" / "l0-physical" / "one.yml").write_text("---\n", encoding="utf-8")
    monkeypatch.setattr(convergence, "run_command", lambda argv, cwd: (0, "node-b : ok=1 changed=0 x=0"))
    index = load_index(mini.index_path)
    assert convergence.check_convergence_suite(index, mini).status is CheckStatus.PASSED


def test_build_runner_covers_each_mechanism_and_passes_the_exit_code(mini: Workspace, monkeypatch):
    seen: list[int] = []

    def fake(argv, cwd):
        seen.append(1)
        return 0, ""

    monkeypatch.setattr(convergence, "run_command", fake)
    for mechanism, path in (
        ("ansible", "ansible/l0-physical/one.yml"),
        ("opentofu", "tofu/l0-physical/one.tf"),
        ("kubernetes", "k8s/l0-physical/one/"),
    ):
        target = convergence.AutomationTarget(key="K", layer="l0-physical", path=path, mechanism=mechanism)
        runner = convergence.build_runner(target, mini)
        assert runner is not None
        run = runner()
        assert run.changed == ()
        assert run.errored is False
        assert run.command, "every runner must record the command it ran, for the finding to name"
    assert len(seen) == 3


@pytest.mark.parametrize(("mechanism", "code"), [("ansible", 1), ("opentofu", 1), ("kubernetes", 2)])
def test_every_runner_surfaces_its_tools_failure(mini: Workspace, monkeypatch, mechanism: str, code: int):
    monkeypatch.setattr(convergence, "run_command", lambda argv, cwd: (code, "it broke"))
    target = convergence.AutomationTarget(key="K", layer="l0-physical", path="a/b", mechanism=mechanism)
    runner = convergence.build_runner(target, mini)
    assert runner is not None
    assert runner().errored is True


def test_build_runner_declines_an_unknown_mechanism(mini: Workspace):
    target = convergence.AutomationTarget(
        key="K", layer="l0-physical", path="pixi.toml", mechanism="repository-tooling"
    )
    assert convergence.build_runner(target, mini) is None


def test_push_based_layers_are_the_lowest_three():
    assert convergence.PUSH_BASED_LAYERS == ("l0-physical", "l1-hypervisor", "l2-foundation")
