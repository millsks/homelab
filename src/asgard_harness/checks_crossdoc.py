"""Cross-document detectors: back-references, the template sentinel, Runbook shape, layer discipline.

The dual-form contract is bidirectional, so both directions are walked. The two exemptions the
Index states — the manual literal is not a path, and `runbooks/TEMPLATE.md` is not a Runbook — are
implemented from that specification rather than discovered as false failures.
"""

from __future__ import annotations

import re

from asgard_harness import defects
from asgard_harness.findings import CheckResult, Finding, result, skipped
from asgard_harness.index_document import TEMPLATE_SENTINEL, ProcedureIndex
from asgard_harness.markdown import parse_front_matter
from asgard_harness.references import read_automation_reference
from asgard_harness.workspace import LAYERS, Workspace

FRONT_MATTER_FIELDS = ("procedure_key", "procedure_automation")
"""The two fields the dual-form contract puts in Runbook front matter."""

_STEP_RE = re.compile(r"^###\s+Step\b.*$", re.MULTILINE)
_SUBSECTION_RE = re.compile(r"^####\s+(.+?)\s*$", re.MULTILINE)
_SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
_LAYER_TOKEN_RE = re.compile(r"\bl(\d)-[a-z-]+")


def check_template_sentinel(workspace: Workspace) -> CheckResult:
    """Unfilled template sentinel in any file under `runbooks/` other than the template.

    Scoped to the two front-matter fields, not to the string: documents that discuss the sentinel
    are not defects. That scoping is the Index's, not an invention here.

    Args:
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    files = workspace.runbook_files()
    findings: list[Finding] = []
    for path in files:
        fields = parse_front_matter(path.read_text(encoding="utf-8", errors="replace")) or {}
        for field in FRONT_MATTER_FIELDS:
            if fields.get(field, "").strip() == TEMPLATE_SENTINEL:
                findings.append(
                    Finding(
                        defect=defects.UNFILLED_TEMPLATE_SENTINEL,
                        subject=workspace.relative(path),
                        detail=f"front-matter field {field!r} still carries the sentinel {TEMPLATE_SENTINEL!r}",
                        location=workspace.relative(path),
                    )
                )
    return result(
        "Template sentinel",
        defects.UNFILLED_TEMPLATE_SENTINEL,
        len(files),
        "Runbooks (template excluded by path)",
        findings,
    )


def check_back_references(index: ProcedureIndex, workspace: Workspace) -> CheckResult:
    """Broken back-reference, in both directions.

    Runbook to Automation: every file under `runbooks/` names a real key and the Automation path
    that key's entry declares, and the entry names that file back.

    Automation to Runbook: every Automation entry point that exists on disk declares its key and
    Runbook in its own tool's native mechanism, and both agree with the Index.

    Args:
        index: The parsed Index.
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    examined = 0

    for path in workspace.runbook_files():
        examined += 1
        relative = workspace.relative(path)
        fields = parse_front_matter(path.read_text(encoding="utf-8", errors="replace"))
        if fields is None:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=relative,
                    detail="no YAML front matter, so the Runbook names no Procedure",
                    location=relative,
                )
            )
            continue
        key = fields.get("procedure_key", "").strip()
        automation = fields.get("procedure_automation", "").strip()
        if key == TEMPLATE_SENTINEL:
            continue
        entry = index.entry(key)
        if entry is None:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=relative,
                    detail=f"procedure_key {key!r} resolves to no Index entry",
                    location=relative,
                )
            )
            continue
        if automation != entry.automation:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=relative,
                    detail=f"procedure_automation {automation!r} does not match the Index's {entry.automation!r}",
                    location=relative,
                )
            )
        if entry.runbook.rstrip("/") != relative:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=relative,
                    detail=f"{entry.key} names {entry.runbook!r} as its Runbook, not this file",
                    location=relative,
                )
            )

    for entry in index.entries:
        if entry.is_manual_literal or not workspace.declared_exists(entry.automation):
            continue
        examined += 1
        relative = workspace.relative(workspace.resolve(entry.automation))
        reference = read_automation_reference(workspace.resolve(entry.automation), entry.automation, relative)
        if reference is None:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=entry.automation,
                    detail=f"{entry.key}'s Automation has no readable entry point to carry a back-reference",
                    location=relative,
                )
            )
            continue
        if reference.key != entry.key:
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=reference.carrier,
                    detail=(
                        f"declares procedure_key {reference.key or 'nothing'!r} via its {reference.mechanism} "
                        f"mechanism; the Index names it as {entry.key}"
                    ),
                    location=reference.carrier,
                )
            )
        if reference.runbook.rstrip("/") != entry.runbook.rstrip("/"):
            findings.append(
                Finding(
                    defect=defects.BROKEN_BACK_REFERENCE,
                    subject=reference.carrier,
                    detail=(
                        f"declares procedure_runbook {reference.runbook or 'nothing'!r}; "
                        f"the Index names {entry.runbook!r}"
                    ),
                    location=reference.carrier,
                )
            )
    return result("Dual-form back-references", defects.BROKEN_BACK_REFERENCE, examined, "halves walked", findings)


def required_runbook_sections(workspace: Workspace) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """The sections a Runbook must carry, read out of the template itself.

    Deriving the requirement from `runbooks/TEMPLATE.md` keeps the shape defined in one place: the
    file the ownership table names as its declaring mechanism.

    Args:
        workspace: The repository under audit.

    Returns:
        A pair of the required level-2 section titles and the required per-step level-4 headings.
    """
    if not workspace.template_path.is_file():
        return ((), ())
    text = workspace.template_path.read_text(encoding="utf-8", errors="replace")
    sections = tuple(dict.fromkeys(_SECTION_RE.findall(text)))
    steps = _STEP_RE.search(text)
    subsections = tuple(dict.fromkeys(_SUBSECTION_RE.findall(text[steps.start() :]))) if steps else ()
    return sections, subsections


def check_runbook_shape(workspace: Workspace) -> CheckResult:
    """Every Runbook carries the template's required headings, and ends with its verification.

    This is the verification `docs/OWNERSHIP.md` names for the "Runbook shape" resource class.

    Args:
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    sections, subsections = required_runbook_sections(workspace)
    if not sections:
        return skipped(
            "Runbook shape",
            defects.RUNBOOK_MISSING_SECTION,
            "Runbooks",
            f"{workspace.relative(workspace.template_path)} is absent, so the required shape is undefined",
        )
    files = workspace.runbook_files()
    findings: list[Finding] = []
    for path in files:
        relative = workspace.relative(path)
        text = path.read_text(encoding="utf-8", errors="replace")
        present = _SECTION_RE.findall(text)
        for section in sections:
            if section not in present:
                findings.append(
                    Finding(
                        defect=defects.RUNBOOK_MISSING_SECTION,
                        subject=relative,
                        detail=f"missing the required section '## {section}'",
                        location=relative,
                    )
                )
        if present and present[-1] != sections[-1]:
            findings.append(
                Finding(
                    defect=defects.RUNBOOK_MISSING_SECTION,
                    subject=relative,
                    detail=f"ends with '## {present[-1]}'; FR-5 requires it to end with '## {sections[-1]}'",
                    location=relative,
                )
            )
        for step in _STEP_RE.finditer(text):
            end = text.find("\n## ", step.end())
            next_step = _STEP_RE.search(text, step.end())
            if next_step is not None and (end == -1 or next_step.start() < end):
                end = next_step.start()
            block = text[step.end() : end if end != -1 else len(text)]
            block_subsections = _SUBSECTION_RE.findall(block)
            for subsection in subsections:
                if subsection not in block_subsections:
                    findings.append(
                        Finding(
                            defect=defects.RUNBOOK_MISSING_SECTION,
                            subject=f"{relative} — {step.group(0).lstrip('# ').strip()}",
                            detail=f"step is missing the required heading '#### {subsection}'",
                            location=relative,
                        )
                    )
    return result(
        "Runbook shape",
        defects.RUNBOOK_MISSING_SECTION,
        len(files),
        "Runbooks",
        findings,
        note=f"{len(sections)} required sections, {len(subsections)} required per-step headings",
    )


def check_layer_dependencies(workspace: Workspace) -> CheckResult:
    """Upward layer dependency: a layer directory referencing a higher-numbered layer.

    The stratified layers are the design's single enforceable claim, and until now nothing enforced
    it. A reference from `lN` to `lM` where `M > N` points upward and is a defect.

    Args:
        workspace: The repository under audit.

    Returns:
        The check result.
    """
    findings: list[Finding] = []
    examined = 0
    unreadable: list[str] = []
    for _tool, layer, directory in workspace.layer_directories():
        own = LAYERS.index(layer)
        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue
            relative = workspace.relative(path)
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                # NOT counted as examined. In a harness whose discipline is "report what you
                # examined", the count is the claim — a file that could not be read was not read,
                # and inflating the count is the quiet version of reporting a pass.
                unreadable.append(relative)
                continue
            examined += 1
            upward = sorted({token for token in _LAYER_TOKEN_RE.findall(text) if int(token) > own})
            if upward:
                findings.append(
                    Finding(
                        defect=defects.UPWARD_LAYER_DEPENDENCY,
                        subject=relative,
                        detail=f"sits at {layer} but references layer(s) {['l' + n for n in upward]}; "
                        "dependencies point only downward",
                        location=relative,
                    )
                )
    note = ""
    if unreadable:
        note = f"{len(unreadable)} file(s) not decodable as UTF-8 and therefore NOT examined: {sorted(unreadable)}"
    return result(
        "Layer dependency direction",
        defects.UPWARD_LAYER_DEPENDENCY,
        examined,
        "files under a layer directory",
        findings,
        note,
    )
