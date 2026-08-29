"""The harness's report vocabulary: findings, check results, and the audit report.

Two rules from the story are enforced structurally here rather than left to reviewer discipline:

- **A finding always names its subject.** `Finding` refuses to be constructed without one, so
  "audit failed" cannot be a result.
- **A check always reports what it examined.** `CheckResult` carries a count and a noun, and a
  check that could not run reports `SKIPPED` with a reason rather than passing silently.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum


class CheckStatus(StrEnum):
    """Outcome of a single check."""

    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class Finding:
    """One detected defect.

    Attributes:
        defect: The defect-class identifier from `asgard_harness.defects`.
        subject: The offending key, path, or row. Never empty.
        detail: What is wrong with that subject, in one sentence.
        location: Optional `path:line` pointer to where the subject is declared.
    """

    defect: str
    subject: str
    detail: str
    location: str = ""

    def __post_init__(self) -> None:
        """Reject a finding that names nothing.

        Raises:
            ValueError: If `defect`, `subject`, or `detail` is blank.
        """
        for name in ("defect", "subject", "detail"):
            if not getattr(self, name).strip():
                raise ValueError(f"Finding.{name} must be non-empty: a finding that names nothing cannot be acted on")

    def render(self) -> str:
        """Render the finding as a single human-readable line.

        Returns:
            The rendered line, always naming the subject.
        """
        where = f" ({self.location})" if self.location else ""
        return f"{self.defect}: {self.subject}{where} — {self.detail}"


@dataclass(frozen=True, slots=True)
class CheckResult:
    """The outcome of one detector.

    Attributes:
        name: Human-readable name of the check.
        defect: The defect class this check detects.
        examined: How many subjects the check looked at.
        noun: What those subjects are, plural (`"entries"`, `"rows"`, `"files"`).
        findings: Every defect found. Empty means the check passed.
        note: Why the check was skipped, or anything the reader needs to interpret the count.
        skipped: Whether the check could not run at all.
    """

    name: str
    defect: str
    examined: int
    noun: str
    findings: tuple[Finding, ...] = ()
    note: str = ""
    skipped: bool = False

    @property
    def status(self) -> CheckStatus:
        """The check's outcome.

        Returns:
            `SKIPPED` if the check could not run, `FAILED` if it found anything, else `PASSED`.
        """
        if self.skipped:
            return CheckStatus.SKIPPED
        return CheckStatus.FAILED if self.findings else CheckStatus.PASSED

    def render(self) -> list[str]:
        """Render the result as report lines.

        Returns:
            One summary line, followed by one line per finding.
        """
        marker = {CheckStatus.PASSED: "PASS", CheckStatus.FAILED: "FAIL", CheckStatus.SKIPPED: "SKIP"}[self.status]
        suffix = f" — {self.note}" if self.note else ""
        head = f"[{marker}] {self.name}: {self.examined} {self.noun} examined{suffix}"
        return [head, *(f"         {finding.render()}" for finding in self.findings)]


def passed(name: str, defect: str, examined: int, noun: str, note: str = "") -> CheckResult:
    """Build a passing result.

    Args:
        name: Human-readable name of the check.
        defect: The defect class this check detects.
        examined: How many subjects the check looked at.
        noun: What those subjects are, plural.
        note: Anything the reader needs to interpret the count.

    Returns:
        A `CheckResult` with no findings.
    """
    return CheckResult(name=name, defect=defect, examined=examined, noun=noun, note=note)


def result(
    name: str,
    defect: str,
    examined: int,
    noun: str,
    findings: Iterable[Finding],
    note: str = "",
) -> CheckResult:
    """Build a result from whatever the detector found.

    Args:
        name: Human-readable name of the check.
        defect: The defect class this check detects.
        examined: How many subjects the check looked at.
        noun: What those subjects are, plural.
        findings: The defects found; an empty iterable means the check passed.
        note: Anything the reader needs to interpret the count.

    Returns:
        A `CheckResult` carrying the findings.
    """
    return CheckResult(name=name, defect=defect, examined=examined, noun=noun, findings=tuple(findings), note=note)


def skipped(name: str, defect: str, noun: str, reason: str) -> CheckResult:
    """Build a skipped result.

    A skipped check is reported as skipped and never as a pass: the repository's own convergence
    tooling row requires each guarded step to say whether it ran.

    Args:
        name: Human-readable name of the check.
        defect: The defect class this check would have detected.
        noun: What the check would have examined, plural.
        reason: Why it could not run.

    Returns:
        A `CheckResult` marked skipped.
    """
    return CheckResult(name=name, defect=defect, examined=0, noun=noun, note=reason, skipped=True)


@dataclass(frozen=True, slots=True)
class AuditReport:
    """Every check the harness ran, and the exit code that follows from them."""

    results: tuple[CheckResult, ...] = field(default=())

    @property
    def findings(self) -> tuple[Finding, ...]:
        """Every finding across every check.

        Returns:
            All findings, in check order.
        """
        return tuple(finding for check in self.results for finding in check.findings)

    @property
    def failed(self) -> tuple[CheckResult, ...]:
        """The checks that found something.

        Returns:
            Failing check results, in order.
        """
        return tuple(check for check in self.results if check.status is CheckStatus.FAILED)

    @property
    def exit_code(self) -> int:
        """The process exit code.

        Returns:
            `1` if any check failed, else `0`.
        """
        return 1 if self.failed else 0

    def render(self) -> str:
        """Render the whole report.

        Reports what was checked, not merely that it passed — the counts are the point.

        Returns:
            The rendered report.
        """
        lines: list[str] = []
        for check in self.results:
            lines.extend(check.render())
        counts = {status: sum(1 for c in self.results if c.status is status) for status in CheckStatus}
        lines.append("")
        lines.append(
            f"{len(self.results)} checks run: "
            f"{counts[CheckStatus.PASSED]} passed, "
            f"{counts[CheckStatus.FAILED]} failed, "
            f"{counts[CheckStatus.SKIPPED]} skipped; "
            f"{len(self.findings)} defect(s) named."
        )
        return "\n".join(lines)

    def as_dict(self) -> dict[str, object]:
        """Render the report as plain data for machine consumption.

        Returns:
            A JSON-serialisable mapping.
        """
        return {
            "exit_code": self.exit_code,
            "checks": [
                {
                    "name": check.name,
                    "defect": check.defect,
                    "status": check.status.value,
                    "examined": check.examined,
                    "noun": check.noun,
                    "note": check.note,
                    "findings": [
                        {
                            "defect": f.defect,
                            "subject": f.subject,
                            "detail": f.detail,
                            "location": f.location,
                        }
                        for f in check.findings
                    ],
                }
                for check in self.results
            ],
        }


def report_of(results: Sequence[CheckResult]) -> AuditReport:
    """Assemble an audit report.

    Args:
        results: The check results, in the order they should be reported.

    Returns:
        The assembled report.
    """
    return AuditReport(results=tuple(results))
