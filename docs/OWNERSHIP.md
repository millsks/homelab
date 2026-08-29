# Declarative Ownership

Governed by **AD-22**. Every configurable resource class in Project Asgard has **exactly one**
declaring owner. Zero owners and two owners are both defects: a class with none means the
Repository's rebuildability claim is false for that class, and a class with two means two
mechanisms can both write it, which the convergence harness structurally cannot detect —
each tool reports zero changes against its own declaration while the two declarations disagree.

## How to read this table

- **Resource class** — a set of configurable attributes that move together. The unit of ownership,
  not the unit of hardware. One appliance can host several classes; one class can span several hosts.
- **Owner** — the single mechanism authorised to *declare* the class. Everything else may read it.
  Drawn from the closed enumeration below; free text is not permitted.
- **Declaring mechanism** — where in this Repository that declaration physically lives, so a
  reader can go from a class to a file without guessing.
- **Verification** — how the declaration is checked against reality. Every class has one, including
  the classes no automation executes. Execution can be manual; verification is automated wherever
  a machine can observe the result.

### Legal Owner values

The Owner column is a closed enumeration. Story 1.3's audit parses it, so a value outside this
list is itself a defect — a sentence in the Owner column cannot be checked mechanically.

| Owner value | Means | Declarations live in |
| --- | --- | --- |
| `OpenTofu` | Provisioning: virtual hardware and Guest existence | `tofu/` |
| `Ansible` | Push configuration: everything inside a host OS | `ansible/` |
| `Kubernetes manifests` | Reconciled in-cluster state, pulled by Argo CD | `k8s/` |
| `Runbook` | **Human-executed.** No Automation half, by decision | `runbooks/` |
| `docs/ record` | **Human-maintained** declaration, consumed by automation but not executed by it | `docs/` |
| `SOPS + age` | Encryption at rest for Repository-stored secret material | `.sops.yaml` and encrypted files in place |
| `Repository tooling` | The convergence gate's own configuration | repository-root tool configuration files |
| `Delegated` | Owned by whichever owner declares the class it attaches to. **Exempt from the one-owner check** — see Audit | co-located with each declaration |

`Runbook` and `docs/ record` both mean human-executed, and neither ever means "not yet automated":

- **`Runbook`** — a Procedure a person carries out, step by step.
- **`docs/ record`** — a declaration a person maintains as a document. An address plan is not run;
  it is read.

Human-executed classes still appear in the Procedure Index, marked as having no Automation half,
and they still carry an automated verification wherever a machine can observe the result.

### Forward references

Three declaring mechanisms named below do not exist yet. They are listed so the class has a stated
home rather than a blank, and each is marked *(forward reference — story N)* in the table. They are
deliberately not stubbed: writing a placeholder before the owning story defines the format produces
a file that story then has to undo.

| Path | Owed by |
| --- | --- |
| `.sops.yaml` | Story 1.4 — encrypted secrets |
| `docs/ESCROW.md` | Story 1.4 — escrow register |
| `docs/ADDRESS-PLAN.md` | Not yet scheduled; a later L0 network story |

This file otherwise holds itself to the rule it states: every other path named below exists.

## The provisioning/configuration boundary

The split between OpenTofu and Ansible is drawn **by attribute, never by moment in time**.
"The guest's first boot" is not a boundary, because first-boot provisioning sits precisely on it —
cloud-init can set an address, and so can Ansible, and both are technically correct.

| | OpenTofu declares | Ansible declares |
| --- | --- | --- |
| Guest existence, name, VMID, target Node | yes | no |
| Virtual hardware: vCPU, memory, disks, NICs, boot order | yes | no |
| Template the guest clones from | yes | no |
| **Exactly one** bootstrap SSH public key | yes | no |
| In-guest IP address, netmask, gateway, DNS resolvers | **no** | yes |
| Hostname as the OS reports it | **no** | yes |
| User accounts, groups, passwords, further SSH keys | **no** | yes |
| Packages, services, files, sysctl, firewall, mounts | **no** | yes |

OpenTofu's handover to Ansible is exactly one thing: **a reachable SSH endpoint authenticated by
the bootstrap key**. Nothing else crosses.

Where a mechanism *can* express an attribute belonging to the other owner, **leaving it unset is
mandatory, not stylistic**. cloud-init's `user`, `password`, `ip_config`, and `nameserver` fields
are available in the Proxmox provider and are deliberately not used beyond the single bootstrap key.
Setting them "just to get the guest reachable" is the exact defect AD-22 exists to prevent: it
creates a second authoritative declaration of the address, and the guest then converges against
whichever tool ran last.

The bootstrap key is single and disposable. Ansible replaces the authorised-key set on first run;
the bootstrap key is not a long-lived administrative credential and is not in the escrow set.

### Where Guests physically land

Node placement is an **OpenTofu** attribute everywhere, without exception, because it is a property
of the Guest's definition rather than of anything inside it. A rule such as AD-26's "no two replicas
share a Node" is therefore *stated* by the layer that cares about it and *declared* in
`tofu/l1-hypervisor/`. Ansible never places a Guest.

---

## L0 — Physical

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| Rack layout, Node placement, cabling map | `Runbook` | `runbooks/l0-physical/` | Manual, against the stated cabling map | Human-executed by decision. |
| Outlet allocation and UPS wiring | `Runbook` | `runbooks/l0-physical/` | Automated: a load-and-runtime read from the UPS daemon, compared to the declared allocation | Which device is on which protected outlet is the whole point; an unprotected Node is invisible until the outage. |
| Node firmware / BIOS settings (boot order, virtualisation extensions, power-loss behaviour, firmware admin password) | `Runbook` | `runbooks/l0-physical/` | Automated where readable from the host OS; direct firmware-screen reading otherwise | Firmware survives an OS reinstall. AD-28: "we reimaged it" is not a check. |
| Out-of-band management state (enabled/disabled, credentials, network) | `Runbook` | `runbooks/l0-physical/` | Automated: port probe from another host **plus** a direct firmware-screen reading | AD-28. State is declared and verified, never inherited. Credentials escrow under AD-24. |
| Household router (Google WiFi) and the uplink | `Runbook` | `runbooks/l0-physical/` | Automated: outbound reachability check | Outside the platform's declarative boundary. Recorded so it is not mistaken for unowned. |
| Wireless bridge (TL-WA3001, client mode) | `Runbook` | `runbooks/l0-physical/` | Automated: link check across the bridge | No management API worth declaring against. |
| Data switch (NICGIGA 10-port, unmanaged) | `Runbook` | `runbooks/l0-physical/` | Automated: link-state and negotiated-speed read from each attached host | Unmanaged: the only configuration is which port a cable is in. That is still a configuration item. |
| Membership switch (Omada ES205G, managed, isolated, no uplink) | `Runbook` | `runbooks/l0-physical/` | Automated: exported running configuration compared against the committed reference export | The **managed switch** required by AD-22's total-coverage rule. Human-executed because no controller is in the Stack; the verification is still automated. |
| Address plan (static assignments, membership segment, DHCP pool boundaries) | `docs/ record` | `docs/ADDRESS-PLAN.md` *(forward reference — later L0 story)* | Automated: declared addresses reconciled against Directory DNS and against what hosts actually answer | Never discovered from running systems. Consumed by Ansible and by DNS; declared in neither. |

## L1 — Hypervisor

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| Proxmox VE installation on each Node (initial install to first boot) | `Runbook` | `runbooks/l1-hypervisor/` | Automated: version, repository set, and cluster-readiness read from the installed host | Human-executed by decision — one of the fourteen `Runbook` classes in this table, and one of the three the architecture calls out as genuinely manual (this, L0 physical work, and storage-appliance initial setup). Note these are *classes*, not layers: no layer is automation-free. L1 alone mixes `Runbook`, `Ansible`, and `OpenTofu` owners, and most L0 classes carry an automated verification even where execution is manual. |
| Proxmox host operating system configuration (repositories, packages, sysctl, host firewall, administrative accounts, local storage and Proxmox storage definitions) | `Ansible` | `ansible/l1-hypervisor/` | Automated: scheduled check-mode run, non-empty diff exits non-zero (AD-23) | The **hypervisor host OS** required by AD-22's total-coverage rule. **Excludes** the time source (owned at L2) and **excludes** NFS client mounts (owned at L3) — see both rows. |
| Proxmox cluster membership and quorum configuration | `Ansible` | `ansible/l1-hypervisor/` | Automated: check-mode run plus a quorum read | Cluster formation is scriptable; only the OS install below it is manual. |
| Guest OS templates (cloud images built once, cloned many times) | `Runbook` | `runbooks/l1-hypervisor/` | Automated: checksum of the stored template against the declared source image and build steps | Built from an upstream cloud image by a stated Procedure. Pinned exactly (AD-20). |
| Guest existence, virtual hardware, Node placement, and the one bootstrap SSH key | `OpenTofu` | `tofu/l1-hypervisor/` | Automated: `tofu plan` reports no changes | Scope is strictly the table under "The provisioning/configuration boundary". **Excludes in-guest addressing, accounts, and passwords.** Node placement for *every* Guest is declared here, including L2's Directory replicas. |
| Guest in-OS identity: hostname, addressing, resolvers, accounts, passwords, authorised keys | `Ansible` | `ansible/l1-hypervisor/`, `ansible/l2-foundation/` | Automated: check-mode run | Owned here even though cloud-init can set all of it. AD-22's whole point. |
| Hypervisor backup jobs (Guest dumps, schedule, retention, target) | `Ansible` | `ansible/l1-hypervisor/` | Automated: an **executed restore**, not the job's existence (AD-21) | A backup that has never been restored does not count as present. |
| **OpenTofu provisioning state** (state file location, backend, locking behaviour) | `OpenTofu` | `tofu/` backend configuration | Automated: a lock-contention test and a state-read from a second machine | The **provisioning tool's own state** required by AD-22. It is an owned, versioned artefact with an escrow entry (AD-24), not a byproduct. State and `*.tfvars` are gitignored: state holds provider-marked-sensitive attributes and this Repository is public. |

## L2 — Foundation

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| Directory server (FreeIPA on `mimir`) installation and configuration | `Ansible` | `ansible/l2-foundation/` | Automated: check-mode run | |
| Directory replica **Guest placement** (which Node each replica lands on) | `OpenTofu` | `tofu/l1-hypervisor/` | Automated: `tofu plan` reports no changes, plus a placement read | AD-26 requires the replica not share a Node with the primary. The *rule* is an L2 concern; the *declaration* is explicit Node assignment in OpenTofu, so OpenTofu owns it. Split from the row below so owner and declaration agree. |
| Directory replication agreements and replica enrolment | `Ansible` | `ansible/l2-foundation/` | Automated: check-mode run plus a replication-status read | Everything about the replica *except* where it lands. |
| POSIX UID/GID numeric ranges | `Ansible` | `ansible/l2-foundation/` | Automated: numeric identity read back after a rebuild | AD-25. Supplied at Directory installation; the product's randomised default range is prohibited. |
| Directory accounts, groups, sudo rules, HBAC rules | `Ansible` | `ansible/l2-foundation/` | Automated: check-mode run | |
| DNS zones and records (`asgard.home.arpa`) | `Ansible` | `ansible/l2-foundation/` | Automated: resolution check for every declared name | Directory-hosted. |
| Kerberos realm and policy | `Ansible` | `ansible/l2-foundation/` | Automated: check-mode run plus a ticket acquisition | |
| Time source and client configuration on every host, Nodes included | `Ansible` | `ansible/l2-foundation/` | Automated: offset read from every host | AD-6: every host points at the Directory. Sole owner of the time source — the L1 host-OS row explicitly excludes it, because a Node's clock is a foundation concern and declaring it twice is exactly the AD-22 defect. |
| Platform CA (step-ca on `draupnir`), roots, intermediates, ACME provisioner | `Ansible` | `ansible/l2-foundation/` | Automated: chain validation from a client that trusts only the platform root | AD-5. The CA root key escrows under AD-24. |
| Platform root trust distribution to hosts | `Ansible` | `ansible/l1-hypervisor/`, `ansible/l2-foundation/` | Automated: check-mode run | |

## L3 — Platform

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| k3s installation and server/agent flags on each Guest | `Ansible` | `ansible/l3-platform/` | Automated: check-mode run plus a node-readiness read | The cluster's *existence* is push-based; everything inside it is not. |
| Cluster bootstrap credentials and the static administrative credential | `Ansible` | `ansible/l3-platform/` | Automated: an authenticated call using the escrowed credential | Escrows under AD-24. |
| Delivery controller (Argo CD) installation and its root application | `Ansible` | `ansible/l3-platform/` | Automated: check-mode run; thereafter Argo CD reconciles itself | The single hand-off point from push to pull. Everything below this row in L3–L5 is reconciled, not pushed. |
| In-cluster platform components: MetalLB, Envoy Gateway, cert-manager, CSI drivers, storage classes | `Kubernetes manifests` | `k8s/l3-platform/` | Automated: continuous reconciliation with self-heal and prune (AD-23) | No imperative `kubectl apply` in any Procedure. |
| Namespaces, RBAC, network policy, Gateways and routes | `Kubernetes manifests` | `k8s/l3-platform/` | Automated: continuous reconciliation | |
| Storage appliance (Synology DS925+) initial setup: DSM install, SHR-2 pool, volume creation | `Runbook` | `runbooks/l3-platform/` | Automated: pool health, redundancy level, and volume geometry read from the DSM API | Human-executed by decision — one of the three the architecture calls out as genuinely manual. |
| Storage appliance ongoing configuration: shares, NFS exports, export permissions, snapshot schedules, replication targets | `Runbook` | `runbooks/l3-platform/` | Automated: state read back from the DSM API and compared against the declared configuration | The **storage appliance** required by AD-22's total-coverage rule. No DSM module ships in `ansible-core` and no official vendor collection exists, so an `Ansible` owner would assert an Automation half that cannot be built — AD-3 forbids that. **Open spike:** whether `ansible.builtin.uri` against the DSM Web API is stable enough across DSM upgrades to own declaration. If it proves out, this row moves to `Ansible` in the same change that moves the declaration. |
| NFS client mount semantics on **every** consumer, Proxmox Nodes and Guests alike (export, options, automount) | `Ansible` | `ansible/l3-platform/` | Automated: check-mode run asserting `hard` plus automount | AD-8: `soft` is prohibited. Sole owner of NFS client mounts anywhere in the platform; the L1 host-OS row excludes them so a Node mounting the appliance has one owner, not two. Local and Proxmox-native storage stays with L1. |

## L4 — Platform services

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| Identity provider (`forseti`, Keycloak): realms, clients, federation to the Directory | `Kubernetes manifests` | `k8s/l4-services/` | Automated: continuous reconciliation plus a token acquisition with expected group claims | |
| Databases (`fafnir`, CloudNativePG): clusters, replicas, continuous archiving | `Kubernetes manifests` | `k8s/l4-services/` | Automated: continuous reconciliation plus an **executed restore** | AD-21. Archiving to shared storage is a precondition of the database running, not a later concern. |
| Cache (`ratatoskr`), registry (Harbor), CI, observability stack | `Kubernetes manifests` | `k8s/l4-services/` | Automated: continuous reconciliation | |
| Runtime secret store (`andvari`, OpenBao): policies, auth methods, mounts | `Kubernetes manifests` | `k8s/l4-services/` | Automated: continuous reconciliation | Unseal material escrows under AD-24. Not to be confused with the Repository-stored secret material below. |
| Certificate issuance for platform services | `Kubernetes manifests` | `k8s/l4-services/` | Automated: expiry and chain check | AD-5: ACME only. No manual installation, no self-signed certificate outside the platform chain. |

## L5 — Workloads

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| The operator's own applications: deployments, configuration, routes, storage claims | `Kubernetes manifests` | `k8s/l5-workloads/` | Automated: continuous reconciliation with self-heal and prune | |
| Workload replica placement across fault domains | `Kubernetes manifests` | `k8s/l5-workloads/` | Automated: reconciliation plus a placement read | AD-26: enforceable anti-affinity, never convention. Workload placement is in-cluster and therefore unrelated to Guest Node placement, which is OpenTofu's. |

## Cross-cutting

| Resource class | Owner | Declaring mechanism | Verification | Notes |
| --- | --- | --- | --- | --- |
| **Control node**: the machine that runs `ansible-playbook` and `tofu apply`, holding the bootstrap key, the provisioning-state credentials, and the SOPS decryption key | `Runbook` | `runbooks/l0-physical/` | Automated: a rebuild-from-Runbook check that the rebuilt node can decrypt, plan, and reach every managed host | **Escrow-relevant under AD-24.** Whatever this machine holds that exists nowhere else is an escrow entry, and AD-24 forbids recovery depending on any single un-escrowed machine — a control node that is the only holder of the decryption key fails that rule outright. Recorded here so the machine that runs the automation is not the one thing the ownership table forgets. |
| Git remote: hosting location, access control, branch protection, and who may push | `Runbook` | `runbooks/l0-physical/` | Automated: a clone from a second machine, plus a probe that a direct push to the default branch is refused | The Repository *is* the desired state (AD-4), so the thing that hosts it is a configuration item. Human-executed through the hosting provider; no declarative mechanism is in the Stack. |
| Convergence tooling: the CI gate, its tasks, linter configuration, and dependency pins | `Repository tooling` | `pixi.toml`, `pyproject.toml`, `.yamllint`, `.gitignore` | Automated: `pixi run ci` exits 0, and each guarded task reports whether it ran or skipped rather than silently passing | The harness that grades every other row has to be owned too. Task guards use an explicit `if`, never a short-circuit chain ending in an echo, because that shape reports success on real failure. |
| Repository-stored secret material (encryption at rest) | `SOPS + age` | `.sops.yaml` *(forward reference — story 1.4)* | Automated: a commit-time check that rejects plaintext and names the offending path | The decrypting key is itself an escrow entry (AD-24) and is held by the control node above. |
| Escrow register (what is held outside Asgard, where, and how it rotates) | `docs/ record` | `docs/ESCROW.md` *(forward reference — story 1.4)* | Manual review on a stated cadence; the list is itself the artefact under review | AD-24: an exhaustive enumerated list, not a set of examples. |
| Procedure enumeration (which Procedures exist, their layer, and whether both halves are present) | `docs/ record` | [`PROCEDURE-INDEX.md`](../PROCEDURE-INDEX.md) | Automated: the convergence harness reports Index entries missing either half | Story 1.2 defines it; story 1.3 verifies it. |
| This ownership table | `docs/ record` | `docs/OWNERSHIP.md` | Automated: an audit that fails and **names the class** on any class with two owners or none | See Audit below. |
| Component version pins | `Delegated` | co-located with each declaration | Automated: pin comparison against installed versions | AD-20. `latest` is prohibited. A pin is an attribute of the thing it pins, so it is owned by that thing's owner. **Exempt from the one-owner check** — see Audit. |

## Audit

The audit that keeps this table honest is built in story 1.3 and runs against the Procedure Index.
Three rules are defined here so the audit has a specification to implement:

- **Two-owner defect** — a resource class reachable from two Owner rows. The audit fails and names
  the class. It does **not** pick a winner: choosing one silently is how a wrong owner becomes
  permanent. Resolution is a human decision recorded as a change to this file.
- **Unowned defect** — a configurable resource class present in the platform and absent from this
  table. The audit fails and names the class. A class awaiting automation is recorded here as
  `Runbook` with its verification named; it is never left blank and never omitted.
- **Illegal Owner value** — an Owner cell whose contents are not one of the values in "Legal Owner
  values". The audit fails and names the row. This rule exists because the first two are only
  checkable if the column is an enumeration; a sentence in the Owner column defeats both.

Both defect rules fail loudly. Neither is a warning.

**Exemptions.** Exactly one Owner value is exempt from the one-owner check: `Delegated`. It means
the class attaches to another class and is owned by whatever owns that one — a version pin belongs
to the declaration it pins, so it legitimately resolves to many owners at once. Treating that as a
two-owner defect would make the audit fail on a correct table, so the audit skips `Delegated` rows
for the one-owner check while still applying the illegal-value and verification-present checks.
No other exemption exists, and adding one requires changing this section.

## Changing an owner

Ownership moves by editing this file in the same change that moves the declaration. A commit that
moves a declaration from one mechanism to another without updating this table produces a two-owner
window, which is the defect this table exists to prevent — the old mechanism still declares the
attribute until its declaration is removed.
