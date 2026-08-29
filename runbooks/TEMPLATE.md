---
procedure_key: TEMPLATE-UNFILLED
procedure_automation: TEMPLATE-UNFILLED
---

<!--
  RUNBOOK TEMPLATE — copy this file to runbooks/<layer>/<slug>.md and fill it in.

  Delete the HTML comments as you go. Do NOT delete a heading. Every heading below is required by
  AD-3's runbook standard, and a Runbook missing one is an incomplete Procedure that story 1.3's
  audit reports by name. If a required section genuinely does not apply, write the reason under the
  heading — never remove the heading, because a removed heading is indistinguishable from a
  forgotten one.

  ── FIRST EDIT: THE FRONT MATTER ───────────────────────────────────────────────────────────────
  Both fields read TEMPLATE-UNFILLED. Replace both. That literal is a sentinel, not a placeholder
  you may leave in place: PROCEDURE-INDEX.md defines `TEMPLATE-UNFILLED` appearing in any file
  other than this one as a defect, so a copied-and-forgotten front matter is grep-visible instead
  of shipping a Runbook that points at a Procedure which does not exist.

    procedure_key         — the key from PROCEDURE-INDEX.md, exactly as written there.
    procedure_automation  — the Automation path from PROCEDURE-INDEX.md, exactly as written there,
                            or the literal `none — by decision` for a manual-by-decision Procedure.
                            The Automation names this file back; see "The dual-form contract" in
                            PROCEDURE-INDEX.md for how each tool declares it.

  The Index — not this file — is authoritative for owning layer, owning story, and status.
  Duplicating them here creates two places to change and one place to forget.

  ── SECOND EDIT: THE LINK DEPTH ────────────────────────────────────────────────────────────────
  The links in the header line below are written with ONE `../`, which is correct from this
  template's own location at runbooks/TEMPLATE.md. Your copy lives one directory deeper, at
  runbooks/<layer>/<slug>.md, so every `../` becomes `../../`:

      this file           runbooks/TEMPLATE.md            ../PROCEDURE-INDEX.md
      your copy           runbooks/l3-platform/foo.md     ../../PROCEDURE-INDEX.md

  The Automation is a code span rather than a link here on purpose: the path it will hold does not
  exist yet, and a template cannot ship a link to a file nobody has written. Make it a link once
  the Automation exists, at the ../../ depth above.

  The template is committed with working links rather than with the depth its copies need, because
  a repository that ships dead links teaches that dead links are normal.
-->

# <Procedure title — the owning story's title from epics.md, verbatim>

**Procedure:** `<PROC-KEY>` · **Automation:** `<automation path, copied from the Index>` · **Index entry:** [`PROCEDURE-INDEX.md`](../PROCEDURE-INDEX.md)

## Change log

<!--
  NFR-4: a change to a system and a change to its Procedure land together. One line per change:
  what changed, and the commit that carried both. Kept at the top so the operational sections end
  with the verification, as FR-5 requires.
-->

| Date | Change | Commit |
| --- | --- | --- |
| | | |

## Why this Procedure exists

<!--
  NFR-2: Runbooks state reasoning, not only commands. A step whose purpose is unstated cannot be
  evaluated when conditions differ from the day it was written. Two or three sentences: what this
  Procedure makes true, and what breaks if it is absent or wrong.
-->

## Scope and boundaries

<!--
  What this Procedure declares, and — as importantly — what it deliberately does not, naming the
  Procedure that does instead. AD-22: a class with two owners is a defect the convergence harness
  structurally cannot detect, so the exclusions are load-bearing rather than tidiness.
-->

**Declares:**

**Does not declare:** <!-- name the owning Procedure for each exclusion -->

## Preconditions

<!--
  What must already be true before step 1. Name the Procedures that make each true, by key, so an
  operator arriving mid-rebuild can walk backwards. Include credentials needed and where they are
  escrowed (AD-24).
-->

| Precondition | Made true by | How to confirm |
| --- | --- | --- |
| | | |

## Procedure

<!--
  Copy the "### Step 1" block below once per step. The four requirements of the runbook standard
  are the four `####` headings inside it. They are headings rather than bold labels so that a
  missing one is a missing heading — visible to a reader skimming the outline, and detectable by
  story 1.3's audit without parsing prose.
-->

### Step 1 — <what this step accomplishes>

#### Why

<!-- The reasoning, not the restated command. -->

#### Command

<!--
  REQUIREMENT 1 OF 4 — actual commands, not delegation.

  State the command the Automation issues, in the order it issues it. "Run the playbook" does NOT
  satisfy this standard: this Runbook is worthless at the one moment it is needed, which is when
  that Automation has just failed. If you find yourself writing a step that delegates, the step is
  not written yet.
-->

```sh
```

#### Expected output

<!--
  REQUIREMENT 2 OF 4 — expected output at each checkpoint.

  State what the command prints when it worked, closely enough that a divergence is locatable
  rather than merely detectable. "It should succeed" locates nothing.
-->

```text
```

#### Automation task

<!--
  REQUIREMENT 3 OF 4 — bidirectional mapping.

  Name the Automation task that performs this step, by that task's `name:` value. The Automation
  task names this section back. A failed task must lead the operator to the paragraph explaining
  what it was attempting.

  For a manual-by-decision Procedure, write: Not applicable — no Automation half by decision.
-->

`<the task name: value in the Automation that performs this step>`

#### Failure modes

<!--
  REQUIREMENT 4 OF 4 — a failure-mode note on every step with a known way to break.

  This is the section a writer under time pressure drops first, which is why it is a required
  heading on every step rather than an optional appendix. If a step has no known failure mode,
  write the literal line `No known failure mode.` so that dropping it is visible rather than
  silent.
-->

- **Looks like:** … **Check first:** …

<!-- Repeat "### Step N" for each step. Delete this comment when the last step is written. -->

## Rollback

<!--
  How to get back to the prior state, and what cannot be undone. AD-20: each layer's Procedure
  states its own rollback. "Restore from backup" is a rollback only if the restore has actually
  been executed (AD-21).
-->

## Alert sources registered

<!--
  AD-23: any scheduled check-mode run, renewal check, or backup check this Procedure introduces is
  an alert source. Add its row to the "Alert sources" table in PROCEDURE-INDEX.md in the same
  change that builds the detector — story 13.5 consumes that table to wire notification, it does
  not populate it. If this Procedure introduces no detector, write "None."
-->

## Verification

<!--
  FR-5: every Runbook ENDS with a verification whose expected output is stated. This is the last
  section on purpose — nothing operational follows it, and the change log sits at the top so it
  cannot displace this one from the end.

  The verification is identical whichever path performed the work — by hand from this Runbook, or
  by the Automation. If the two verifications differ, one of them is not verifying the Procedure.

  For a manual-by-decision Procedure this section carries the whole weight: execution being manual
  never excuses the verification from being automated wherever a machine can observe the result.
-->

**Command:**

```sh
```

**Expected output:**

```text
```

**Convergence check** — AD-3: run the Automation against the system just built by hand.

<!--
  MANUAL-BY-DECISION PROCEDURES: replace this block and the idempotence check below with the
  literal line

      Not applicable — no Automation half by decision.

  Deleting them instead leaves two empty sections that read as forgotten rather than decided, and
  there is nothing to converge against when the Index records the Automation half as `none — by
  decision`.
-->

```sh
```

Expected: **zero changes**. A non-zero result is a documentation defect against this Runbook,
closed at discovery. It is never accommodated by weakening the Automation (FR-3, NFR-5: the
Automation is authoritative for *what*, this Runbook for *why*).

**Idempotence check** — NFR-3: run the Automation a second time. Expected: zero changes again.
