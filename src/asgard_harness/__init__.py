"""The Asgard convergence harness.

The repository states its own rules in two documents: `PROCEDURE-INDEX.md` enumerates every
Procedure the platform requires and lists the defect classes an audit must detect, and
`docs/OWNERSHIP.md` enumerates every configurable resource class and the defects *its* audit must
detect. This package makes those definitions executable.

Nothing here narrows a definition. Where a rule cannot be evaluated mechanically as written, the
check reports itself as skipped and says why — a silent pass is the failure mode the whole epic
exists to prevent.
"""

from asgard_harness.findings import AuditReport, CheckResult, CheckStatus, Finding
from asgard_harness.workspace import Workspace

__all__ = [
    "AuditReport",
    "CheckResult",
    "CheckStatus",
    "Finding",
    "Workspace",
    "__version__",
]

__version__ = "0.1.0"
