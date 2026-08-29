# Procedure Index

Governed by **AD-3**. This is the authoritative enumeration of every Procedure Project Asgard
**requires** — not of the Procedures it happens to have built. Without it, FR-1 ("every operational
activity is documented") quantifies over a set nothing enumerates.

**Derived from:** [`_bmad-output/planning-artifacts/epics.md`](_bmad-output/planning-artifacts/epics.md)
at commit `f5471f8` (2026-08-28).

That provenance line is load-bearing rather than decorative. The Index changes whenever the story
list changes, and without a recorded source commit there is no way to notice that the story list has
*already* changed — the claim "derived from the story list" would be unfalsifiable. Re-deriving the
Index updates this line in the same change. A story added without an Index entry is a Procedure
nobody committed to writing.

Counts appear once, in [Totals](#totals). No other document — this one included — states a Procedure
count as prose: a number restated is a number that goes stale, and this file has already been
through that once.

Nearly every entry is `planned` today. That is correct and is the point: the Index is a work ledger
whose incompleteness is the honest signal. Enumerating only what is built would produce an Index
that grows to match reality and always reports complete, which is exactly the unbounded-set problem
this file exists to close.

---

## What a Procedure is

A **Procedure** is an operational activity in two halves:

- a **Runbook** — the human form: a complete manual procedure, executable start to finish with no
  Automation available; and
- an **Automation** — the machine form: idempotent, reporting zero changes against a system built by
  hand from the Runbook.

Neither half alone qualifies. The two name each other by path, in both directions — see
[The dual-form contract](#the-dual-form-contract).

One carve-out, and it is a decision rather than a shortfall: a Procedure whose declaring owner in
[`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) is `Runbook` or `docs/ record` is **human-executed by
decision** and has no Automation half at all. Racking a Node has no playbook and never will. Those
Procedures carry the status `manual-by-decision`, they still name an automated verification wherever
a machine can observe the result, and they are **never** counted as automation gaps.

## One Procedure per story, and the one exception

**The rule.** One Procedure per story by default. A story whose ownership table splits the work
across **two owners** carries one Procedure per owner, recorded below as an explicit exception with
its reason. A story needing three Procedures is mis-scoped, not exceptional — surface it rather than
splitting it a third time.

This is a human-approved relaxation of the original one-Procedure-per-story constraint. It exists
because the alternative was worse: forcing a two-owner story into one entry hid one of the
architecture's three named manual areas from the audit entirely.

**The exceptions, in full:**

| Story | Split across | Entries | Reason |
| --- | --- | --- | --- |
| 2.3 | `Runbook` and `Ansible` | `PROC-HYPERVISOR-INSTALL`, `PROC-NODE-BUILD` | [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) splits the Node build into two resource classes with two different owners: *Proxmox VE installation on each Node* (`Runbook`, human-executed by decision — the architecture's second named manual area) and *Proxmox host operating system configuration* (`Ansible`). Held as one entry, the manual installation would have had no row of its own, and an audit walking the Index could not have seen the manual area at all. Split, each half carries the status its owner implies. |

Every other story has exactly one entry. An entry count above one for a story not listed here is a
defect — see [Defects this Index reports](#defects-this-index-reports).

## How to read the table

Every entry carries seven fields, and an entry missing any of them is itself a defect:

- **Key** — the stable identifier. See [Key namespace rules](#key-namespace-rules).
- **Title** — the owning story's title from `epics.md`, **verbatim**. Titles are not paraphrased,
  because the audit matches entries to stories on the story number and a drifting title is drift
  nothing would catch. The one permitted addition: a story split under the exception above carries a
  parenthetical owner qualifier, so its two entries are distinguishable.
- **Layer** — the owning layer, `l0-physical` through `l5-workloads`. The layer whose capability the
  Procedure delivers: the layer that would be missing something if the Procedure did not exist.
  Repository, control-node, and power concerns sit at `l0-physical`, matching the Cross-cutting rows
  of [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md), which declare them in `runbooks/l0-physical/`.
- **Story** — the single owning story, `<epic>.<story>`. Exactly one, always, even where two entries
  name the same story under the exception above.
- **Runbook** — where the human half lives. For a `docs/ record` Procedure the human form *is* the
  record, so the path is the document itself.
- **Automation** — where the machine half lives, or the literal `none — by decision`.
- **Status** — one value from the closed set below.

A path in the Runbook or Automation column names where that half **will** live. Most of them do not
exist yet; the path is a commitment, not a claim. The status column is what says whether the half is
there.

### Key namespace rules

- **Form.** `PROC-<SUBJECT>`, uppercase, hyphenated. Derived from the Procedure's subject — **never**
  from its story number or its layer, so renumbering a story or moving a Procedure between layers
  does not invalidate a reference to it.
- **Uniqueness.** Keys are unique across the Index, and so are Runbook paths. Two entries sharing
  either are a defect. Uniqueness is not automatic: because the layer is deliberately excluded from
  the key, a subject that recurs at more than one layer must be qualified in the key itself. *Cluster*
  is the live example — Asgard has a hypervisor cluster and a workload cluster, so
  `PROC-NODE-CLUSTER-FORMATION` and `PROC-WORKLOAD-CLUSTER-COMPOSITION` each carry the qualifier
  rather than relying on the Layer column to tell them apart.
- **Vendor neutrality.** A key names the role, not the product. `epics.md` says "the second OS
  family" rather than naming a distribution precisely so the family can change; a key that hardcodes
  the vendor would be invalidated by a swap that changes nothing about the Procedure's subject.
- **Rename.** The key is stable; the slug and both paths are not. When a Procedure's subject changes
  enough that the key no longer describes it, the key, the slug, and both paths move together in one
  change, and the old key is recorded as retired below. A key is never silently reused for a
  different subject.
- **Retirement.** When a story is dropped from `epics.md`, its entry is removed and the key is
  recorded as retired, never deleted outright and never reassigned. A dangling reference that
  resolves to *retired* is diagnosable; one that resolves to a different Procedure is not.

**Retired keys:** none yet.

### Path conventions

| Half | Convention |
| --- | --- |
| Runbook | `runbooks/<layer>/<slug>.md`, where `<slug>` is the key's subject, lowercased |
| Ansible Automation | `ansible/<layer>/<slug>.yml` — the playbook is the named entry point; roles hang below it |
| OpenTofu Automation | `tofu/<layer>/<slug>.tf` |
| Kubernetes Automation | `k8s/<layer>/<slug>/` — a kustomization directory |
| `docs/ record` human form | the record itself, e.g. `docs/ESCROW.md` |
| Repository tooling Automation | the tool configuration itself, e.g. `pixi.toml` |

### Status — a closed enumeration

The Owner column of [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) is a closed enumeration for the same
reason this one is: story 1.3's audit parses it, and a sentence cannot be checked mechanically. A
value outside this set is a defect.

| Status | Means |
| --- | --- |
| `planned` | Neither half exists yet. The owning story has not been executed. **Normal today — this is the denominator.** |
| `incomplete` | One half exists and the other does not, and the absence is not a decision. **A defect.** The audit names it; it is never hidden and never silently tolerated. |
| `complete` | Both halves exist and name each other by path. |
| `manual-by-decision` | The Automation half does not exist **by decision**. The entry names an automated verification instead. **Never a gap.** |

`manual-by-decision` is assigned from the architecture at the time the entry is written — it is a
statement about the contract, not a reading of the filesystem. The other three are derived from what
is actually present. Where they disagree with what is on disk, the disagreement is the defect.

`manual-by-decision` says only what the *Automation* half is. It does not assert that the Runbook is
written. Runbook presence for those entries is tracked in
[Deliberately manual work](#deliberately-manual-work), and an unwritten one is a defect there, so no
half goes unaccounted for.

**Provisional manual decisions.** A `manual-by-decision` entry is normally permanent — nothing will
ever automate racking a Node. Two are instead *provisional*: an open spike could resolve in favour
of an Automation half. Because the status wording says "by decision" and not "for now", the
provisionality is recorded beside the entry rather than inside its status, and a resolved spike moves
the status in the same change that moves the declaration in `docs/OWNERSHIP.md`. Nothing about the
status blocks the spike from resolving.

---

## The dual-form contract

The contract is **bidirectional**. Defining only one direction leaves the other to be invented once
per remaining Procedure.

### Runbook names its Automation

Every Runbook opens with YAML front matter naming the Procedure and its Automation:

```yaml
---
procedure_key: PROC-GATEWAY-TLS
procedure_automation: k8s/l3-platform/gateway-tls/
---
```

The Index remains authoritative for layer, owning story, and status; the front matter carries only
the two fields that make the back-reference resolvable, so there is one place to change when a
status moves.

[`runbooks/TEMPLATE.md`](runbooks/TEMPLATE.md) is the required starting point for every Runbook. It
carries the front matter and the four sections the runbook standard requires.

### Automation names its Runbook

Every Automation entry point declares `procedure_key` and `procedure_runbook` in its own tool's
native declaration mechanism. One convention, three expressions — chosen so the value is
machine-readable in each tool rather than buried in a comment story 1.3's audit would have to parse
by hand:

**Ansible** — play-level vars in the entry-point playbook:

```yaml
- name: Node build
  hosts: nodes
  vars:
    procedure_key: PROC-NODE-BUILD
    procedure_runbook: runbooks/l1-hypervisor/node-build.md
```

**OpenTofu** — a `locals` block in the root module. Locals may be unset-and-unused without warning,
which is what makes this safe to require of every module:

```hcl
locals {
  procedure_key     = "PROC-GUEST-PROVISIONING"
  procedure_runbook = "runbooks/l1-hypervisor/guest-provisioning.md"
}
```

**Kubernetes** — `commonAnnotations` in the set's `kustomization.yaml`, so every object the set
produces carries the reference and a running cluster can be asked which Runbook explains an object:

```yaml
commonAnnotations:
  asgard.home.arpa/procedure-key: PROC-GATEWAY-TLS
  asgard.home.arpa/procedure-runbook: runbooks/l3-platform/gateway-tls.md
```

**Repository tooling** — a comment on the task or configuration block, in the form
`# Procedure: PROC-<KEY> — runbook: runbooks/<layer>/<slug>.md`. Tool configuration files have no
free-form metadata mechanism; this is the one case where a comment is the only available carrier.

**Step-level mapping is required too, not just file-level.** Each Runbook step names the Automation
task that performs it, and each Automation task's `name:` names the Runbook section that explains
it. File-level references alone tell an operator which document to open; step-level references tell
them where in it to look, which is the thing they need at 2 a.m. with a failed task on screen.

### Two exemptions from back-reference resolution

Both are stated here so story 1.3's audit implements them from a specification rather than
discovering them as false failures and inventing an ad-hoc exclusion.

1. **The literal `none — by decision` in an Automation cell is not a path.** An audit that resolves
   it as one fails every `manual-by-decision` entry on its first run. The literal means the entry has
   no Automation half; an entry carrying it **must** have status `manual-by-decision`, and an entry
   with that status **must** carry the literal. Either one without the other is a defect.

2. **[`runbooks/TEMPLATE.md`](runbooks/TEMPLATE.md) is not a Runbook.** It is the shape every Runbook
   is cut from, and its front matter is deliberately unfilled, so an audit walking `runbooks/**/*.md`
   must exclude it by path. Its front matter carries the sentinel `TEMPLATE-UNFILLED` in both fields.
   The inverse hazard is the reason the sentinel exists rather than a plausible-looking placeholder:
   a writer who copies the template and forgets to edit the front matter would otherwise ship a
   Runbook pointing at an example Procedure that does not exist, and nothing would catch it. So:
   **a `procedure_key` or `procedure_automation` field carrying `TEMPLATE-UNFILLED` in any file
   under `runbooks/` other than `TEMPLATE.md` is a defect**, and it is grep-visible rather than
   plausible. The rule is scoped to those front-matter fields on purpose: prose that *names* the
   sentinel — this paragraph, the defect list below, and the note in
   [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) — must not trip the rule that defines it.

---

## Deliberately manual work

The Procedures listed here have no Automation half by decision; their count is in
[Totals](#totals). Three areas of the architecture drive them — L0 physical work, hypervisor
installation, and the storage appliance's initial setup — plus the `docs/ record` declarations,
which are read rather than run.

Each names its verification. Execution being manual never excuses verification from being automated:

| Key | Story | Why no Automation | Verification | Human form written? | Provisional? |
| --- | --- | --- | --- | --- | --- |
| `PROC-REPO-SKELETON` | 1.1 | `docs/ record` — the ownership table is maintained, not executed | The ownership audit: fails and names any class with two owners, none, an illegal Owner value, or no covering Procedure | Yes — `docs/OWNERSHIP.md` | No |
| `PROC-PROCEDURE-INDEX` | 1.2 | `docs/ record` — this file is maintained, not executed | The Index audit: reports every entry missing either half, and every story with no entry | Yes — this file | No |
| `PROC-ADDRESS-PLAN` | 2.1 | `docs/ record` — addresses are declared, never discovered from running systems | Two halves, and only one exists yet: **today**, `pixi run audit` checks the plan's internal consistency — collisions, statics inside the DHCP pool, a Node on one segment only, a consumed reservation, a route on the isolated segment, an address in no declared range. **Owed**, reconciliation of the declared addresses against Directory DNS (story 4.3) and against what hosts actually answer (story 2.3), neither of which exists to reconcile against yet | Yes — [`docs/ADDRESS-PLAN.md`](docs/ADDRESS-PLAN.md) | No |
| `PROC-OOB-MANAGEMENT` | 2.2 | Firmware-resident; no declarative mechanism is in the Stack | Port probe from another host **plus** a direct firmware-screen reading (AD-28). An OS reinstall is explicitly not evidence | No | No |
| `PROC-HYPERVISOR-INSTALL` | 2.3 | Initial install to first boot is performed at the console. The architecture's second named manual area | Version, repository set, and cluster-readiness read from the installed host | No | No |
| `PROC-STORAGE-POOL` | 3.1 | Appliance initial setup — DSM installation, SHR-2 pool creation, and volume creation are performed through the appliance's own first-run wizard, before anything on the network can reach it | Pool health, redundancy level, and volume geometry read from the DSM API | No | **Partly** — see below |
| `PROC-ESCROW-REGISTER` | 14.2 | `docs/ record` — the escrow list is reviewed, not run | Review on a stated cadence; the list is itself the artefact under review (AD-24) | No | No |
| `PROC-POWER-INVENTORY` | 15.1 | Physical work: which device is plugged into which protected outlet | Load-and-runtime read from the UPS daemon, compared against the declared allocation | No | No |
| `PROC-POWER-DRILL` | 15.5 | Physical work: mains power is removed by hand. Nothing can automate pulling the plug | Measured runtime under real load, and the interval between the last Node completing shutdown and the appliance ceasing to serve, both recorded as numbers in the Repository | No | No |

**`PROC-STORAGE-POOL` covers two ownership rows with one status, and only one of them is settled.**
Story 3.1 delivers both the appliance's *initial setup* (pool creation — permanently manual, for the
reason in the table) and its *first export* (ongoing configuration — manual **for now**). The second
carries a live spike recorded in [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md): whether
`ansible.builtin.uri` against the DSM Web API is stable enough across DSM upgrades to own the
declaration. If it proves out, the ongoing-configuration class moves to `Ansible`, and this entry
gains an Automation half in the same change. Both rows share the `Runbook` owner today, so the
two-owner exception does not apply and they stay one entry — but the status must not be read as
closing the spike. It is not closed.

---

## The Index

### Epic 1 — Repository, Procedure standard, and secret handling

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-REPO-SKELETON` | Repository skeleton with layered ownership | `l0-physical` | 1.1 | `docs/OWNERSHIP.md` | none — by decision | `manual-by-decision` |
| `PROC-PROCEDURE-INDEX` | Procedure Index and the dual-form contract | `l0-physical` | 1.2 | `PROCEDURE-INDEX.md` | none — by decision | `manual-by-decision` |
| `PROC-CONVERGENCE-HARNESS` | Convergence test harness | `l0-physical` | 1.3 | `runbooks/l0-physical/convergence-harness.md` | `pixi.toml` | `complete` |
| `PROC-REPO-SECRETS` | Encrypted secrets before a secret store exists | `l0-physical` | 1.4 | `runbooks/l0-physical/repo-secrets.md` | `.sops.yaml` | `complete` |

`PROC-CONVERGENCE-HARNESS` was recorded here as `incomplete` — `pixi.toml` existed and already ran
the gate, while its Runbook did not. That was exactly one half present, which is the
incomplete-Procedure defect this file defines, and it was recorded rather than rounded down because
an Index that softened its own first defect would have no standing to report anyone else's. Story
1.3 closed it by writing [`runbooks/l0-physical/convergence-harness.md`](runbooks/l0-physical/convergence-harness.md)
and adding the back-reference comment to `pixi.toml`. It is the Index's first `complete` entry, and
the audit that reports the defect is the same audit that now agrees the defect is gone.

`PROC-REPO-SECRETS` is the second. It went from `planned` to `complete` in one change rather than
passing through `incomplete`, because both halves had to land together: a policy declaring which
paths are encrypted is worthless without the check that enforces it, and the check has nothing to
enforce without the policy. It is `complete` while protecting nothing — no credential exists yet —
and that is the point of the story rather than a weakness in it. A plaintext secret survives its
own deletion, so the mechanism has to predate the first secret; the alternative is building it
after the mistake, on a public repository, under time pressure.

### Epic 2 — Nodes, cluster, network, and break-glass

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-ADDRESS-PLAN` | Address plan and interface allocation | `l0-physical` | 2.1 | `docs/ADDRESS-PLAN.md` | none — by decision | `manual-by-decision` |
| `PROC-OOB-MANAGEMENT` | Out-of-band management claimed or disabled | `l0-physical` | 2.2 | `runbooks/l0-physical/oob-management.md` | none — by decision | `manual-by-decision` |
| `PROC-HYPERVISOR-INSTALL` | Node build — hypervisor, dual-homed networking (hypervisor installation) | `l1-hypervisor` | 2.3 | `runbooks/l1-hypervisor/hypervisor-install.md` | none — by decision | `manual-by-decision` |
| `PROC-NODE-BUILD` | Node build — hypervisor, dual-homed networking (host OS configuration) | `l1-hypervisor` | 2.3 | `runbooks/l1-hypervisor/node-build.md` | `ansible/l1-hypervisor/node-build.yml` | `planned` |
| `PROC-BREAK-GLASS` | Break-glass access that survives every dependency | `l1-hypervisor` | 2.4 | `runbooks/l1-hypervisor/break-glass.md` | `ansible/l1-hypervisor/break-glass.yml` | `planned` |
| `PROC-NODE-CLUSTER-FORMATION` | Cluster formation | `l1-hypervisor` | 2.5 | `runbooks/l1-hypervisor/node-cluster-formation.md` | `ansible/l1-hypervisor/node-cluster-formation.yml` | `planned` |
| `PROC-GUEST-PROVISIONING` | Declarative Guest provisioning | `l1-hypervisor` | 2.6 | `runbooks/l1-hypervisor/guest-provisioning.md` | `tofu/l1-hypervisor/guest-provisioning.tf` | `planned` |
| `PROC-GUEST-SNAPSHOT` | Snapshot and rollback | `l1-hypervisor` | 2.7 | `runbooks/l1-hypervisor/guest-snapshot.md` | `ansible/l1-hypervisor/guest-snapshot.yml` | `planned` |
| `PROC-NODE-REBUILD` | Node rebuild from the repository | `l1-hypervisor` | 2.8 | `runbooks/l1-hypervisor/node-rebuild.md` | `ansible/l1-hypervisor/node-rebuild.yml` | `planned` |

`PROC-ADDRESS-PLAN` keeps the status `manual-by-decision` now that story 2.1 has written
[`docs/ADDRESS-PLAN.md`](docs/ADDRESS-PLAN.md), and that is not a story left half-finished. The
status says what the *Automation* half is, and for a `docs/ record` the answer is permanently "none,
by decision" — an address plan is read, not run. What changed is tracked where the Index says it is
tracked: the entry's "Human form written?" cell in
[Deliberately manual work](#deliberately-manual-work), and the recomputed
[Totals](#totals) figure that column feeds. Its verification is now half-built rather than absent,
and the entry says which half and what the other one waits on, because a verification recorded as a
single sentence would have read as complete the moment the first half landed.

### Epic 3 — Shared storage, first export

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-STORAGE-POOL` | Storage pool and first export | `l3-platform` | 3.1 | `runbooks/l3-platform/storage-pool.md` | none — by decision | `manual-by-decision` |
| `PROC-NFS-CLIENT-MOUNT` | Client mount with deliberate semantics | `l3-platform` | 3.2 | `runbooks/l3-platform/nfs-client-mount.md` | `ansible/l3-platform/nfs-client-mount.yml` | `planned` |

### Epic 4 — Directory, DNS, time, and network login

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-HOST-BUILD-DIRECTORY` | Directory Guest built on the second OS family | `l2-foundation` | 4.1 | `runbooks/l2-foundation/host-build-directory.md` | `ansible/l2-foundation/host-build-directory.yml` | `planned` |
| `PROC-DIRECTORY-INSTALL` | Directory installed with pinned numeric identity | `l2-foundation` | 4.2 | `runbooks/l2-foundation/directory-install.md` | `ansible/l2-foundation/directory-install.yml` | `planned` |
| `PROC-DNS-ZONE` | DNS zone and records | `l2-foundation` | 4.3 | `runbooks/l2-foundation/dns-zone.md` | `ansible/l2-foundation/dns-zone.yml` | `planned` |
| `PROC-TIME-AUTHORITY` | Time authority | `l2-foundation` | 4.4 | `runbooks/l2-foundation/time-authority.md` | `ansible/l2-foundation/time-authority.yml` | `planned` |
| `PROC-HOST-ENROLMENT` | Host enrolment and network login | `l2-foundation` | 4.5 | `runbooks/l2-foundation/host-enrolment.md` | `ansible/l2-foundation/host-enrolment.yml` | `planned` |

### Epic 5 — Platform certificate authority

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-PLATFORM-CA` | Platform CA with ACME | `l2-foundation` | 5.1 | `runbooks/l2-foundation/platform-ca.md` | `ansible/l2-foundation/platform-ca.yml` | `planned` |
| `PROC-TRUST-DISTRIBUTION` | Trust distributed automatically | `l2-foundation` | 5.2 | `runbooks/l2-foundation/trust-distribution.md` | `ansible/l2-foundation/trust-distribution.yml` | `planned` |
| `PROC-CERT-RENEWAL` | Automatic issuance and renewal | `l2-foundation` | 5.3 | `runbooks/l2-foundation/cert-renewal.md` | `ansible/l2-foundation/cert-renewal.yml` | `planned` |

### Epic 6 — Kubernetes cluster with storage and gateway

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-CONTROL-PLANE` | Control plane across fault domains | `l3-platform` | 6.1 | `runbooks/l3-platform/control-plane.md` | `ansible/l3-platform/control-plane.yml` | `planned` |
| `PROC-WORKLOAD-CLUSTER-COMPOSITION` | Worker Guests and cluster composition in the repository | `l3-platform` | 6.2 | `runbooks/l3-platform/workload-cluster-composition.md` | `ansible/l3-platform/workload-cluster-composition.yml` | `planned` |
| `PROC-STORAGE-CLASSES` | Storage classes from the appliance | `l3-platform` | 6.3 | `runbooks/l3-platform/storage-classes.md` | `k8s/l3-platform/storage-classes/` | `planned` |
| `PROC-LB-ADDRESS-POOL` | Load balancer address pool | `l3-platform` | 6.4 | `runbooks/l3-platform/lb-address-pool.md` | `k8s/l3-platform/lb-address-pool/` | `planned` |
| `PROC-GATEWAY-TLS` | Gateway with automatic TLS | `l3-platform` | 6.5 | `runbooks/l3-platform/gateway-tls.md` | `k8s/l3-platform/gateway-tls/` | `planned` |

### Epic 7 — Identity provider and federation

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-IDP-DEPLOY` | Identity provider deployed | `l4-services` | 7.1 | `runbooks/l4-services/idp-deploy.md` | `k8s/l4-services/idp-deploy/` | `planned` |
| `PROC-IDP-FEDERATION` | Federation to the directory | `l4-services` | 7.2 | `runbooks/l4-services/idp-federation.md` | `k8s/l4-services/idp-federation/` | `planned` |
| `PROC-GROUP-CLAIMS` | Group membership as token claims | `l4-services` | 7.3 | `runbooks/l4-services/group-claims.md` | `k8s/l4-services/group-claims/` | `planned` |
| `PROC-CLIENT-REGISTRATION` | Client registration Procedure | `l4-services` | 7.4 | `runbooks/l4-services/client-registration.md` | `k8s/l4-services/client-registration/` | `planned` |

### Epic 8 — Reference application, end to end — SKELETON GATE

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-RECONCILIATION` | Reconciliation from the repository | `l3-platform` | 8.1 | `runbooks/l3-platform/reconciliation.md` | `ansible/l3-platform/reconciliation.yml` | `planned` |
| `PROC-REFERENCE-APP` | The operator's own application, authenticated | `l5-workloads` | 8.2 | `runbooks/l5-workloads/reference-app.md` | `k8s/l5-workloads/reference-app/` | `planned` |

### Epic 9 — Storage depth

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-HOME-DIRECTORIES` | Portable Home Directories | `l3-platform` | 9.1 | `runbooks/l3-platform/home-directories.md` | `ansible/l3-platform/home-directories.yml` | `planned` |
| `PROC-DATABASE-STORAGE` | Database storage off the appliance | `l4-services` | 9.2 | `runbooks/l4-services/database-storage.md` | `k8s/l4-services/database-storage/` | `planned` |

### Epic 10 — Identity depth

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-DIRECTORY-REPLICA` | Directory replica across fault domains | `l2-foundation` | 10.1 | `runbooks/l2-foundation/directory-replica.md` | `ansible/l2-foundation/directory-replica.yml` | `planned` |
| `PROC-CENTRAL-AUTHZ` | Central authorization and privilege escalation | `l2-foundation` | 10.2 | `runbooks/l2-foundation/central-authz.md` | `ansible/l2-foundation/central-authz.yml` | `planned` |
| `PROC-OFFLINE-CACHE` | Bounded offline credential cache | `l2-foundation` | 10.3 | `runbooks/l2-foundation/offline-cache.md` | `ansible/l2-foundation/offline-cache.yml` | `planned` |
| `PROC-REVOCATION-BOUNDS` | Revocation with recorded bounds | `l2-foundation` | 10.4 | `runbooks/l2-foundation/revocation-bounds.md` | `ansible/l2-foundation/revocation-bounds.yml` | `planned` |

### Epic 11 — Delivery depth

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-INTERNAL-REGISTRY` | Internal registry | `l4-services` | 11.1 | `runbooks/l4-services/internal-registry.md` | `k8s/l4-services/internal-registry/` | `planned` |
| `PROC-IMAGE-BUILD` | Images built from committed source | `l4-services` | 11.2 | `runbooks/l4-services/image-build.md` | `k8s/l4-services/image-build/` | `planned` |
| `PROC-WORKLOAD-ROLLBACK` | Rollback through the repository | `l5-workloads` | 11.3 | `runbooks/l5-workloads/workload-rollback.md` | `k8s/l5-workloads/workload-rollback/` | `planned` |

### Epic 12 — Stateful services

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-DATABASE-CLUSTER` | Replicated database cluster | `l4-services` | 12.1 | `runbooks/l4-services/database-cluster.md` | `k8s/l4-services/database-cluster/` | `planned` |
| `PROC-DATABASE-PROVISIONING` | Database provisioning for workloads | `l4-services` | 12.2 | `runbooks/l4-services/database-provisioning.md` | `k8s/l4-services/database-provisioning/` | `planned` |
| `PROC-DATABASE-ARCHIVING` | Continuous archiving and proven restore | `l4-services` | 12.3 | `runbooks/l4-services/database-archiving.md` | `k8s/l4-services/database-archiving/` | `planned` |
| `PROC-CACHE` | Cache available to workloads | `l4-services` | 12.4 | `runbooks/l4-services/cache.md` | `k8s/l4-services/cache/` | `planned` |

### Epic 13 — Observability

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-METRICS` | Metrics with bounded retention | `l4-services` | 13.1 | `runbooks/l4-services/metrics.md` | `k8s/l4-services/metrics/` | `planned` |
| `PROC-LOGS` | Centralised searchable logs | `l4-services` | 13.2 | `runbooks/l4-services/logs.md` | `k8s/l4-services/logs/` | `planned` |
| `PROC-STORAGE-HEALTH` | Storage and appliance health visible | `l4-services` | 13.3 | `runbooks/l4-services/storage-health.md` | `k8s/l4-services/storage-health/` | `planned` |
| `PROC-AUTH-EVENTS` | Authentication events recorded | `l4-services` | 13.4 | `runbooks/l4-services/auth-events.md` | `k8s/l4-services/auth-events/` | `planned` |
| `PROC-ALERTING` | Alerting in three independent tiers | `l4-services` | 13.5 | `runbooks/l4-services/alerting.md` | `k8s/l4-services/alerting/` | `planned` |

### Epic 14 — Secrets management

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-RUNTIME-SECRETS` | Runtime secret delivery | `l4-services` | 14.1 | `runbooks/l4-services/runtime-secrets.md` | `k8s/l4-services/runtime-secrets/` | `planned` |
| `PROC-ESCROW-REGISTER` | Escrow completeness | `l0-physical` | 14.2 | `docs/ESCROW.md` | none — by decision | `manual-by-decision` |

### Epic 15 — Power continuity

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-POWER-INVENTORY` | Battery-backed inventory | `l0-physical` | 15.1 | `runbooks/l0-physical/power-inventory.md` | none — by decision | `manual-by-decision` |
| `PROC-UPS-SIGNALLING` | UPS signalling to clients | `l0-physical` | 15.2 | `runbooks/l0-physical/ups-signalling.md` | `ansible/l0-physical/ups-signalling.yml` | `planned` |
| `PROC-SHUTDOWN-ORDER` | Ordered shutdown by measured margin | `l0-physical` | 15.3 | `runbooks/l0-physical/shutdown-order.md` | `ansible/l0-physical/shutdown-order.yml` | `planned` |
| `PROC-POWER-EVENTS` | Power events visible and alerted | `l0-physical` | 15.4 | `runbooks/l0-physical/power-events.md` | `ansible/l0-physical/power-events.yml` | `planned` |
| `PROC-POWER-DRILL` | The power drill | `l0-physical` | 15.5 | `runbooks/l0-physical/power-drill.md` | none — by decision | `manual-by-decision` |

### Epic 16 — Backup and verified restore

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-BACKUP-NATIVE` | Native backup per data class | `l3-platform` | 16.1 | `runbooks/l3-platform/backup-native.md` | `ansible/l3-platform/backup-native.yml` | `planned` |
| `PROC-BACKUP-COVERAGE` | Coverage enumerated, exclusions deliberate | `l3-platform` | 16.2 | `runbooks/l3-platform/backup-coverage.md` | `ansible/l3-platform/backup-coverage.yml` | `planned` |
| `PROC-RESTORE-DRILL` | Restores executed, not assumed | `l3-platform` | 16.3 | `runbooks/l3-platform/restore-drill.md` | `ansible/l3-platform/restore-drill.yml` | `planned` |

### Epic 17 — Single sign-on breadth

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-ACCOUNT-LOCK-MAPPING` | Account-lock mapping — build what does not ship | `l4-services` | 17.1 | `runbooks/l4-services/account-lock-mapping.md` | `k8s/l4-services/account-lock-mapping/` | `planned` |
| `PROC-WORKLOAD-CLUSTER-OIDC` | Cluster access through the identity provider | `l3-platform` | 17.2 | `runbooks/l3-platform/workload-cluster-oidc.md` | `ansible/l3-platform/workload-cluster-oidc.yml` | `planned` |
| `PROC-ADMIN-SSO` | Administrative interfaces behind one login | `l4-services` | 17.3 | `runbooks/l4-services/admin-sso.md` | `k8s/l4-services/admin-sso/` | `planned` |
| `PROC-FORWARD-AUTH` | Forward-auth for services without native support | `l4-services` | 17.4 | `runbooks/l4-services/forward-auth.md` | `k8s/l4-services/forward-auth/` | `planned` |

### Epic 18 — Destructive rebuild drill — DOCUMENTATION GATE

| Key | Title | Layer | Story | Runbook | Automation | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `PROC-PLATFORM-REBUILD` | Full platform rebuild Procedure | `l0-physical` | 18.1 | `runbooks/l0-physical/platform-rebuild.md` | `ansible/l0-physical/platform-rebuild.yml` | `planned` |
| `PROC-REBUILD-DRILL` | The destructive drill | `l1-hypervisor` | 18.2 | `runbooks/l1-hypervisor/rebuild-drill.md` | `ansible/l1-hypervisor/rebuild-drill.yml` | `planned` |

---

## Totals

The only place in the Repository where a Procedure count is stated. Every other document references
this section rather than restating a figure. The audit recomputes these from the tables above and
from `epics.md`; a disagreement is a defect, not a rounding.

| | Count |
| --- | --- |
| Stories in [`epics.md`](_bmad-output/planning-artifacts/epics.md) at `f5471f8` | 67 |
| Entries in this Index | 68 |
| Stories carrying two entries under the two-owner exception | 1 |
| `complete` | 2 |
| `incomplete` | 0 |
| `manual-by-decision` | 9 |
| `planned` | 57 |
| Human forms written (`manual-by-decision` entries) | 3 |

Per layer: `l0-physical` 13 · `l1-hypervisor` 8 · `l2-foundation` 12 · `l3-platform` 13 ·
`l4-services` 20 · `l5-workloads` 2.

Two `complete` entries are the accurate reading of a platform whose first Procedure against
hardware has not yet been executed: both — `PROC-CONVERGENCE-HARNESS` and `PROC-REPO-SECRETS` — run
on the control node and touch no managed system. The `planned` entries are the denominator FR-1 was
missing.

Every figure above is recomputed by `pixi run audit` from the entry tables and from `epics.md`;
"Human forms written" is recomputed from the filesystem. Its label now names its scope, because it
totals the "Human form written?" column of [Deliberately manual work](#deliberately-manual-work)
and nothing else — Runbook presence for the other statuses is what those statuses already record,
and a figure whose scope has to be inferred is a figure that will be recomputed wrongly. A figure
this file states that the audit does not know how to recompute is itself reported as a defect,
because a number nothing checks is a number that goes stale.

### What these counts do and do not measure

The Index is a denominator for FR-1 — "every operational activity is documented" — and for nothing
else. Two nearby claims it does **not** support, stated here because an earlier draft of this file
implied both:

- **SM-1 is not counted here.** Its denominator is undocumented *steps encountered during a Node
  rebuild*, and it is measured by executing the drill in story 18.2 — not by counting Index entries.
  A complete Index with a badly written Runbook scores perfectly here and fails SM-1 outright.
- **SM-2 is rescoped by this Index, deliberately and visibly.** "Convergence holds for every
  Procedure" can only be evaluated where there is an Automation to converge. The
  `manual-by-decision` entries have none by decision, so they are outside SM-2's reach: their
  equivalent evidence is the named verification in
  [Deliberately manual work](#deliberately-manual-work), which is a weaker guarantee and is not
  interchangeable with a zero-changes run. SM-2 therefore covers the entries with an Automation half
  — the `planned`, `incomplete`, and `complete` rows — and the manual entries are measured
  separately. Reading the entry total as SM-2's denominator would overstate convergence coverage by
  the size of the manual set.

---

## Alert sources

AD-23 requires the push-based layers (L0–L2) to carry scheduled check-mode runs whose non-empty diff
exits non-zero, and story 5.3 requires certificate-renewal failure to be detected before expiry.
Those detectors register **in the table below**, and story 13.5 wires every registered source to
notification. A source registered and left unwired when 13.5 completes is a defect against 13.5.

**How registration works:** the story that builds a detector adds its row here, in the same change
that builds it. That is the single rule; [`runbooks/TEMPLATE.md`](runbooks/TEMPLATE.md) states the
same one from the writer's side. Registration is not deferred to 13.5 — 13.5 consumes this table, it
does not populate it.

Story 1.3 built the first three detectors and registered them below; story 1.4 added the fourth, and
story 2.1 the fifth. They are the harness's own runs,
not any Procedure's check-mode run: the four required by the epics above — one per push-based
Automation — still do not exist, because no push-based Automation exists. `pixi run drift` is the
mechanism those four will register through; it reports zero targets today and says so rather than
reporting a pass over an empty set.

A detector that runs *inside* an already-registered task still gets its own row. The alternative is
a table that stops growing while the thing it enumerates does not, and 13.5 consumes this table —
it would wire a source it can see and silently miss one folded into another source's row.

| Source | Registering story | Wired by | Status |
| --- | --- | --- | --- |
| `pixi run drift` — scheduled check-mode run over the push-based layers L0–L2. A non-empty diff exits non-zero, as does a run that failed to complete; every run is recorded to `drift-record.json` | 1.3 | 13.5 | Registered, unwired |
| `pixi run audit` — the Index and ownership audit. Any defect class named exits non-zero | 1.3 | 13.5 | Registered, unwired |
| `pixi run audit` — the address-plan consistency check over [`docs/ADDRESS-PLAN.md`](docs/ADDRESS-PLAN.md): collisions, statics inside the DHCP pool, a Node on one segment only, a consumed reservation, a route on the isolated segment, an illegal kind, a range that does not tile its segment, an address in no declared range. Runs inside the audit task and exits non-zero on any of them | 2.1 | 13.5 | Registered, unwired |
| `pixi run converge` — scheduled AD-3 convergence and NFR-3 idempotence run: every Automation run twice, first run for convergence and second for idempotence. A check-mode run that *failed to complete* exits non-zero too, and is never read as a clean run | 1.3 | 13.5 | Registered, unwired |
| `pixi run secrets` — the plaintext-secret and encryption-policy scan over every tracked file. Runs at commit time through the hook in `.pre-commit-config.yaml` and in the gate through `pixi run ci`; any defect named exits non-zero | 1.4 | 13.5 | Registered, unwired |

---

## Defects this Index reports

Story 1.3 builds the audit. **It is not built here.** These are the defect classes it must detect,
stated so 1.3 has a specification rather than an intuition. Each fails loudly; none is a warning.

**Entry-level:**

- **Incomplete Procedure** — an entry with exactly one half present where both are required. The
  audit fails and names the key and the missing half. It never downgrades the entry to
  `manual-by-decision` to make the failure go away: that status is a decision recorded in the
  architecture, not a way out of an unfinished Procedure. *This is the single definition of the rule;
  [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) names it and supplies the ownership-side input rather than
  restating it.*
- **Status disagrees with the filesystem** — an entry whose status is `complete` while a named path
  is absent, or `planned` while a half exists. The audit fails and names the key. A stale status is
  worse than an honest `planned`, because it is the one reading nobody re-checks.
- **Illegal status value** — a Status cell outside the closed set. The audit fails and names the
  entry. The rules above are only checkable because the column is an enumeration.
- **Missing verification on a `manual-by-decision` entry** — a deliberately-manual Procedure with no
  named verification. Execution being manual is a decision; verification being absent is a gap.
- **Unwritten human form on a `manual-by-decision` entry** — an entry whose Runbook path does not
  exist. Because the status does not track file presence for these entries, nothing else would catch
  it. The audit fails and names the key. Most are unwritten today and that is expected while their
  owning stories are unstarted; the rule exists so the count cannot quietly stop shrinking.
- **Mismatched manual literal** — an entry whose Automation cell is `none — by decision` without the
  status `manual-by-decision`, or the reverse. The two are one fact recorded twice and must agree.

**Namespace-level:**

- **Duplicate key** — two entries sharing a key, or two entries resolving to the same Runbook path.
  The audit fails and names both entries. A shared key makes every reference ambiguous; a shared
  Runbook path means one of the two Procedures has no human form of its own.
- **Retired key reused** — an entry using a key listed under *Retired keys*. The audit fails and
  names it.

**Index-to-story:**

- **Story with no entry** — a story in `epics.md` with no Index entry. The audit fails and names the
  story. This is the rule that keeps the Index a *requirements* enumeration rather than an inventory
  of what happens to exist.
- **Entry with no story** — an entry whose Story cell names a story absent from `epics.md`. The audit
  fails and names the entry.
- **Story over its entry allowance** — a story with more than one entry that is not listed in the
  two-owner exception table, or any story with more than two entries at all. Three Procedures for one
  story is mis-scoping, and the exception exists to be narrow.
- **Stale provenance** — the recorded source commit for `epics.md` no longer matching the file's
  current commit. The story list may have changed under the Index; a human re-derives and updates
  the provenance line.

**Cross-document:**

- **Broken back-reference** — a Runbook whose `procedure_automation` does not resolve to the
  Automation the Index names, or an Automation whose `procedure_runbook` does not resolve to the
  Runbook the Index names. The contract is bidirectional; a one-way reference is half a contract.
  Subject to the two exemptions in [The dual-form contract](#the-dual-form-contract).
- **Unfilled template sentinel** — a `procedure_key` or `procedure_automation` front-matter field
  carrying `TEMPLATE-UNFILLED` in any file under `runbooks/` other than `TEMPLATE.md`. Scoped to
  the front-matter fields, not to the string: documents that discuss the sentinel are not defects.
- **Ownership class with no covering Procedure** — a resource class in
  [`docs/OWNERSHIP.md`](docs/OWNERSHIP.md) whose Procedure column names no Index key, or names one
  that does not exist here. Many classes may map to one Procedure; zero is not permitted, because an
  uncovered class is a declaration nobody has committed to documenting.
- **Totals disagree with the tables** — any figure in [Totals](#totals) that the audit recomputes
  differently from the entry tables and from `epics.md`. The Totals section is the one place a count
  is stated, which is precisely why it is the one place a wrong count would propagate from.

An activity performed that has no entry here is itself a defect: it is recorded in the Index and
closed before the activity counts as complete (story 1.2 acceptance criteria).

---

## Open questions for human decision

Surfaced rather than resolved, because resolving them silently is how a wrong answer becomes
permanent.

- **No story produces zero Procedures.** Every story in `epics.md` maps to at least one operational
  activity, so nothing is listed here today. When a story that produces no operational activity is
  written, it is surfaced here for a human decision and never silently omitted from the Index.
