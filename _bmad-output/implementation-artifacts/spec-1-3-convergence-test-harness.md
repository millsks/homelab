---
title: 'Story 1.3 — Convergence test harness'
type: 'feature'
created: '2026-08-29'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'd1d5d51598dca02a866ce1373572001a2dd06b14'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every claim the repository makes about itself is currently checked by throwaway scripts or by eye. The Procedure Index defines nine defect classes and nothing detects any of them; the ownership table defines four and nothing detects those either. Two stories have now shipped defects that only adversarial review caught — an index contradicting its own status definitions, a gate reporting success while a linter failed.

**Approach:** Build the harness that makes those definitions executable, and prove it fails. A harness whose failure path is never exercised is the same defect as a gate that cannot fail — which this repository has already shipped once.

## Boundaries & Constraints

**Always:**
- Every defect class already **defined** in `PROCEDURE-INDEX.md` and `docs/OWNERSHIP.md` gets a detector. Definitions without detection are what this story exists to end.
- The harness proves its own failure path: a known-bad fixture is injected, the harness is asserted to exit non-zero, and the fixture is removed. An acceptance criterion of "the check passes" is insufficient — story 1.1 satisfied exactly that criterion with a broken gate.
- Convergence and idempotence are checked by running Automation twice and asserting no changes on the second run. No Automation exists yet, so both are proven against fixtures now and become real when the first role lands.
- Push-based layers get a scheduled check-mode run whose non-empty diff exits non-zero and is recorded. It is registered as an alert source; it does not depend on alerting existing.
- The harness is itself covered by tests. A checker nobody checks is the recursion this repository keeps falling into.
- Failures name the offending key, path, or row. "Audit failed" is not a result.

**Ask First:**
- Any defect class the harness cannot implement as defined — report it rather than silently narrowing the definition.
- Relaxing a definition to make a detector pass.

**Never:**
- Do not weaken a definition in `PROCEDURE-INDEX.md` or `docs/OWNERSHIP.md` to make a check pass. A disagreement between definition and reality is the finding, not the bug.
- Do not write Runbook or Automation content for any Procedure — the harness checks Procedures; it does not author them.
- Do not create `.sops.yaml`, `docs/ESCROW.md`, or `docs/ADDRESS-PLAN.md` — story 1.4 and later own those.
- Do not wire alerting. Registration only.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Clean repository | Index agrees with filesystem and epics | Exit 0, counts reported | N/A |
| Entry status disagrees with disk | `planned` entry whose Automation exists | Exit non-zero, key named | Never auto-corrected |
| Story added to epics, no entry | 69th story appears | Exit non-zero, story named | N/A |
| Entry references a missing story | Story deleted from epics | Exit non-zero, key named | N/A |
| Duplicate key or runbook path | Two entries collide | Exit non-zero, both named | N/A |
| Ownership class with no Procedure | A `Runbook` row with no covering key | Exit non-zero, class named | N/A |
| Totals disagree with tables | Hand-edited count | Exit non-zero, both figures shown | N/A |
| Template sentinel outside template | A copied runbook still says `TEMPLATE-UNFILLED` | Exit non-zero, file named | Template itself exempt |
| Automation not idempotent | Second consecutive run reports changes | Exit non-zero, changed items named | N/A |
| Harness self-check | Known-bad fixture injected | Harness exits non-zero; fixture removed after | A passing self-check is a failure |

</frozen-after-approval>

## Code Map

- `PROCEDURE-INDEX.md` -- 68 entries, nine defect classes defined, provenance recorded at `f5471f8`; the primary input
- `docs/OWNERSHIP.md` -- 51 rows each carrying a covering Procedure key; four defect classes defined
- `_bmad-output/planning-artifacts/epics.md` -- 67 stories; the story-set equality source
- `runbooks/TEMPLATE.md` -- carries the `TEMPLATE-UNFILLED` sentinel and is exempt from discovery by path
- `pixi.toml:14` -- `check` task guards on `[ -d src ]` and currently skips; `lint` chain is where a new check joins
- `pyproject.toml` -- ruff and mypy configured, `_bmad-output` excluded; no `[project]` table today
- `_bmad-output/implementation-artifacts/deferred-work.md` -- entries naming this story: lint-index, the layer-dependency check, per-root×layer expected-empty mapping
- `spec-1-1-*.md`, `spec-1-2-*.md` -- both `done`; their Code Maps and Design Notes carry the gate-guard and index-format history

**Read-only:** `_bmad/`, `.claude/`, `.agents/`, `.bmad-loop/`.

## Tasks & Acceptance

**Execution:**
- [x] `src/` -- create the harness package with the index, ownership, and convergence checkers -- Python enters the repository here; a src layout activates the existing mypy task and matches the project standard
- [x] `tests/` -- unit tests per detector, including one asserting each detector fires on its own bad fixture -- a checker nobody checks is the recursion to avoid
- [x] `pixi.toml` -- add `test` and `cov` tasks, and join the harness to the `lint` chain -- closes the deferred gap where the standard task set was incomplete because nothing needed it
- [x] `pyproject.toml` -- pytest and coverage configuration -- the standard requires a coverage gate
- [x] `PROCEDURE-INDEX.md` -- register the check-mode detectors as alert sources; move `PROC-CONVERGENCE-HARNESS` from `incomplete` toward its real state -- the entry describing this story must reflect what this story built
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- mark the entries this story closes -- a ledger that only grows is not a ledger

**Acceptance Criteria:**
- Given a clean repository, when the harness runs, then it exits 0 and reports what it checked rather than only that it passed.
- Given each defect class defined in either document, when a fixture exhibiting it is injected, then the harness exits non-zero and names the offending key, path, or row.
- Given the harness, when its own test suite runs, then every detector has a test proving it fires, and coverage meets the project threshold.
- Given any Automation, when it is run twice consecutively, then the second run reports zero changes; proven against a fixture while no real Automation exists.
- Given a push-based layer, when its scheduled check-mode run finds a non-empty diff, then it exits non-zero and is recorded, and it is registered as an alert source without depending on alerting.
- Given `pixi run ci`, when it runs, then it includes the harness and exits 0.

## Design Notes

**This story turns the repository into a Python project, and that is a deliberate scope decision worth naming.** The harness cannot be a shell one-liner: it parses two Markdown tables, cross-references a third document, and compares against the filesystem. Written as throwaway scripts it would be exactly what stories 1.1 and 1.2 relied on — unversioned, untested, and re-derived each time.

A `src/` layout activates the `check` task that has been skipping since the workspace was created, and brings the `test` and `cov` tasks that were deliberately omitted when there was no code to run them against. The cost is real: this repository now has a test suite to maintain. The alternative — a checker with no tests, enforcing a discipline it does not itself follow — is the failure mode this whole epic exists to prevent.

## Verification

**Commands:**
- `pixi run ci` -- expected: exits 0, harness included in the chain
- `pixi run test` -- expected: all detector tests pass
- `pixi run cov` -- expected: coverage at or above the project threshold
- Inject each bad fixture in turn, run the harness -- expected: non-zero exit naming the defect; repository restored afterwards

**Manual checks:**
- Confirm no definition in `PROCEDURE-INDEX.md` or `docs/OWNERSHIP.md` was weakened to make a detector pass.
- Confirm the self-check removes its fixtures, leaving the working tree clean.
