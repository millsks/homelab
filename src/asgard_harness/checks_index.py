"""Detectors for the defect classes `PROCEDURE-INDEX.md` defines.

Each function here implements exactly one class from § "Defects this Index reports", in the order
that section lists them. Where the Index's wording could be satisfied by more than one reading, the
docstring records which reading was implemented and why, because narrowing a definition silently is
the failure this story exists to prevent.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable

from asgard_harness import defects
from asgard_harness.epics import Story
from asgard_harness.findings import CheckResult, Finding, result, skipped
from asgard_harness.index_document import ProcedureIndex
from asgard_harness.workspace import Workspace


def _at(index: ProcedureIndex, line: int) -> str:
    return f"{index.path.name}:{line}"


def check_status_enumeration(index: ProcedureIndex) -> CheckResult:
    """Illegal status value: a Status cell outside the Index's closed set.

    The closed set is read from the Index's own status table, so the enumeration has one home.

    Args:
        index: The parsed Index.

    Returns:
        The check result.
    """
    if not index.legal_statuses:
        return skipped(
            "Status enumeration",
            defects.ILLEGAL_STATUS_VALUE,
            "entries",
            "the Index states no closed status enumeration, so no status can be judged legal",
        )
    findings = [
        Finding(
            defect=defects.ILLEGAL_STATUS_VALUE,
            subject=entry.key,
            detail=f"status {entry.status!r} is outside the closed set {sorted(index.legal_statuses)}",
            location=_at(index, entry.line),
        )
        for entry in index.entries
        if entry.status not in index.legal_statuses
    ]
    return result("Status enumeration", defects.ILLEGAL_STATUS_VALUE, len(index.entries), "entries", findings)


def check_incomplete_procedure(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Incomplete Procedure: exactly one half present where both are required.

    Entries carrying the manual literal require no Automation half and are excluded, per the first
    exemption in the dual-form contract.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    examined = 0
    for entry in index.entries:
        if entry.is_manual_literal:
            continue
        examined += 1
        runbook = workspace.declared_exists(entry.runbook)
        automation = workspace.declared_exists(entry.automation)
        if runbook == automation:
            continue
        missing = "Automation" if runbook else "Runbook"
        present = entry.runbook if runbook else entry.automation
        absent = entry.automation if runbook else entry.runbook
        findings.append(
            Finding(
                defect=defects.INCOMPLETE_PROCEDURE,
                subject=entry.key,
                detail=f"{present!r} exists but the {missing} half {absent!r} does not",
                location=_at(index, entry.line),
            )
        )
    return result(
        "Incomplete Procedure",
        defects.INCOMPLETE_PROCEDURE,
        examined,
        "entries requiring both halves",
        findings,
    )


def check_status_matches_filesystem(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Status disagrees with the filesystem.

    `manual-by-decision` is excluded: the Index states it is assigned from the architecture and is
    not a reading of the filesystem. The other three statuses are derived from what is present.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    examined = 0
    for entry in index.entries:
        if entry.status == "manual-by-decision" or entry.status not in index.legal_statuses:
            continue
        examined += 1
        halves: list[tuple[str, str, bool]] = [("Runbook", entry.runbook, workspace.declared_exists(entry.runbook))]
        if not entry.is_manual_literal:
            halves.append(("Automation", entry.automation, workspace.declared_exists(entry.automation)))
        present = [name for name, _, exists in halves if exists]
        absent = [(name, path) for name, path, exists in halves if not exists]
        expected: dict[str, int] = {"complete": len(halves), "incomplete": 1, "planned": 0}
        wanted = expected.get(entry.status)
        if wanted is None or len(present) == wanted:
            continue
        detail = (
            f"status {entry.status!r} expects {wanted} half/halves on disk but {len(present)} present"
            f" (present: {present or 'none'}; absent: {[path for _, path in absent] or 'none'})"
        )
        findings.append(
            Finding(
                defect=defects.STATUS_DISAGREES_WITH_FILESYSTEM,
                subject=entry.key,
                detail=detail,
                location=_at(index, entry.line),
            )
        )
    return result(
        "Status against filesystem",
        defects.STATUS_DISAGREES_WITH_FILESYSTEM,
        examined,
        "filesystem-derived entries",
        findings,
    )


def check_manual_literal(index: ProcedureIndex) -> CheckResult:
    """Mismatched manual literal: the literal and the status are one fact recorded twice.

    Args:
        index: The parsed Index.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    for entry in index.entries:
        manual_status = entry.status == "manual-by-decision"
        if entry.is_manual_literal == manual_status:
            continue
        detail = (
            f"Automation cell is the manual literal but status is {entry.status!r}"
            if entry.is_manual_literal
            else f"status is 'manual-by-decision' but the Automation cell is {entry.automation!r}, not the literal"
        )
        findings.append(
            Finding(
                defect=defects.MISMATCHED_MANUAL_LITERAL,
                subject=entry.key,
                detail=detail,
                location=_at(index, entry.line),
            )
        )
    return result(
        "Manual literal agreement", defects.MISMATCHED_MANUAL_LITERAL, len(index.entries), "entries", findings
    )


def check_manual_verification(index: ProcedureIndex) -> CheckResult:
    """Missing verification on a `manual-by-decision` entry.

    Execution being manual is a decision; verification being absent is a gap. An entry with no row
    at all in the "Deliberately manual work" table names no verification anywhere, so it fails here
    too.

    Args:
        index: The parsed Index.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    manual = [entry for entry in index.entries if entry.status == "manual-by-decision"]
    for entry in manual:
        row = index.manual_row(entry.key)
        if row is None:
            findings.append(
                Finding(
                    defect=defects.MISSING_MANUAL_VERIFICATION,
                    subject=entry.key,
                    detail="no row in 'Deliberately manual work', so no verification is named",
                    location=_at(index, entry.line),
                )
            )
        elif not row.verification.strip():
            findings.append(
                Finding(
                    defect=defects.MISSING_MANUAL_VERIFICATION,
                    subject=entry.key,
                    detail="the Verification cell in 'Deliberately manual work' is empty",
                    location=_at(index, row.line),
                )
            )
    return result(
        "Manual verification named",
        defects.MISSING_MANUAL_VERIFICATION,
        len(manual),
        "manual-by-decision entries",
        findings,
    )


def check_manual_human_form(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Unwritten human form on a `manual-by-decision` entry.

    The Index tracks Runbook presence for these entries in the "Human form written?" column of
    "Deliberately manual work", precisely because the status does not. This detector therefore
    checks that column against disk in both directions: a `Yes` whose file is absent, and a `No`
    whose file is present, are each a disagreement between the record and reality.

    Most of these Runbooks are unwritten today, which the Index states is expected while their
    owning stories are unstarted. The count is not silently tolerated — it is recomputed as
    "Human forms written" in Totals, so it cannot quietly stop shrinking.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    manual = [entry for entry in index.entries if entry.status == "manual-by-decision"]
    for entry in manual:
        row = index.manual_row(entry.key)
        if row is None:
            continue
        recorded = row.human_form_written
        exists = workspace.declared_exists(entry.runbook)
        if recorded is None:
            findings.append(
                Finding(
                    defect=defects.UNWRITTEN_MANUAL_HUMAN_FORM,
                    subject=entry.key,
                    detail=f"'Human form written?' cell {row.human_form!r} states neither Yes nor No",
                    location=_at(index, row.line),
                )
            )
        elif recorded != exists:
            state = "exists" if exists else "does not exist"
            findings.append(
                Finding(
                    defect=defects.UNWRITTEN_MANUAL_HUMAN_FORM,
                    subject=entry.key,
                    detail=f"recorded as human form written={recorded}, but {entry.runbook!r} {state}",
                    location=_at(index, row.line),
                )
            )
    return result(
        "Manual human form recorded",
        defects.UNWRITTEN_MANUAL_HUMAN_FORM,
        len(manual),
        "manual-by-decision entries",
        findings,
    )


def check_duplicate_keys(index: ProcedureIndex) -> CheckResult:
    """Duplicate key, and two entries resolving to the same Runbook path.

    Args:
        index: The parsed Index.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    by_key: defaultdict[str, list[int]] = defaultdict(list)
    by_runbook: defaultdict[str, list[str]] = defaultdict(list)
    for entry in index.entries:
        by_key[entry.key].append(entry.line)
        if entry.runbook:
            by_runbook[entry.runbook].append(entry.key)
    for key, lines in sorted(by_key.items()):
        if len(lines) > 1:
            findings.append(
                Finding(
                    defect=defects.DUPLICATE_KEY,
                    subject=key,
                    detail=f"appears {len(lines)} times, at lines {lines}",
                    location=_at(index, lines[0]),
                )
            )
    for path, keys in sorted(by_runbook.items()):
        if len(set(keys)) > 1:
            findings.append(
                Finding(
                    defect=defects.DUPLICATE_RUNBOOK_PATH,
                    subject=path,
                    detail=f"claimed as the Runbook of more than one Procedure: {sorted(set(keys))}",
                    location=index.path.name,
                )
            )
    return result("Key and Runbook uniqueness", defects.DUPLICATE_KEY, len(index.entries), "entries", findings)


def check_retired_keys(index: ProcedureIndex) -> CheckResult:
    """Retired key reused: an entry using a key listed under *Retired keys*.

    Args:
        index: The parsed Index.

    Returns:
        The check result.
    """
    findings = [
        Finding(
            defect=defects.RETIRED_KEY_REUSED,
            subject=entry.key,
            detail="key is recorded as retired and must never be reassigned",
            location=_at(index, entry.line),
        )
        for entry in index.entries
        if entry.key in index.retired_keys
    ]
    return result(
        "Retired keys not reused",
        defects.RETIRED_KEY_REUSED,
        len(index.retired_keys),
        "retired keys",
        findings,
        note="none recorded as retired" if not index.retired_keys else "",
    )


def check_story_coverage(index: ProcedureIndex, stories: list[Story]) -> CheckResult:
    """Story with no entry, entry with no story, and story over its entry allowance.

    Args:
        index: The parsed Index.
        stories: The stories parsed from `epics.md`.

    Returns:
        The check result.
    """
    if not stories:
        return skipped(
            "Index against story list",
            defects.STORY_WITH_NO_ENTRY,
            "stories",
            "epics.md yielded no stories, so the story-set equality cannot be evaluated",
        )
    findings: list[Finding] = []
    by_story: defaultdict[str, list[str]] = defaultdict(list)
    for entry in index.entries:
        by_story[entry.story].append(entry.key)
    known = {story.number: story for story in stories}
    allowance = {row.story: row for row in index.exceptions}

    for story in stories:
        if story.number not in by_story:
            findings.append(
                Finding(
                    defect=defects.STORY_WITH_NO_ENTRY,
                    subject=f"story {story.number} — {story.title}",
                    detail="no Index entry; a Procedure nobody committed to writing",
                    location=f"epics.md:{story.line}",
                )
            )
    for entry in index.entries:
        if entry.story not in known:
            findings.append(
                Finding(
                    defect=defects.ENTRY_WITH_NO_STORY,
                    subject=entry.key,
                    detail=f"Story cell {entry.story!r} names a story absent from epics.md",
                    location=_at(index, entry.line),
                )
            )
    for story_number, keys in sorted(by_story.items()):
        exception = allowance.get(story_number)
        permitted = 2 if exception else 1
        if len(keys) > permitted:
            reason = "listed in the two-owner exception table" if exception else "not listed in the exception table"
            findings.append(
                Finding(
                    defect=defects.STORY_OVER_ENTRY_ALLOWANCE,
                    subject=f"story {story_number}",
                    detail=f"carries {len(keys)} entries {sorted(keys)} but is allowed {permitted} ({reason})",
                    location=index.path.name,
                )
            )
        elif exception and sorted(keys) != sorted(exception.keys):
            findings.append(
                Finding(
                    defect=defects.STORY_OVER_ENTRY_ALLOWANCE,
                    subject=f"story {story_number}",
                    detail=f"exception names {sorted(exception.keys)} but the Index carries {sorted(keys)}",
                    location=_at(index, exception.line),
                )
            )
    return result(
        "Index against story list",
        defects.STORY_WITH_NO_ENTRY,
        len(stories),
        "stories",
        findings,
        note=f"{len(index.entries)} entries across {len(by_story)} stories",
    )


def check_provenance(
    index: ProcedureIndex,
    workspace: Workspace,
    resolve_commit: Callable[[Workspace], str | None] | None = None,
) -> CheckResult:
    """Stale provenance: the recorded `epics.md` commit no longer matches the file's own.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.
        resolve_commit: Optional override for how the current commit is discovered. The self-check
            supplies one, because its throwaway copies are not git repositories.

    Returns:
        The check result.
    """
    if index.provenance_commit is None:
        return result(
            "Provenance of the story list",
            defects.STALE_PROVENANCE,
            1,
            "provenance lines",
            [
                Finding(
                    defect=defects.STALE_PROVENANCE,
                    subject=index.path.name,
                    detail="no 'at commit `<hash>`' provenance recorded, so the derivation is unfalsifiable",
                    location=index.path.name,
                )
            ],
        )
    resolver = resolve_commit or (lambda ws: ws.git_commit_for(ws.epics_path))
    current = resolver(workspace)
    if current is None:
        return skipped(
            "Provenance of the story list",
            defects.STALE_PROVENANCE,
            "provenance lines",
            f"git could not name the commit that last touched {workspace.relative(workspace.epics_path)}",
        )
    length = min(len(current), len(index.provenance_commit))
    if current[:length] == index.provenance_commit[:length]:
        return result(
            "Provenance of the story list",
            defects.STALE_PROVENANCE,
            1,
            "provenance lines",
            [],
            note=f"recorded {index.provenance_commit}, current {current}",
        )
    return result(
        "Provenance of the story list",
        defects.STALE_PROVENANCE,
        1,
        "provenance lines",
        [
            Finding(
                defect=defects.STALE_PROVENANCE,
                subject=index.path.name,
                detail=(
                    f"records deriving from epics.md at {index.provenance_commit!r} "
                    f"but the file's current commit is {current!r}; re-derive and update the line"
                ),
                location=index.path.name,
            )
        ],
    )


def check_alert_sources(index: ProcedureIndex, stories: list[Story]) -> CheckResult:
    """Every registered alert source names a real registering story and a real wiring story.

    AD-23 requires each detector to register here in the change that builds it. The rows are only
    consumable by story 13.5 if the stories they name resolve.

    Args:
        index: The parsed Index.
        stories: The stories parsed from `epics.md`.

    Returns:
        The check result.
    """
    if not stories:
        return skipped(
            "Alert-source registration",
            defects.UNREGISTERED_ALERT_SOURCE,
            "alert sources",
            "epics.md yielded no stories, so the registering stories cannot be resolved",
        )
    known = {story.number for story in stories}
    findings: list[Finding] = []
    for source in index.alert_sources:
        for label, value in (("Registering story", source.registering_story), ("Wired by", source.wired_by)):
            if value not in known:
                findings.append(
                    Finding(
                        defect=defects.UNREGISTERED_ALERT_SOURCE,
                        subject=source.source,
                        detail=f"{label} cell {value!r} names a story absent from epics.md",
                        location=_at(index, source.line),
                    )
                )
    return result(
        "Alert-source registration",
        defects.UNREGISTERED_ALERT_SOURCE,
        len(index.alert_sources),
        "registered sources",
        findings,
        note="none registered" if not index.alert_sources else "",
    )


def _recompute_totals(index: ProcedureIndex, stories: list[Story], workspace: Workspace) -> dict[str, int]:
    by_story: defaultdict[str, int] = defaultdict(int)
    for entry in index.entries:
        by_story[entry.story] += 1
    computed = {
        "stories": len(stories),
        "entries": len(index.entries),
        "exception_stories": sum(1 for count in by_story.values() if count == 2),
        # Scoped to `manual-by-decision` entries, matching the "Human form written?" column of
        # "Deliberately manual work" that this figure exists to total. Counting every entry with a
        # Runbook on disk would silently redefine the figure — it is the only reason the number
        # moved from 2 to 3 when this story's own Runbook landed, and that Runbook belongs to a
        # `complete` entry whose Runbook presence the status already tracks.
        "human_forms_written": sum(
            1
            for entry in index.entries
            if entry.status == "manual-by-decision" and workspace.declared_exists(entry.runbook)
        ),
    }
    for status in index.legal_statuses:
        computed[f"status:{status}"] = sum(1 for entry in index.entries if entry.status == status)
    return computed


def _canonical_total(label: str, legal_statuses: frozenset[str]) -> str | None:
    stripped = label.strip()
    lowered = stripped.casefold()
    if stripped in legal_statuses:
        return f"status:{stripped}"
    if lowered.startswith("stories in"):
        return "stories"
    if lowered.startswith("entries in this index"):
        return "entries"
    if lowered.startswith("stories carrying two entries"):
        return "exception_stories"
    if lowered.startswith("human forms written"):
        return "human_forms_written"
    return None


def check_totals(index: ProcedureIndex, stories: list[Story], workspace: Workspace) -> CheckResult:
    """Totals disagree with the tables.

    Every figure in Totals is recomputed from the entry tables and from `epics.md`, including the
    per-layer prose line. A stated figure the audit cannot recompute is itself reported: a number
    nothing checks is a number that goes stale.

    Args:
        index: The parsed Index.
        stories: The stories parsed from `epics.md`.
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    if not stories:
        return skipped(
            "Totals",
            defects.TOTALS_DISAGREE,
            "figures",
            "epics.md yielded no stories, so the story count cannot be recomputed",
        )
    computed = _recompute_totals(index, stories, workspace)
    findings: list[Finding] = []
    seen: set[str] = set()
    for label, stated in index.totals.figures.items():
        canonical = _canonical_total(label, index.legal_statuses)
        line = index.totals.lines.get(label, 0)
        if canonical is None:
            findings.append(
                Finding(
                    defect=defects.UNRECOMPUTED_TOTAL,
                    subject=label,
                    detail="Totals states a figure the audit does not know how to recompute",
                    location=_at(index, line),
                )
            )
            continue
        seen.add(canonical)
        if computed[canonical] != stated:
            findings.append(
                Finding(
                    defect=defects.TOTALS_DISAGREE,
                    subject=label,
                    detail=f"Totals states {stated}, the tables give {computed[canonical]}",
                    location=_at(index, line),
                )
            )
    for canonical in sorted(set(computed) - seen):
        findings.append(
            Finding(
                defect=defects.TOTALS_DISAGREE,
                subject=canonical,
                detail=f"Totals states no figure for this, which the tables give as {computed[canonical]}",
                location=f"{index.path.name}: Totals",
            )
        )

    per_layer_computed: defaultdict[str, int] = defaultdict(int)
    for entry in index.entries:
        per_layer_computed[entry.layer] += 1
    for layer in sorted(set(per_layer_computed) | set(index.totals.per_layer)):
        stated_layer = index.totals.per_layer.get(layer)
        actual = per_layer_computed.get(layer, 0)
        if stated_layer != actual:
            findings.append(
                Finding(
                    defect=defects.TOTALS_DISAGREE,
                    subject=f"per layer: {layer}",
                    detail=f"Totals states {stated_layer if stated_layer is not None else 'nothing'}, "
                    f"the tables give {actual}",
                    location=_at(index, index.totals.per_layer_line),
                )
            )
    return result(
        "Totals",
        defects.TOTALS_DISAGREE,
        len(index.totals.figures) + len(index.totals.per_layer),
        "stated figures",
        findings,
    )
