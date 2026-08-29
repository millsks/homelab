from __future__ import annotations

from pathlib import Path

import pytest

from asgard_harness.references import automation_mechanism, read_automation_reference


@pytest.mark.parametrize(
    ("declared", "expected"),
    [
        ("ansible/l1-hypervisor/node-build.yml", "ansible"),
        ("tofu/l1-hypervisor/guest.tf", "opentofu"),
        ("k8s/l3-platform/gateway-tls/", "kubernetes"),
        ("pixi.toml", "repository-tooling"),
    ],
)
def test_mechanism_is_derived_from_the_declared_path(declared: str, expected: str):
    assert automation_mechanism(declared) == expected


def test_ansible_play_vars_are_read(tmp_path: Path):
    path = tmp_path / "play.yml"
    path.write_text(
        "- name: Build\n  hosts: nodes\n  vars:\n"
        "    procedure_key: PROC-NODE-BUILD\n"
        "    procedure_runbook: runbooks/l1-hypervisor/node-build.md\n",
        encoding="utf-8",
    )
    reference = read_automation_reference(path, "ansible/x.yml", "ansible/x.yml")
    assert reference.key == "PROC-NODE-BUILD"
    assert reference.runbook == "runbooks/l1-hypervisor/node-build.md"
    assert reference.mechanism == "ansible"


def test_opentofu_locals_are_read(tmp_path: Path):
    path = tmp_path / "main.tf"
    path.write_text(
        'locals {\n  procedure_key     = "PROC-GUEST-PROVISIONING"\n'
        '  procedure_runbook = "runbooks/l1-hypervisor/guest-provisioning.md"\n}\n',
        encoding="utf-8",
    )
    reference = read_automation_reference(path, "tofu/x.tf", "tofu/x.tf")
    assert reference.key == "PROC-GUEST-PROVISIONING"


def test_kustomize_common_annotations_are_read(tmp_path: Path):
    directory = tmp_path / "set"
    directory.mkdir()
    (directory / "kustomization.yaml").write_text(
        "commonAnnotations:\n"
        "  asgard.home.arpa/procedure-key: PROC-GATEWAY-TLS\n"
        "  asgard.home.arpa/procedure-runbook: runbooks/l3-platform/gateway-tls.md\n",
        encoding="utf-8",
    )
    reference = read_automation_reference(directory, "k8s/x/", "k8s/x")
    assert reference.key == "PROC-GATEWAY-TLS"
    assert reference.carrier == "k8s/x/kustomization.yaml"


def test_kustomize_directory_without_a_kustomization_is_unreadable(tmp_path: Path):
    directory = tmp_path / "set"
    directory.mkdir()
    assert read_automation_reference(directory, "k8s/x/", "k8s/x") is None


def test_kustomize_path_that_is_not_a_directory_is_unreadable(tmp_path: Path):
    path = tmp_path / "set"
    path.write_text("x\n", encoding="utf-8")
    assert read_automation_reference(path, "k8s/x/", "k8s/x") is None


def test_repository_tooling_comment_is_read(tmp_path: Path):
    path = tmp_path / "pixi.toml"
    path.write_text("# Procedure: PROC-CONVERGENCE-HARNESS — runbook: runbooks/l0-physical/x.md\n", encoding="utf-8")
    reference = read_automation_reference(path, "pixi.toml", "pixi.toml")
    assert reference.key == "PROC-CONVERGENCE-HARNESS"
    assert reference.runbook == "runbooks/l0-physical/x.md"


def test_a_declaration_that_is_absent_reads_as_empty(tmp_path: Path):
    path = tmp_path / "pixi.toml"
    path.write_text("[tasks]\n", encoding="utf-8")
    reference = read_automation_reference(path, "pixi.toml", "pixi.toml")
    assert reference.key == ""
    assert reference.runbook == ""


def test_a_missing_file_is_unreadable(tmp_path: Path):
    assert read_automation_reference(tmp_path / "gone.yml", "ansible/gone.yml", "ansible/gone.yml") is None
