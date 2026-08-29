"""Convergence, idempotence, and scheduled check-mode drift detection.

AD-3 makes convergence the definition of done: Automation run against a system built by hand from
its Runbook reports zero changes, and NFR-3 adds that a second consecutive run reports zero changes
too. AD-23 adds that the push-based layers L0-L2 carry scheduled check-mode runs whose non-empty
diff exits non-zero and is recorded.

**A run that errored is not a run that found no changes.** Each tool signals "changes present" with
its own exit code and signals failure with a different one, so each parser encodes its own
convention and a decision is only made from a run that actually completed. Reading a crashed tool
as a clean run is the same defect as a gate guard that reports success on failure — the harness had
it, which is why the distinction is now structural: `RunResult.error` is set by the parser, and
every decision function refuses to judge a run that carries it.

Exit-code conventions, each from its tool's own documentation:

| Tool | No changes | Changes present | Failure |
| --- | --- | --- | --- |
| `ansible-playbook --check` | 0 | 0 (reported in the play recap, not the exit code) | any non-zero |
| `tofu plan -detailed-exitcode` | 0 | 2 | 1 |
| `kubectl diff` | 0 | 1 | greater than 1 |

No Automation exists in this repository yet, so nothing real is run today and the discovery step
says so out loud rather than reporting a pass over an empty set. What is real now is the decision
logic, and the self-check exercises every outcome of it — clean, changed, and errored — against
fixtures.
"""

from __future__ import annotations

import re
import shlex
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from asgard_harness import defects
from asgard_harness.findings import CheckResult, Finding, result, skipped
from asgard_harness.index_document import ProcedureIndex
from asgard_harness.references import automation_mechanism
from asgard_harness.workspace import LAYERS, Workspace

PUSH_BASED_LAYERS: tuple[str, ...] = LAYERS[:3]
"""L0-L2 have no reconciliation loop, so drift is only visible via a scheduled check-mode run."""

LAUNCH_FAILURE_EXIT_CODE = 127
"""What `run_command` reports when the tool could not be started at all."""

_ANSIBLE_RECAP_RE = re.compile(r"^(\S+)\s*:\s*ok=\d+\s+changed=(\d+)", re.MULTILINE)
_TOFU_CHANGE_RE = re.compile(r"^\s*#\s+(\S+)\s+will be\b", re.MULTILINE)
_KUBECTL_DIFF_RE = re.compile(r"^diff\b.*?\s(\S+)$", re.MULTILINE)

_OUTPUT_TAIL_CHARS = 400


@dataclass(frozen=True, slots=True)
class RunResult:
    """The outcome of one check-mode run of an Automation.

    Attributes:
        changed: The items the run reported as changed. Only meaningful when `error` is empty.
        exit_code: The tool's own exit code.
        output: The raw output, kept so a failure can be recorded rather than summarised away.
        error: Why the tool itself failed, or `""` when it completed. A non-empty value means the
            run proves nothing: it is neither "converged" nor "drifted", and must never be read as
            zero changes.
        command: The command that was run, for naming in a finding.
    """

    changed: tuple[str, ...] = ()
    exit_code: int = 0
    output: str = ""
    error: str = ""
    command: str = ""

    @property
    def errored(self) -> bool:
        """Whether the tool failed rather than completing.

        Returns:
            True when the run cannot support any conclusion about convergence.
        """
        return bool(self.error)


Runner = Callable[[], RunResult]
"""A callable that performs one check-mode run and reports what it would change."""


def _tail(output: str) -> str:
    stripped = output.strip()
    if len(stripped) <= _OUTPUT_TAIL_CHARS:
        return stripped
    return "…" + stripped[-_OUTPUT_TAIL_CHARS:]


def _failure(tool: str, exit_code: int, output: str, command: str, meaning: str) -> RunResult:
    detail = f"{tool} exited {exit_code} ({meaning})"
    if command:
        detail += f" running `{command}`"
    tail = _tail(output)
    if tail:
        detail += f"; last output: {tail}"
    return RunResult(changed=(), exit_code=exit_code, output=output, error=detail, command=command)


def parse_ansible_check(exit_code: int, output: str, command: str = "") -> RunResult:
    """Read an `ansible-playbook --check --diff` run.

    Check mode reports changes in the play recap, never in the exit code, so **any** non-zero exit
    is a failure of the tool: 1 error, 2 host failures, 3 unreachable, 4 parse error.

    Args:
        exit_code: The playbook's exit code.
        output: The playbook's combined output.
        command: The command that produced it, for naming in a finding.

    Returns:
        A run result naming every host reporting a non-zero change count, or carrying an error.
    """
    if exit_code != 0:
        meanings = {
            1: "error",
            2: "one or more hosts failed",
            3: "one or more hosts unreachable",
            4: "parse error",
            LAUNCH_FAILURE_EXIT_CODE: "could not be started",
        }
        return _failure("ansible-playbook", exit_code, output, command, meanings.get(exit_code, "unexpected failure"))
    changed = tuple(host for host, count in _ANSIBLE_RECAP_RE.findall(output) if int(count) > 0)
    return RunResult(changed=changed, exit_code=exit_code, output=output, command=command)


def parse_tofu_plan(exit_code: int, output: str, command: str = "") -> RunResult:
    """Read a `tofu plan -detailed-exitcode` run.

    The documented convention is 0 for no changes, 2 for changes present, and 1 for an error.
    Anything else — a missing binary, an uninitialised module — is also a failure.

    Args:
        exit_code: The plan's exit code.
        output: The plan's combined output.
        command: The command that produced it, for naming in a finding.

    Returns:
        A run result naming every resource address the plan would touch, or carrying an error.
    """
    if exit_code not in (0, 2):
        meaning = "could not be started" if exit_code == LAUNCH_FAILURE_EXIT_CODE else "error"
        return _failure("tofu plan", exit_code, output, command, meaning)
    changed = tuple(dict.fromkeys(_TOFU_CHANGE_RE.findall(output)))
    if exit_code == 2 and not changed:
        changed = ("<plan reports changes but names no resource address>",)
    return RunResult(changed=changed, exit_code=exit_code, output=output, command=command)


def parse_kubectl_diff(exit_code: int, output: str, command: str = "") -> RunResult:
    """Read a `kubectl diff` run.

    The documented convention is 0 for no differences and 1 for differences present; anything
    greater than 1 is an error — most often no reachable cluster.

    Args:
        exit_code: The diff's exit code.
        output: The diff's combined output.
        command: The command that produced it, for naming in a finding.

    Returns:
        A run result naming every object with a difference, or carrying an error.
    """
    if exit_code not in (0, 1):
        meaning = "could not be started" if exit_code == LAUNCH_FAILURE_EXIT_CODE else "error"
        return _failure("kubectl diff", exit_code, output, command, meaning)
    changed = tuple(dict.fromkeys(_KUBECTL_DIFF_RE.findall(output)))
    if exit_code == 1 and not changed:
        changed = ("<diff reports differences but names no object>",)
    return RunResult(changed=changed, exit_code=exit_code, output=output, command=command)


def run_command(argv: Sequence[str], cwd: Path) -> tuple[int, str]:
    """Run a check-mode command and capture its result.

    Args:
        argv: The command and its arguments. Never passed through a shell.
        cwd: The working directory.

    Returns:
        The exit code and the combined output. A command that cannot be launched at all returns
        `LAUNCH_FAILURE_EXIT_CODE` and the reason as its output, which every parser treats as a
        tool failure rather than as a clean run.
    """
    try:
        completed = subprocess.run(list(argv), cwd=cwd, capture_output=True, text=True, check=False, timeout=900)
    except (OSError, subprocess.SubprocessError) as error:
        return LAUNCH_FAILURE_EXIT_CODE, f"could not run {shlex.join(argv)}: {error}"
    return completed.returncode, completed.stdout + completed.stderr


def _errored_finding(name: str, run: RunResult) -> Finding:
    return Finding(
        defect=defects.AUTOMATION_CHECK_FAILED,
        subject=name,
        detail=f"the check-mode run did not complete, so it proves nothing about convergence: {run.error}",
        location=run.command or name,
    )


def check_convergence_and_idempotence(name: str, runner: Runner) -> list[Finding]:
    """AD-3 convergence on the first run, NFR-3 idempotence on the second.

    Both halves of the claim are checked, and they are separate defects. Convergence is about the
    *first* run against a system built by hand from the Runbook reporting zero changes; idempotence
    is about the second consecutive run also reporting zero. Checking only the second and calling it
    both is how a gap gets papered over.

    A run that errored ends the check immediately: a second run cannot rescue a first that never
    completed, and reporting "converged" from a crashed tool is the failure this module exists to
    prevent.

    Args:
        name: What is being run, for the finding's subject.
        runner: Performs one check-mode run.

    Returns:
        Every finding, in the order the two claims are made.
    """
    first = runner()
    if first.errored:
        return [_errored_finding(name, first)]
    findings: list[Finding] = []
    if first.changed:
        findings.append(
            Finding(
                defect=defects.AUTOMATION_NOT_CONVERGED,
                subject=name,
                detail=(
                    f"the first check-mode run reported {len(first.changed)} change(s) against the system as "
                    f"built: {list(first.changed)}. AD-3: this is a documentation defect closed at discovery, "
                    "never accommodated by weakening the Automation"
                ),
                location=first.command or name,
            )
        )
    second = runner()
    if second.errored:
        findings.append(_errored_finding(name, second))
        return findings
    if second.changed:
        findings.append(
            Finding(
                defect=defects.AUTOMATION_NOT_IDEMPOTENT,
                subject=name,
                detail=f"the second consecutive run reported {len(second.changed)} change(s): {list(second.changed)}",
                location=second.command or name,
            )
        )
    return findings


def check_drift(name: str, runner: Runner) -> CheckResult:
    """Scheduled check-mode drift detection: a non-empty diff is a defect, and so is a failed run.

    Args:
        name: What is being run, for the finding's subject.
        runner: Performs one check-mode run.

    Returns:
        The check result, naming the drifted items when the diff is non-empty, or the tool failure
        when the run did not complete.
    """
    run = runner()
    if run.errored:
        return result(
            f"Drift — {name}", defects.CHECK_MODE_DIFF_NOT_EMPTY, 1, "check-mode run", [_errored_finding(name, run)]
        )
    findings: list[Finding] = []
    if run.changed:
        findings.append(
            Finding(
                defect=defects.CHECK_MODE_DIFF_NOT_EMPTY,
                subject=name,
                detail=f"check-mode run reported {len(run.changed)} change(s): {list(run.changed)}",
                location=run.command or name,
            )
        )
    return result(f"Drift — {name}", defects.CHECK_MODE_DIFF_NOT_EMPTY, 1, "check-mode run", findings)


@dataclass(frozen=True, slots=True)
class AutomationTarget:
    """An Automation half that exists on disk and can be run in check mode.

    Attributes:
        key: The Procedure key.
        layer: The owning layer.
        path: The Automation path as the Index writes it.
        mechanism: Which tool declares it.
    """

    key: str
    layer: str
    path: str
    mechanism: str

    @property
    def name(self) -> str:
        """How the target is named in a finding.

        Returns:
            The key and the declared path.
        """
        return f"{self.key} ({self.path})"


def discover_all(
    index: ProcedureIndex, workspace: Workspace, *, layers: Sequence[str] | None = None
) -> list[AutomationTarget]:
    """Find every Automation half that exists on disk, whatever its mechanism.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.
        layers: Restrict to these layers; `None` means every layer.

    Returns:
        The targets, in Index order, including ones with no check mode.
    """
    wanted = set(layers) if layers is not None else set(LAYERS)
    return [
        AutomationTarget(
            key=entry.key,
            layer=entry.layer,
            path=entry.automation,
            mechanism=automation_mechanism(entry.automation),
        )
        for entry in index.entries
        if not entry.is_manual_literal and entry.layer in wanted and workspace.declared_exists(entry.automation)
    ]


def discover_targets(
    index: ProcedureIndex, workspace: Workspace, *, layers: Sequence[str] | None = None
) -> list[AutomationTarget]:
    """Find the Automation halves that exist and could be run in check mode.

    Repository tooling is excluded: its "check-mode run" is this harness, and running the harness
    against itself proves nothing about convergence.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.
        layers: Restrict to these layers; `None` means every layer.

    Returns:
        The runnable targets, in Index order.
    """
    return [
        target for target in discover_all(index, workspace, layers=layers) if target.mechanism != "repository-tooling"
    ]


def _nothing_to_run_reason(index: ProcedureIndex, workspace: Workspace, layers: Sequence[str] | None) -> str:
    """Say precisely why there is nothing to run, naming what was excluded and why.

    "No Automation half exists" was simply untrue: `pixi.toml` is declared as the Automation half of
    PROC-CONVERGENCE-HARNESS and it exists. A skip reason that misstates the situation is a skip
    nobody will re-examine.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.
        layers: The layers under consideration, or `None` for all.

    Returns:
        The reason, naming any excluded Automation half.
    """
    scope = "" if layers is None else f" under layers {list(layers)}"
    excluded = [
        target for target in discover_all(index, workspace, layers=layers) if target.mechanism == "repository-tooling"
    ]
    if not excluded:
        return (
            f"no Automation half exists on disk{scope} yet; the decision logic is proven against fixtures "
            "by the self-check and becomes real when the first role lands"
        )
    named = ", ".join(f"{target.key} ({target.path})" for target in excluded)
    return (
        f"the only Automation half present{scope} is repository tooling — {named} — whose check-mode run IS this "
        "harness, so running it against itself would prove nothing about convergence. No tool-driven Automation "
        "exists yet; the decision logic is proven against fixtures by the self-check"
    )


RunnerFactory = Callable[[AutomationTarget], Runner | None]
CheckFunction = Callable[[str, Runner], Sequence[Finding]]


def run_targets(
    targets: Sequence[AutomationTarget], make_runner: RunnerFactory, check: CheckFunction
) -> tuple[list[Finding], int]:
    """Apply a check to every target, reporting the ones that cannot be run.

    A target the harness has no check mode for is a **finding**, not a silent skip: it would
    otherwise be counted as examined while nothing examined it, which is a silent pass wearing the
    costume of a count.

    Args:
        targets: The Automation halves to check.
        make_runner: Builds a runner, or returns `None` when the mechanism cannot be driven.
        check: Applies the decision logic to one runner.

    Returns:
        Every finding, and how many targets were actually run.
    """
    findings: list[Finding] = []
    ran = 0
    for target in targets:
        runner = make_runner(target)
        if runner is None:
            findings.append(
                Finding(
                    defect=defects.AUTOMATION_NO_CHECK_MODE,
                    subject=target.name,
                    detail=(
                        f"declared by the {target.mechanism} mechanism, which the harness has no check-mode "
                        "runner for; it was NOT checked and must not be counted as converged"
                    ),
                    location=target.path,
                )
            )
            continue
        ran += 1
        findings.extend(check(target.name, runner))
    return findings, ran


def check_convergence_suite(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Run every discoverable Automation twice, checking convergence then idempotence.

    This shells out to the real tools against real infrastructure, so it belongs to the scheduled
    run and **not** to the merge gate — see `asgard_harness.audit`.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result. With no Automation on disk the result is `SKIPPED`, naming the reason —
        never a pass over an empty set.
    """
    targets = discover_targets(index, workspace)
    if not targets:
        return skipped(
            "Convergence and idempotence",
            defects.AUTOMATION_NOT_CONVERGED,
            "Automation halves",
            _nothing_to_run_reason(index, workspace, None),
        )
    findings, ran = run_targets(
        targets, lambda target: build_runner(target, workspace), check_convergence_and_idempotence
    )
    note = f"{len(targets) - ran} target(s) had no runnable check mode" if ran != len(targets) else ""
    return result(
        "Convergence and idempotence",
        defects.AUTOMATION_NOT_CONVERGED,
        ran,
        "Automation halves run twice",
        findings,
        note,
    )


def check_drift_suite(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Scheduled check-mode run over the push-based layers.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result. With no push-based Automation on disk the result is `SKIPPED`.
    """
    targets = discover_targets(index, workspace, layers=PUSH_BASED_LAYERS)
    if not targets:
        return skipped(
            "Scheduled drift detection",
            defects.CHECK_MODE_DIFF_NOT_EMPTY,
            "push-based Automation halves",
            _nothing_to_run_reason(index, workspace, PUSH_BASED_LAYERS)
            + "; this detector is registered as an alert source and becomes real when the first role lands",
        )
    findings, ran = run_targets(
        targets, lambda target: build_runner(target, workspace), lambda name, runner: check_drift(name, runner).findings
    )
    note = f"{len(targets) - ran} target(s) had no runnable check mode" if ran != len(targets) else ""
    return result(
        "Scheduled drift detection",
        defects.CHECK_MODE_DIFF_NOT_EMPTY,
        ran,
        "push-based Automation halves",
        findings,
        note,
    )


def build_runner(target: AutomationTarget, workspace: Workspace) -> Runner | None:
    """Build the check-mode runner for one Automation half.

    Every runner passes the tool's real exit code to its parser. Discarding it is what let a failed
    tool read as a clean run.

    Args:
        target: The Automation half to run.
        workspace: The repository under audit.

    Returns:
        A runner, or `None` when the mechanism has no check mode the harness knows how to drive.
        The caller reports that by name; it never treats it as a pass.
    """
    root = workspace.root
    if target.mechanism == "ansible":

        def ansible() -> RunResult:
            argv = ["ansible-playbook", "--check", "--diff", target.path]
            code, output = run_command(argv, root)
            return parse_ansible_check(code, output, shlex.join(argv))

        return ansible
    if target.mechanism == "opentofu":

        def opentofu() -> RunResult:
            argv = ["tofu", "plan", "-detailed-exitcode", "-input=false"]
            module = workspace.resolve(target.path).parent
            code, output = run_command(argv, module)
            return parse_tofu_plan(code, output, f"{shlex.join(argv)} (in {workspace.relative(module)})")

        return opentofu
    if target.mechanism == "kubernetes":

        def kubernetes() -> RunResult:
            argv = ["kubectl", "diff", "-k", target.path]
            code, output = run_command(argv, root)
            return parse_kubectl_diff(code, output, shlex.join(argv))

        return kubernetes
    return None
