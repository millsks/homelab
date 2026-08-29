"""A parsed `docs/OWNERSHIP.md`.

The Owner column is a closed enumeration for exactly one reason: the audit parses it, and a
sentence cannot be checked mechanically. The enumeration is read out of the document's own "Legal
Owner values" table rather than restated here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from asgard_harness.markdown import find_table, find_tables, parse_tables

CLASS_HEADERS = ("Resource class", "Owner", "Declaring mechanism", "Verification", "Procedure", "Notes")
OWNER_HEADERS = ("Owner value", "Means", "Declarations live in")

DELEGATED_OWNER = "Delegated"
"""The single Owner value exempt from the one-owner check; it resolves transitively."""

_KEY_RE = re.compile(r"PROC-[A-Z0-9]+(?:-[A-Z0-9]+)*")
_WHITESPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True, slots=True)
class OwnershipRow:
    """One resource class and its declaring owner.

    Attributes:
        resource_class: The class name, verbatim.
        owner: The declaring mechanism, drawn from the closed enumeration.
        mechanism: Where the declaration physically lives.
        verification: How the declaration is checked against reality.
        procedures: The covering Procedure keys named in the Procedure column.
        procedure_cell: The raw Procedure cell, for rows that name no key.
        notes: The Notes cell.
        layer: The level-2 heading the row sits under.
        line: 1-based line number of the row.
    """

    resource_class: str
    owner: str
    mechanism: str
    verification: str
    procedures: tuple[str, ...]
    procedure_cell: str
    notes: str
    layer: str
    line: int

    @property
    def normalised_class(self) -> str:
        """The class name reduced for comparison.

        Returns:
            Lower-cased with collapsed whitespace, so that two rows naming the same class are
            recognised as the same class.
        """
        return _WHITESPACE_RE.sub(" ", self.resource_class).strip().casefold()

    @property
    def is_delegated(self) -> bool:
        """Whether the row carries the `Delegated` owner.

        Returns:
            True when the class is owned transitively by whatever owns the class it attaches to.
        """
        return self.owner.strip() == DELEGATED_OWNER


@dataclass(frozen=True, slots=True)
class OwnershipTable:
    """Everything the harness reads out of `docs/OWNERSHIP.md`.

    Attributes:
        rows: Every resource-class row, in document order.
        legal_owners: The closed Owner enumeration, read from the document.
        path: Where the document was read from.
    """

    rows: tuple[OwnershipRow, ...]
    legal_owners: frozenset[str]
    path: Path


def parse_ownership(text: str, path: Path) -> OwnershipTable:
    """Parse an ownership table document.

    Args:
        text: The whole document.
        path: Where it was read from, used for reporting locations.

    Returns:
        The parsed ownership table.
    """
    tables = parse_tables(text)
    rows = tuple(
        OwnershipRow(
            resource_class=row.cell(0),
            owner=row.cell(1),
            mechanism=row.cell(2),
            verification=row.cell(3),
            procedures=tuple(_KEY_RE.findall(row.cell(4))),
            procedure_cell=row.cell(4),
            notes=row.cell(5),
            layer=table.section,
            line=row.line,
        )
        for table in find_tables(tables, CLASS_HEADERS)
        for row in table.rows
        if row.cell(0)
    )
    owner_table = find_table(tables, OWNER_HEADERS)
    legal_owners = frozenset(row.cell(0) for row in (owner_table.rows if owner_table else ()) if row.cell(0))
    return OwnershipTable(rows=rows, legal_owners=legal_owners, path=path)


def load_ownership(path: Path) -> OwnershipTable:
    """Read and parse an ownership table.

    Args:
        path: Path to `docs/OWNERSHIP.md`.

    Returns:
        The parsed table. A missing file yields an empty table; the detectors report the emptiness.
    """
    if not path.is_file():
        return OwnershipTable(rows=(), legal_owners=frozenset(), path=path)
    return parse_ownership(path.read_text(encoding="utf-8"), path)
