from __future__ import annotations

import shutil
from pathlib import Path

from asgard_harness import checks_crossdoc
from asgard_harness.findings import CheckStatus
from asgard_harness.index_document import load_index
from asgard_harness.workspace import Workspace

GOOD_RUNBOOK = """---
procedure_key: PROC-ONE
procedure_automation: ansible/l0-physical/one.yml
---

# One

## Why this Procedure exists

## Procedure

### Step 1 — do it

#### Why

#### Command

#### Expected output

#### Automation task

#### Failure modes

## Rollback

## Verification
"""

GOOD_PLAYBOOK = """---
- name: One
  hosts: all
  vars:
    procedure_key: PROC-ONE
    procedure_runbook: runbooks/l0-physical/one.md
"""


def _write_runbook(workspace: Workspace, text: str = GOOD_RUNBOOK) -> Path:
    path = workspace.runbooks_dir / "l0-physical" / "one.md"
    path.write_text(text, encoding="utf-8")
    return path


def _write_playbook(workspace: Workspace, text: str = GOOD_PLAYBOOK) -> Path:
    path = workspace.root / "ansible" / "l0-physical" / "one.yml"
    path.write_text(text, encoding="utf-8")
    return path


def _subjects(check) -> list[str]:
    return [finding.subject for finding in check.findings]


# --- template sentinel ---------------------------------------------------------------------------


def test_template_sentinel_is_clean_when_only_the_template_carries_it(mini: Workspace):
    assert checks_crossdoc.check_template_sentinel(mini).status is CheckStatus.PASSED


def test_template_sentinel_fires_on_a_copied_template(mini: Workspace):
    shutil.copyfile(mini.template_path, mini.runbooks_dir / "l0-physical" / "copy.md")
    check = checks_crossdoc.check_template_sentinel(mini)
    assert set(_subjects(check)) == {"runbooks/l0-physical/copy.md"}
    assert {"procedure_key", "procedure_automation"} == {finding.detail.split("'")[1] for finding in check.findings}


def test_template_sentinel_ignores_prose_naming_the_sentinel(mini: Workspace):
    _write_runbook(mini, GOOD_RUNBOOK + "\nThis mentions TEMPLATE-UNFILLED in prose.\n")
    assert checks_crossdoc.check_template_sentinel(mini).status is CheckStatus.PASSED


# --- back-references -----------------------------------------------------------------------------


def test_back_references_pass_in_both_directions(mini: Workspace):
    _write_runbook(mini)
    _write_playbook(mini)
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.PASSED
    assert check.examined == 2


def test_back_references_fire_without_front_matter(mini: Workspace):
    _write_runbook(mini, "# One\n")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert "no YAML front matter" in check.findings[0].detail


def test_back_references_fire_on_an_unknown_key(mini: Workspace):
    _write_runbook(mini, "---\nprocedure_key: PROC-NOPE\nprocedure_automation: x\n---\n")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert "resolves to no Index entry" in check.findings[0].detail


def test_back_references_fire_on_the_wrong_automation(mini: Workspace):
    _write_runbook(mini, "---\nprocedure_key: PROC-ONE\nprocedure_automation: ansible/wrong.yml\n---\n")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert any("does not match the Index" in f.detail for f in check.findings)


def test_back_references_fire_when_the_index_names_another_file(mini: Workspace):
    path = mini.runbooks_dir / "l0-physical" / "elsewhere.md"
    path.write_text("---\nprocedure_key: PROC-ONE\nprocedure_automation: ansible/l0-physical/one.yml\n---\n", "utf-8")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert any("as its Runbook, not this file" in f.detail for f in check.findings)


def test_back_references_skip_a_file_still_carrying_the_sentinel(mini: Workspace):
    shutil.copyfile(mini.template_path, mini.runbooks_dir / "l0-physical" / "copy.md")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert check.status is CheckStatus.PASSED


def test_back_references_fire_when_the_automation_declares_nothing(mini: Workspace):
    _write_playbook(mini, "---\n- name: One\n  hosts: all\n")
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert any("procedure_key" in f.detail for f in check.findings)


def test_back_references_fire_on_an_unreadable_kustomization(mini: Workspace):
    directory = mini.root / "ansible" / "l0-physical" / "one.yml"
    directory.mkdir(parents=True, exist_ok=True)
    check = checks_crossdoc.check_back_references(load_index(mini.index_path), mini)
    assert any("no readable entry point" in f.detail for f in check.findings)


# --- Runbook shape -------------------------------------------------------------------------------


def test_runbook_shape_passes_on_a_complete_runbook(mini: Workspace):
    _write_runbook(mini)
    check = checks_crossdoc.check_runbook_shape(mini)
    assert check.status is CheckStatus.PASSED
    assert "4 required sections" in check.note


def test_runbook_shape_fires_on_a_missing_section(mini: Workspace):
    _write_runbook(mini, GOOD_RUNBOOK.replace("## Rollback\n", ""))
    check = checks_crossdoc.check_runbook_shape(mini)
    assert any("## Rollback" in f.detail for f in check.findings)


def test_runbook_shape_fires_when_verification_is_not_last(mini: Workspace):
    _write_runbook(mini, GOOD_RUNBOOK + "\n## Afterthought\n")
    check = checks_crossdoc.check_runbook_shape(mini)
    assert any("requires it to end with" in f.detail for f in check.findings)


def test_runbook_shape_fires_on_a_step_missing_a_required_heading(mini: Workspace):
    _write_runbook(mini, GOOD_RUNBOOK.replace("#### Failure modes\n", ""))
    check = checks_crossdoc.check_runbook_shape(mini)
    assert any("#### Failure modes" in f.detail for f in check.findings)


def test_runbook_shape_checks_every_step(mini: Workspace):
    two_steps = GOOD_RUNBOOK.replace("## Rollback", "### Step 2 — second\n\n#### Why\n\n## Rollback")
    _write_runbook(mini, two_steps)
    check = checks_crossdoc.check_runbook_shape(mini)
    assert any("Step 2" in f.subject for f in check.findings)


def test_runbook_shape_skips_without_a_template(mini: Workspace):
    mini.template_path.unlink()
    assert checks_crossdoc.check_runbook_shape(mini).status is CheckStatus.SKIPPED


def test_required_sections_are_read_from_the_template(mini: Workspace):
    sections, subsections = checks_crossdoc.required_runbook_sections(mini)
    assert sections[-1] == "Verification"
    assert "Failure modes" in subsections


def test_required_sections_on_a_repository_without_a_template(tmp_path: Path):
    assert checks_crossdoc.required_runbook_sections(Workspace(root=tmp_path)) == ((), ())


# --- layer discipline ----------------------------------------------------------------------------


def test_layer_dependencies_pass_on_an_empty_tree(mini: Workspace):
    assert checks_crossdoc.check_layer_dependencies(mini).status is CheckStatus.PASSED


def test_layer_dependencies_fire_on_an_upward_reference(mini: Workspace):
    target = mini.root / "ansible" / "l0-physical" / "upward.yml"
    target.write_text("# see ansible/l2-foundation/time.yml\n", encoding="utf-8")
    check = checks_crossdoc.check_layer_dependencies(mini)
    assert _subjects(check) == ["ansible/l0-physical/upward.yml"]
    assert "l2" in check.findings[0].detail


def test_layer_dependencies_allow_a_downward_reference(mini: Workspace):
    directory = mini.root / "ansible" / "l1-hypervisor"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "downward.yml").write_text("# see ansible/l0-physical/base.yml\n", encoding="utf-8")
    assert checks_crossdoc.check_layer_dependencies(mini).status is CheckStatus.PASSED


def test_an_undecodable_file_is_not_counted_as_examined(mini: Workspace):
    """The count is the claim: a file that could not be read was not examined."""
    (mini.root / "ansible" / "l0-physical" / "blob.bin").write_bytes(b"\xff\xfe\x00binary")
    check = checks_crossdoc.check_layer_dependencies(mini)
    assert check.status is CheckStatus.PASSED
    assert check.examined == 0
    assert "NOT examined" in check.note
    assert "ansible/l0-physical/blob.bin" in check.note


def test_readable_files_alongside_an_undecodable_one_are_still_counted(mini: Workspace):
    (mini.root / "ansible" / "l0-physical" / "blob.bin").write_bytes(b"\xff\xfe\x00binary")
    (mini.root / "ansible" / "l0-physical" / "fine.yml").write_text("---\n", encoding="utf-8")
    check = checks_crossdoc.check_layer_dependencies(mini)
    assert check.examined == 1
