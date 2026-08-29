"""A parsed `PROCEDURE-INDEX.md`.

The Index states its own closed enumerations — the status set, the two-owner exception, the retired
keys, the totals. This module reads all of them out of the document rather than restating them in
Python, so that changing a rule means changing the document and nothing else. A rule hardcoded here
would be a second place to change and a first place to forget.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from asgard_harness.markdown import Table, find_table, find_tables, parse_tables

MANUAL_LITERAL = "none — by decision"
"""The literal that means an entry has no Automation half. It is not a path."""

TEMPLATE_SENTINEL = "TEMPLATE-UNFILLED"
"""Front-matter sentinel marking `runbooks/TEMPLATE.md` as not itself a Runbook."""

ENTRY_HEADERS = ("Key", "Title", "Layer", "Story", "Runbook", "Automation", "Status")
MANUAL_HEADERS = ("Key", "Story", "Why no Automation", "Verification", "Human form written?", "Provisional?")
EXCEPTION_HEADERS = ("Story", "Split across", "Entries", "Reason")
STATUS_HEADERS = ("Status", "Means")
ALERT_HEADERS = ("Source", "Registering story", "Wired by", "Status")
TOTALS_HEADERS = ("", "Count")

_KEY_RE = re.compile(r"PROC-[A-Z0-9]+(?:-[A-Z0-9]+)*")
_COMMIT_RE = re.compile(r"at commit `([0-9a-f]{7,40})`")
_PER_LAYER_LINE_RE = re.compile(r"^Per layer:", re.MULTILINE)
_PER_LAYER_RE = re.compile(r"`(l\d-[a-z-]+)`\s+(\d+)")
_RETIRED_LINE_RE = re.compile(r"^\*\*Retired keys:\*\*\s*(.+?)\s*$", re.MULTILINE)
_YES_NO_RE = re.compile(r"^(yes|no)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """One row of the Index tables.

    Attributes:
        key: The stable `PROC-…` identifier.
        title: The owning story's title, verbatim.
        layer: The owning layer.
        story: The `<epic>.<story>` identifier of the single owning story.
        runbook: Where the human half lives, as declared.
        automation: Where the machine half lives, or `MANUAL_LITERAL`.
        status: One value from the Index's closed status enumeration.
        line: 1-based line number of the row.
    """

    key: str
    title: str
    layer: str
    story: str
    runbook: str
    automation: str
    status: str
    line: int

    @property
    def is_manual_literal(self) -> bool:
        """Whether the Automation cell carries the manual literal.

        Returns:
            True when the cell means "no Automation half", rather than naming a path.
        """
        return self.automation.strip() == MANUAL_LITERAL


@dataclass(frozen=True, slots=True)
class ManualRow:
    """One row of the "Deliberately manual work" table.

    Attributes:
        key: The Procedure key.
        story: The owning story.
        reason: Why the Procedure has no Automation half.
        verification: The named automated verification.
        human_form: The raw "Human form written?" cell.
        provisional: The raw "Provisional?" cell.
        line: 1-based line number of the row.
    """

    key: str
    story: str
    reason: str
    verification: str
    human_form: str
    provisional: str
    line: int

    @property
    def human_form_written(self) -> bool | None:
        """The recorded claim about whether the human form exists.

        Returns:
            True for a `Yes…` cell, False for a `No…` cell, `None` when the cell states neither and
            so records nothing checkable.
        """
        match = _YES_NO_RE.match(self.human_form.strip())
        if match is None:
            return None
        return match.group(1).casefold() == "yes"


@dataclass(frozen=True, slots=True)
class ExceptionRow:
    """One row of the two-owner exception table.

    Attributes:
        story: The story permitted more than one entry.
        keys: The keys that story is permitted to carry.
        line: 1-based line number of the row.
    """

    story: str
    keys: tuple[str, ...]
    line: int


@dataclass(frozen=True, slots=True)
class AlertSource:
    """One row of the alert-source registration table.

    Attributes:
        source: The detector being registered.
        registering_story: The story that built it.
        wired_by: The story that wires it to notification.
        status: Free text describing registration state.
        line: 1-based line number of the row.
    """

    source: str
    registering_story: str
    wired_by: str
    status: str
    line: int


@dataclass(frozen=True, slots=True)
class Totals:
    """The Totals section, as written.

    Attributes:
        figures: Raw label to stated count, in document order.
        per_layer: Layer name to stated count, from the per-layer prose line.
        lines: Raw label to the 1-based line number that states it.
        per_layer_line: 1-based line number of the per-layer prose line, or 0 when absent.
    """

    figures: dict[str, int] = field(default_factory=dict)
    per_layer: dict[str, int] = field(default_factory=dict)
    lines: dict[str, int] = field(default_factory=dict)
    per_layer_line: int = 0


@dataclass(frozen=True, slots=True)
class ProcedureIndex:
    """Everything the harness reads out of `PROCEDURE-INDEX.md`.

    Attributes:
        entries: Every Index entry, in document order.
        manual_rows: The "Deliberately manual work" rows.
        exceptions: The two-owner exception rows.
        alert_sources: The registered alert sources.
        totals: The Totals section as written.
        legal_statuses: The closed status enumeration, read from the document.
        retired_keys: Keys recorded as retired.
        provenance_commit: The `epics.md` commit the Index records deriving from.
        path: Where the document was read from.
    """

    entries: tuple[IndexEntry, ...]
    manual_rows: tuple[ManualRow, ...]
    exceptions: tuple[ExceptionRow, ...]
    alert_sources: tuple[AlertSource, ...]
    totals: Totals
    legal_statuses: frozenset[str]
    retired_keys: frozenset[str]
    provenance_commit: str | None
    path: Path

    def entry(self, key: str) -> IndexEntry | None:
        """Look one entry up by key.

        Args:
            key: The `PROC-…` identifier.

        Returns:
            The entry, or `None` when the Index has no such key.
        """
        for entry in self.entries:
            if entry.key == key:
                return entry
        return None

    @property
    def keys(self) -> frozenset[str]:
        """Every key in the Index.

        Returns:
            The set of entry keys.
        """
        return frozenset(entry.key for entry in self.entries)

    def manual_row(self, key: str) -> ManualRow | None:
        """Look one deliberately-manual row up by key.

        Args:
            key: The `PROC-…` identifier.

        Returns:
            The row, or `None` when the table has no such key.
        """
        for row in self.manual_rows:
            if row.key == key:
                return row
        return None


def _parse_totals(tables: list[Table], text: str) -> Totals:
    table = find_table(tables, TOTALS_HEADERS, section="Totals")
    figures: dict[str, int] = {}
    lines: dict[str, int] = {}
    if table is not None:
        for row in table.rows:
            label = row.cell(0).strip()
            value = row.cell(1).strip()
            if not label or not value.isdigit():
                continue
            figures[label] = int(value)
            lines[label] = row.line
    per_layer: dict[str, int] = {}
    per_layer_line = 0
    match = _PER_LAYER_LINE_RE.search(text)
    if match is not None:
        per_layer_line = text.count("\n", 0, match.start()) + 1
        end = text.find("\n\n", match.start())
        tail = text[match.start() : end if end != -1 else len(text)]
        per_layer = {name: int(count) for name, count in _PER_LAYER_RE.findall(tail)}
    return Totals(figures=figures, per_layer=per_layer, lines=lines, per_layer_line=per_layer_line)


def _parse_retired_keys(text: str) -> frozenset[str]:
    match = _RETIRED_LINE_RE.search(text)
    if match is None:
        return frozenset()
    return frozenset(_KEY_RE.findall(match.group(1)))


def parse_index(text: str, path: Path) -> ProcedureIndex:
    """Parse a Procedure Index document.

    Args:
        text: The whole document.
        path: Where it was read from, used for reporting locations.

    Returns:
        The parsed Index.
    """
    tables = parse_tables(text)

    entries = tuple(
        IndexEntry(
            key=row.cell(0),
            title=row.cell(1),
            layer=row.cell(2),
            story=row.cell(3),
            runbook=row.cell(4),
            automation=row.cell(5),
            status=row.cell(6),
            line=row.line,
        )
        for table in find_tables(tables, ENTRY_HEADERS, section="The Index")
        for row in table.rows
        if row.cell(0)
    )

    manual_table = find_table(tables, MANUAL_HEADERS)
    manual_rows = tuple(
        ManualRow(
            key=row.cell(0),
            story=row.cell(1),
            reason=row.cell(2),
            verification=row.cell(3),
            human_form=row.cell(4),
            provisional=row.cell(5),
            line=row.line,
        )
        for row in (manual_table.rows if manual_table else ())
        if row.cell(0)
    )

    exception_table = find_table(tables, EXCEPTION_HEADERS)
    exceptions = tuple(
        ExceptionRow(story=row.cell(0), keys=tuple(_KEY_RE.findall(row.cell(2))), line=row.line)
        for row in (exception_table.rows if exception_table else ())
        if row.cell(0)
    )

    alert_table = find_table(tables, ALERT_HEADERS, section="Alert sources")
    alert_sources = tuple(
        AlertSource(
            source=row.cell(0),
            registering_story=row.cell(1),
            wired_by=row.cell(2),
            status=row.cell(3),
            line=row.line,
        )
        for row in (alert_table.rows if alert_table else ())
        if row.cell(0)
    )

    status_table = find_table(tables, STATUS_HEADERS)
    legal_statuses = frozenset(row.cell(0) for row in (status_table.rows if status_table else ()) if row.cell(0))

    commit_match = _COMMIT_RE.search(text)

    return ProcedureIndex(
        entries=entries,
        manual_rows=manual_rows,
        exceptions=exceptions,
        alert_sources=alert_sources,
        totals=_parse_totals(tables, text),
        legal_statuses=legal_statuses,
        retired_keys=_parse_retired_keys(text),
        provenance_commit=commit_match.group(1) if commit_match else None,
        path=path,
    )


def load_index(path: Path) -> ProcedureIndex:
    """Read and parse a Procedure Index.

    Args:
        path: Path to `PROCEDURE-INDEX.md`.

    Returns:
        The parsed Index. A missing file yields an empty Index; the detectors report the emptiness.
    """
    if not path.is_file():
        return ProcedureIndex(
            entries=(),
            manual_rows=(),
            exceptions=(),
            alert_sources=(),
            totals=Totals(),
            legal_statuses=frozenset(),
            retired_keys=frozenset(),
            provenance_commit=None,
            path=path,
        )
    return parse_index(path.read_text(encoding="utf-8"), path)
