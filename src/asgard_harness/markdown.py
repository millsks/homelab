"""Markdown primitives: GFM pipe tables and YAML front matter.

Both governing documents state their rules as tables, so this parser is what turns a written rule
into an executable one. It is deliberately narrow — pipe tables and the two front-matter fields the
dual-form contract defines — because a general Markdown parser would invite the harness to depend
on prose, and prose is exactly what cannot be checked mechanically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_FENCE_RE = re.compile(r"^\s{0,3}(?:```|~~~)")
_DELIMITER_CELL_RE = re.compile(r"^:?-{2,}:?$")
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
_LINK_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


@dataclass(frozen=True, slots=True)
class Row:
    """One body row of a pipe table.

    Attributes:
        cells: The cleaned cell values, one per header column.
        line: 1-based line number of the row in its source file.
    """

    cells: tuple[str, ...]
    line: int

    def cell(self, index: int) -> str:
        """Return one cell, or the empty string when the row is short.

        A short row is a defect in the document, not a reason for the harness to raise: the
        detector that cares reports it by name.

        Args:
            index: Zero-based column index.

        Returns:
            The cell value, or `""` if the row has no such column.
        """
        return self.cells[index] if index < len(self.cells) else ""


@dataclass(frozen=True, slots=True)
class Table:
    """One GFM pipe table, with the headings it sits under.

    Attributes:
        headers: The cleaned header cells.
        rows: The body rows.
        heading: Text of the nearest preceding heading of any level.
        section: Text of the nearest preceding level-2 heading.
        line: 1-based line number of the header row.
    """

    headers: tuple[str, ...]
    rows: tuple[Row, ...]
    heading: str
    section: str
    line: int

    def column(self, name: str) -> int:
        """Index of a named column.

        Args:
            name: The header text to find, compared case-insensitively after cleaning.

        Returns:
            The zero-based column index, or `-1` when the table has no such column.
        """
        wanted = name.strip().casefold()
        for index, header in enumerate(self.headers):
            if header.casefold() == wanted:
                return index
        return -1


def clean(cell: str) -> str:
    """Reduce a Markdown cell to the value it states.

    Link syntax collapses to its label, code spans and bold markers are dropped, and surrounding
    whitespace is removed. Everything else is left alone: a cell's content is data.

    Args:
        cell: The raw cell text.

    Returns:
        The cleaned value.
    """
    text = _LINK_RE.sub(r"\1", cell)
    text = text.replace("**", "").replace("`", "")
    return text.strip()


def split_row(line: str) -> tuple[str, ...]:
    """Split one pipe-table line into its raw cells.

    Args:
        line: The source line, expected to start with `|`.

    Returns:
        The raw (uncleaned) cell strings.
    """
    stripped = line.strip()
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    return tuple(part for part in stripped.split("|"))


def _is_delimiter(line: str) -> bool:
    cells = [cell.strip() for cell in split_row(line)]
    return bool(cells) and all(_DELIMITER_CELL_RE.fullmatch(cell) for cell in cells)


def parse_tables(text: str) -> list[Table]:
    """Extract every pipe table in a Markdown document.

    Fenced code blocks are skipped, so an example table inside a fence is not mistaken for a
    declaration.

    Args:
        text: The whole document.

    Returns:
        Every table found, in document order.
    """
    lines = text.splitlines()
    tables: list[Table] = []
    heading = ""
    section = ""
    in_fence = False
    index = 0
    while index < len(lines):
        line = lines[index]
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            index += 1
            continue
        if in_fence:
            index += 1
            continue
        match = _HEADING_RE.match(line)
        if match:
            heading = clean(match.group(2))
            if len(match.group(1)) == 2:
                section = heading
            index += 1
            continue
        if line.lstrip().startswith("|") and index + 1 < len(lines) and _is_delimiter(lines[index + 1]):
            headers = tuple(clean(cell) for cell in split_row(line))
            header_line = index + 1
            index += 2
            rows: list[Row] = []
            while index < len(lines) and lines[index].lstrip().startswith("|"):
                rows.append(Row(cells=tuple(clean(cell) for cell in split_row(lines[index])), line=index + 1))
                index += 1
            tables.append(Table(headers=headers, rows=tuple(rows), heading=heading, section=section, line=header_line))
            continue
        index += 1
    return tables


def find_table(tables: list[Table], headers: tuple[str, ...], *, section: str | None = None) -> Table | None:
    """Find the one table with a given header row.

    Args:
        tables: Candidate tables, typically from `parse_tables`.
        headers: The exact header cells to match, case-insensitively.
        section: Optional level-2 heading the table must sit under.

    Returns:
        The first matching table, or `None`.
    """
    wanted = tuple(header.casefold() for header in headers)
    for table in tables:
        if tuple(header.casefold() for header in table.headers) != wanted:
            continue
        if section is not None and table.section.casefold() != section.casefold():
            continue
        return table
    return None


def find_tables(tables: list[Table], headers: tuple[str, ...], *, section: str | None = None) -> list[Table]:
    """Find every table with a given header row.

    Args:
        tables: Candidate tables, typically from `parse_tables`.
        headers: The exact header cells to match, case-insensitively.
        section: Optional level-2 heading the tables must sit under.

    Returns:
        Every matching table, in document order.
    """
    wanted = tuple(header.casefold() for header in headers)
    matched: list[Table] = []
    for table in tables:
        if tuple(header.casefold() for header in table.headers) != wanted:
            continue
        if section is not None and table.section.casefold() != section.casefold():
            continue
        matched.append(table)
    return matched


def parse_front_matter(text: str) -> dict[str, str] | None:
    """Parse a document's YAML front matter.

    Only flat `key: value` pairs are read. The dual-form contract defines exactly two fields, and a
    Runbook that needs nested front matter has outgrown the contract rather than the parser.

    Args:
        text: The whole document.

    Returns:
        The parsed fields, or `None` when the document has no front matter block.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            continue
        fields[key.strip()] = value.strip().strip("'\"")
    return None


def headings(text: str, level: int) -> list[str]:
    """List every heading at one level, outside fenced code blocks.

    Args:
        text: The whole document.
        level: The heading level, 1 through 6.

    Returns:
        The heading texts, in document order.
    """
    found: list[str] = []
    in_fence = False
    for line in text.splitlines():
        if _FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = _HEADING_RE.match(line)
        if match and len(match.group(1)) == level:
            found.append(clean(match.group(2)))
    return found
