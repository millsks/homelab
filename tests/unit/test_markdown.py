from __future__ import annotations

import pytest

from asgard_harness.markdown import (
    clean,
    find_table,
    find_tables,
    headings,
    parse_front_matter,
    parse_tables,
    split_row,
)

DOC = """# Title

## Section A

### Sub

| Key | Value |
| --- | :---: |
| `a` | **1** |
| [`b`](x.md) | 2 |

## Section B

```
| Fenced | Table |
| --- | --- |
| no | no |
```

| Key | Value |
| --- | --- |
| c | 3 |
"""


def test_parse_tables_finds_both_real_tables_and_skips_fences():
    tables = parse_tables(DOC)
    assert len(tables) == 2
    assert tables[0].heading == "Sub"
    assert tables[0].section == "Section A"
    assert tables[1].section == "Section B"
    assert [row.cells for row in tables[0].rows] == [("a", "1"), ("b", "2")]


def test_row_line_numbers_point_at_the_source():
    table = parse_tables(DOC)[0]
    assert DOC.splitlines()[table.rows[0].line - 1].startswith("| `a`")


def test_row_cell_tolerates_a_short_row():
    table = parse_tables("| A | B | C |\n| --- | --- | --- |\n| only |\n")[0]
    assert table.rows[0].cell(0) == "only"
    assert table.rows[0].cell(2) == ""


def test_column_lookup_is_case_insensitive_and_reports_absence():
    table = parse_tables(DOC)[0]
    assert table.column("key") == 0
    assert table.column("nope") == -1


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("  `code`  ", "code"),
        ("**bold**", "bold"),
        ("[label](target.md)", "label"),
        ("[`x`](../x.md) and text", "x and text"),
        ("", ""),
    ],
)
def test_clean_reduces_a_cell_to_its_value(raw: str, expected: str):
    assert clean(raw) == expected


def test_split_row_handles_missing_edge_pipes():
    assert split_row("a | b") == ("a ", " b")
    assert split_row("| a | b |") == (" a ", " b ")


def test_find_table_matches_headers_and_section():
    tables = parse_tables(DOC)
    assert find_table(tables, ("Key", "Value"), section="Section B") is tables[1]
    assert find_table(tables, ("Key", "Value"), section="Nowhere") is None
    assert find_table(tables, ("Nope",)) is None


def test_find_tables_returns_every_match():
    assert len(find_tables(parse_tables(DOC), ("Key", "Value"))) == 2
    assert find_tables(parse_tables(DOC), ("Key", "Value"), section="Section A") != []


def test_parse_front_matter_reads_flat_fields():
    assert parse_front_matter("---\na: 1\nb: 'two'\n# note\n\n---\nbody\n") == {"a": "1", "b": "two"}


def test_parse_front_matter_returns_none_without_a_block():
    assert parse_front_matter("no front matter\n") is None


def test_parse_front_matter_returns_none_when_unterminated():
    assert parse_front_matter("---\na: 1\n") is None


def test_parse_front_matter_on_empty_document():
    assert parse_front_matter("") is None


def test_headings_skips_fenced_content():
    assert headings(DOC, 2) == ["Section A", "Section B"]
    assert headings(DOC, 1) == ["Title"]
