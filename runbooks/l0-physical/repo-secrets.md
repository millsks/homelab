---
procedure_key: PROC-REPO-SECRETS
procedure_automation: .sops.yaml
---

# Encrypted secrets before a secret store exists

**Procedure:** `PROC-REPO-SECRETS` · **Automation:** [`.sops.yaml`](../../.sops.yaml) · **Index entry:** [`PROCEDURE-INDEX.md`](../../PROCEDURE-INDEX.md)

## Change log

| Date | Change | Commit |
| --- | --- | --- |
| 2026-08-29 | Story 1.4 — `.sops.yaml`, the commit-time and gate-time plaintext scan, `.pre-commit-config.yaml`, and this Runbook. `PROC-REPO-SECRETS` closed from `planned` to `complete` | `feat(asgard): encrypted secrets before a secret store exists` |

## Why this Procedure exists

This Repository is public, and it is the desired state of the whole platform (AD-4). Configuration
that carries a credential therefore has nowhere safe to put it: there is no runtime secret store
yet — that is `andvari`, story 14.1 — and there will not be one until most of the platform it
depends on exists.

The asymmetry is what forces the order of work. **A plaintext secret survives its own deletion.**
Removing it in a later commit leaves it in history, and rewriting the history of a public
repository that others may already have cloned is not a remedy — it is a rotation, performed late,
under pressure, on a credential whose exposure window nobody can bound. So the rejection has to
happen *before* the commit exists, which means the mechanism has to exist before the first
credential does. That is why this Procedure ships with nothing yet to protect: it is the only
moment at which it can be built calmly.

If this Procedure is absent or wrong, the failure is silent until it is permanent.

## Scope and boundaries

**Declares:** encryption at rest for secret material stored *in this Repository* — which paths are
encrypted, to which recipients, and the check that rejects plaintext. This is the
"Repository-stored secret material" resource class in
[`docs/OWNERSHIP.md`](../../docs/OWNERSHIP.md), owned by `SOPS + age`, plus the
`.pre-commit-config.yaml` half of the "Convergence tooling" class.

**Does not declare:**

- **The runtime secret store.** Delivering secrets to running workloads is `PROC-RUNTIME-SECRETS`
  (story 14.1). The two are routinely confused and must not be: this Procedure is what makes the
  Repository publishable *before* that store exists, and it does not become redundant when it
  arrives — a Repository still has to hold the material that bootstraps the store itself.
- **The escrow register.** `PROC-ESCROW-REGISTER` (story 14.2) enumerates everything held outside
  the platform, exhaustively, as its own reviewed artefact. The age identity below is one entry in
  that register; the record here is this Procedure's own statement of where it is held, and the
  register subsumes rather than replaces it.
- **What the gate checks generally.** `PROC-CONVERGENCE-HARNESS` owns the gate; this Procedure adds
  one task to it.
- **OpenTofu state and `*.tfvars`.** Both are gitignored and never enter the Repository at all, so
  they are outside encryption rather than covered by it. State is an owned artefact with its own
  escrow entry — see the OpenTofu provisioning-state row of the ownership table.
- **Any secret this mechanism cannot encrypt.** SOPS encrypts *values* in structured documents.
  Material with no such structure — a binary keytab, a PKCS#12 bundle — is out of scope for the
  rules below and is a human decision to widen them, recorded here before it is made, never
  discovered by an operator improvising at the time.

## Preconditions

| Precondition | Made true by | How to confirm |
| --- | --- | --- |
| A control node with the Repository cloned | `PROC-CONVERGENCE-HARNESS` ("Control node" class) | `git -C <repo> rev-parse --show-toplevel` prints the repository root |
| The pinned environment materialised, providing `sops` and `age` | `PROC-CONVERGENCE-HARNESS`, step 1 | `pixi run sops --version` prints `sops 3.13.3`; `pixi run age --version` prints a version |
| Two escrow destinations that are **not** the control node | The operator, before step 2 | Named in *Escrow of the decryption key* below. AD-24 forbids recovery depending on any single un-escrowed machine, so this precondition is the rule, not paperwork |
| No credential is being committed while this Procedure is being executed | — | Steps 1 to 3 create and record a key. Nothing is encrypted until step 4, and nothing needs to be |

## Procedure

### Step 1 — Generate the control-node age identity

#### Why

`.sops.yaml` ships with the sentinel `AGE-RECIPIENT-UNSET` in place of a recipient, because
generating a key at authoring time would have put the only copy of its private half on one
machine — the exact failure AD-24 names. The identity is generated here, by the operator, so that
step 2 can escrow it before anything depends on it.

An age identity is a single line of text. It is the whole of the decryption capability: whoever
holds it reads every secret this Repository will ever carry.

#### Command

```sh
mkdir -p ~/.config/sops/age
umask 077
pixi run age-keygen -o ~/.config/sops/age/keys.txt
pixi run age-keygen -y ~/.config/sops/age/keys.txt
```

#### Expected output

```text
Public key: age1qy8mfxexamplepublicrecipientvaluegoeshere000000000000000000
age1qy8mfxexamplepublicrecipientvaluegoeshere000000000000000000
```

The first line is written to standard error by `age-keygen -o`; the second is the same public key
re-derived from the file, which is what step 3 records. The private half stays in
`~/.config/sops/age/keys.txt` and begins `AGE-SECRET-KEY-1…`. **That line never leaves the
holders named below, and never enters this Repository in any form.**

#### Automation task

Not applicable — key generation has no Automation half by decision. Generating the identity
automatically would mean the automation held it, and an identity held by the thing that runs
unattended is an identity nobody escrowed. The Automation half of this Procedure,
[`.sops.yaml`](../../.sops.yaml), declares the *recipient*; it never creates one.

#### Failure modes

- **Looks like:** `age-keygen: command not found`. **Check first:** the command is being run
  through `pixi run`; `age` is a dev-feature dependency and is not on the bare system `PATH`.
- **Looks like:** the file is created world-readable. **Check first:** `umask 077` ran in the *same*
  shell as `age-keygen`; `stat -f '%Sp' ~/.config/sops/age/keys.txt` must show `-rw-------`.

### Step 2 — Escrow the identity before anything depends on it

#### Why

The order matters and is the reason this is a step of its own rather than a note on step 1. Once
step 3 records the public half and step 4 encrypts something, the Repository has content that only
this identity can read. Escrowing after that point means there is a window in which the platform's
recoverability depends on one unbackedup file on one machine — which is precisely the state AD-24
exists to forbid.

#### Command

```sh
cat ~/.config/sops/age/keys.txt
```

Then, by hand, place the contents in each holder named in *Escrow of the decryption key* below, and
record the date in that table. The transfer is deliberately manual: a scripted copy would need a
credential for the destination, which is a second secret with the same problem.

#### Expected output

```text
# created: 2026-08-29T00:00:00Z
# public key: age1qy8mfxexamplepublicrecipientvaluegoeshere000000000000000000
AGE-SECRET-KEY-1…
```

Three lines. The escrowed copy is all three, verbatim — the comments carry the public key and the
creation date, which is what lets a future operator match an escrowed identity to the recipient in
`.sops.yaml` without decrypting anything.

#### Automation task

Not applicable — no Automation half by decision. Escrow is a human act by definition: an automated
escrow is a copy to a system that then needs its own escrow.

#### Failure modes

- **Looks like:** the escrow copy is truncated to the `AGE-SECRET-KEY-1` line alone. **Check
  first:** whether the holder's storage stripped the comment lines. The identity still decrypts, but
  nothing then tells a future operator which recipient it corresponds to; re-record all three lines.
- **Looks like:** both escrow destinations turn out to be on the control node — a password manager
  whose vault file lives in the same home directory, for instance. **Check first:** that each holder
  survives the total loss of the control node. If it does not, it is not an escrow.

### Step 3 — Record the public recipient in the committed policy

#### Why

Encryption is declarative: which paths are encrypted and to whom is committed configuration, not
operator memory. Until this step [`.sops.yaml`](../../.sops.yaml) carries the sentinel, and the
harness reports the sentinel as a defect the moment any file matching a creation rule exists — so
the sentinel cannot outlive the first real secret.

Only the **public** half is recorded. It is a recipient, not a credential; publishing it lets
anyone encrypt *to* the platform and nobody decrypt from it.

#### Command

```sh
$EDITOR .sops.yaml   # replace AGE-RECIPIENT-UNSET with the age1... public key from step 1
pixi run secrets
```

#### Expected output

```text
[PASS] Encryption policy declared: 1 declared creation rules examined
[PASS] Declared paths are encrypted: 0 files covered by a creation rule examined — no path matches any creation rule yet
[PASS] Plaintext secret material: <n> files scanned examined — tracked and untracked files git would add (gitignored paths excluded); 0 encrypted, 0 covered by a creation rule; ...
3 checks run: 3 passed, 0 failed, 0 skipped; 0 defect(s) named.
```

The note naming `AGE-RECIPIENT-UNSET` disappears from the first line once a real recipient is
recorded. Its continued presence means the edit did not take.

#### Automation task

The `creation_rules[].age` field in [`.sops.yaml`](../../.sops.yaml) — the Automation half of this
Procedure. It is enforced by the `secrets` task in [`pixi.toml`](../../pixi.toml), which is what
the command above runs.

#### Failure modes

- **Looks like:** `[FAIL] Encryption policy declared … still names the AGE-RECIPIENT-UNSET
  sentinel`. **Check first:** whether a file matching a creation rule was committed before the
  recipient was recorded. Encrypt or remove that file; the order in this Runbook exists to prevent
  exactly this.
- **Looks like:** the private half was pasted instead of the public one. **Check first:** the value
  begins `age1`, not `AGE-SECRET-KEY-1`. If the private half was committed, it is compromised:
  generate a new identity, re-escrow, re-encrypt, and treat the old one as public.

### Step 4 — Encrypt a file

#### Why

The naming convention is the whole rule: a file is encrypted when its name says so. Anything
matching `<name>.sops.yaml`, `.sops.yml`, `.sops.json`, or `.sops.env`, anywhere in the tree, is
covered by the committed policy — and the gate fails and names the path if such a file is not
encrypted. The convention keeps secret material beside the declaration that consumes it rather than
in a separate directory that has to be remembered.

SOPS encrypts *values*, not keys. `directory_bind_password: ENC[AES256_GCM,…]` still tells a reader
what the value is for. That is a deliberate property of the format — it is what makes an encrypted
file reviewable in a diff — and not a leak.

#### Command

```sh
$EDITOR ansible/l0-physical/example.sops.yaml   # write the plaintext values
pixi run sops --encrypt --in-place ansible/l0-physical/example.sops.yaml
```

#### Expected output

```text
directory_bind_password: ENC[AES256_GCM,data:gEueqFqdTAdumvt0…,iv:s+KoMmq4…,tag:AtRfOCVu…,type:str]
sops:
    age:
        - enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            …
            -----END AGE ENCRYPTED FILE-----
          recipient: age1qy8mfxexamplepublicrecipientvaluegoeshere000000000000000000
    lastmodified: "2026-08-29T00:00:00Z"
    mac: ENC[AES256_GCM,data:g7vs1Vbn…,type:str]
    unencrypted_suffix: _unencrypted
    version: 3.13.3
```

Every value is `ENC[AES256_GCM,…]`. A value still readable is a value SOPS did not encrypt —
usually a key ending in `_unencrypted`, which the format exempts by design.

#### Automation task

The `creation_rules[].path_regex` field in [`.sops.yaml`](../../.sops.yaml) selects the recipient
for this path; `sops` reads it from the Repository root with no flag. The `secrets` task in
[`pixi.toml`](../../pixi.toml) is what enforces that a matching path is actually encrypted.

#### Failure modes

- **Looks like:** `config file not found, or has no creation rules`. **Check first:** the command
  ran from the Repository root. SOPS searches upward from the file's directory for `.sops.yaml`.
- **Looks like:** the file is encrypted to a recipient nobody holds. **Check first:** the recipient
  line in the output matches the public key from step 1. Re-encrypting to a lost recipient is not
  recoverable from inside this Repository — that is what step 2 is for.
- **Looks like:** the working file was edited after encryption and now mixes ciphertext with new
  plaintext. **Check first:** always edit with `sops <file>`, which decrypts to a temporary buffer
  and re-encrypts on save, rather than with a plain editor.

### Step 5 — Install the commit-time hook

#### Why

The hook is the *earliest* place the rejection can happen, and earliest is the only place that
helps: a secret rejected at commit time never enters history at all.

The hook is deliberately not the only place. It lives in `.git/hooks`, which no clone carries and
which nobody is obliged to install — and story 1.3 recorded what happens when the opposite is
assumed: a hook installed with no configuration present rejected every commit in the Repository
until it was uninstalled by hand. So the same scan runs in the gate, for every clone and every CI
run, and the hook is an accelerator rather than the control.

#### Command

```sh
pixi run bootstrap
```

#### Expected output

```text
pre-commit installed at .git/hooks/pre-commit
pre-commit installed at .git/hooks/commit-msg
```

Both lines. `.pre-commit-config.yaml` declares `default_install_hook_types`, so a single
`pre-commit install` installs both; only one line means the configuration was not read.

#### Automation task

The `bootstrap` task in [`pixi.toml`](../../pixi.toml), reading
[`.pre-commit-config.yaml`](../../.pre-commit-config.yaml). Its `asgard-secret-scan` hook runs
`pixi run secrets` — the same task step 3 ran, and the same code the gate runs inside
`pixi run audit`, rather than a second implementation that could drift from it.

#### Failure modes

- **Looks like:** every commit is rejected with an error about a missing configuration file.
  **Check first:** whether `.pre-commit-config.yaml` is present. This is the story-1.3 failure
  named above; the recovery is `pre-commit uninstall`, and it is why the hook and the configuration
  land in the same change.
- **Looks like:** every commit is rejected, and the failing hook prints `secrets: command not
  found` followed by a list of pixi tasks. **Check first:** whether the task the hook names is
  **committed**, not merely present in the working tree. pre-commit reverts unstaged changes before
  it runs, so the `pixi.toml` a hook sees is the staged one; `pixi run <name>` then finds no task,
  falls back to running `<name>` as a shell command, exits 127, and pre-commit renders that
  *identically to the scan finding a credential*. Recovery is `pre-commit uninstall`, commit
  `pixi.toml` and `.pre-commit-config.yaml` together, then `pixi run bootstrap` again. This is the
  sibling of the failure above and it bit this very story: the first verification staged everything
  before committing, which left pre-commit nothing to revert and hid the bug entirely.
- **Looks like:** `sops` or `age` disappears from the environment after a failed commit. **Check
  first:** the same cause. A hook that runs `pixi run` while `pixi.toml` is reverted makes pixi
  re-solve the environment from the *committed* manifest and remove any dependency the working
  tree had added.
- **Looks like:** a hook fails with `pixi: command not found` under a GUI git client. **Check
  first:** the client's `PATH`. Every hook shells out through `pixi run` on purpose — that is what
  guarantees a commit runs the tools `pixi.lock` resolved and nothing else — so `pixi` must be
  reachable from wherever commits are made.

## Escrow of the decryption key

AD-24: the identity that decrypts Repository-stored secret material is escrowed **outside this
Repository and outside any single un-escrowed machine**. A copy held only on the control node fails
that rule outright, so the control node is listed below as a *holder*, not as the escrow.

| Holder | Location | Not the control node? | Rotation | Escrowed on |
| --- | --- | --- | --- | --- |
| Control node | `~/.config/sops/age/keys.txt`, mode `0600`, on the machine that runs `sops`, `ansible-playbook`, and `tofu apply` | No — this is the working copy | Replaced whenever the identity is rotated below | n/a |
| Operator's password manager | Entry `asgard / sops-age-control-node`, holding all three lines of the identity file verbatim | Yes — survives the total loss of the control node | Re-recorded within the same session as any rotation | *(record the date when step 2 is executed)* |
| Offline copy, held off-site | Encrypted removable volume or a printed copy, stored physically apart from the platform | Yes — survives the loss of both the control node and the password manager | Re-recorded within the same session as any rotation | *(record the date when step 2 is executed)* |

**Current state, stated rather than implied:** no identity has been generated yet. `.sops.yaml`
carries the `AGE-RECIPIENT-UNSET` sentinel, nothing in the Repository is encrypted, and the two
escrow dates above are therefore blank by fact and not by omission. Step 2 fills them in, and it
runs before step 3 for exactly that reason.

**Rotation.** The identity is rotated when a holder is lost, when a person with access leaves, or
on the cadence `PROC-ESCROW-REGISTER` sets — whichever comes first. Rotation is: generate a new
identity (step 1), escrow it (step 2), add the new recipient to `.sops.yaml` *alongside* the old
one, re-encrypt every covered file with `sops updatekeys`, then remove the old recipient and
destroy its escrowed copies. Removing the old recipient first would leave the covered files
readable by nothing.

**One entry in a larger register.** `PROC-ESCROW-REGISTER` (story 14.2) enumerates everything held
outside the platform, and this identity is one of its entries. That register is authoritative for
the review cadence; this table is authoritative for where this particular key lives.

## Rollback

Rolling back this Procedure means removing the encryption mechanism, and it divides sharply by
whether anything has been encrypted yet.

**Nothing encrypted (the state at the time of writing).** Delete `.sops.yaml`,
`.pre-commit-config.yaml`, and the `secrets` and `commit-msg` tasks from `pixi.toml`, and run
`pre-commit uninstall`. The gate stops enforcing the plaintext rule and the Index entry returns to
`planned`. Nothing is lost, because nothing depended on it.

**Something encrypted.** Every covered file must be decrypted with `sops --decrypt --in-place`
*before* the policy is removed, and the resulting plaintext must not be committed — which means the
material needs somewhere else to go in the same change. There is nowhere else until story 14.1, so
in practice this Procedure is not reversible once used, and that is a property to know in advance
rather than discover.

**What cannot be undone at all:** a plaintext secret that reached history. Rolling back the check
does not remove the commit. The credential is rotated at its source; the Repository is not the
remedy.

## Alert sources registered

One, registered in the *Alert sources* table of
[`PROCEDURE-INDEX.md`](../../PROCEDURE-INDEX.md) in the same change that built it:

`pixi run secrets` — the plaintext-secret and encryption-policy scan. It runs at commit time
through the hook and in the gate through `pixi run ci`, and any defect it names exits non-zero.
Story 13.5 wires it to notification; registration does not wait for that.

## Verification

**Command:**

```sh
pixi run secrets
```

**Expected output:**

```text
[PASS] Encryption policy declared: 1 declared creation rules examined
[PASS] Declared paths are encrypted: 0 files covered by a creation rule examined — no path matches any creation rule yet
[PASS] Plaintext secret material: <n> files scanned examined — tracked and untracked files git would add (gitignored paths excluded); 0 encrypted, 0 covered by a creation rule; vendored trees not scanned: [...]
3 checks run: 3 passed, 0 failed, 0 skipped; 0 defect(s) named.
```

`<n>` is written as a placeholder on purpose: the count moves every time a file is added, and an
expected-output block stating a number that is wrong on the day it ships teaches a reader to skim
past this section. What must hold is that every check passes, that the scanned count is non-zero
and roughly the number of tracked files outside the vendored trees, and that the run states *what*
it scanned. A check reporting `0 files
scanned` has passed over nothing and is a failure of this verification, not a pass.

The verification is identical whichever path performed the work, because there is only one scan:
the hook, the `secrets` task, and `pixi run audit` all call the same code.

**Verify in both directions.** A rejected commit is only evidence that the check works if a clean
commit is also accepted — a hook that rejects everything satisfies the first half perfectly and
detects nothing. So the verification is two commits, not one: stage a file carrying a plaintext
credential and confirm the commit is rejected *and names the path*, then remove it, commit a file
carrying none, and confirm `git log` moved. Reading an exit code through a pipe reports the pipe's
status rather than the command's; check `$?` directly, or check that `HEAD` changed.

**Convergence check** — AD-3: run the Automation against the system just built by hand.

```sh
pixi run audit
```

Expected: **zero changes**. `.sops.yaml` is a declarative policy rather than a tool that converges a
system, so its convergence check is the audit reporting that the policy, the Index entry, and the
filesystem agree — the same three checks the command above runs, plus the dual-form back-reference
resolving `.sops.yaml` to this Runbook and back. Any disagreement is a documentation defect against
this Runbook, closed at discovery. It is never accommodated by weakening the Automation (FR-3,
NFR-5: the Automation is authoritative for *what*, this Runbook for *why*).

**Idempotence check** — NFR-3: run the Automation a second time. Expected: zero changes again.

```sh
pixi run audit && pixi run audit
```

Both runs report the same counts and the same zero defects. The scan reads and never writes, so a
second run differing from the first would mean something else changed the tree between them.
