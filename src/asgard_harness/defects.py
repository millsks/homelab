"""The defect-class identifiers the harness detects.

Every identifier here corresponds to a defect class already **defined** in
`PROCEDURE-INDEX.md` § "Defects this Index reports" or in `docs/OWNERSHIP.md` § "Audit". The
identifier is what a self-check fixture asserts against, so the mapping from a written definition
to an executable detector is itself checkable rather than a matter of trust.
"""

from __future__ import annotations

from typing import Final

# --- PROCEDURE-INDEX.md, entry-level -------------------------------------------------------------

INCOMPLETE_PROCEDURE: Final = "incomplete-procedure"
STATUS_DISAGREES_WITH_FILESYSTEM: Final = "status-disagrees-with-filesystem"
ILLEGAL_STATUS_VALUE: Final = "illegal-status-value"
MISSING_MANUAL_VERIFICATION: Final = "missing-verification-on-manual-entry"
UNWRITTEN_MANUAL_HUMAN_FORM: Final = "unwritten-human-form-on-manual-entry"
MISMATCHED_MANUAL_LITERAL: Final = "mismatched-manual-literal"

# --- PROCEDURE-INDEX.md, namespace-level ---------------------------------------------------------

DUPLICATE_KEY: Final = "duplicate-key"
DUPLICATE_RUNBOOK_PATH: Final = "duplicate-runbook-path"
RETIRED_KEY_REUSED: Final = "retired-key-reused"

# --- PROCEDURE-INDEX.md, Index-to-story ----------------------------------------------------------

STORY_WITH_NO_ENTRY: Final = "story-with-no-entry"
ENTRY_WITH_NO_STORY: Final = "entry-with-no-story"
STORY_OVER_ENTRY_ALLOWANCE: Final = "story-over-entry-allowance"
STALE_PROVENANCE: Final = "stale-provenance"

# --- PROCEDURE-INDEX.md, cross-document ----------------------------------------------------------

BROKEN_BACK_REFERENCE: Final = "broken-back-reference"
UNFILLED_TEMPLATE_SENTINEL: Final = "unfilled-template-sentinel"
UNCOVERED_OWNERSHIP_CLASS: Final = "ownership-class-with-no-covering-procedure"
TOTALS_DISAGREE: Final = "totals-disagree-with-tables"
UNRECOMPUTED_TOTAL: Final = "totals-row-not-recomputed"

# --- docs/OWNERSHIP.md § Audit -------------------------------------------------------------------

TWO_OWNER_CLASS: Final = "two-owner-class"
ILLEGAL_OWNER_VALUE: Final = "illegal-owner-value"
MISSING_OWNERSHIP_VERIFICATION: Final = "ownership-row-without-verification"

# --- docs/OWNERSHIP.md § "Runbook shape" verification ---------------------------------------------

RUNBOOK_MISSING_SECTION: Final = "runbook-missing-required-section"

# --- Alert-source registration (AD-23) -----------------------------------------------------------

UNREGISTERED_ALERT_SOURCE: Final = "alert-source-row-unresolvable"

# --- Convergence (AD-3, NFR-3, AD-23) ------------------------------------------------------------

AUTOMATION_NOT_CONVERGED: Final = "automation-not-converged"
AUTOMATION_NOT_IDEMPOTENT: Final = "automation-not-idempotent"
CHECK_MODE_DIFF_NOT_EMPTY: Final = "check-mode-diff-not-empty"

# A check-mode run that ERRORED proves nothing about convergence, and must never be read as a
# clean run. This is the defect class that did not exist in the first cut of the harness: every
# parser set an exit code and no decision consulted it, so `tofu plan` in an uninitialised module,
# `kubectl diff` with no reachable cluster, and a missing binary all reported zero changes and
# passed. That is the same shape as story 1.1's `&& cmd || echo` gate guard, one layer down.
AUTOMATION_CHECK_FAILED: Final = "automation-check-run-failed"
AUTOMATION_NO_CHECK_MODE: Final = "automation-has-no-known-check-mode"

# --- Repository-stored secret material (AD-15, AD-24) --------------------------------------------
#
# The ownership row for "Repository-stored secret material" names its verification as "a commit-time
# check that rejects plaintext and names the offending path". These are the classes that check
# reports. It runs in the gate as well as at commit time: a pre-commit hook lives in `.git/hooks`,
# which no clone carries, so a rule enforced only there is a rule a fresh clone does not have.

PLAINTEXT_SECRET: Final = "plaintext-secret-in-repository"
UNENCRYPTED_DECLARED_PATH: Final = "declared-encrypted-path-in-plaintext"
UNDECLARED_ENCRYPTION_POLICY: Final = "encryption-policy-undeclared"

# --- docs/ADDRESS-PLAN.md § "What the check enforces" ---------------------------------------------
#
# The address plan is a `docs/ record`: nothing executes it, so the only thing a machine can say
# about it today is whether it agrees with itself. The plan's other verification — reconciliation
# against Directory DNS and against what hosts actually answer — needs a directory and running
# hosts, which stories 4.3 and 2.3 build. That gap is recorded in the deferred-work ledger rather
# than closed by implementing something weaker under the same name.

ADDRESS_PLAN_COLLISION: Final = "address-plan-collision"
ADDRESS_PLAN_IN_DHCP_POOL: Final = "address-plan-inside-dhcp-pool"
ADDRESS_PLAN_RESERVATION_CONSUMED: Final = "address-plan-reservation-consumed"
ADDRESS_PLAN_NODE_ON_ONE_SEGMENT: Final = "address-plan-node-on-one-segment"
ADDRESS_PLAN_ROUTE_ON_ISOLATED: Final = "address-plan-route-on-isolated-segment"
ADDRESS_PLAN_ILLEGAL_KIND: Final = "address-plan-illegal-kind"
ADDRESS_PLAN_RANGE_COVERAGE: Final = "address-plan-range-coverage"
ADDRESS_PLAN_UNDECLARED_ADDRESS: Final = "address-plan-address-in-no-declared-range"

# --- Layer discipline (the design's single enforceable claim) ------------------------------------

UPWARD_LAYER_DEPENDENCY: Final = "upward-layer-dependency"

# --- The self-check itself -----------------------------------------------------------------------

SELF_CHECK_DID_NOT_FIRE: Final = "self-check-fixture-did-not-fire"
