---
procedure_key: PROC-CONVERGENCE-HARNESS
procedure_automation: pixi.toml
---

# Convergence test harness

**Procedure:** `PROC-CONVERGENCE-HARNESS` · **Automation:** [`pixi.toml`](../../pixi.toml) · **Index entry:** [`PROCEDURE-INDEX.md`](../../PROCEDURE-INDEX.md)

## Change log

| Date | Change | Commit |
| --- | --- | --- |
| 2026-08-29 | Story 1.3 — harness built, Runbook written, `PROC-CONVERGENCE-HARNESS` closed from `incomplete` to `complete` | `feat(asgard): convergence test harness` |

## Why this Procedure exists

Every claim the Repository makes about itself was, until this Procedure, checked by throwaway
scripts or by eye. [`PROCEDURE-INDEX.md`](../../PROCEDURE-INDEX.md) defines the defect classes an
audit must detect and [`docs/OWNERSHIP.md`](../../docs/OWNERSHIP.md) defines four more; nothing
detected any of them. Two stories shipped defects that only adversarial review caught — an index
contradicting its own status definitions, and a gate reporting success while a linter failed.

This Procedure makes those written definitions executable, and — as importantly — proves they can
fail. A gate that cannot fail is worse than no gate, because it converts an unchecked claim into a
checked-looking one. If this Procedure is absent or wrong, every later story's "done" is an
assertion rather than a result.

## Scope and boundaries

**Declares:** the convergence gate itself — its tasks, its linter configuration, its dependency
pins, and the harness package that implements the audit. This is the "Convergence tooling" resource
class in [`docs/OWNERSHIP.md`](../../docs/OWNERSHIP.md), owned by `Repository tooling`, plus the
"Control node" class that runs it.

**Does not declare:**

- What each defect class *is*. The Index and the ownership table define them; the harness reads the
  definitions out of those documents at run time and never restates one. Changing a rule means
  changing the document.
- Any Procedure's Runbook or Automation content. The harness checks Procedures; it does not author
  them.
- Notification. Detectors register as alert sources in the Index's *Alert sources* table; wiring
  them to notification is `PROC-ALERTING` (story 13.5). Registration does not depend on alerting
  existing.
- Encryption at rest for Repository-stored secrets — `PROC-REPO-SECRETS`.

## Preconditions

| Precondition | Made true by | How to confirm |
| --- | --- | --- |
| A control node with the Repository cloned | `PROC-CONVERGENCE-HARNESS` (this Procedure, "Control node" class) | `git -C <repo> rev-parse --show-toplevel` prints the repository root |
| `pixi` on `PATH` | Operator workstation setup; see the README onboarding | `pixi --version` prints a version |
| The pinned environment materialised | This Procedure, step 1 | `pixi list python` shows the pinned interpreter |
| No credentials of any kind, **for the audit and self-check** | — | Steps 2, 3, and 6 read committed documents and the working tree only. Nothing is escrowed for them. |
| Reachability of the managed hosts, **for `drift` and `converge` only** | The Procedures that build those hosts | Steps 4 and 5 shell out to `ansible-playbook`, `tofu plan`, and `kubectl diff`. They are scheduled runs, never part of the merge gate, and they are the only steps here that need credentials. |

## Procedure

### Step 1 — Materialise the pinned environment

#### Why

The harness is Python, and AD-20 prohibits `latest`: the interpreter and every tool are pinned in
[`pixi.toml`](../../pixi.toml) and locked in `pixi.lock`. Installing from the lock file rather than
re-solving is what makes a run on the control node and a run in CI the same run.

#### Command

```sh
pixi install --locked
```

#### Expected output

```text
✔ The default environment has been installed.
```

A line reporting that the lock file is out of date is a failure of this step, not a warning: it
means the manifest and the lock disagree and the two machines would not install the same thing.

#### Automation task

`pixi.toml` task `bootstrap` — and, for every subsequent step, the `depends-on` chain of the task
named there.

#### Failure modes

- **Looks like:** `the lock file is not up-to-date with the manifest`. **Check first:** whether a
  dependency was added to `pixi.toml` without re-running `pixi install` and committing `pixi.lock`.
- **Looks like:** TLS failures resolving `conda-forge`. **Check first:** `.pixi/config.toml` sets
  `tls-root-certs = "system"`; a control node behind an inspecting proxy needs its root in the OS
  store.

### Step 2 — Run the audit

#### Why

The audit is the half of the harness that reads. It parses the Index, the ownership table, and the
story list, cross-references all three against the working tree, and reports every defect class
both documents define — naming the offending key, path, or row for each. It reports what it
examined, not only that it passed: a count is the difference between a check and a claim.

#### Command

```sh
pixi run audit
```

#### Expected output

```text
2026-08-29T00:00:00Z [info     ] [PASS] Status enumeration: 68 entries examined command=audit
...
2026-08-29T00:00:00Z [info     ] [SKIP] Unowned resource class: 0 rows examined — not mechanically decidable: ... command=audit
2026-08-29T00:00:00Z [info     ] 21 checks run: 20 passed, 0 failed, 1 skipped; 0 defect(s) named. command=audit
```

Output is rendered by `structlog`, so each line carries a timestamp, a level, and `command=audit`;
`--json` emits the whole report as one machine-readable event instead.

Every check is `[PASS]`, `[SKIP]`, or `[FAIL]`. **Exactly one** `[SKIP]` is expected — the
unowned-class rule, which is not mechanically decidable and says so. That number is pinned by a
test: a `[SKIP]` does not fail the gate, so a detector quietly degrading to one — a shallow clone
silencing the provenance check, say — would leave the gate green with a rule no longer enforced.
A `[FAIL]` line is followed by one indented line per defect, each naming its subject.

This step reaches no managed system and needs no credential. Keep it that way: `drift` and
`converge` below are the runs that shell out to real tools, and they are scheduled rather than
part of the gate.

#### Automation task

`pixi.toml` task `audit`.

#### Failure modes

- **Looks like:** `totals-disagree-with-tables`. **Check first:** an entry was added or a status
  moved without updating the Totals section. The tables are authoritative; Totals is recomputed
  from them.
- **Looks like:** `stale-provenance`. **Check first:** `epics.md` changed. A human re-derives the
  Index and updates the provenance line; the audit never re-derives it.
- **Looks like:** `[SKIP] Provenance of the story list`. **Check first:** whether the checkout is
  shallow. A shallow clone cannot name the commit that last touched a file, and the audit reports
  that it could not rather than passing.

### Step 3 — Prove the harness can fail

#### Why

An acceptance criterion of "the check passes" is insufficient — story 1.1 satisfied exactly that
criterion with a broken gate. The self-check injects a known-bad fixture for every defect class the
harness claims to detect, asserts the audit exits non-zero *and names that defect class*, and
deletes the fixture. A fixture that fails to provoke its defect is itself reported as a failure.

Fixtures are applied to a throwaway copy of the Repository, never to the working tree. That is
deliberate: a self-check that mutates the tree it is checking leaves a dirty tree behind whenever
it is interrupted.

#### Command

```sh
pixi run selfcheck
git status --porcelain
```

#### Expected output

```text
2026-08-29T00:00:00Z [info     ] [PASS] Self-check baseline: 1 unmutated copies examined command=selfcheck
2026-08-29T00:00:00Z [info     ] [PASS] Fixture — an entry's status is outside the closed set: ... — named PROC-REPO-SECRETS command=selfcheck
...
2026-08-29T00:00:00Z [info     ] [PASS] an errored tofu plan is a failure, not a clean run: 1 fixtures examined command=selfcheck
2026-08-29T00:00:00Z [info     ] 37 checks run: 37 passed, 0 failed, 0 skipped; 0 defect(s) named. command=selfcheck
```

The fixtures come in two kinds. Most mutate a copied document and assert the audit names the defect.
The rest are *runner* fixtures with no filesystem at all: they script a check-mode run — clean,
changed, or **errored** — and assert the convergence logic decides correctly. The errored cases
exist because the first cut of this harness read a failed `tofu plan` as a run that found no
changes, which is the same defect as a gate guard that reports success on failure.

A fixture that needs git — only the stale-provenance one does — reports `[SKIP]` when git cannot
answer, rather than passing. Comparing the Index against a hash the Index itself supplied would be
a fixture proving itself.

`git status --porcelain` prints nothing. The self-check leaves the working tree exactly as it found
it.

#### Automation task

`pixi.toml` task `selfcheck`.

#### Failure modes

- **Looks like:** `self-check-fixture-did-not-fire`. **Check first:** whether the detector was
  narrowed, or whether the fixture's target moved — a fixture that can no longer find the row it
  edits reports why, and that reason is the finding.
- **Looks like:** the baseline itself failing. **Check first:** the audit output from step 2. No
  fixture proves anything while the unmutated copy already fails.

### Step 4 — Run the scheduled check-mode drift detection

#### Why

AD-23: the push-based layers have no reconciliation loop, so drift on them is invisible until
something breaks. A scheduled check-mode run makes it visible — a non-empty diff exits non-zero and
is recorded to a file, so the run is evidence rather than a console message somebody watched go by.
No Automation exists for those layers yet, so the run reports zero targets today and says so.

#### Command

```sh
pixi run drift
cat drift-record.json
```

#### Expected output

```text
[SKIP] Scheduled drift detection: 0 push-based Automation halves examined — the only Automation half
present under [... the three push-based layers, listed by name ...] is repository tooling —
PROC-CONVERGENCE-HARNESS (pixi.toml) — whose check-mode run IS this harness ...
```

`drift-record.json` holds the same result as JSON, including the exit code. Once the first
push-based Automation lands, this step reports one line per Automation, and a non-empty diff names
the changed items.

**A run that failed is not a run that found nothing.** Each tool signals "changes present" with a
different exit code from the one it uses for failure — `tofu plan -detailed-exitcode` uses 2 for
changes and 1 for an error, `kubectl diff` uses 1 for differences and above 1 for an error, and
`ansible-playbook --check` reports changes in the play recap so any non-zero exit is a failure. The
harness reads each convention and reports a failed run as a defect naming the tool, the exit code,
and the command. It never reports it as converged.

#### Automation task

`pixi.toml` task `drift`.

#### Failure modes

- **Looks like:** `check-mode-diff-not-empty`. **Check first:** the named items. A non-empty diff
  means a running system was changed outside the Repository. AD-4: the change is promoted into the
  Repository or reverted — never accommodated by relaxing the Automation.
- **Looks like:** `automation-check-run-failed`. **Check first:** the exit code and command in the
  finding. The run proves nothing — it is neither converged nor drifted — and must be re-run once
  the tool works. An uninitialised OpenTofu module and an unreachable cluster both land here.
- **Looks like:** `automation-has-no-known-check-mode`. **Check first:** whether a new Automation
  mechanism was introduced without a runner in `asgard_harness.convergence`. The target was **not**
  checked and is reported by name rather than skipped past.

### Step 5 — Run the scheduled convergence and idempotence check

#### Why

AD-3 makes convergence the definition of done: Automation run against a system built by hand from
its Runbook reports **zero** changes. NFR-3 adds that a second consecutive run also reports zero.
These are two separate claims about two separate runs, and this step checks both — the first run
for convergence, the second for idempotence. Checking only the second and calling it both is how a
gap gets papered over.

Like drift, this reaches real hosts, so it is scheduled and is deliberately not in the gate.

#### Command

```sh
pixi run converge
```

#### Expected output

```text
[SKIP] Convergence and idempotence: 0 Automation halves examined — the only Automation half present
is repository tooling — PROC-CONVERGENCE-HARNESS (pixi.toml) — whose check-mode run IS this harness,
so running it against itself would prove nothing about convergence ...
```

The skip reason names what was excluded and why. "No Automation half exists" would be untrue: one
is declared and present, and the reason it is not run is a decision, not an absence.

#### Automation task

`pixi.toml` task `converge`.

#### Failure modes

- **Looks like:** `automation-not-converged`. **Check first:** the named items on the *first* run.
  The system does not match what the Repository declares. FR-3: this is a documentation defect
  closed at discovery, never accommodated by weakening the Automation.
- **Looks like:** `automation-not-idempotent`. **Check first:** the named items on the second run.
  A task that reports a change every time it runs is usually a command module with no `changed_when`
  or a template rewritten with fresh timestamps.

### Step 6 — Run the whole gate

#### Why

The gate is the definition of done. It chains the linters, the validators, the harness's own test
suite, the audit, and the self-check, so that "it passed on my machine" and "it passed in CI" mean
the same thing. Running it before every commit is the point at which a defect is cheap.

#### Command

```sh
pixi run ci
```

#### Expected output

```text
CI gate passed
```

Any step exiting non-zero stops the chain, and the failing step names itself. A guarded step that
finds nothing to do prints that it skipped — never nothing.

#### Automation task

`pixi.toml` task `ci`, and the tasks in its `depends-on` chain.

#### Failure modes

- **Looks like:** the gate passing while a step visibly errored. **Check first:** whether a task
  guard uses `dir && cmd || echo`. That shape reports success on real failure and is prohibited;
  guards use an explicit `if`.
- **Looks like:** `mypy` reporting no files. **Check first:** whether `src/` is present. The `check`
  task guards on it, and a guard that skips is reported, not silent.

## Rollback

The harness only ever reads: the audit and self-check read files, and the scheduled runs invoke
their tools in **check mode**, which computes a diff without applying it. There is nothing to undo
on a failed run. Rolling back the *harness itself* is an ordinary revert of the commit that changed it,
followed by `pixi install --locked` to restore the pinned environment.

One thing cannot be undone by reverting: a defect the harness reported has already been observed.
Reverting the detector does not unfind it. A finding is closed by fixing the Repository or by a
human changing the definition in the document that states it — never by removing the check.

## Alert sources registered

Three, all registered in the *Alert sources* table of
[`PROCEDURE-INDEX.md`](../../PROCEDURE-INDEX.md) in the same change that built them:

- `pixi run drift` — the scheduled check-mode run over the push-based layers.
- `pixi run converge` — the scheduled convergence and idempotence run.
- `pixi run audit` — the Index and ownership audit.

All three are registered and unwired. Story 13.5 consumes that table and wires them to notification;
this Procedure does not depend on alerting existing.

## Verification

**Command:**

```sh
pixi run ci && git status --porcelain
```

**Expected output:**

```text
CI gate passed
```

`git status --porcelain` prints nothing: the gate, including the self-check, leaves the working
tree clean.

**Convergence check** — AD-3: run the Automation against the system just built by hand.

```sh
pixi run audit
```

Expected: **zero changes**. A non-zero result is a documentation defect against this Runbook,
closed at discovery. It is never accommodated by weakening the Automation (FR-3, NFR-5: the
Automation is authoritative for *what*, this Runbook for *why*).

**Idempotence check** — NFR-3: run the Automation a second time. Expected: zero changes again.

```sh
pixi run audit && pixi run audit
```

The audit is a pure reader, so idempotence is structural rather than incidental: it has no write
path that a second run could take differently.
