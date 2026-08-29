"""Conventional-commit validation, implemented here rather than pulled from a hook registry.

`.pre-commit-config.yaml` in this Repository uses `repo: local` hooks exclusively, so that every
tool a commit runs comes from `pixi.lock` and nothing else. The usual conventional-commit hook is a
remote repository that pre-commit installs into a virtualenv of its own at `--install-hooks` time:
a second toolchain, resolved from the network, unpinned by anything this Repository controls, in a
project whose AD-20 prohibits `latest`. The deferred-work ledger recorded that trade-off as this
story's to weigh; this module is the weighing. It is thirty lines, and it removes the second
toolchain entirely.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

TYPES: tuple[str, ...] = (
    "build",
    "chore",
    "ci",
    "docs",
    "feat",
    "fix",
    "perf",
    "refactor",
    "revert",
    "style",
    "test",
)
"""The Conventional Commits type set. `pyproject.toml`'s git-cliff parsers group a subset of these."""

_SUBJECT = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([^()\n]+\))?!?: .+$")

_EXEMPT_PREFIXES: tuple[str, ...] = ("Merge ", "Revert ", "fixup! ", "squash! ", "amend! ")
"""Subjects git itself generates. Rejecting them would block a merge nobody hand-wrote."""


@dataclass(frozen=True, slots=True)
class MessageVerdict:
    """The outcome of validating one commit message.

    Attributes:
        ok: Whether the message may become a commit.
        subject: The subject line as read, for reporting.
        reason: Why it was rejected, empty when it was not.
    """

    ok: bool
    subject: str
    reason: str = ""


def subject_of(message: str) -> str:
    """The first line that is not a git comment or blank.

    Args:
        message: The whole commit message file contents.

    Returns:
        The subject line, or `""` when the message is empty.
    """
    for line in message.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        return line.rstrip()
    return ""


def validate(message: str) -> MessageVerdict:
    """Check a commit message against the Conventional Commits form.

    Args:
        message: The whole commit message file contents.

    Returns:
        The verdict, naming what is wrong when something is.
    """
    subject = subject_of(message)
    if not subject:
        return MessageVerdict(ok=False, subject="", reason="the commit message is empty")
    if subject.startswith(_EXEMPT_PREFIXES):
        return MessageVerdict(ok=True, subject=subject)
    if _SUBJECT.match(subject):
        return MessageVerdict(ok=True, subject=subject)
    return MessageVerdict(
        ok=False,
        subject=subject,
        reason=(
            "does not match 'type(scope): description'. "
            f"Type must be one of {list(TYPES)}; scope is optional; '!' before the colon marks a "
            "breaking change; a space after the colon and a non-empty description are required"
        ),
    )


def validate_file(path: Path) -> MessageVerdict:
    """Validate the commit message git wrote to a file.

    Args:
        path: The message file git passes to the `commit-msg` hook.

    Returns:
        The verdict. An unreadable file is a rejection, never a pass: a hook that cannot see the
        message it is judging has not judged it.
    """
    try:
        return validate(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        return MessageVerdict(ok=False, subject=str(path), reason=f"the commit message file could not be read: {error}")
