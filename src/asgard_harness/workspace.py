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

VENDORED_ROOTS: tuple[str, ...] = ("_bmad", ".claude", ".agents", ".bmad-loop", ".pixi", ".github/agents")
"""Trees that are committed here but are not this project's to hold to its rules.

The same list `.yamllint` and `pyproject.toml` already exclude, named once more here because the
secret scan needs it too. The scan reports the exclusion in its own output rather than applying it
quietly: a credential placed inside one of these trees is invisible to the check, which is a real
limit and is recorded in the deferred-work ledger rather than hidden behind a green tick.
"""

UNWALKED_DIRECTORIES: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
        ".ansible",
        ".terraform",
        "htmlcov",
        "node_modules",
    }
)
"""Caches and tool working directories. Nothing in them is committed, so nothing in them is scanned."""


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

    def is_vendored(self, relative: str) -> bool:
        """Whether a repository-relative path sits inside a vendored tree.

        Args:
            relative: A POSIX-style repository-relative path.

        Returns:
            True when the path is under one of `VENDORED_ROOTS`.
        """
        return any(relative == root or relative.startswith(f"{root}/") for root in VENDORED_ROOTS)

    def _git_tracked(self) -> list[str] | None:
        """Every path git tracks, or `None` when git cannot answer for this directory.

        The toplevel is compared against the root deliberately. A throwaway copy created inside
        somebody's home directory could sit under an unrelated repository, and `git ls-files` would
        then answer for *that* repository — enumerating a set of paths that has nothing to do with
        the workspace under audit, which is worse than not answering at all.

        Returns:
            Repository-relative paths, or `None`.
        """
        try:
            toplevel = subprocess.run(
                ["git", "-C", str(self.root), "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            if toplevel.returncode != 0 or Path(toplevel.stdout.strip() or "/nonexistent").resolve() != self.root:
                return None
            listed = subprocess.run(
                # --cached AND --others --exclude-standard: everything git tracks, plus everything
                # it does not yet track but would. Tracked-only was a hole with a friendly face —
                # a developer could create a file holding a credential, run the scan, and be told
                # the Repository was clean, because the file was not tracked *yet*. Ignored paths
                # stay out, which is what makes `.gitignore` the declared way to exclude a scratch
                # file rather than an accident of not having run `git add`.
                ["git", "-C", str(self.root), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
                capture_output=True,
                text=True,
                check=False,
                timeout=60,
            )
        except (OSError, subprocess.SubprocessError):
            return None
        if listed.returncode != 0:
            return None
        return [entry for entry in listed.stdout.split("\0") if entry]

    def _walked(self) -> list[str]:
        """Every file under the root, skipping caches and tool working directories.

        Returns:
            Repository-relative paths, sorted.
        """
        found: list[str] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.is_symlink():
                continue
            relative = self.relative(path)
            if any(part in UNWALKED_DIRECTORIES for part in path.relative_to(self.root).parts[:-1]):
                continue
            found.append(relative)
        return found

    def scannable_files(self) -> tuple[list[Path], str]:
        """The files the secret scan covers, and how they were enumerated.

        The scope is everything git tracks **plus everything it would track if asked** — not
        tracked-only. A secret matters once it is committed, but the moment to catch it is before
        that, and a file a developer has just written is exactly the file most likely to hold one.

        What stays out is what `.gitignore` excludes, which is the point: excluding a scratch file
        becomes a declared decision in a committed file rather than a side effect of not having run
        `git add`. When git cannot answer — a source export, a throwaway copy — the tree is walked
        instead, rather than the scan reporting a pass over nothing.

        Returns:
            A pair of absolute paths and a phrase naming how they were found, for the report. The
            phrase goes into the report verbatim: a scan whose scope the reader cannot see is a
            scan whose clean result they cannot interpret.
        """
        listed = self._git_tracked()
        source = (
            "tracked and untracked files git would add (gitignored paths excluded)"
            if listed is not None
            else "files walked, git could not answer (gitignored paths are NOT excluded)"
        )
        relatives = listed if listed is not None else self._walked()
        paths = [self.root / relative for relative in relatives if not self.is_vendored(relative)]
        return [path for path in paths if path.is_file()], source

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
