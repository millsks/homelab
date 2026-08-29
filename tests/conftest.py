"""Fixtures shared by the unit and integration suites."""

from __future__ import annotations

from pathlib import Path

import pytest

from asgard_harness.workspace import Workspace

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """The real repository root."""
    return REPO_ROOT


@pytest.fixture(scope="session")
def repo_workspace(repo_root: Path) -> Workspace:
    """A workspace over the real repository. Read-only: never mutate through this."""
    return Workspace(root=repo_root)
