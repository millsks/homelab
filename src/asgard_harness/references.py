"""Reading the dual-form contract's back-references out of each tool's native mechanism.

One convention, four expressions. The Index defines each one, so each gets an extractor here rather
than a comment the audit would have to parse by hand.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

_ANSIBLE_KEY_RE = re.compile(r"^\s*procedure_key\s*:\s*[\"']?([^\"'\s#]+)", re.MULTILINE)
_ANSIBLE_RUNBOOK_RE = re.compile(r"^\s*procedure_runbook\s*:\s*[\"']?([^\"'\s#]+)", re.MULTILINE)
_TOFU_KEY_RE = re.compile(r"procedure_key\s*=\s*\"([^\"]+)\"")
_TOFU_RUNBOOK_RE = re.compile(r"procedure_runbook\s*=\s*\"([^\"]+)\"")
_KUSTOMIZE_KEY_RE = re.compile(r"asgard\.home\.arpa/procedure-key\s*:\s*[\"']?([^\"'\s#]+)")
_KUSTOMIZE_RUNBOOK_RE = re.compile(r"asgard\.home\.arpa/procedure-runbook\s*:\s*[\"']?([^\"'\s#]+)")
_TOOLING_RE = re.compile(r"#\s*Procedure:\s*(PROC-[A-Z0-9-]+)\s*—\s*runbook:\s*(\S+)")

_KUSTOMIZATION_NAMES = ("kustomization.yaml", "kustomization.yml")


@dataclass(frozen=True, slots=True)
class AutomationReference:
    """What an Automation entry point declares about its Runbook.

    Attributes:
        key: The `procedure_key` it declares, or `""`.
        runbook: The `procedure_runbook` it declares, or `""`.
        carrier: The file the declaration was read from, repository-relative.
        mechanism: Which of the four conventions was used.
    """

    key: str
    runbook: str
    carrier: str
    mechanism: str


def _search(text: str, key_re: re.Pattern[str], runbook_re: re.Pattern[str]) -> tuple[str, str]:
    key = key_re.search(text)
    runbook = runbook_re.search(text)
    return (key.group(1) if key else "", runbook.group(1) if runbook else "")


def automation_mechanism(declared: str) -> str:
    """Classify an Automation path by the declaration mechanism its tool uses.

    Args:
        declared: The Automation path exactly as the Index writes it.

    Returns:
        One of `ansible`, `opentofu`, `kubernetes`, or `repository-tooling`.
    """
    path = declared.strip()
    if path.startswith("ansible/"):
        return "ansible"
    if path.startswith("tofu/"):
        return "opentofu"
    if path.startswith("k8s/"):
        return "kubernetes"
    return "repository-tooling"


def read_automation_reference(path: Path, declared: str, relative: str) -> AutomationReference | None:
    """Read the back-reference an Automation entry point declares.

    Args:
        path: The resolved path of the Automation entry point.
        declared: The Automation path as the Index writes it, used to pick the mechanism.
        relative: The repository-relative path, used for reporting.

    Returns:
        The declaration found, or `None` when the entry point cannot be read at all — a missing
        file, or a kustomization directory with no `kustomization.yaml`.
    """
    mechanism = automation_mechanism(declared)
    carrier = path
    if mechanism == "kubernetes":
        if not path.is_dir():
            return None
        for name in _KUSTOMIZATION_NAMES:
            candidate = path / name
            if candidate.is_file():
                carrier = candidate
                break
        else:
            return None
    if not carrier.is_file():
        return None
    text = carrier.read_text(encoding="utf-8", errors="replace")
    if mechanism == "ansible":
        key, runbook = _search(text, _ANSIBLE_KEY_RE, _ANSIBLE_RUNBOOK_RE)
    elif mechanism == "opentofu":
        key, runbook = _search(text, _TOFU_KEY_RE, _TOFU_RUNBOOK_RE)
    elif mechanism == "kubernetes":
        key, runbook = _search(text, _KUSTOMIZE_KEY_RE, _KUSTOMIZE_RUNBOOK_RE)
    else:
        match = _TOOLING_RE.search(text)
        key, runbook = (match.group(1), match.group(2)) if match else ("", "")
    carrier_name = relative if carrier == path else f"{relative}/{carrier.name}"
    return AutomationReference(key=key, runbook=runbook, carrier=carrier_name, mechanism=mechanism)
