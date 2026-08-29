"""The harness against the real repository.

The unit suite proves each detector fires against a synthetic document. This suite proves it fires
against *these* documents, which is the claim that actually matters: a detector that only works on
a fixture is a detector that has never met the Index.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
from ruamel import yaml

from asgard_harness.audit import EXPECTED_AUDIT_SKIPS, run_audit, run_convergence, run_drift, run_secrets
from asgard_harness.checks_secrets import is_sops_encrypted
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index
from asgard_harness.ownership_document import load_ownership
from asgard_harness.selfcheck import FIXTURES, SUBJECT_KEY, SUBJECT_RUNBOOK, Fixture, run_fixture, run_self_check
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


# --- Story 1.4: repository-stored secret material -------------------------------------------------


def test_the_repo_secrets_procedure_is_complete(repo_workspace: Workspace):
    entry = load_index(repo_workspace.index_path).entry("PROC-REPO-SECRETS")
    assert entry is not None
    assert entry.status == "complete"
    assert repo_workspace.declared_exists(entry.runbook)
    assert repo_workspace.declared_exists(entry.automation)


def test_the_repository_holds_no_plaintext_secret_and_says_what_it_scanned(repo_workspace: Workspace):
    report = run_secrets(repo_workspace)
    assert report.exit_code == 0, report.render()
    scan = next(check for check in report.results if check.name == "Plaintext secret material")
    assert scan.examined > 0, "a scan that examined nothing has proven nothing"
    assert "gitignored paths excluded" in scan.note


def test_the_selfcheck_subject_entry_is_still_inert(repo_workspace: Workspace):
    """The fixtures need a `planned` entry with neither half on disk, and the only one for its story.

    When this fails, the story owning `selfcheck.SUBJECT_KEY` has landed and the constant must be
    re-pointed at another still-`planned` entry — along with `SUBJECT_RUNBOOK`. Without this test
    that event surfaces as a dozen unrelated-looking fixture failures.
    """
    index = load_index(repo_workspace.index_path)
    entry = index.entry(SUBJECT_KEY)
    assert entry is not None, f"{SUBJECT_KEY} is not in the Index at all"
    assert entry.status == "planned", f"{SUBJECT_KEY} has landed; re-point selfcheck.SUBJECT_KEY"
    assert not repo_workspace.declared_exists(entry.runbook)
    assert not repo_workspace.declared_exists(entry.automation)
    assert entry.runbook == SUBJECT_RUNBOOK
    assert [e.key for e in index.entries if e.story == entry.story] == [SUBJECT_KEY]


def test_the_gate_chain_names_the_secret_scan(repo_root: Path):
    """A check that only ever runs inside another one is a check nobody notices going missing."""
    manifest = (repo_root / "pixi.toml").read_text(encoding="utf-8")
    ci_line = next(line for line in manifest.splitlines() if line.startswith("ci = "))
    assert '"secrets"' in ci_line, ci_line


def test_every_commit_hook_comes_from_the_pixi_environment(repo_root: Path):
    """All-local hooks: no second toolchain, and `--install-hooks` needs no network."""
    config = yaml.YAML(typ="safe").load((repo_root / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    assert [repo["repo"] for repo in config["repos"]] == ["local"]
    hooks = {hook["id"]: hook for hook in config["repos"][0]["hooks"]}
    assert hooks["asgard-secret-scan"]["entry"] == "pixi run --manifest-path pixi.toml secrets"
    assert hooks["asgard-secret-scan"]["stages"] == ["pre-commit"]
    assert hooks["asgard-conventional-commit"]["stages"] == ["commit-msg"]
    assert set(config["default_install_hook_types"]) == {"pre-commit", "commit-msg"}
    assert all(hook["language"] == "system" for hook in hooks.values())


def test_every_hook_entry_names_a_task_pixi_actually_declares(repo_root: Path):
    """`pixi run <name>` falls back to running <name> as a shell command when no task matches.

    A hook whose task cannot be resolved therefore exits 127 and pre-commit renders it exactly like
    the scan finding a credential — commit rejected, nothing checked. This test needs no pixi and
    no environment: it reads both files and fails naming the task, in every checkout.
    """
    config = yaml.YAML(typ="safe").load((repo_root / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    manifest = (repo_root / "pixi.toml").read_text(encoding="utf-8")
    declared = {
        line.split("=", 1)[0].strip()
        for line in manifest.splitlines()
        if "=" in line and not line.startswith((" ", "\t", "#")) and not line.startswith("[")
    }
    entries = [hook["entry"] for repo in config["repos"] for hook in repo["hooks"]]
    assert entries, "no hooks configured"
    for entry in entries:
        tokens = entry.split()
        assert tokens[:4] == ["pixi", "run", "--manifest-path", "pixi.toml"], entry
        assert tokens[4] in declared, f"{entry!r} names a task pixi.toml does not declare"


def test_the_secret_hook_passes_on_the_clean_repository(repo_root: Path):
    """The direction the first cut of this story never tested.

    A hook that rejects everything satisfies "it fires on bad input" perfectly. Only running it
    against input it must accept distinguishes a working check from a broken one, and this is the
    assertion that turns `command not found` from an invisible failure into a red build.
    """
    completed = subprocess.run(
        ["pre-commit", "run", "asgard-secret-scan", "--all-files"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Passed" in completed.stdout


def test_every_hook_entry_names_a_task_the_COMMITTED_manifest_declares(repo_root: Path):
    """The test that would have caught it: pre-commit runs hooks against COMMITTED content.

    Before running a hook, pre-commit reverts unstaged changes, so the `pixi.toml` the hook sees is
    the staged/committed one, not the working tree. A hook naming a task that exists only in the
    working tree therefore resolves to nothing, pixi runs the name as a shell command, and every
    commit is rejected with `command not found` — rendered by pre-commit exactly like the scan
    finding a credential.

    That is what shipped. The first verification of this story staged everything before committing,
    which left pre-commit nothing to revert and hid the bug completely.

    The working-tree check above says the configuration will be consistent *after* this commit;
    this one says it is consistent *now*, which is what the installed hooks actually run against.
    A failure here means `pixi.toml` and `.pre-commit-config.yaml` have not landed together.
    """
    config = yaml.YAML(typ="safe").load((repo_root / ".pre-commit-config.yaml").read_text(encoding="utf-8"))
    committed = subprocess.run(
        ["git", "-C", str(repo_root), "show", "HEAD:pixi.toml"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    declared = {
        line.split("=", 1)[0].strip()
        for line in committed.splitlines()
        if "=" in line and not line.startswith((" ", "\t", "#")) and not line.startswith("[")
    }
    for repo in config["repos"]:
        for hook in repo["hooks"]:
            task = hook["entry"].split()[-1]
            assert task in declared, (
                f"hook {hook['id']!r} runs `pixi run ... {task}`, which HEAD:pixi.toml does not declare. "
                "pre-commit reverts unstaged changes before running, so this hook resolves to a shell "
                "command and blocks EVERY commit with `command not found`. Commit pixi.toml and "
                ".pre-commit-config.yaml in the same change."
            )


def test_the_pre_commit_configuration_is_valid(repo_root: Path):
    """`pixi run bootstrap` was broken from the workspace commit until this story; it must stay fixed."""
    completed = subprocess.run(
        ["pre-commit", "validate-config", ".pre-commit-config.yaml"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_the_command_the_hook_runs_rejects_a_staged_secret_and_names_the_path(tmp_path: Path, repo_root: Path):
    """End to end through the real entry point, in a throwaway git repository.

    The hook's `entry` is `pixi run secrets`, which is this command. Running it here rather than
    driving `git commit` in the developer's own checkout keeps the proof from installing hooks into
    the repository the test is running in.
    """
    tree = tmp_path / "repo"
    tree.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=tree, check=True)
    shutil.copyfile(repo_root / ".sops.yaml", tree / ".sops.yaml")
    # Assembled, never spelled out: this file is itself scanned by the check it is proving.
    (tree / "bind.env").write_text("DIRECTORY_BIND_TOKEN" + "=" + "Qx7mZ2pR9tL4vB8n\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=tree, check=True)

    completed = subprocess.run(
        [sys.executable, "-m", "asgard_harness", "secrets", "--root", str(tree)],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONPATH": str(repo_root / "src")},
    )
    assert completed.returncode == 1, completed.stdout
    assert "bind.env" in completed.stdout
    assert "Qx7mZ2pR9tL4vB8n" not in completed.stdout, "the report must never echo the secret it found"


def test_an_encrypted_file_yields_nothing_without_the_key(tmp_path: Path):
    """AD-15's substantive claim, proven against a real ephemeral key rather than asserted.

    Nothing here touches the Repository's own policy or any real identity: `age-keygen` makes a
    throwaway key inside `tmp_path`, and it is discarded with the directory.
    """
    for tool in ("sops", "age-keygen"):
        assert shutil.which(tool), f"{tool} comes from the pixi environment; run through `pixi run`"

    identity = tmp_path / "key.txt"
    subprocess.run(["age-keygen", "-o", str(identity)], capture_output=True, check=True)
    public = subprocess.run(
        ["age-keygen", "-y", str(identity)], capture_output=True, text=True, check=True
    ).stdout.strip()

    (tmp_path / ".sops.yaml").write_text(
        f"creation_rules:\n  - path_regex: (^|/)[^/]+\\.sops\\.ya?ml$\n    age: {public}\n", encoding="utf-8"
    )
    # Named `plaintext` rather than `secret`: this file is scanned by the check it is proving, and
    # `secret = "<literal>"` is exactly the shape the assignment pattern exists to catch.
    plaintext = "Qx7mZ2pR9tL4vB8n-bind"
    covered = tmp_path / "bind.sops.yaml"
    covered.write_text(f"directory_bind_password: {plaintext}\n", encoding="utf-8")

    subprocess.run(
        ["sops", "--encrypt", "--in-place", covered.name],
        cwd=tmp_path,
        capture_output=True,
        check=True,
        env={**os.environ, "SOPS_AGE_KEY_FILE": str(identity)},
    )

    ciphertext = covered.read_text(encoding="utf-8")
    assert plaintext not in ciphertext, "the plaintext survived encryption"
    assert "ENC[AES256_GCM," in ciphertext
    assert is_sops_encrypted(ciphertext)

    without_key = subprocess.run(
        ["sops", "--decrypt", covered.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
        env={key: value for key, value in os.environ.items() if key != "SOPS_AGE_KEY_FILE"},
    )
    assert without_key.returncode != 0, "decryption without the key must fail, loudly"
    assert plaintext not in without_key.stdout
    assert "no master key was able to decrypt" in without_key.stderr

    with_key = subprocess.run(
        ["sops", "--decrypt", covered.name],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, "SOPS_AGE_KEY_FILE": str(identity)},
    )
    assert plaintext in with_key.stdout, "the key must still recover the value it encrypted"


def test_an_encrypted_repository_file_reads_as_ciphertext_to_the_scan(tmp_path: Path):
    """The scan accepts a covered path only once it is genuinely encrypted, not merely named."""
    assert shutil.which("sops"), "sops comes from the pixi environment; run through `pixi run`"
    identity = tmp_path / "key.txt"
    subprocess.run(["age-keygen", "-o", str(identity)], capture_output=True, check=True)
    public = subprocess.run(
        ["age-keygen", "-y", str(identity)], capture_output=True, text=True, check=True
    ).stdout.strip()

    tree = tmp_path / "repo"
    tree.mkdir()
    (tree / ".sops.yaml").write_text(
        f"creation_rules:\n  - path_regex: (^|/)[^/]+\\.sops\\.ya?ml$\n    age: {public}\n", encoding="utf-8"
    )
    covered = tree / "bind.sops.yaml"
    covered.write_text("directory_bind_password: Qx7mZ2pR9tL4vB8n\n", encoding="utf-8")
    workspace = Workspace(root=tree)

    before = run_secrets(workspace)
    assert before.exit_code == 1
    assert {finding.defect for finding in before.findings} == {"declared-encrypted-path-in-plaintext"}

    subprocess.run(
        ["sops", "--encrypt", "--in-place", covered.name],
        cwd=tree,
        capture_output=True,
        check=True,
        env={**os.environ, "SOPS_AGE_KEY_FILE": str(identity)},
    )
    assert run_secrets(workspace).exit_code == 0
