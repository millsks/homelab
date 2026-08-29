---
title: 'Story 1.2 — Procedure Index and the dual-form contract'
type: 'feature'
created: '2026-08-28'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'c5cbf8d7c727b393bf1a96d17603679c173d42ad'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** "Every operational activity is documented" quantifies over a set nothing enumerates, so it cannot be checked and the two headline success measures — zero undocumented rebuild steps, and convergence holding for every Procedure — have no denominator. Separately, nothing defines what a Runbook must contain, so 66 remaining stories would each invent a shape.

**Approach:** Enumerate every Procedure the platform requires up front, derived from the story list rather than from what happens to exist, and give each entry a status so incompleteness is visible rather than implied. Pair it with a Runbook template that makes the runbook standard mechanical instead of remembered.

## Boundaries & Constraints

**Always:**
- The Index enumerates every Procedure the platform **requires**, not only those already built. An entry for unbuilt work is the normal case today and is what makes the denominator real.
- One Procedure per story, as the epic list already fixes. A story that genuinely needs two Procedures is a signal the story was mis-scoped — surface it rather than silently splitting.
- Every entry carries: stable key, title, owning layer, owning story, Runbook path, Automation path, and status.
- Status is a closed enumeration. An entry missing either half is `incomplete`, and that is a defect the Index reports rather than hides.
- Procedures whose Automation half does not exist **by decision** — physical work, hypervisor installation, appliance initial setup — are marked as deliberate, never as gaps. Their verification is still automated where possible.
- The Runbook template enforces all four requirements of the runbook standard: actual commands rather than delegation, expected output per checkpoint, bidirectional mapping to the Automation, and a failure-mode note on any step with a known way to break.
- The Automation side names its Runbook too. Define one convention for how a role, module, or manifest set declares the Runbook that explains it.

**Ask First:**
- Any status value beyond the closed set.
- Any Procedure in the Index that does not map to exactly one story.

**Never:**
- Do not build the audit that checks the Index — that is story 1.3. Define the defects it must detect; do not implement detection.
- Do not write Runbook or Automation content for any Procedure. This story writes the Index and the template only.
- Do not create `.sops.yaml`, `docs/ESCROW.md`, or `docs/ADDRESS-PLAN.md` — story 1.4 and later own those.
- Do not invent Procedures that no story requires.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Entry lookup | A Procedure key | One entry: layer, story, both paths, status | N/A |
| Both halves present | Runbook and Automation both exist | Status `complete` | N/A |
| One half missing | Runbook exists, Automation does not | Status `incomplete`, reported as a defect | Named, not hidden |
| Deliberately manual | Physical, hypervisor install, appliance setup | Status `manual-by-decision`, verification still named | Never counted as a gap |
| Not yet started | Neither half exists | Status `planned` with owning story | Normal today; the denominator |
| Story with no Procedure | A story producing no operational activity | Surface for human decision | Do not silently omit |

</frozen-after-approval>

## Code Map

- `PROCEDURE-INDEX.md` -- currently a stub deferring to this story; replaced wholesale
- `_bmad-output/planning-artifacts/epics.md` -- the 67 stories the Index derives from; the Phase 0 preamble fixes one-Procedure-per-story and names the three manual-only areas
- `docs/OWNERSHIP.md:21` -- closed Owner enumeration; the Index is a `docs/ record` and its row needs updating from stub to real
- `docs/OWNERSHIP.md:185` -- Audit section already defines two-owner and unowned defects; incomplete-Procedure is the third and belongs beside them
- `runbooks/l0-physical/` … `runbooks/l5-workloads/` -- exist, empty; the template lands at `runbooks/TEMPLATE.md`
- `README.md` -- points at the Index; needs the Index described as real rather than pending
- `.yamllint`, `pixi.toml` -- gate config; the Index is Markdown, which nothing in the gate lints (deferred finding)

**Read-only:** `_bmad/`, `.claude/`, `.agents/`, `.bmad-loop/`.

## Tasks & Acceptance

**Execution:**
- [x] `PROCEDURE-INDEX.md` -- replace the stub with the contract definition plus all 67 entries derived from the story list -- the story's substance; without the enumeration FR-1 stays uncountable
- [x] `runbooks/TEMPLATE.md` -- the Runbook template enforcing the four runbook-standard requirements -- makes the standard mechanical rather than remembered across 66 stories
- [x] `PROCEDURE-INDEX.md` -- define the Automation-side back-reference convention -- the contract is bidirectional; only defining one direction leaves the other to be invented
- [x] `docs/OWNERSHIP.md` -- update the Procedure Index row from stub to real, and add the incomplete-Procedure defect beside the two existing ones -- the audit story needs all three defined in one place
- [x] `README.md` -- describe the Index as the authoritative enumeration -- it is now the entry point for understanding what the platform requires

**Acceptance Criteria:**
- Given the Index, when its entries are counted, then there is exactly one per story in the epic list, and every entry names a story that exists.
- Given any entry, when it is read, then it carries a key, layer, owning story, Runbook path, Automation path, and a status from the closed set.
- Given the three deliberately-manual areas, when their entries are read, then each is `manual-by-decision` with its verification named, and none reads as a gap.
- Given the Runbook template, when it is compared against the runbook standard, then each of the four requirements has a corresponding section a writer cannot skip silently.
- Given a Runbook written from the template, when its Automation is located, then each names the other by path.
- Given `pixi run ci`, when it runs, then it passes.

## Design Notes

**The fork worth stating: the Index enumerates what the platform *requires*, not what it *has*.** Enumerating only built Procedures would make the Index grow to match reality and always report complete — which is precisely the unbounded-set problem that made FR-1 uncheckable before the PRD review rewrote it. Deriving from the story list means the Index is nearly all `planned` today, and that is correct: it is a work ledger whose incompleteness is the honest signal.

The consequence to accept: the Index changes whenever the story list changes. That is a feature — a story added without an Index entry is a Procedure nobody committed to writing.

## Verification

**Commands:**
- `pixi run ci` -- expected: exits 0
- `grep -c` entries in `PROCEDURE-INDEX.md` against story count in `epics.md` -- expected: both 67

**Manual checks:**
- Read the three `manual-by-decision` entries and confirm each names a verification rather than reading as an automation gap.
- Confirm the template's failure-mode section is required rather than optional, since it is the part a writer under time pressure drops first.
