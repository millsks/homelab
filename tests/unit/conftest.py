"""A miniature repository the unit tests mutate.

The detectors are tested against a small synthetic workspace rather than against the real
repository, for two reasons: a unit test that depends on the real Index fails whenever the Index
changes for unrelated reasons, and a synthetic baseline can be made deliberately clean so that each
test's mutation is the only difference. Proof that the detectors fire against the *real* documents
is the integration suite's job.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from asgard_harness.workspace import Workspace

MINI_COMMIT = "abc1234"

MINI_INDEX = """# Procedure Index

**Derived from:** [`epics.md`](epics.md) at commit `abc1234` (2026-01-01).

### Status — a closed enumeration

| Status | Means |
| --- | --- |
| `planned` | Neither half exists yet. |
| `incomplete` | One half exists and the other does not. |
| `complete` | Both halves exist. |
| `manual-by-decision` | The Automation half does not exist by decision. |

**Retired keys:** none yet.

## One Procedure per story, and the one exception

| Story | Split across | Entries | Reason |
| --- | --- | --- | --- |
| 1.2 | `Runbook` and `Ansible` | `PROC-TWO-A`, `PROC-TWO-B` | two owners |

## Deliberately manual work

| Key | Story | Why no Automation | Verification | Human form written? | Provisional? |
| --- | --- | --- | --- | --- | --- |
| `PROC-TWO-A` | 1.2 | physical work | a port probe | No | No |
| `PROC-MANUAL` | 1.3 | `docs/ record` | a read of the record | Yes — `docs/MANUAL.md` | No |

## The Index

### Epic 1 — Mini

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-ONE` | One | `l0-physical` | 1.1 | `runbooks/l0-physical/one.md` | `ansible/l0-physical/one.yml` | `planned` |
| `PROC-TWO-A` | Two (manual) | `l0-physical` | 1.2 | `runbooks/l0-physical/two-a.md` | none — by decision | `manual-by-decision` |
| `PROC-TWO-B` | Two (automated) | `l1-hypervisor` | 1.2 | `runbooks/l1-hypervisor/two-b.md` | `ansible/l1-hypervisor/two-b.yml` | `planned` |
| `PROC-MANUAL` | Manual | `l1-hypervisor` | 1.3 | `docs/MANUAL.md` | none — by decision | `manual-by-decision` |

## Alert sources

| Source | Registering story | Wired by | Status |
| --- | --- | --- | --- |
| `mini drift` | 1.1 | 1.3 | Registered, unwired |

## Totals

| | Count |
| --- | --- |
| Stories in [`epics.md`](epics.md) at `abc1234` | 3 |
| Entries in this Index | 4 |
| Stories carrying two entries under the two-owner exception | 1 |
| `complete` | 0 |
| `incomplete` | 0 |
| `manual-by-decision` | 2 |
| `planned` | 2 |
| Human forms written | 1 |

Per layer: `l0-physical` 2 · `l1-hypervisor` 2.

Nothing follows.
"""

MINI_OWNERSHIP = """# Declarative Ownership

### Legal Owner values

| Owner value | Means | Declarations live in |
| --- | --- | --- |
| `Ansible` | Push configuration | `ansible/` |
| `Runbook` | Human-executed | `runbooks/` |
| `docs/ record` | Human-maintained | `docs/` |
| `Delegated` | Owned transitively | co-located |

## L0 — Physical

| Resource class | Owner | Declaring mechanism | Verification | Procedure | Notes |
| --- | --- | --- | --- | --- | --- |
| Racking and cabling | `Runbook` | `runbooks/l0-physical/` | Manual, against the cabling map | `PROC-TWO-A` | |
| Host OS configuration | `Ansible` | `ansible/l0-physical/` | Automated: check-mode run | `PROC-ONE`, `PROC-TWO-B` | |

## Cross-cutting

| Resource class | Owner | Declaring mechanism | Verification | Procedure | Notes |
| --- | --- | --- | --- | --- | --- |
| The record itself | `docs/ record` | `docs/MANUAL.md` | Automated: the audit | `PROC-MANUAL` | |
| Component version pins | `Delegated` | co-located | Automated: pin comparison | `Delegated` — whatever covers the pinned class | |
"""

MINI_SOPS = """---
# Procedure: PROC-MINI — runbook: runbooks/l0-physical/mini.md
creation_rules:
  - path_regex: (^|/)[^/]+\\.sops\\.ya?ml$
    age: age1miniexamplerecipient
"""
"""The miniature encryption policy.

The mini repository needs one because `run_audit` enforces the policy's presence: a workspace with
no `.sops.yaml` is a defect, which is the whole point of that detector, and a baseline that trips it
would make every other unit test fail for an unrelated reason.
"""

MINI_ADDRESS_PLAN = """# Address Plan

## Segments

| Segment | Network | Mask | Gateway | Isolated | Purpose |
| --- | --- | --- | --- | --- | --- |
| `data` | `10.0.0.0/29` | `255.255.255.248` | `10.0.0.1` | no | Bulk traffic. |
| `membership` | `10.9.9.0/29` | `255.255.255.248` | none — no route off-segment | yes | Membership only. |

## Address ranges

| Range | Segment | First | Last | Type | Purpose |
| --- | --- | --- | --- | --- | --- |
| `data-network` | `data` | `10.0.0.0` | `10.0.0.0` | `reserved` | Network address. |
| `data-edge` | `data` | `10.0.0.1` | `10.0.0.1` | `allocatable` | The router. |
| `data-hosts` | `data` | `10.0.0.2` | `10.0.0.3` | `allocatable` | Hosts. |
| `data-growth` | `data` | `10.0.0.4` | `10.0.0.4` | `reserved` | Growth: a third host. |
| `data-dhcp` | `data` | `10.0.0.5` | `10.0.0.6` | `dhcp-pool` | The router hands these out. |
| `data-broadcast` | `data` | `10.0.0.7` | `10.0.0.7` | `reserved` | Broadcast address. |
| `membership-network` | `membership` | `10.9.9.0` | `10.9.9.0` | `reserved` | Network address. |
| `membership-nodes` | `membership` | `10.9.9.1` | `10.9.9.3` | `allocatable` | Node membership interfaces. |
| `membership-growth` | `membership` | `10.9.9.4` | `10.9.9.6` | `reserved` | Growth: a third node. |
| `membership-broadcast` | `membership` | `10.9.9.7` | `10.9.9.7` | `reserved` | Broadcast address. |

## Allocations

| Address | Segment | Holds | Kind | Interface | Traffic class | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `10.0.0.1` | `data` | `mini-router` | `gateway` | Its LAN interface | Outbound | |
| `10.0.0.2` | `data` | `node-a` | `node` | Adapter | Bulk | |
| `10.0.0.3` | `data` | `node-b` | `node` | Adapter | Bulk | |
| `10.9.9.2` | `membership` | `node-a` | `node` | Onboard | Membership | |
| `10.9.9.3` | `membership` | `node-b` | `node` | Onboard | Membership | |

## Kinds — a closed enumeration

| Kind | Means |
| --- | --- |
| `node` | Homed on every declared segment. |
| `gateway` | The default route off a segment. |
| `appliance` | Single-homed on the data segment. |
"""
"""The miniature address plan.

Deliberately tiny — two `/29` segments — because the coverage detector requires the declared ranges
to tile their segment exactly, and a `/24` would need ten rows per segment to say the same thing.
"""

MINI_EPICS = """# Mini epics

### Story 1.1: One

Text.

### Story 1.2: Two

Text.

### Story 1.3: Manual

Text.
"""

MINI_TEMPLATE = """---
procedure_key: TEMPLATE-UNFILLED
procedure_automation: TEMPLATE-UNFILLED
---

# Title

## Why this Procedure exists

## Procedure

### Step 1 — do the thing

#### Why

#### Command

#### Expected output

#### Automation task

#### Failure modes

## Rollback

## Verification
"""


def build_mini_repo(root: Path) -> Workspace:
    """Write the miniature repository into a directory.

    Args:
        root: The directory to build into.

    Returns:
        A workspace over it.
    """
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / "_bmad-output" / "planning-artifacts").mkdir(parents=True, exist_ok=True)
    (root / "runbooks" / "l0-physical").mkdir(parents=True, exist_ok=True)
    (root / "runbooks" / "l1-hypervisor").mkdir(parents=True, exist_ok=True)
    (root / "ansible" / "l0-physical").mkdir(parents=True, exist_ok=True)
    (root / "PROCEDURE-INDEX.md").write_text(MINI_INDEX, encoding="utf-8")
    (root / ".sops.yaml").write_text(MINI_SOPS, encoding="utf-8")
    (root / "docs" / "OWNERSHIP.md").write_text(MINI_OWNERSHIP, encoding="utf-8")
    (root / "docs" / "ADDRESS-PLAN.md").write_text(MINI_ADDRESS_PLAN, encoding="utf-8")
    (root / "docs" / "MANUAL.md").write_text("# Manual record\n", encoding="utf-8")
    (root / "_bmad-output" / "planning-artifacts" / "epics.md").write_text(MINI_EPICS, encoding="utf-8")
    (root / "runbooks" / "TEMPLATE.md").write_text(MINI_TEMPLATE, encoding="utf-8")
    return Workspace(root=root)


@pytest.fixture
def mini(tmp_path: Path) -> Workspace:
    """A clean miniature repository, rebuilt for every test."""
    return build_mini_repo(tmp_path / "mini")


@pytest.fixture
def mini_commit() -> str:
    """The commit the miniature Index records deriving from."""
    return MINI_COMMIT
