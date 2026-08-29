"""The harness proving its own failure path.

A harness whose failure path is never exercised is the same defect as a gate that cannot fail, and
this repository has already shipped one of those. So: for every defect class the harness claims to
detect, a known-bad fixture is injected into a throwaway copy of the repository, the audit is
asserted to exit non-zero *and to name that defect class*, and the copy is deleted. A fixture that
does not fire is itself a failure — a passing self-check over a fixture that changed nothing would
prove exactly as much as no self-check at all.

Fixtures are applied to a copy, never to the working tree, so the working tree is clean whatever
happens — including when the process is killed part-way through.
"""

from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path

from asgard_harness import defects
from asgard_harness.audit import run_audit
from asgard_harness.convergence import (
    LAUNCH_FAILURE_EXIT_CODE,
    AutomationTarget,
    Runner,
    RunResult,
    check_convergence_and_idempotence,
    check_drift,
    parse_ansible_check,
    parse_kubectl_diff,
    parse_tofu_plan,
    run_targets,
)
from asgard_harness.findings import AuditReport, CheckResult, Finding, report_of, result, skipped
from asgard_harness.index_document import load_index
from asgard_harness.markdown import clean, split_row
from asgard_harness.workspace import Workspace

COPIED_PATHS: tuple[str, ...] = (
    "PROCEDURE-INDEX.md",
    "README.md",
    "pixi.toml",
    "pyproject.toml",
    ".yamllint",
    ".gitignore",
    "docs",
    "runbooks",
    "ansible",
    "tofu",
    "k8s",
    "src",
    "tests",
    ".github",
    "_bmad-output/planning-artifacts/epics.md",
)
"""Everything a fixture can reach.

This must cover every path any detector reads, not merely every path a detector reads *today*. A
detector that reads something outside this set sees an empty workspace in every fixture, so it can
never fire and the fixture proving it fires would prove nothing — the self-check would report a row
of passes over a detector that was structurally unable to fail. `test_copy_set_covers_every_path_a
_detector_reads` pins that, deriving the roots from `Workspace` rather than restating them.
"""

_COPY_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc", ".pytest_cache", ".coverage", "htmlcov")

ENTRY_ANCHOR = "## The Index"
MANUAL_ANCHOR = "## Deliberately manual work"

_STATUS_COLUMN = 6
_AUTOMATION_COLUMN = 5
_RUNBOOK_COLUMN = 4
_STORY_COLUMN = 3
_VERIFICATION_COLUMN = 3
_HUMAN_FORM_COLUMN = 4
_OWNER_COLUMN = 1
_OWNERSHIP_VERIFICATION_COLUMN = 3
_OWNERSHIP_PROCEDURE_COLUMN = 4

SUBJECT_KEY = "PROC-REPO-SECRETS"
"""The entry fixtures mutate. Story 1.4 is unstarted, so neither half exists and the row is inert."""


class FixtureError(RuntimeError):
    """A fixture could not be applied because the document no longer has the shape it targets."""


@dataclass(frozen=True, slots=True)
class Fixture:
    """One known-bad state and the defect class it must provoke.

    Attributes:
        name: What the fixture does, in a few words.
        defect: The defect-class identifier the audit must name.
        apply: Mutates a copied workspace into the known-bad state.
    """

    name: str
    defect: str
    apply: Callable[[Workspace], None]
    requires_git: bool = False
    """Whether the fixture needs git to answer for the real repository.

    The provenance fixture is the only one that does. It edits the commit the Index records and
    relies on the detector comparing it against the commit git reports — so if git cannot answer,
    there is nothing to compare against and the fixture must SKIP saying so. The first cut fell
    back to the Index's own recorded hash, which meant the detector was handed the value the
    document supplied and "passed" while exercising no git at all: a fixture that proves itself.
    """


@dataclass(frozen=True, slots=True)
class FixtureOutcome:
    """What happened when one fixture was injected.

    Attributes:
        fixture: The fixture that was injected.
        exit_code: The audit's exit code with the fixture in place.
        subjects: The subjects the audit named for the expected defect class.
        error: Why the fixture could not be applied at all, if it could not.
    """

    fixture: Fixture
    exit_code: int
    subjects: tuple[str, ...]
    error: str = ""
    skipped_reason: str = ""

    @property
    def fired(self) -> bool:
        """Whether the fixture provoked the defect it targets.

        Returns:
            True when the audit exited non-zero and named the expected defect class.
        """
        return not self.error and not self.skipped_reason and self.exit_code != 0 and bool(self.subjects)


# --- Document surgery ----------------------------------------------------------------------------


def _lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()


def _write(path: Path, lines: Iterable[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _row_index(lines: list[str], key: str, anchor: str) -> int:
    start = 0
    if anchor:
        for number, line in enumerate(lines):
            if line.strip() == anchor:
                start = number
                break
        else:
            raise FixtureError(f"anchor {anchor!r} not found")
    for number in range(start, len(lines)):
        line = lines[number]
        if not line.lstrip().startswith("|"):
            continue
        cells = split_row(line)
        if cells and clean(cells[0]) == key:
            return number
    raise FixtureError(f"no table row keyed {key!r} after {anchor or 'the start of the file'}")


def _render_row(cells: list[str]) -> str:
    return "| " + " | ".join(cell.strip() for cell in cells) + " |"


def set_cell(path: Path, key: str, column: int, value: str, *, anchor: str = "") -> None:
    """Replace one cell of the table row keyed by its first column.

    Args:
        path: The document to edit.
        key: The value of the row's first cell, cleaned.
        column: Zero-based column index to replace.
        value: The replacement cell text, written verbatim.
        anchor: A heading line the row must appear after, disambiguating tables that share a key.

    Raises:
        FixtureError: If the row or the column does not exist.
    """
    lines = _lines(path)
    number = _row_index(lines, key, anchor)
    cells = [cell.strip() for cell in split_row(lines[number])]
    if column >= len(cells):
        raise FixtureError(f"row {key!r} has {len(cells)} columns; cannot set column {column}")
    cells[column] = value
    lines[number] = _render_row(cells)
    _write(path, lines)


def duplicate_row(path: Path, key: str, changes: dict[int, str], *, anchor: str = "") -> None:
    """Insert a copy of one table row, with some cells replaced.

    Args:
        path: The document to edit.
        key: The value of the row's first cell, cleaned.
        changes: Zero-based column index to replacement text.
        anchor: A heading line the row must appear after.

    Raises:
        FixtureError: If the row does not exist.
    """
    lines = _lines(path)
    number = _row_index(lines, key, anchor)
    cells = [cell.strip() for cell in split_row(lines[number])]
    for column, value in changes.items():
        if column < len(cells):
            cells[column] = value
    lines.insert(number + 1, _render_row(cells))
    _write(path, lines)


def delete_row(path: Path, key: str, *, anchor: str = "") -> None:
    """Delete one table row.

    Args:
        path: The document to edit.
        key: The value of the row's first cell, cleaned.
        anchor: A heading line the row must appear after.

    Raises:
        FixtureError: If the row does not exist.
    """
    lines = _lines(path)
    del lines[_row_index(lines, key, anchor)]
    _write(path, lines)


def replace_text(path: Path, old: str, new: str) -> None:
    """Replace the first occurrence of a literal string.

    Args:
        path: The document to edit.
        old: The literal to find.
        new: The replacement.

    Raises:
        FixtureError: If the literal is absent, which means the fixture no longer targets anything.
    """
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise FixtureError(f"{path.name} no longer contains {old!r}; the fixture targets nothing")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


# --- The fixtures --------------------------------------------------------------------------------


def _illegal_status(workspace: Workspace) -> None:
    set_cell(workspace.index_path, SUBJECT_KEY, _STATUS_COLUMN, "`nearly`", anchor=ENTRY_ANCHOR)


def _incomplete_procedure(workspace: Workspace) -> None:
    set_cell(workspace.index_path, SUBJECT_KEY, _RUNBOOK_COLUMN, "`README.md`", anchor=ENTRY_ANCHOR)
    set_cell(workspace.index_path, SUBJECT_KEY, _STATUS_COLUMN, "`incomplete`", anchor=ENTRY_ANCHOR)


def _status_disagrees(workspace: Workspace) -> None:
    set_cell(workspace.index_path, SUBJECT_KEY, _STATUS_COLUMN, "`complete`", anchor=ENTRY_ANCHOR)


def _mismatched_manual_literal(workspace: Workspace) -> None:
    set_cell(workspace.index_path, SUBJECT_KEY, _AUTOMATION_COLUMN, "none — by decision", anchor=ENTRY_ANCHOR)


def _missing_manual_verification(workspace: Workspace) -> None:
    set_cell(workspace.index_path, "PROC-POWER-DRILL", _VERIFICATION_COLUMN, "", anchor=MANUAL_ANCHOR)


def _unwritten_human_form(workspace: Workspace) -> None:
    set_cell(workspace.index_path, "PROC-POWER-DRILL", _HUMAN_FORM_COLUMN, "Yes", anchor=MANUAL_ANCHOR)


def _duplicate_key(workspace: Workspace) -> None:
    duplicate_row(workspace.index_path, SUBJECT_KEY, {}, anchor=ENTRY_ANCHOR)


def _duplicate_runbook_path(workspace: Workspace) -> None:
    duplicate_row(
        workspace.index_path,
        SUBJECT_KEY,
        {0: "`PROC-REPO-SECRETS-TWIN`"},
        anchor=ENTRY_ANCHOR,
    )


def _unregistered_alert_source(workspace: Workspace) -> None:
    replace_text(workspace.index_path, "| 1.3 | 13.5 |", "| 99.9 | 13.5 |")


def _retired_key_reused(workspace: Workspace) -> None:
    replace_text(workspace.index_path, "**Retired keys:** none yet.", f"**Retired keys:** `{SUBJECT_KEY}`.")


def _story_with_no_entry(workspace: Workspace) -> None:
    delete_row(workspace.index_path, SUBJECT_KEY, anchor=ENTRY_ANCHOR)


def _entry_with_no_story(workspace: Workspace) -> None:
    set_cell(workspace.index_path, SUBJECT_KEY, _STORY_COLUMN, "99.9", anchor=ENTRY_ANCHOR)


def _story_over_allowance(workspace: Workspace) -> None:
    duplicate_row(
        workspace.index_path,
        SUBJECT_KEY,
        {
            0: "`PROC-REPO-SECRETS-EXTRA`",
            4: "`runbooks/l0-physical/repo-secrets-extra.md`",
        },
        anchor=ENTRY_ANCHOR,
    )


def _stale_provenance(workspace: Workspace) -> None:
    index = load_index(workspace.index_path)
    if index.provenance_commit is None:
        raise FixtureError("no provenance line to make stale")
    replace_text(workspace.index_path, f"`{index.provenance_commit}`", "`0000000`")


def _broken_back_reference(workspace: Workspace) -> None:
    target = workspace.runbooks_dir / "l0-physical" / "repo-secrets.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "---\nprocedure_key: PROC-REPO-SECRETS\nprocedure_automation: ansible/l0-physical/wrong.yml\n---\n",
        encoding="utf-8",
    )


def _template_sentinel(workspace: Workspace) -> None:
    target = workspace.runbooks_dir / "l0-physical" / "copied-from-template.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(workspace.template_path, target)


def _runbook_missing_section(workspace: Workspace) -> None:
    runbooks = [path for path in workspace.runbook_files() if path.name != "TEMPLATE.md"]
    if not runbooks:
        raise FixtureError("no Runbook exists to remove a section from")
    replace_text(runbooks[0], "\n## Rollback\n", "\n")


# Both totals fixtures address the row STRUCTURALLY, by its label, rather than by matching a
# literal line containing today's count. A fixture that matches a number stops targeting anything
# the moment the number legitimately changes — and a fixture that targets nothing is a self-check
# that proves nothing, which is the failure mode this module is entirely about.
def _totals_disagree(workspace: Workspace) -> None:
    set_cell(workspace.index_path, "Entries in this Index", 1, "999")


def _unrecomputed_total(workspace: Workspace) -> None:
    duplicate_row(workspace.index_path, "Entries in this Index", {0: "Bananas"})


def _upward_layer_dependency(workspace: Workspace) -> None:
    target = workspace.root / "ansible" / "l0-physical" / "upward.yml"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# reads ansible/l2-foundation/time-authority.yml\n", encoding="utf-8")


def _two_owner_class(workspace: Workspace) -> None:
    duplicate_row(workspace.ownership_path, "DNS zones and records (asgard.home.arpa)", {_OWNER_COLUMN: "`OpenTofu`"})


def _illegal_owner_value(workspace: Workspace) -> None:
    set_cell(workspace.ownership_path, "This ownership table", _OWNER_COLUMN, "whoever gets there first")


def _missing_ownership_verification(workspace: Workspace) -> None:
    set_cell(workspace.ownership_path, "This ownership table", _OWNERSHIP_VERIFICATION_COLUMN, "")


def _uncovered_ownership_class(workspace: Workspace) -> None:
    set_cell(workspace.ownership_path, "This ownership table", _OWNERSHIP_PROCEDURE_COLUMN, "`PROC-DOES-NOT-EXIST`")


FIXTURES: tuple[Fixture, ...] = (
    Fixture("an entry's status is outside the closed set", defects.ILLEGAL_STATUS_VALUE, _illegal_status),
    Fixture("an entry has exactly one half on disk", defects.INCOMPLETE_PROCEDURE, _incomplete_procedure),
    Fixture("an entry claims complete with neither half", defects.STATUS_DISAGREES_WITH_FILESYSTEM, _status_disagrees),
    Fixture(
        "an entry carries the manual literal without the status",
        defects.MISMATCHED_MANUAL_LITERAL,
        _mismatched_manual_literal,
    ),
    Fixture("a manual entry names no verification", defects.MISSING_MANUAL_VERIFICATION, _missing_manual_verification),
    Fixture(
        "a manual entry claims a human form that is absent",
        defects.UNWRITTEN_MANUAL_HUMAN_FORM,
        _unwritten_human_form,
    ),
    Fixture("two entries share a key", defects.DUPLICATE_KEY, _duplicate_key),
    Fixture("two entries claim the same Runbook path", defects.DUPLICATE_RUNBOOK_PATH, _duplicate_runbook_path),
    Fixture(
        "an alert source names a story that does not exist",
        defects.UNREGISTERED_ALERT_SOURCE,
        _unregistered_alert_source,
    ),
    Fixture("an entry reuses a retired key", defects.RETIRED_KEY_REUSED, _retired_key_reused),
    Fixture("a story loses its only entry", defects.STORY_WITH_NO_ENTRY, _story_with_no_entry),
    Fixture("an entry names a story that does not exist", defects.ENTRY_WITH_NO_STORY, _entry_with_no_story),
    Fixture("a story gains a second, unexcepted entry", defects.STORY_OVER_ENTRY_ALLOWANCE, _story_over_allowance),
    Fixture(
        "the recorded story-list commit goes stale",
        defects.STALE_PROVENANCE,
        _stale_provenance,
        requires_git=True,
    ),
    Fixture("a Runbook names the wrong Automation", defects.BROKEN_BACK_REFERENCE, _broken_back_reference),
    Fixture("a copied template keeps its sentinel", defects.UNFILLED_TEMPLATE_SENTINEL, _template_sentinel),
    Fixture("a Runbook loses a required section", defects.RUNBOOK_MISSING_SECTION, _runbook_missing_section),
    Fixture("a Totals figure is hand-edited", defects.TOTALS_DISAGREE, _totals_disagree),
    Fixture("Totals states a figure nothing recomputes", defects.UNRECOMPUTED_TOTAL, _unrecomputed_total),
    Fixture("a low layer references a higher one", defects.UPWARD_LAYER_DEPENDENCY, _upward_layer_dependency),
    Fixture("a resource class gains a second owner", defects.TWO_OWNER_CLASS, _two_owner_class),
    Fixture("an Owner cell is a sentence", defects.ILLEGAL_OWNER_VALUE, _illegal_owner_value),
    Fixture(
        "a resource class names no verification",
        defects.MISSING_OWNERSHIP_VERIFICATION,
        _missing_ownership_verification,
    ),
    Fixture("a resource class names no real Procedure", defects.UNCOVERED_OWNERSHIP_CLASS, _uncovered_ownership_class),
)


# --- Running the self-check ----------------------------------------------------------------------


def copy_workspace(source: Workspace, destination: Path) -> Workspace:
    """Copy the parts of a workspace a fixture can reach.

    Args:
        source: The workspace to copy from.
        destination: An existing empty directory to copy into.

    Returns:
        A workspace rooted at the copy.
    """
    for relative in COPIED_PATHS:
        origin = source.root / relative
        target = destination / relative
        if origin.is_dir():
            shutil.copytree(origin, target, ignore=_COPY_IGNORE)
        elif origin.is_file():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin, target)
    return Workspace(root=destination)


def run_fixture(source: Workspace, fixture: Fixture, commit: str | None) -> FixtureOutcome:
    """Inject one fixture into a throwaway copy and audit it.

    Args:
        source: The real workspace to copy.
        fixture: The known-bad state to inject.
        commit: The commit the provenance check should believe `epics.md` sits at.

    Returns:
        What the audit did with the fixture in place.
    """
    with tempfile.TemporaryDirectory(prefix="asgard-selfcheck-") as directory:
        copy = copy_workspace(source, Path(directory) / "repo")
        try:
            fixture.apply(copy)
        except (FixtureError, OSError) as error:
            return FixtureOutcome(fixture=fixture, exit_code=0, subjects=(), error=str(error))
        report = run_audit(copy, resolve_commit=lambda _ws: commit)
        subjects = tuple(finding.subject for finding in report.findings if finding.defect == fixture.defect)
        return FixtureOutcome(fixture=fixture, exit_code=report.exit_code, subjects=subjects)


def _baseline_result(source: Workspace, commit: str | None) -> tuple[CheckResult, bool]:
    with tempfile.TemporaryDirectory(prefix="asgard-selfcheck-") as directory:
        copy = copy_workspace(source, Path(directory) / "repo")
        report = run_audit(copy, resolve_commit=lambda _ws: commit)
    if report.exit_code == 0:
        return (
            result("Self-check baseline", defects.SELF_CHECK_DID_NOT_FIRE, 1, "unmutated copies", []),
            True,
        )
    findings = [
        Finding(
            defect=defects.SELF_CHECK_DID_NOT_FIRE,
            subject="unmutated copy of the repository",
            detail=(
                "the baseline audit already fails, so no fixture can prove anything: "
                f"{[f.render() for f in report.findings]}"
            ),
            location="self-check",
        )
    ]
    return (
        result("Self-check baseline", defects.SELF_CHECK_DID_NOT_FIRE, 1, "unmutated copies", findings),
        False,
    )


@dataclass(frozen=True, slots=True)
class RunnerFixture:
    """A convergence-logic fixture: a scripted set of runs, and whether the check must fire.

    These need no filesystem. They exist because the convergence decision logic is the part of the
    harness with no real Automation to exercise it yet, and the part that already shipped the
    defect this whole module is about — a failed tool run being read as a clean one.

    Attributes:
        name: What the fixture represents.
        runs: The results the runner returns, in order.
        must_fire: Whether the check is required to report a defect.
        expect_defect: The defect class that must be named, when one must be.
    """

    name: str
    runs: tuple[RunResult, ...]
    must_fire: bool
    expect_defect: str = ""


def _scripted(runs: tuple[RunResult, ...]) -> Runner:
    stream = iter(runs)
    # A runner asked for more runs than the fixture scripted is a bug in the fixture, not a clean
    # run: return an errored result rather than a default RunResult, which would read as "no
    # changes" and quietly re-create the defect these fixtures exist to catch.
    return lambda: next(stream, RunResult(error="fixture exhausted: the check ran more times than scripted"))


CONVERGENCE_FIXTURES: tuple[RunnerFixture, ...] = (
    RunnerFixture(
        "a converged, idempotent Automation is accepted",
        (RunResult(), RunResult()),
        must_fire=False,
    ),
    RunnerFixture(
        "a first run with changes is not converged",
        (RunResult(changed=("node-a",)), RunResult()),
        must_fire=True,
        expect_defect=defects.AUTOMATION_NOT_CONVERGED,
    ),
    RunnerFixture(
        "a second run with changes is not idempotent",
        (RunResult(), RunResult(changed=("node-a",))),
        must_fire=True,
        expect_defect=defects.AUTOMATION_NOT_IDEMPOTENT,
    ),
    RunnerFixture(
        "an errored ansible check-mode run is a failure, not a clean run",
        (parse_ansible_check(2, "fatal: [node-a]: UNREACHABLE!", "ansible-playbook --check x.yml"),),
        must_fire=True,
        expect_defect=defects.AUTOMATION_CHECK_FAILED,
    ),
    RunnerFixture(
        "an errored tofu plan is a failure, not a clean run",
        (parse_tofu_plan(1, "Error: Backend initialization required", "tofu plan -detailed-exitcode"),),
        must_fire=True,
        expect_defect=defects.AUTOMATION_CHECK_FAILED,
    ),
    RunnerFixture(
        "an errored kubectl diff is a failure, not a clean run",
        (parse_kubectl_diff(2, "The connection to the server was refused", "kubectl diff -k k8s/x"),),
        must_fire=True,
        expect_defect=defects.AUTOMATION_CHECK_FAILED,
    ),
    RunnerFixture(
        "a tool that could not be started is a failure, not a clean run",
        (parse_tofu_plan(LAUNCH_FAILURE_EXIT_CODE, "could not run tofu: No such file", "tofu plan"),),
        must_fire=True,
        expect_defect=defects.AUTOMATION_CHECK_FAILED,
    ),
)
"""Every outcome of the convergence decision logic: clean, changed on either run, and errored.

The errored cases are the ones that matter. Each is built by the real parser from the real exit
code its tool documents, so a parser that stopped distinguishing failure from cleanliness would
turn these red rather than going unnoticed.
"""


def _drift_runner_fixtures() -> list[CheckResult]:
    """Prove the drift detector fires on a non-empty diff and on a failed run.

    Returns:
        One check result per fixture.
    """
    cases = (
        ("drift accepts a genuinely empty check-mode diff", RunResult(), False),
        ("drift rejects a non-empty check-mode diff", RunResult(changed=("host-a", "host-b")), True),
        (
            "drift rejects an errored check-mode run rather than reading it as empty",
            parse_kubectl_diff(2, "The connection to the server was refused", "kubectl diff -k k8s/x"),
            True,
        ),
    )
    results: list[CheckResult] = []
    for name, run, must_fire in cases:
        observed = check_drift(name, _scripted((run,)))
        results.append(_expect(observed.findings, fires=must_fire, name=name, defect=""))
    return results


def _runner_fixtures() -> list[CheckResult]:
    """Prove the convergence and drift decision logic fires exactly when it should.

    Returns:
        One check result per runner fixture.
    """
    results: list[CheckResult] = []
    for fixture in CONVERGENCE_FIXTURES:
        findings = check_convergence_and_idempotence(fixture.name, _scripted(fixture.runs))
        results.append(_expect(findings, fires=fixture.must_fire, name=fixture.name, defect=fixture.expect_defect))
    results.extend(_drift_runner_fixtures())

    # An Automation whose mechanism the harness cannot drive must be reported by name, never
    # skipped past while the surrounding count still claims it was examined.
    undrivable = AutomationTarget(key="PROC-FIXTURE", layer="l0-physical", path="weird/thing", mechanism="unknown")
    findings, ran = run_targets([undrivable], lambda _target: None, check_convergence_and_idempotence)
    results.append(
        _expect(
            findings,
            fires=True,
            name="an Automation with no known check mode is named, not silently skipped",
            defect=defects.AUTOMATION_NO_CHECK_MODE,
        )
    )
    results.append(
        _expect(
            [] if ran == 0 else [Finding(defect=defects.SELF_CHECK_DID_NOT_FIRE, subject="run_targets", detail="x")],
            fires=False,
            name="an Automation with no known check mode is not counted as run",
            defect="",
        )
    )
    return results


def _expect(findings: Sequence[Finding], *, fires: bool, name: str, defect: str) -> CheckResult:
    """Assert a decision fired, or did not, and that it named the right defect class.

    Args:
        findings: What the decision logic produced.
        fires: Whether it was required to produce anything.
        name: The fixture's name, for reporting.
        defect: The defect class that must appear, when one must.

    Returns:
        A passing result when the observation matches the requirement, else a failing one naming
        the mismatch.
    """
    fired = bool(findings)
    named = {finding.defect for finding in findings}
    if fired == fires and (not fires or not defect or defect in named):
        return result(name, defects.SELF_CHECK_DID_NOT_FIRE, 1, "fixtures", [])
    if fired != fires:
        detail = (
            "did not fire on a known-bad fixture; a check that cannot fail is the defect this module exists to prevent"
            if fires
            else f"fired on a known-good fixture, naming {sorted(named)}"
        )
    else:
        detail = f"fired but named {sorted(named)} rather than the required {defect!r}"
    return result(
        name,
        defects.SELF_CHECK_DID_NOT_FIRE,
        1,
        "fixtures",
        [Finding(defect=defects.SELF_CHECK_DID_NOT_FIRE, subject=name, detail=detail, location="self-check")],
    )


def run_self_check(workspace: Workspace) -> AuditReport:
    """Prove every detector fails on a known-bad fixture, then leave nothing behind.

    Args:
        workspace: The real repository, copied per fixture and never mutated.

    Returns:
        A report in which a passing fixture — one that failed to provoke its defect — is itself a
        finding.
    """
    # NO fallback to the Index's own recorded hash. Handing the provenance detector the value the
    # document under test supplied makes the fixture self-referential: it would compare the
    # document against itself and report PASS while exercising no git at all. When git cannot
    # answer, the fixture that depends on it SKIPs and says so.
    commit = workspace.git_commit_for(workspace.epics_path)
    baseline, usable = _baseline_result(workspace, commit)
    results: list[CheckResult] = [baseline]
    if not usable:
        return report_of(results)
    for fixture in FIXTURES:
        if fixture.requires_git and commit is None:
            results.append(
                skipped(
                    f"Fixture — {fixture.name}",
                    fixture.defect,
                    "injected fixtures",
                    f"git could not name the commit that last touched "
                    f"{workspace.relative(workspace.epics_path)}, so there is nothing for the detector to "
                    "compare the Index against; this fixture proves nothing here and is NOT reported as a pass",
                )
            )
            continue
        outcome = run_fixture(workspace, fixture, commit)
        if outcome.fired:
            results.append(
                result(
                    f"Fixture — {fixture.name}",
                    fixture.defect,
                    1,
                    "injected fixtures",
                    [],
                    note=f"named {outcome.subjects[0]}",
                )
            )
            continue
        detail = (
            outcome.error
            or f"audit exited {outcome.exit_code} and named no {fixture.defect}; a passing self-check is a failure"
        )
        results.append(
            result(
                f"Fixture — {fixture.name}",
                defects.SELF_CHECK_DID_NOT_FIRE,
                1,
                "injected fixtures",
                [
                    Finding(
                        defect=defects.SELF_CHECK_DID_NOT_FIRE,
                        subject=fixture.defect,
                        detail=detail,
                        location="self-check",
                    )
                ],
            )
        )
    results.extend(_runner_fixtures())
    return report_of(results)
