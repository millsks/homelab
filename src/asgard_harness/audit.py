"""The audit: every detector, run against one workspace, reported as one thing.

The order below is the order the two documents state their defect classes in, so a reader can hold
the report and the definition side by side.

**`run_audit` is a pure reader and must stay one.** It parses committed documents and stats the
working tree; it opens no network connection, needs no credential, and touches no managed system.
That is what makes it safe to sit in the merge gate, and it is what the Procedure's own Runbook
promises in its preconditions. The convergence suite shells out to `ansible-playbook`, `tofu plan`,
and `kubectl diff` against real infrastructure, so it lives in `run_convergence`, which the
schedule runs and the gate does not. Putting it in the gate would have meant every pull request
reaching production hosts the moment the first role landed.
"""

from __future__ import annotations

from collections.abc import Callable

from asgard_harness import checks_crossdoc, checks_index, checks_ownership, checks_secrets, convergence
from asgard_harness.epics import load_stories
from asgard_harness.findings import AuditReport, CheckResult, report_of
from asgard_harness.index_document import load_index
from asgard_harness.ownership_document import load_ownership
from asgard_harness.secrets_policy import POLICY_FILENAME, load_policy
from asgard_harness.workspace import Workspace

CommitResolver = Callable[[Workspace], str | None]

EXPECTED_AUDIT_SKIPS: frozenset[str] = frozenset({"Unowned resource class"})
"""The only check `run_audit` may report as SKIPPED against a complete checkout.

A SKIP does not fail the gate, so a detector that quietly degrades to SKIP — a shallow clone
silencing the provenance check, say — would leave the gate green while one rule stopped being
enforced. The integration suite asserts the skipped set equals exactly this, which turns any new
silent degradation into a test failure.
"""


def run_audit(workspace: Workspace, *, resolve_commit: CommitResolver | None = None) -> AuditReport:
    """Run every document and filesystem detector against a workspace.

    Reads only. Safe for the merge gate.

    Args:
        workspace: The repository under audit.
        resolve_commit: Optional override for how the `epics.md` commit is discovered. The
            self-check supplies one because its throwaway copies are not git repositories.

    Returns:
        The assembled report. Its `exit_code` is non-zero when any detector found anything.
    """
    index = load_index(workspace.index_path)
    ownership = load_ownership(workspace.ownership_path)
    stories = load_stories(workspace.epics_path)

    results: list[CheckResult] = [
        checks_index.check_status_enumeration(index),
        checks_index.check_incomplete_procedure(index, workspace),
        checks_index.check_status_matches_filesystem(index, workspace),
        checks_index.check_manual_literal(index),
        checks_index.check_manual_verification(index),
        checks_index.check_manual_human_form(index, workspace),
        checks_index.check_duplicate_keys(index),
        checks_index.check_retired_keys(index),
        checks_index.check_story_coverage(index, stories),
        checks_index.check_provenance(index, workspace, resolve_commit),
        checks_index.check_alert_sources(index, stories),
        checks_crossdoc.check_back_references(index, workspace),
        checks_crossdoc.check_template_sentinel(workspace),
        checks_crossdoc.check_runbook_shape(workspace),
        checks_crossdoc.check_layer_dependencies(workspace),
        checks_ownership.check_owner_enumeration(ownership),
        checks_ownership.check_one_owner(ownership),
        checks_ownership.check_verification_present(ownership),
        checks_ownership.check_procedure_coverage(ownership, index),
        checks_ownership.unowned_defect_status(ownership),
        *checks_secrets.run_secret_checks(workspace, load_policy(workspace.root / POLICY_FILENAME)),
        checks_index.check_totals(index, stories, workspace),
    ]
    return report_of(results)


def run_secrets(workspace: Workspace) -> AuditReport:
    """Run only the secret-handling checks.

    This is what the commit-time hook runs, and it is deliberately the *same code* the gate runs
    inside `run_audit` rather than a second implementation that could drift from it. The hook needs
    it alone because a commit must not wait on the document audit, and because a Repository can be
    perfectly documented and still be carrying a credential.

    Reads only. Safe for the merge gate and for a commit hook.

    Args:
        workspace: The repository under audit.

    Returns:
        The assembled report.
    """
    return report_of(checks_secrets.run_secret_checks(workspace, load_policy(workspace.root / POLICY_FILENAME)))


def run_drift(workspace: Workspace) -> AuditReport:
    """Run only the scheduled check-mode drift detection.

    This is the run AD-23 puts on a schedule for the push-based layers. A non-empty diff exits
    non-zero, and so does a check-mode run that failed to complete.

    **Reaches managed systems.** Scheduled, never in the merge gate.

    Args:
        workspace: The repository under audit.

    Returns:
        The assembled report.
    """
    index = load_index(workspace.index_path)
    return report_of([convergence.check_drift_suite(index, workspace)])


def run_convergence(workspace: Workspace) -> AuditReport:
    """Run every discoverable Automation twice: AD-3 convergence, then NFR-3 idempotence.

    **Reaches managed systems.** Scheduled, never in the merge gate.

    Args:
        workspace: The repository under audit.

    Returns:
        The assembled report.
    """
    index = load_index(workspace.index_path)
    return report_of([convergence.check_convergence_suite(index, workspace)])
