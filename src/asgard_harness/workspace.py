"""The repository under audit.

Every path the harness touches is resolved through a `Workspace`, so the same code audits the real
repository and the throwaway copies the self-check mutates. A checker that can only run against its
own repository cannot prove it fails.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

TOOL_ROOTS: tuple[str, ...] = ("runbooks", "ansible", "tofu", "k8s")
"""Directory roots that mirror the dependency layers, one subdirectory per layer."""

LAYERS: tuple[str, ...] = (
    "l0-physical",
    "l1-hypervisor",
    "l2-foundation",
    "l3-platform",
    "l4-services",
    "l5-workloads",
)
"""The six stratified dependency layers, lowest first. Dependencies point only downward."""


@dataclass(frozen=True, slots=True)
class Workspace:
    """A repository root the harness reads.

    Attributes:
        root: The repository root directory.
    """

    root: Path

    @property
    def index_path(self) -> Path:
        """Path to the Procedure Index.

        Returns:
            `PROCEDURE-INDEX.md` under the root.
        """
        return self.root / "PROCEDURE-INDEX.md"

    @property
    def ownership_path(self) -> Path:
        """Path to the ownership table.

        Returns:
            `docs/OWNERSHIP.md` under the root.
        """
        return self.root / "docs" / "OWNERSHIP.md"

    @property
    def epics_path(self) -> Path:
        """Path to the story list the Index derives from.

        Returns:
            `_bmad-output/planning-artifacts/epics.md` under the root.
        """
        return self.root / "_bmad-output" / "planning-artifacts" / "epics.md"

    @property
    def runbooks_dir(self) -> Path:
        """Path to the Runbook tree.

        Returns:
            `runbooks/` under the root.
        """
        return self.root / "runbooks"

    @property
    def template_path(self) -> Path:
        """Path to the Runbook template.

        The template is not a Runbook; it is excluded from the Runbook walk by path, per the second
        exemption in the dual-form contract.

        Returns:
            `runbooks/TEMPLATE.md` under the root.
        """
        return self.runbooks_dir / "TEMPLATE.md"

    def resolve(self, declared: str) -> Path:
        """Resolve a repository-relative path as declared in a table cell.

        Args:
            declared: The path exactly as the Index or ownership table writes it. A trailing
                slash — used for kustomization directories — is tolerated.

        Returns:
            The absolute path.
        """
        return self.root / declared.strip().rstrip("/")

    def declared_exists(self, declared: str) -> bool:
        """Whether a path named in a table cell is present on disk.

        Args:
            declared: The path exactly as the table writes it.

        Returns:
            True when the path exists.
        """
        return bool(declared.strip()) and self.resolve(declared).exists()

    def relative(self, path: Path) -> str:
        """Express an absolute path the way the tables write it.

        Args:
            path: A path inside the workspace.

        Returns:
            The POSIX-style repository-relative path, or the absolute path when it lies outside.
        """
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return path.as_posix()

    def runbook_files(self) -> list[Path]:
        """Every file the Runbook walk covers.

        Returns:
            All `runbooks/**/*.md` except the template, sorted.
        """
        if not self.runbooks_dir.is_dir():
            return []
        template = self.template_path
        return sorted(path for path in self.runbooks_dir.rglob("*.md") if path != template)

    def layer_directories(self) -> Iterator[tuple[str, str, Path]]:
        """Every existing `<tool root>/<layer>/` directory.

        Yields:
            Triples of tool root, layer name, and directory path.
        """
        for tool in TOOL_ROOTS:
            for layer in LAYERS:
                directory = self.root / tool / layer
                if directory.is_dir():
                    yield tool, layer, directory

    def git_commit_for(self, path: Path) -> str | None:
        """The short hash of the commit that last touched a path.

        Args:
            path: The file to ask about.

        Returns:
            The abbreviated commit hash, or `None` when git cannot answer — no repository, no
            history for the path, or git not installed. The caller reports the skip; it never
            treats an unanswerable question as a pass.
        """
        try:
            completed = subprocess.run(
                ["git", "-C", str(self.root), "log", "-1", "--format=%h", "--", str(path)],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if completed.returncode != 0:
            return None
        return completed.stdout.strip() or None
