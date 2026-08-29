"""Detectors for the defect classes `docs/OWNERSHIP.md` § Audit defines.

Four rules are named there. Three are implemented here — two-owner, illegal Owner value, and
uncovered class — plus the verification-present check the Exemptions paragraph requires. The
fourth, the incomplete-Procedure defect, is defined in the Index and implemented in
`checks_index`, exactly as that section says.

The **unowned defect** — "a configurable resource class present in the platform and absent from
this table" — is not implemented, and deliberately not approximated. Deciding it requires an
independent enumeration of the platform's resource classes, which by construction does not exist:
this table *is* that enumeration. `unowned_defect_status` reports the gap by name rather than
letting a check that cannot see the defect report a pass.
"""

from __future__ import annotations

from collections import defaultdict

from asgard_harness import defects
from asgard_harness.findings import CheckResult, Finding, result, skipped
from asgard_harness.index_document import ProcedureIndex
from asgard_harness.ownership_document import OwnershipTable


def _at(table: OwnershipTable, line: int) -> str:
    return f"{table.path.name}:{line}"


def check_owner_enumeration(ownership: OwnershipTable) -> CheckResult:
    """Illegal Owner value: an Owner cell outside the document's own closed enumeration.

    Args:
        ownership: The parsed ownership table.

    Returns:
        The check result.
    """
    if not ownership.legal_owners:
        return skipped(
            "Owner enumeration",
            defects.ILLEGAL_OWNER_VALUE,
            "rows",
            "the table states no 'Legal Owner values' enumeration, so no Owner can be judged legal",
        )
    findings = [
        Finding(
            defect=defects.ILLEGAL_OWNER_VALUE,
            subject=row.resource_class,
            detail=f"Owner {row.owner!r} is outside the closed set {sorted(ownership.legal_owners)}",
            location=_at(ownership, row.line),
        )
        for row in ownership.rows
        if row.owner not in ownership.legal_owners
    ]
    return result("Owner enumeration", defects.ILLEGAL_OWNER_VALUE, len(ownership.rows), "rows", findings)


def check_one_owner(ownership: OwnershipTable) -> CheckResult:
    """Two-owner defect: a resource class reachable from two Owner rows.

    `Delegated` rows are exempt, and that is the only exemption the document allows. The audit does
    not pick a winner; resolution is a human decision recorded as a change to the table.

    Args:
        ownership: The parsed ownership table.

    Returns:
        The check result.
    """
    grouped: defaultdict[str, list[tuple[str, str, int]]] = defaultdict(list)
    examined = 0
    for row in ownership.rows:
        if row.is_delegated:
            continue
        examined += 1
        grouped[row.normalised_class].append((row.resource_class, row.owner, row.line))
    findings: list[Finding] = []
    for occurrences in grouped.values():
        owners = {owner for _, owner, _ in occurrences}
        if len(owners) > 1:
            name = occurrences[0][0]
            lines = [line for _, _, line in occurrences]
            findings.append(
                Finding(
                    defect=defects.TWO_OWNER_CLASS,
                    subject=name,
                    detail=f"declared by {sorted(owners)} at lines {lines}; the audit does not pick a winner",
                    location=_at(ownership, lines[0]),
                )
            )
    return result(
        "One declaring owner per class",
        defects.TWO_OWNER_CLASS,
        examined,
        "non-delegated rows",
        findings,
        note=f"{len(ownership.rows) - examined} Delegated row(s) exempt",
    )


def check_verification_present(ownership: OwnershipTable) -> CheckResult:
    """Every class carries a verification, including the classes no automation executes.

    The Exemptions paragraph states this check applies to `Delegated` rows too, so nothing here is
    skipped.

    Args:
        ownership: The parsed ownership table.

    Returns:
        The check result.
    """
    findings = [
        Finding(
            defect=defects.MISSING_OWNERSHIP_VERIFICATION,
            subject=row.resource_class,
            detail="the Verification cell is empty; execution may be manual, verification may not be absent",
            location=_at(ownership, row.line),
        )
        for row in ownership.rows
        if not row.verification.strip()
    ]
    return result(
        "Verification named per class",
        defects.MISSING_OWNERSHIP_VERIFICATION,
        len(ownership.rows),
        "rows",
        findings,
    )


def check_procedure_coverage(ownership: OwnershipTable, index: ProcedureIndex) -> CheckResult:
    """Uncovered-class defect: a row whose Procedure column names no Index key, or a missing one.

    The rule runs class to Procedure and not the reverse: a Procedure with no row here is not a
    defect. `Delegated` is the single exception and resolves transitively.

    Args:
        ownership: The parsed ownership table.
        index: The parsed Index, supplying the set of real keys.

    Returns:
        The check result.
    """
    if not index.entries:
        return skipped(
            "Ownership class coverage",
            defects.UNCOVERED_OWNERSHIP_CLASS,
            "rows",
            "the Index yielded no entries, so no Procedure key can be resolved",
        )
    known = index.keys
    findings: list[Finding] = []
    examined = 0
    for row in ownership.rows:
        if row.is_delegated:
            continue
        examined += 1
        if not row.procedures:
            findings.append(
                Finding(
                    defect=defects.UNCOVERED_OWNERSHIP_CLASS,
                    subject=row.resource_class,
                    detail=f"Procedure cell {row.procedure_cell!r} names no Index key; zero is not permitted",
                    location=_at(ownership, row.line),
                )
            )
            continue
        missing = [key for key in row.procedures if key not in known]
        if missing:
            findings.append(
                Finding(
                    defect=defects.UNCOVERED_OWNERSHIP_CLASS,
                    subject=row.resource_class,
                    detail=f"names {missing}, which do not exist in {index.path.name}",
                    location=_at(ownership, row.line),
                )
            )
    return result(
        "Ownership class coverage",
        defects.UNCOVERED_OWNERSHIP_CLASS,
        examined,
        "non-delegated rows",
        findings,
    )


def unowned_defect_status(ownership: OwnershipTable) -> CheckResult:
    """Report the unowned defect as unimplementable rather than as passing.

    Args:
        ownership: The parsed ownership table.

    Returns:
        A skipped check result naming why the class cannot be detected as defined.
    """
    return skipped(
        "Unowned resource class",
        "unowned-resource-class",
        "rows",
        f"not mechanically decidable: deciding it needs an enumeration of the platform's resource classes "
        f"independent of this table, and this table — {len(ownership.rows)} rows — is the only such "
        "enumeration. Reported, not narrowed",
    )
