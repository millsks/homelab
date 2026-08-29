"""Conventional-commit validation — the hook this Repository implements rather than imports."""

from __future__ import annotations

from pathlib import Path

import pytest

from asgard_harness import cli
from asgard_harness.commit_message import TYPES, subject_of, validate, validate_file


@pytest.mark.parametrize(
    "subject",
    [
        "feat: add the thing",
        "fix(asgard): stop the thing",
        "feat(asgard)!: replace the thing",
        "chore: routine",
        "docs(readme): explain",
        "refactor!: reshape",
    ],
)
def test_conventional_subjects_are_accepted(subject: str):
    assert validate(subject).ok


@pytest.mark.parametrize("commit_type", TYPES)
def test_every_declared_type_is_accepted(commit_type: str):
    assert validate(f"{commit_type}: something").ok


@pytest.mark.parametrize(
    "subject",
    [
        "add the thing",
        "feat add the thing",
        "feat:no space",
        "feat:",
        "Feat: capitalised type",
        "feature: not a declared type",
        "feat(): empty scope",
    ],
)
def test_non_conventional_subjects_are_rejected_with_a_reason(subject: str):
    verdict = validate(subject)
    assert not verdict.ok
    assert "type(scope): description" in verdict.reason
    assert verdict.subject == subject


@pytest.mark.parametrize(
    "subject",
    ["Merge pull request #7 from x", 'Revert "feat: x"', "fixup! feat: x", "squash! feat: x", "amend! feat: x"],
)
def test_git_generated_subjects_are_exempt(subject: str):
    assert validate(subject).ok


def test_comments_and_blank_lines_are_skipped_when_finding_the_subject():
    message = "\n\n# Please enter the commit message\nfeat: the real subject\n\nbody\n"
    assert subject_of(message) == "feat: the real subject"
    assert validate(message).ok


def test_an_empty_message_is_rejected():
    verdict = validate("\n# only comments\n")
    assert not verdict.ok
    assert verdict.reason == "the commit message is empty"


def test_a_message_file_is_read_and_judged(tmp_path: Path):
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("feat(asgard): land the thing\n", encoding="utf-8")
    assert validate_file(path).ok


def test_an_unreadable_message_file_is_a_rejection_not_a_pass(tmp_path: Path):
    """A hook that cannot see the message it is judging has not judged it."""
    verdict = validate_file(tmp_path / "does-not-exist")
    assert not verdict.ok
    assert "could not be read" in verdict.reason


def test_the_cli_rejects_when_git_passed_no_message_file(capsys):
    cli.configure_logging(as_json=False)
    assert cli.check_commit_message([]) == 1
    assert "exactly one commit message file" in capsys.readouterr().out


def test_the_cli_rejects_when_git_passed_more_than_one(tmp_path: Path, capsys):
    cli.configure_logging(as_json=False)
    assert cli.check_commit_message([tmp_path / "a", tmp_path / "b"]) == 1
    capsys.readouterr()


def test_the_cli_accepts_a_conventional_message(tmp_path: Path, capsys):
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("fix: correct the thing\n", encoding="utf-8")
    cli.configure_logging(as_json=False)
    assert cli.main(["commit-msg", str(path)]) == 0
    assert "commit message accepted" in capsys.readouterr().out


def test_the_cli_rejects_a_non_conventional_message_and_names_the_subject(tmp_path: Path, capsys):
    path = tmp_path / "COMMIT_EDITMSG"
    path.write_text("just some words\n", encoding="utf-8")
    cli.configure_logging(as_json=False)
    assert cli.main(["commit-msg", str(path)]) == 1
    out = capsys.readouterr().out
    assert "commit message rejected" in out
    assert "just some words" in out
