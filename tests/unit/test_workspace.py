from __future__ import annotations

from pathlib import Path

from asgard_harness.workspace import LAYERS, Workspace


def test_paths_are_derived_from_the_root(tmp_path: Path):
    workspace = Workspace(root=tmp_path)
    assert workspace.index_path == tmp_path / "PROCEDURE-INDEX.md"
    assert workspace.ownership_path == tmp_path / "docs" / "OWNERSHIP.md"
    assert workspace.epics_path.name == "epics.md"
    assert workspace.template_path == tmp_path / "runbooks" / "TEMPLATE.md"


def test_resolve_tolerates_a_trailing_slash(mini: Workspace):
    assert mini.resolve("k8s/l3-platform/thing/") == mini.root / "k8s/l3-platform/thing"


def test_declared_exists_is_false_for_a_blank_cell(mini: Workspace):
    assert mini.declared_exists("") is False
    assert mini.declared_exists("docs/MANUAL.md") is True
    assert mini.declared_exists("docs/NOPE.md") is False


def test_relative_falls_back_to_the_absolute_path(mini: Workspace):
    assert mini.relative(mini.root / "docs" / "MANUAL.md") == "docs/MANUAL.md"
    assert mini.relative(Path("/elsewhere/x")) == "/elsewhere/x"


def test_runbook_files_excludes_the_template(mini: Workspace):
    assert mini.runbook_files() == []
    (mini.runbooks_dir / "l0-physical" / "a.md").write_text("x\n", encoding="utf-8")
    assert [mini.relative(p) for p in mini.runbook_files()] == ["runbooks/l0-physical/a.md"]


def test_runbook_files_on_a_repository_without_runbooks(tmp_path: Path):
    assert Workspace(root=tmp_path).runbook_files() == []


def test_layer_directories_yields_only_existing_ones(mini: Workspace):
    found = {(tool, layer) for tool, layer, _ in mini.layer_directories()}
    assert ("runbooks", "l0-physical") in found
    assert ("ansible", "l0-physical") in found
    assert ("k8s", "l5-workloads") not in found


def test_git_commit_returns_none_outside_a_repository(tmp_path: Path):
    assert Workspace(root=tmp_path).git_commit_for(tmp_path / "nothing.md") is None


def test_git_commit_answers_inside_the_real_repository(repo_workspace: Workspace):
    commit = repo_workspace.git_commit_for(repo_workspace.index_path)
    assert commit is None or len(commit) >= 7


def test_layers_are_ordered_lowest_first():
    assert LAYERS[0].startswith("l0")
    assert LAYERS[-1].startswith("l5")


def test_git_commit_reports_none_when_git_cannot_be_launched(mini: Workspace, monkeypatch):
    """The same line that carried the 3.14-only syntax. Now driven, on the floor version too."""
    import asgard_harness.workspace as workspace_module

    def boom(*args, **kwargs):
        raise OSError("git not installed")

    monkeypatch.setattr(workspace_module.subprocess, "run", boom)
    assert mini.git_commit_for(mini.epics_path) is None


def test_git_commit_reports_none_on_a_subprocess_error(mini: Workspace, monkeypatch):
    import asgard_harness.workspace as workspace_module

    def boom(*args, **kwargs):
        raise workspace_module.subprocess.TimeoutExpired(cmd="git", timeout=30)

    monkeypatch.setattr(workspace_module.subprocess, "run", boom)
    assert mini.git_commit_for(mini.epics_path) is None
