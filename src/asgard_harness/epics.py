"""The story list the Procedure Index derives from.

`epics.md` is the story-set equality source: every story must have an entry and every entry must
name a story. Only the story headings are read — the surrounding prose is not a contract.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_STORY_RE = re.compile(r"^###\s+Story\s+(\d+\.\d+)\s*:\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True, slots=True)
class Story:
    """One story from the epic breakdown.

    Attributes:
        number: The `<epic>.<story>` identifier.
        title: The story title, verbatim.
        line: 1-based line number of its heading.
    """

    number: str
    title: str
    line: int


def parse_stories(text: str) -> list[Story]:
    """Extract every story heading from an epic breakdown.

    Args:
        text: The whole document.

    Returns:
        The stories, in document order.
    """
    stories: list[Story] = []
    for match in _STORY_RE.finditer(text):
        line = text.count("\n", 0, match.start()) + 1
        stories.append(Story(number=match.group(1), title=match.group(2), line=line))
    return stories


def load_stories(path: Path) -> list[Story]:
    """Read and parse an epic breakdown.

    Args:
        path: Path to `epics.md`.

    Returns:
        The stories, in document order. An unreadable file yields an empty list; the detector that
        depends on it reports the emptiness rather than raising.
    """
    if not path.is_file():
        return []
    return parse_stories(path.read_text(encoding="utf-8"))
