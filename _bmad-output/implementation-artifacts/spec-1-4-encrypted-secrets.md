---
title: 'Story 1.4 — Encrypted secrets before a secret store exists'
type: 'feature'
created: '2026-08-29'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'b8bad518c8ab9f06d9e9942bb1f2794d38077186'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The platform must be built before any runtime secret store exists, so early configuration carries credentials with nowhere safe to put them — in a repository that is public. Nothing today stops a plaintext secret being committed, and a secret in git history survives its own deletion.

**Approach:** Encryption at rest with a key held outside the repository, plus a commit-time check that rejects plaintext before it becomes history. Prove the rejection fires rather than asserting it.

## Boundaries & Constraints

**Always:**
- No plaintext credential, key, or token in the working tree or in history.
- Encrypted material in the repository is unusable without a key held outside it.
- The check names the offending path. A rejection that does not say what or where is one nobody can act on.
- The decryption key is escrowed outside the repository **and outside any single un-escrowed machine** — a key held only on the operator's workstation fails this, which the ledger already records as the rule.
- The check proves it fires: a fixture carrying a plaintext secret is rejected, then removed. "The hook is installed" is not evidence.
- Encryption is declarative — which paths are encrypted, and to which recipients, is committed configuration rather than operator memory.

**Ask First:**
- Any secret material the chosen mechanism cannot encrypt.
- Widening the encrypted-path rules beyond what the platform actually needs.

**Never:**
- Do not build the runtime secret store — that is `andvari`, story 14.1. This story covers repository-stored material only.
- Do not commit any real credential, encrypted or otherwise. There is no live secret yet; the mechanism is proven against fixtures.
- Do not weaken any existing harness check to accommodate new files.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Clean commit | No secret material | Commit proceeds | N/A |
| Plaintext secret staged | A credential in a tracked file | Rejected, path named | Never auto-redacted |
| Encrypted file committed | Encrypted content | Proceeds; unreadable without the key | N/A |
| Repository read without the key | Any clone | Ciphertext only, nothing recoverable | N/A |
| Key absent | Operator without the key | Cannot decrypt; everything else still works | Clear failure, not silent |
| Hook never installed | Fresh clone | The same scan still runs in the gate | Protection must not depend on a hook nobody installed |

</frozen-after-approval>

## Code Map

- `PROCEDURE-INDEX.md:289` -- `PROC-REPO-SECRETS`, this story's entry, `planned`, Runbook path reserved, `.sops.yaml` recorded as owed by this story
- `src/asgard_harness/selfcheck.py:82` -- **`SUBJECT_KEY = "PROC-REPO-SECRETS"`, chosen because this story was unstarted.** Landing this story makes that fixture non-inert; it must be re-pointed and the harness kept green. Related literals at `:289` and `:315`
- `docs/OWNERSHIP.md` -- the repository-secret-material row names `SOPS + age` with `.sops.yaml` as declaring mechanism
- `_bmad-output/implementation-artifacts/deferred-work.md` -- records that `pixi run bootstrap` is broken, that this story owns `.pre-commit-config.yaml`, and that a hook installed without a config blocked every commit during story 1.3
- `pixi.toml` -- `bootstrap` exists and fails; the gate chain is where a repository-wide scan joins
- `.gitignore` -- already excludes state and caches

**Read-only:** `_bmad/`, `.claude/`, `.agents/`, `.bmad-loop/`.

## Tasks & Acceptance

**Execution:**
- [ ] `.sops.yaml` -- declarative encryption rules: which paths, which recipients -- policy committed rather than remembered
- [ ] `.pre-commit-config.yaml` -- the commit-time plaintext check plus the formatting and conventional-commit hooks the standard expects -- closes the deferred item and makes `bootstrap` work for the first time
- [ ] `pixi.toml` -- join the secret scan to the gate chain -- a check that runs only at commit time is absent from a fresh clone and from CI
- [ ] `src/asgard_harness/selfcheck.py` -- re-point the `PROC-REPO-SECRETS` fixture -- this story is what makes it non-inert
- [ ] `runbooks/l0-physical/repo-secrets.md` -- this Procedure's Runbook, per the template -- completing this story's own Procedure, as story 1.3 established
- [ ] `PROCEDURE-INDEX.md` -- move `PROC-REPO-SECRETS` to its true status; update Totals -- the entry describing this story must reflect what it built
- [ ] `_bmad-output/implementation-artifacts/deferred-work.md` -- close the bootstrap entries this story resolves

**Acceptance Criteria:**
- Given a staged file containing a plaintext credential, when a commit is attempted, then it is rejected and the offending path is named.
- Given the same check against the clean repository, when it runs, then it passes and reports what it scanned.
- Given an encrypted file, when the repository is read without the key, then no secret is recoverable.
- Given the escrow record, when inspected, then it says where the key is held, satisfying the outside-any-single-machine rule rather than restating it.
- Given a fresh clone where `bootstrap` was never run, when the gate runs, then the secret scan still executes.
- Given `pixi run bootstrap`, when it runs, then it succeeds — which it has not done since the workspace was created.
- Given `pixi run ci`, `pixi run audit`, and `pixi run selfcheck`, when they run, then all pass.

## Design Notes

**There is no real secret to protect yet, and that is the point.** The mechanism must exist before the first credential does, because a plaintext secret survives its own deletion — rewriting history on a public repository others may have cloned is not a remedy. So this story is proven entirely against fixtures, as story 1.3 was.

**The commit-time check cannot be the only check.** A pre-commit hook lives in `.git/hooks`, which no clone carries and which story 1.3 demonstrated can be installed in a broken state that blocks all work. The same scan therefore runs in the gate, present for every clone and every CI run.

## Verification

**Commands:**
- `pixi run ci`, `pixi run audit`, `pixi run selfcheck` -- expected: all exit 0
- `pixi run bootstrap` -- expected: succeeds against a real config
- Stage a fixture containing a plaintext credential, attempt a commit -- expected: rejected, path named; fixture removed, tree left clean

**Manual checks:**
- Confirm no real credential was committed, encrypted or not.
- Confirm the escrow record names a location rather than restating the rule.
