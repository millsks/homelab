---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'step-04-final-validation']
status: complete
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-homelab-2026-08-28/prd.md
  - _bmad-output/planning-artifacts/architecture/architecture-homelab-2026-08-28/ARCHITECTURE-SPINE.md
  - _bmad-output/planning-artifacts/architecture/architecture-homelab-2026-08-28/SOLUTION-DESIGN.md
  - _bmad-output/planning-artifacts/architecture/architecture-homelab-2026-08-28/DIAGRAMS.md
  - _bmad-output/planning-artifacts/briefs/brief-homelab-2026-08-28/brief.md
  - _bmad-output/planning-artifacts/briefs/brief-homelab-2026-08-28/addendum.md
---

# Project Asgard - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Project Asgard, decomposing the requirements from the PRD, UX Design if it exists, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

**Procedure Discipline**

- **FR-1**: Every procedure exists in both forms, against an enumerated set
- **FR-2**: Manual execution produces a converged system
- **FR-3**: Documentation defects are resolved at discovery
- **FR-4**: All configuration originates in the Repository
- **FR-5**: Procedures declare their verification

**Hypervisor Foundation**

- **FR-6**: Four Nodes form one Cluster
- **FR-7**: A Node can be rebuilt from the Repository
- **FR-8**: Guests are provisioned declaratively
- **FR-9**: Guests can be snapshotted and rolled back
- **FR-10**: The Cluster is manageable when the Directory is unavailable

**Network and Name Resolution**

- **FR-11**: Every Node, Guest, and service is reachable by name
- **FR-12**: Addressing is deterministic and recorded
- **FR-13**: Name resolution survives a single failure
- **FR-14**: Household devices are unaffected

**Shared Storage**

- **FR-15**: Home Directories are identical on every host
- **FR-16**: Storage unavailability degrades rather than hangs
- **FR-17**: Workloads obtain Persistent Volumes on demand
- **FR-18**: PostgreSQL does not run on NFS
- **FR-19**: Storage capacity and health are visible

**Identity and Directory**

- **FR-20**: One Account authenticates to every host
- **FR-21**: Authorization is driven by Group membership
- **FR-22**: Disabling an Account revokes host access within a bounded window
- **FR-23**: Hosts authenticate during a Directory outage for known Accounts
- **FR-24**: Break-glass access exists on every host and survives storage loss
- **FR-25**: The Directory survives loss of one instance
- **FR-26**: Accounts are defined in the Repository

**Certificate Authority**

- **FR-27**: One authority issues all internal certificates
- **FR-28**: Trust is distributed automatically
- **FR-29**: Certificates renew without manual action

**Single Sign-On and Federation**

- **FR-30**: The IdP federates to the Directory
- **FR-31**: Group membership appears in Tokens as claims
- **FR-32**: Administrative interfaces authenticate through the IdP
- **FR-33**: Workloads can be registered as Relying Parties
- **FR-34**: Services without native OIDC are fronted
- **FR-35**: Account disablement propagates to Relying Parties within stated, per-party bounds
- **FR-36**: Authentication events are recorded

**Kubernetes Platform**

- **FR-37**: Yggdrasil survives loss of one Control Plane Guest
- **FR-38**: Control Plane Guests are distributed across Nodes
- **FR-39**: `kubectl` authenticates through the IdP
- **FR-40**: Yggdrasil is rebuildable from the Repository
- **FR-41**: Workloads reach the network by stable name

**Continuous Delivery**

- **FR-42**: Workload state reconciles from the Repository
- **FR-43**: Container images are built and stored within Asgard
- **FR-44**: A new application reaches production by a documented path
- **FR-45**: Deployments can be rolled back

**Stateful Services**

- **FR-46**: Workloads can obtain a database
- **FR-47**: PostgreSQL is backed up and restorable
- **FR-48**: Redis is available to Workloads

**Observability**

- **FR-49**: Platform metrics are collected and retained
- **FR-50**: Logs are centralized and searchable
- **FR-51**: Failures generate alerts
- **FR-52**: Dashboards authenticate through the IdP

**Secrets Management**

- **FR-53**: No plaintext secret is committed
- **FR-54**: Workloads obtain secrets without manual injection
- **FR-55**: Break-glass credentials are held outside Asgard

**Power Continuity**

- **FR-56**: The platform shuts down cleanly on sustained power loss
- **FR-57**: Shutdown order is achieved by tuned delay, with proven margin
- **FR-58**: All shutdown participants remain powered until they act
- **FR-59**: Power events are visible and alerted
- **FR-60**: The Shutdown Sequence is proven by Drill

**Backup and Recovery**

- **FR-61**: Platform state is backed up automatically
- **FR-62**: Backups survive loss of any single Node
- **FR-63**: Restores are verified, not assumed
- **FR-64**: The platform can be rebuilt from Repository and backups

**Network and Name Resolution**

- **FR-65**: Nodes are wired, dual-homed, and separate membership traffic from bulk traffic

### NonFunctional Requirements

**Documentation Quality**

- **NFR-1**: Every Procedure is executable by the operator six months later with no recall of building it. Ambiguity is a defect.
- **NFR-2**: Runbooks state reasoning, not only commands. A step whose purpose is unstated cannot be evaluated when conditions differ.
- **NFR-3**: Automation is idempotent without exception. Any Automation that fails on a second run is defective.
- **NFR-4**: Procedures are versioned with the systems they describe; a change to a system and to its Procedure land together.
- **NFR-5**: Where a Runbook and its Automation disagree, the Automation is authoritative for *what* and the Runbook for *why*, and the disagreement is a defect to be closed rather than tolerated.

**Capacity**

- **NFR-6**: Capacity is bounded from two sides so it cannot be satisfied by relocating a service. **(a)** Total committed Guest memory across the Cluster does not exceed 90 GB of the 128 GB physical, and **(b)** at least 15 GB remains schedulable…
- **NFR-7**: Loss of any one Node leaves sufficient capacity to run all identity, storage, and Yggdrasil control functions, though not necessarily all Workloads. NFR-6's 90 GB ceiling exists to make this achievable: three Nodes provide 96 GB.
- **NFR-8**: Observability retention is bounded so storage growth is predictable rather than discovered at exhaustion.
- **NFR-9**: Guests declare explicit memory limits; no component relies on unbounded default sizing.

**Security**

- **NFR-10**: No credential, key, or token exists in plaintext in the Repository or its history.
- **NFR-11**: Every HTTPS and OIDC endpoint in Asgard presents a certificate chaining to Draupnir, and no such endpoint is served over plaintext HTTP. Named exclusions, which use their own transport security rather than Draupnir certificates: SSH…
- **NFR-12**: Direct remote root login is disabled on every Node and Guest; privilege escalation is through a named Account.
- **NFR-13**: Break-glass credentials are unique per host, not shared.
- **NFR-14**: No Asgard service is reachable from the internet, and no inbound path from outside the LAN exists. Access requires presence on the local network.
- **NFR-15**: Authentication events are recorded and retained per FR-36 and FR-50.

**Reliability**

- **NFR-16**: Identity, storage, and Yggdrasil control tolerate loss of one Node without operator intervention.
- **NFR-17**: No unattended failure results in data corruption. Availability may be sacrificed; integrity may not.
- **NFR-18**: Every recovery Procedure is proven by execution before being relied upon. Configured-but-untested is treated as not present.
- **NFR-19**: Failure conditions are detected and alerted rather than discovered during use.

**Operability**

- **NFR-20**: The operator can determine current platform state from the Repository and the observability system without logging into individual hosts.
- **NFR-21**: Routine operations require no Break-glass credential.
- **NFR-22**: Adding a Node, Guest, or Workload follows an existing Procedure rather than requiring a new one.
- **NFR-23**: Snapshot-before-change is available for every Guest, so experimentation is cheap by default.

### Additional Requirements

Extracted from the architecture spine (28 ADs), which is **binding** on every story. Each story cites the ADs governing it alongside the FRs it realizes.

**No code starter template applies** — this is an infrastructure platform, not a codebase. Its equivalent, and therefore the true first story, is the **Repository skeleton plus the Procedure Index**: the layered tree (`l0-physical/` … `l5-workloads/`, `runbooks/`, `ansible/`) and `PROCEDURE-INDEX.md`, which AD-3 makes the authoritative enumeration of what "every operational activity" means. Without it, FR-1 quantifies over an unbounded set and SM-1/SM-2 have no denominator.

**Structural constraints on how every story is built**

- **AD-3 · Procedure duality.** A story is not done when the thing works. It is done when a Runbook and its Automation both exist, are cross-referenced, and the Automation reports zero changes against a system built by hand from the Runbook.
- **AD-22 · Ownership split by attribute, not by moment.** OpenTofu declares Proxmox API objects and hands each Guest exactly one thing — a reachable SSH endpoint with a bootstrap key. Ansible declares everything inside the OS, *including* addressing and accounts that cloud-init could also set. Where a tool can express the other's attribute, leaving it unset is mandatory.
- **AD-17 · Mixed-OS from the first role.** Debian-family hypervisor, RHEL-family Directory Guests. Ansible is OS-family aware from role one; the Procedure Index carries a host-build Runbook per family.
- **AD-23 · Drift detection differs by layer.** L3–L5 reconcile continuously with self-heal and prune. L0–L2 are push-based with no loop, so they need scheduled check-mode runs whose non-empty diff raises an alert.
- **AD-20 · Version discipline.** Exact pins only; the distribution package wins over upstream; upgrades run bottom-up through the layers; component EOL is checked before any epic depends on one.
- **AD-19 · Capacity is checked before placement.** ≤90 GB committed and ≥15 GB schedulable in-cluster, both verified in the same commit that places a service.

**Platform-wide technical requirements**

- **AD-5 · ACME is the only issuance protocol.** Manual certificate installation is prohibited. The Directory's own CA is scoped to its internal certificates only; `draupnir` (step-ca) issues everything else.
- **AD-14 · Gateway API is the only north-south routing model.** Ingress resources are not used, even for migration convenience.
- **AD-8 · Storage placement by I/O class.** Local NVMe for Guest disks and databases; NFS default class (RWX) for home directories and shared volumes; iSCSI second class (RWO) for block semantics. Nothing database-shaped reaches the HDD-only appliance by any protocol. Mounts are `hard` plus automount; `soft` is prohibited.
- **AD-25 · POSIX UID/GID ranges are pinned in the Repository** and supplied at Directory installation. The product default is prohibited, because shared storage authorizes by number and a rebuild issuing different numbers orphans every volume.
- **AD-26 · Replica placement is enforceable in configuration** — anti-affinity for Workloads, explicit Node assignment for Guests. No two instances of a replicated set share a Node.
- **AD-24 · Escrow is an exhaustive enumerated list**, not examples, and must not require any single un-escrowed machine.
- **AD-27 · Cold start is ordered and drilled.** Platform-critical images resolve from upstream or the node cache, never from the internal registry that runs inside the cluster it serves.
- **AD-28 · Out-of-band management is verified positively** — port probe plus firmware screen — never inferred from an OS reinstall.
- **AD-11 · Shutdown ordering is tuned delay with a measured, recorded margin**, not coordination.
- **AD-21 · Backup uses each system's native mechanism.** No general abstraction layer. A restore that has not been executed does not count.

**Pinned stack** — Proxmox VE 9.2 · k3s 1.36.4+k3s1 · Rocky Linux 10.x · FreeIPA 4.12.2 (distribution package authoritative) · Keycloak 26.7.2 · step-ca 0.30.2 · cert-manager 1.21.1 · MetalLB 0.16.x · Envoy Gateway 1.9.x · CloudNativePG 1.30.0 · OpenTofu 1.12.6 · ansible-core 2.20.8 · OpenBao 2.6.2

**Build-time gates** that must be settled before the epics depending on them: UPS on the appliance's supported-device list; DSM 7.3+; whether ISP equipment is combined or separate; deterministic USB NIC naming; EEE behaviour on the membership switch.

### UX Design Requirements

**Not applicable.** Project Asgard has no user interface and a single operator. There is no UX design contract, and none was expected — the closest analogue is runbook legibility, which the PRD already governs as NFR-1 through NFR-5 (executable six months later by someone with no recall of building it; reasoning stated, not just commands) and which every story inherits through AD-3.

Administrative interfaces that *do* have UIs — the hypervisor, the storage appliance, dashboards — are third-party products consumed as-is, not designed here. They appear in requirements only as Relying Parties under FR-32 and FR-52.

### FR Coverage Map

### FR Coverage Map

| FR | Epic | |
|---|---|---|
| FR-1 | S1 | Every procedure exists in both forms, against an enumerated… |
| FR-2 | S1 | Manual execution produces a converged system |
| FR-3 | S1 | Documentation defects are resolved at discovery |
| FR-4 | S1 | All configuration originates in the Repository |
| FR-5 | S1 | Procedures declare their verification |
| FR-6 | S2 | Four Nodes form one Cluster |
| FR-7 | S2 | A Node can be rebuilt from the Repository |
| FR-8 | S2 | Guests are provisioned declaratively |
| FR-9 | S2 | Guests can be snapshotted and rolled back |
| FR-10 | S2 | The Cluster is manageable when the Directory is unavailable |
| FR-11 | S4 | Every Node, Guest, and service is reachable by name |
| FR-12 | S2 | Addressing is deterministic and recorded |
| FR-13 | D2 | Name resolution survives a single failure |
| FR-14 | S2 | Household devices are unaffected |
| FR-15 | D1 | Home Directories are identical on every host |
| FR-16 | S3 | Storage unavailability degrades rather than hangs |
| FR-17 | S6 | Workloads obtain Persistent Volumes on demand |
| FR-18 | D1 | PostgreSQL does not run on NFS |
| FR-19 | D5 | Storage capacity and health are visible |
| FR-20 | S4 | One Account authenticates to every host |
| FR-21 | D2 | Authorization is driven by Group membership |
| FR-22 | D2 | Disabling an Account revokes host access within a bounded w… |
| FR-23 | D2 | Hosts authenticate during a Directory outage for known Acco… |
| FR-24 | S2 | Break-glass access exists on every host and survives storag… |
| FR-25 | D2 | The Directory survives loss of one instance |
| FR-26 | S4 | Accounts are defined in the Repository |
| FR-27 | S5 | One authority issues all internal certificates |
| FR-28 | S5 | Trust is distributed automatically |
| FR-29 | S5 | Certificates renew without manual action |
| FR-30 | S7 | The IdP federates to the Directory |
| FR-31 | S7 | Group membership appears in Tokens as claims |
| FR-32 | D9 | Administrative interfaces authenticate through the IdP |
| FR-33 | S7 | Workloads can be registered as Relying Parties |
| FR-34 | D9 | Services without native OIDC are fronted |
| FR-35 | D9 | Account disablement propagates to Relying Parties within st… |
| FR-36 | D5 | Authentication events are recorded |
| FR-37 | S6 | Yggdrasil survives loss of one Control Plane Guest |
| FR-38 | S6 | Control Plane Guests are distributed across Nodes |
| FR-39 | D9 | `kubectl` authenticates through the IdP |
| FR-40 | S6 | Yggdrasil is rebuildable from the Repository |
| FR-41 | S6 | Workloads reach the network by stable name |
| FR-42 | S8 | Workload state reconciles from the Repository |
| FR-43 | D3 | Container images are built and stored within Asgard |
| FR-44 | S8 | A new application reaches production by a documented path |
| FR-45 | D3 | Deployments can be rolled back |
| FR-46 | D4 | Workloads can obtain a database |
| FR-47 | D4 | PostgreSQL is backed up and restorable |
| FR-48 | D4 | Redis is available to Workloads |
| FR-49 | D5 | Platform metrics are collected and retained |
| FR-50 | D5 | Logs are centralized and searchable |
| FR-51 | D5 | Failures generate alerts |
| FR-52 | D9 | Dashboards authenticate through the IdP |
| FR-53 | S1 | No plaintext secret is committed |
| FR-54 | D6 | Workloads obtain secrets without manual injection |
| FR-55 | D6 | Break-glass credentials are held outside Asgard |
| FR-56 | D7 | The platform shuts down cleanly on sustained power loss |
| FR-57 | D7 | Shutdown order is achieved by tuned delay, with proven margin |
| FR-58 | D7 | All shutdown participants remain powered until they act |
| FR-59 | D7 | Power events are visible and alerted |
| FR-60 | D7 | The Shutdown Sequence is proven by Drill |
| FR-61 | D8 | Platform state is backed up automatically |
| FR-62 | D8 | Backups survive loss of any single Node |
| FR-63 | D8 | Restores are verified, not assumed |
| FR-64 | D10 | The platform can be rebuilt from Repository and backups |
| FR-65 | S2 | Nodes are wired, dual-homed, and separate membership traffi… |

## Epic List

### Epic S1: Repository, Procedure standard, and secret handling

*Walking Skeleton*

The operator can write a Procedure and have its two halves checked against each other. Establishes the layered repository tree, the Procedure Index that makes FR-1 countable, and encrypted secret handling that works before any secret store exists.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-53
**Governed by:** AD-3, AD-4, AD-15, AD-16, AD-20, AD-22

### Epic S2: Nodes, cluster, network, and break-glass

*Walking Skeleton*

The operator can create and manage Guests across four clustered Nodes, and can always get back in. Break-glass and firmware management land here — before Directory login exists — because enabling centralised auth without an independent way in risks a lockout.

**FRs covered:** FR-6, FR-7, FR-8, FR-9, FR-10, FR-12, FR-14, FR-24, FR-65
**Governed by:** AD-1, AD-7, AD-9, AD-17, AD-22, AD-27, AD-28

### Epic S3: Shared storage, first export

*Walking Skeleton*

The operator can mount storage from the appliance on a Guest, with mount semantics decided deliberately — hard plus automount, so an outage degrades rather than wedges.

**FRs covered:** FR-16
**Governed by:** AD-8, AD-22

### Epic S4: Directory, DNS, time, and network login

*Walking Skeleton*

The operator logs into all four Nodes with one account, and asgard.home.arpa resolves for real. Numeric identity ranges are pinned at install, because a rebuild issuing different UIDs would orphan every future volume.

**FRs covered:** FR-11, FR-20, FR-26
**Governed by:** AD-2, AD-6, AD-17, AD-25

### Epic S5: Platform certificate authority

*Walking Skeleton*

Every internal endpoint presents a trusted certificate, renewed without intervention. Sequenced before the cluster because it runs outside it and the cluster's own endpoints need it.

**FRs covered:** FR-27, FR-28, FR-29
**Governed by:** AD-5, AD-18

### Epic S6: Kubernetes cluster with storage and gateway

*Walking Skeleton*

The operator can deploy a Workload and reach it by name over TLS. Three control-plane Guests from the start, one per Node — the spread is required and costs almost nothing now versus a rebuild later.

**FRs covered:** FR-17, FR-37, FR-38, FR-40, FR-41
**Governed by:** AD-1, AD-8, AD-14, AD-19, AD-26

### Epic S7: Identity provider and federation

*Walking Skeleton*

The operator's one Directory account authenticates to a service through OIDC, with group membership arriving as token claims. Follows the cluster because it runs inside it.

**FRs covered:** FR-30, FR-31, FR-33
**Governed by:** AD-2, AD-10, AD-18

### Epic S8: Reference application, end to end — SKELETON GATE

*Walking Skeleton*

The operator's own code, committed to the Repository, deployed by reconciliation, authenticating against the IdP and authorising from claims. Proves every integration seam in the design.

**FRs covered:** FR-42, FR-44
**Governed by:** AD-3, AD-14, AD-27

### Epic D1: Storage depth

*Deepen*

Home Directories follow the operator to every host, volumes provision on demand in both classes, and the database sits on storage that suits it.

**FRs covered:** FR-15, FR-18
**Governed by:** AD-8, AD-25

### Epic D2: Identity depth

*Deepen*

Identity survives losing an instance, authorisation is driven centrally by group membership, and revocation is bounded rather than indefinite.

**FRs covered:** FR-13, FR-21, FR-22, FR-23, FR-25
**Governed by:** AD-2, AD-9, AD-10, AD-26

### Epic D3: Delivery depth

*Deepen*

Images are built from committed source inside the platform, traceable to the commit that produced them, and a bad deployment can be reversed through the Repository.

**FRs covered:** FR-43, FR-45
**Governed by:** AD-4, AD-20, AD-27

### Epic D4: Stateful services

*Deepen*

Workloads obtain a database and a cache through a documented Procedure, with the database replicated and continuously archived.

**FRs covered:** FR-46, FR-47, FR-48
**Governed by:** AD-8, AD-19, AD-21, AD-26

### Epic D5: Observability

*Deepen*

The operator learns about failures from the platform rather than by noticing, and can answer 'what changed' during a drill.

**FRs covered:** FR-19, FR-36, FR-49, FR-50, FR-51
**Governed by:** AD-12, AD-19, AD-23

### Epic D6: Secrets management

*Deepen*

Secrets reach Workloads at runtime and are revocable, and everything needed to recover the platform is escrowed outside it.

**FRs covered:** FR-54, FR-55
**Governed by:** AD-15, AD-24

### Epic D7: Power continuity

*Deepen*

An unattended power failure ends with the platform cleanly down and nothing corrupted — proven by pulling the plug, not by reading configuration.

**FRs covered:** FR-56, FR-57, FR-58, FR-59, FR-60
**Governed by:** AD-11, AD-12

### Epic D8: Backup and verified restore

*Deepen*

Every class of data has a restore that has actually been performed, because a backup that has never been read is an assumption.

**FRs covered:** FR-61, FR-62, FR-63
**Governed by:** AD-21, AD-24

### Epic D9: Single sign-on breadth

*Deepen*

One account and one session reach every administrative interface, including kubectl and services with no native OIDC support.

**FRs covered:** FR-32, FR-34, FR-35, FR-39, FR-52
**Governed by:** AD-10, AD-14

### Epic D10: Destructive rebuild drill — DOCUMENTATION GATE

*Deepen*

A Node is destroyed and restored from the Repository with zero undocumented steps. Proves the documentation rather than the architecture.

**FRs covered:** FR-64
**Governed by:** AD-3, AD-22, AD-27
---

# Phase 0 — Walking Skeleton

Every story below delivers a **Procedure**: an ordered Runbook stating reasoning at each decision point, idempotent Automation, and a verification identical whichever performed the work. A story is done when the Automation reports **zero changes** against a system built by hand from its Runbook (AD-3), and when the Procedure appears in `PROCEDURE-INDEX.md` (FR-1).

Throughout, *the operator* is the single administrator this platform serves.

## Epic S1: Repository, Procedure standard, and secret handling

Establishes how everything afterwards gets written. The Procedure Index is what makes FR-1 countable and SM-1/SM-2 measurable — without it, "every operational activity" quantifies over an unbounded set.

**FRs covered:** FR-1, FR-2, FR-3, FR-4, FR-5, FR-53 · **Governed by:** AD-3, AD-4, AD-15, AD-16, AD-20, AD-22

### Story S1.1: Repository skeleton with layered ownership

As the operator,
I want a repository whose structure mirrors the platform's dependency layers,
So that every artefact has one obvious home and ownership is never ambiguous.

**Realizes:** FR-4

**Acceptance Criteria:**

**Given** an empty repository
**When** the skeleton is created
**Then** directories exist for each layer L0 through L5, plus `runbooks/` and `ansible/`
**And** an ownership table names exactly one declaring owner for every configurable resource class, including the hypervisor host OS, the storage appliance, and each network device
**And** the table states the provisioning/configuration split by **attribute** rather than by moment — the provisioning tool declares virtual hardware and guest existence and hands over one reachable SSH endpoint; the configuration tool declares everything inside the OS, including addressing and accounts
**And** no resource class appears with two owners or none

### Story S1.2: Procedure Index and the dual-form contract

As the operator,
I want an authoritative list of every Procedure the platform requires,
So that "every operational activity is documented" is a countable claim rather than an aspiration.

**Realizes:** FR-1, FR-5

**Acceptance Criteria:**

**Given** the repository skeleton exists
**When** the Procedure Index is created
**Then** `PROCEDURE-INDEX.md` lists every Procedure with its Runbook path, Automation path, and owning layer
**And** each Runbook names the Automation that performs it and each Automation names the Runbook that explains it
**And** every Runbook ends with a verification whose expected output is stated
**And** an Index entry missing either half is reported as an incomplete Procedure

**Given** an activity is performed that has no Index entry
**When** the omission is noticed
**Then** it is recorded as a defect in the Index and closed before the activity counts as complete

### Story S1.3: Convergence test harness

As the operator,
I want to prove that my runbooks and my automation agree,
So that documentation drift is detectable rather than discovered years later.

**Realizes:** FR-2, FR-3

**Acceptance Criteria:**

**Given** a system built by following a Runbook by hand
**When** that Procedure's Automation is run against it
**Then** the Automation reports zero changes
**And** any difference is recorded as a documentation defect against the Procedure, never accommodated by weakening the Automation

**Given** any Automation
**When** it is run twice consecutively
**Then** the second run also reports zero changes

**Given** a push-based layer with no reconciliation loop
**When** the scheduled check-mode run executes
**Then** a non-empty diff exits non-zero and is recorded, so it cannot pass silently
**And** the check is registered in the Procedure Index as an alert source, to be wired to notification in D5.5 — this story does not depend on alerting existing

### Story S1.4: Encrypted secrets before a secret store exists

As the operator,
I want to commit configuration containing secret material to a public repository safely,
So that the platform can be built before any runtime secret store is available.

**Realizes:** FR-53

**Acceptance Criteria:**

**Given** the repository is pushed to a remote
**When** its contents and full history are inspected
**Then** no plaintext credential, key, or token is present
**And** encrypted secret material is unusable without a key held outside the repository

**Given** a commit containing a plaintext secret is attempted
**When** the commit-time check runs
**Then** the commit is rejected with the offending path named

**Given** the decryption key
**When** its storage location is examined
**Then** it is escrowed outside the repository and outside any single un-escrowed machine

## Epic S2: Nodes, cluster, network, and break-glass

Four clustered Nodes and a guaranteed way back in. Break-glass and firmware management land here deliberately — **before** Directory login exists in S4, because enabling centralised authentication without an independent path first is how a lockout becomes unrecoverable.

**FRs covered:** FR-6, FR-7, FR-8, FR-9, FR-10, FR-12, FR-14, FR-24, FR-65 · **Governed by:** AD-1, AD-7, AD-9, AD-17, AD-22, AD-27, AD-28

### Story S2.1: Address plan and interface allocation

As the operator,
I want every address determined before anything is built,
So that a rebuilt Node returns to the same address without archaeology.

**Realizes:** FR-12, FR-14

**Acceptance Criteria:**

**Given** the repository
**When** the address plan is consulted
**Then** every Node, Guest, and service has a declared address, assigned statically outside the household DHCP pool
**And** each Node's two interfaces are named with their traffic class: onboard for cluster membership, adapter for storage and workload traffic
**And** the membership segment uses a private range with no gateway and no route to any other network

**Given** the household network
**When** Asgard is brought up
**Then** non-Asgard devices continue to use the household router unchanged, and Asgard does not serve DHCP for the household LAN

### Story S2.2: Out-of-band management claimed or disabled

As the operator,
I want the firmware management interface in a known and chosen state,
So that a remote power-and-console interface is not sitting on my flat network at vendor defaults.

**Realizes:** FR-24 (out-of-band as a Break-glass path)

**Acceptance Criteria:**

**Given** a Node in its as-delivered state
**When** its management state is established
**Then** it is verified two ways — a port probe from another host, and a direct reading of the firmware setup screen
**And** an operating-system reinstall is explicitly **not** accepted as evidence of state, because the interface is firmware-resident and untouched by it

**Given** the interface is found enabled
**When** the Node is prepared
**Then** its credentials are changed from vendor defaults before the Node joins the Cluster, and the replacement is escrowed
**And** a firmware administrator password is set so the setting cannot be silently reverted by physical access

**Given** the interface is found disabled or is deliberately disabled
**When** the decision is recorded
**Then** the disabled state is declared in the repository rather than inherited

### Story S2.3: Node build — hypervisor, dual-homed networking

As the operator,
I want a Node built to a documented standard,
So that all four are identical and a fifth would be too.

**Realizes:** FR-65, FR-6 (partial)

**Acceptance Criteria:**

**Given** bare hardware
**When** the Node build Procedure is followed
**Then** the hypervisor is installed at the pinned version, with guest storage on local NVMe
**And** the onboard interface carries only cluster membership on the isolated switch, and the adapter carries storage, workload, backup and outbound traffic
**And** wireless interfaces are disabled rather than left available as a fallback
**And** interface naming is deterministic across reboots and matches the address plan

**Given** the Node build Automation
**When** it runs against a hand-built Node
**Then** it reports zero changes

### Story S2.4: Break-glass access that survives every dependency

As the operator,
I want a way into every host that depends on nothing else,
So that the emergency path works during the emergency it exists for.

**Realizes:** FR-24

**Acceptance Criteria:**

**Given** any Node or Guest
**When** its accounts are inspected
**Then** a named local administrative account exists with privilege escalation, unique per host, unmanaged by any directory
**And** its home directory is local **and** lies outside every path the shared filesystem manages — local alone is insufficient, since a home nested under a network mount is shadowed while mounted and invisible under an automounter
**And** direct remote root login is disabled

**Given** the shared storage is unavailable
**When** the operator logs in with the break-glass account
**Then** the session lands in a working shell and local diagnostics are possible

**Given** the break-glass credentials
**When** their storage is examined
**Then** they are escrowed outside the platform and recoverable without any platform component running

### Story S2.5: Cluster formation

As the operator,
I want four Nodes managed as one Cluster,
So that guests can be placed, moved, and recovered across them.

**Realizes:** FR-6, FR-10

**Acceptance Criteria:**

**Given** four built Nodes
**When** the Cluster is formed
**Then** cluster status reports four healthy members with membership traffic confined to the isolated segment
**And** loss of any one Node leaves the remaining three operating and manageable
**And** the Cluster management interface authenticates with a local realm that works with no directory present

### Story S2.6: Declarative Guest provisioning

As the operator,
I want Guests defined in the repository rather than clicked into existence,
So that a destroyed Guest returns from its declaration.

**Realizes:** FR-8

**Acceptance Criteria:**

**Given** a Guest declaration in the repository
**When** the provisioning tool is applied
**Then** the Guest is created with the declared virtual hardware, storage, and placement
**And** the tool sets **only** provisioning attributes and hands over exactly one reachable SSH endpoint with a bootstrap key — it does not set in-guest addressing, accounts, or passwords, which belong to the configuration tool
**And** applying the declaration repeatedly converges rather than duplicating

**Given** provisioning state
**When** its handling is examined
**Then** it is a versioned artefact with a stated location and locking behaviour, and appears in the escrow list

### Story S2.7: Snapshot and rollback

As the operator,
I want to snapshot a Guest before a risky change,
So that experimenting costs minutes rather than an afternoon.

**Realizes:** FR-9

**Acceptance Criteria:**

**Given** a running Guest
**When** a snapshot is taken and a destructive change is made
**Then** restoring the snapshot returns the Guest to its prior state including disk contents, without reinstallation

### Story S2.8: Node rebuild from the repository

As the operator,
I want to destroy a Node and bring it back,
So that the claim of reproducibility is evidence rather than assertion.

**Realizes:** FR-7

**Acceptance Criteria:**

**Given** a deliberately destroyed Node
**When** the rebuild Procedure is followed
**Then** it requires no information held outside the repository except escrowed break-glass credentials
**And** the rebuilt Node rejoins the Cluster and resumes hosting Guests without manual storage or network reconfiguration
**And** the Automation reports zero changes against the rebuilt Node

**Given** a step was required but not documented
**When** the rebuild is performed
**Then** the gap is recorded as a documentation defect and closed before the rebuild counts as complete

## Epic S3: Shared storage, first export

The skeleton's proof that storage mounts. Thin by design — the substantive storage work is D1 — but it carries one decision that must be made at first mount rather than revisited later.

**FRs covered:** FR-16 · **Governed by:** AD-8, AD-22

### Story S3.1: Storage pool and first export

As the operator,
I want the appliance serving a share,
So that Guests have somewhere shared to write.

**Realizes:** FR-16 (partial)

**Acceptance Criteria:**

**Given** the appliance with its drives installed
**When** the storage Procedure is followed
**Then** the pool is created at the declared redundancy level, tolerating two drive failures
**And** the appliance's configuration is declared in the repository as a configuration item with a named owner, not treated as an exception
**And** one export exists with declared access controls

### Story S3.2: Client mount with deliberate semantics

As the operator,
I want storage interruptions to degrade rather than wedge,
So that a storage outage does not take the hosts down with it.

**Realizes:** FR-16

**Acceptance Criteria:**

**Given** a Guest consuming the export
**When** the mount is configured
**Then** it is mounted `hard`, so an interruption blocks rather than risking silent corruption — integrity outranks availability
**And** it is automounted, so the path is absent rather than wedged when the appliance is unreachable
**And** `soft` mounts are not used anywhere

**Given** the appliance is powered off
**When** the operator logs into the Guest with the break-glass account
**Then** the session works, no process is stuck unkillable, and recovery on the appliance's return requires no reboot

## Epic S4: Directory, DNS, time, and network login

One account works on all four Nodes, and `asgard.home.arpa` becomes real. Numeric identity is pinned here because it cannot be retrofitted.

**FRs covered:** FR-11, FR-20, FR-26 · **Governed by:** AD-2, AD-6, AD-17, AD-25

### Story S4.1: Directory Guest built on the second OS family

As the operator,
I want the directory host built by automation that knows it is not the hypervisor's OS family,
So that mixed-OS support is proven at the first opportunity rather than retrofitted.

**Realizes:** FR-26 (partial)

**Acceptance Criteria:**

**Given** the automation written so far targets the hypervisor's OS family
**When** the directory Guest is built
**Then** it runs the RHEL-family distribution the directory server requires
**And** the automation selects package names, service names, and firewall tooling by OS family rather than assuming one
**And** a host-build Runbook exists for each family in the Procedure Index

### Story S4.2: Directory installed with pinned numeric identity

As the operator,
I want UID and GID ranges fixed in the repository before any account exists,
So that a future rebuild does not orphan every file on shared storage.

**Realizes:** FR-26

**Acceptance Criteria:**

**Given** the directory installation
**When** it is performed
**Then** POSIX UID and GID ranges are supplied explicitly from the repository, and the product's randomised default range is not used
**And** the same ranges are reproduced by a rebuild, so numeric identity is stable across one

**Given** a file written by an account before a rebuild
**When** the directory is rebuilt from the repository and the file is accessed
**Then** ownership resolves to the same account, because shared storage authorises by number rather than by name

### Story S4.3: DNS zone and records

As the operator,
I want every host reachable by name,
So that nothing downstream has to know an address.

**Realizes:** FR-11

**Acceptance Criteria:**

**Given** the directory serving DNS
**When** any Node, Guest, or service is queried
**Then** forward resolution succeeds within `asgard.home.arpa` and reverse resolution succeeds for every Node and Guest
**And** names follow the naming registry, with any new name taken from the reserve pool and added to the registry in the same change
**And** the provisional resolution used in S2 is retired

### Story S4.4: Time authority

As the operator,
I want internal time to stay coherent when the internet link is down,
So that Kerberos does not fail platform-wide because of a wireless bridge.

**Realizes:** AD-6 — no direct FR; a precondition of FR-20

**Acceptance Criteria:**

**Given** the platform
**When** time sources are inspected
**Then** every Node and Guest synchronises to the directory, and the directory alone synchronises upstream
**And** no host synchronises directly to an external source

**Given** the outbound uplink is unavailable
**When** hosts are compared
**Then** internal clocks remain mutually coherent, well inside the tolerance authentication requires

### Story S4.5: Host enrolment and network login

As the operator,
I want one account that logs into every host,
So that I stop maintaining local users.

**Realizes:** FR-20

**Acceptance Criteria:**

**Given** an enrolled Node or Guest
**When** the operator authenticates with their directory account
**Then** login succeeds, group membership resolves, and no local account was created for routine access
**And** a home directory is provisioned on first login without manual intervention
**And** a password change takes effect on every host without per-host action

**Given** the break-glass account
**When** enrolment completes
**Then** it remains local, unmanaged by the directory, and still functional

## Epic S5: Platform certificate authority

Trusted TLS everywhere internal, renewed without intervention. Sequenced before the cluster because it runs outside it and the cluster's own endpoints need it.

**FRs covered:** FR-27, FR-28, FR-29 · **Governed by:** AD-5, AD-18

### Story S5.1: Platform CA with ACME

As the operator,
I want one authority issuing every internal certificate over one protocol,
So that renewal is a solved problem rather than four bespoke ones.

**Realizes:** FR-27

**Acceptance Criteria:**

**Given** the platform CA
**When** it is deployed
**Then** it runs outside the Kubernetes cluster, because hosts and the hypervisor depend on it and a CA inside the cluster would invert the layering
**And** it exposes an ACME endpoint
**And** the directory's own integrated CA is scoped to issuing only the directory's internal certificates
**And** the CA root key is escrowed outside the platform

### Story S5.2: Trust distributed automatically

As the operator,
I want no certificate warnings anywhere,
So that trust is real rather than clicked past.

**Realizes:** FR-28

**Acceptance Criteria:**

**Given** any Node or Guest
**When** the trust anchor is examined
**Then** it was installed by automation, not by hand
**And** command-line tools validate internal certificates without per-host manual steps

**Given** any internal TLS endpoint
**When** it is reached from any host
**Then** no certificate warning appears and the chain terminates at the platform CA

### Story S5.3: Automatic issuance and renewal

As the operator,
I want certificates to renew themselves,
So that expiry is not an outage waiting for a calendar reminder.

**Realizes:** FR-29

**Acceptance Criteria:**

**Given** any certificate in the platform
**When** it approaches expiry
**Then** it renews automatically over ACME without operator action
**And** no certificate was installed manually anywhere

**Given** a renewal failure
**When** it occurs
**Then** it is detected and recorded before the certificate expires, with the check registered as an alert source for D5.5 to wire — this story does not depend on alerting existing

## Epic S6: Kubernetes cluster with storage and gateway

Somewhere to deploy, reachable by name over TLS. Three control-plane Guests from the start — the spread is required and costs almost nothing now against a rebuild later.

**FRs covered:** FR-17, FR-37, FR-38, FR-40, FR-41 · **Governed by:** AD-1, AD-8, AD-14, AD-19, AD-26

### Story S6.1: Control plane across fault domains

As the operator,
I want the cluster to survive losing a Node,
So that a single hardware failure is not a platform outage.

**Realizes:** FR-37, FR-38

**Acceptance Criteria:**

**Given** the cluster
**When** control-plane placement is inspected
**Then** three control-plane Guests exist, no two sharing a Node, expressed as an enforceable constraint in configuration rather than as a convention or a diagram
**And** the bundled ingress controller and load balancer are disabled at install

**Given** one control-plane Guest is stopped
**When** the cluster is used
**Then** the API is served, workloads remain schedulable, and the stopped Guest rejoins without a cluster rebuild

**Given** the placement of every Guest
**When** capacity is totalled
**Then** committed memory is within the declared ceiling and the schedulable floor still holds, both checked in the commit that places them

### Story S6.2: Worker Guests and cluster composition in the repository

As the operator,
I want the cluster's composition declared,
So that it can be rebuilt without remembering how it was assembled.

**Realizes:** FR-40

**Acceptance Criteria:**

**Given** the repository
**When** the cluster is rebuilt from it
**Then** composition and configuration come entirely from declarations
**And** persistent volume data survives the rebuild
**And** workloads return by reconciliation rather than manual reapplication

### Story S6.3: Storage classes from the appliance

As the operator,
I want workloads to obtain storage on demand,
So that deploying something with state is not a manual provisioning task.

**Realizes:** FR-17

**Acceptance Criteria:**

**Given** a workload storage claim
**When** it is created
**Then** a volume is provisioned automatically and bound, without manual steps on the appliance
**And** two classes are available — a default file class supporting multi-consumer access, and a block class for workloads wanting their own filesystem
**And** data survives workload restart and rescheduling to a different Worker Guest

**Given** any database-shaped workload
**When** its storage class is chosen
**Then** it is not placed on appliance-backed storage by any protocol, because the appliance is spinning-disk only

### Story S6.4: Load balancer address pool

As the operator,
I want stable addresses for published services,
So that DNS can point at something that does not move.

**Realizes:** FR-41 (partial)

**Acceptance Criteria:**

**Given** the load balancer
**When** a service requests an external address
**Then** it receives one from the declared pool, and the pool sits inside the address plan
**And** the address is stable across rescheduling

### Story S6.5: Gateway with automatic TLS

As the operator,
I want to publish a workload by name over TLS without touching DNS or certificates,
So that shipping something is a commit rather than a checklist.

**Realizes:** FR-41

**Acceptance Criteria:**

**Given** the gateway
**When** it is deployed
**Then** routing uses Gateway API resources only — Ingress resources are not used, so one routing model exists rather than two
**And** listener certificates are issued by the platform CA over ACME

**Given** a published workload
**When** it is reached from the LAN
**Then** it resolves by name within the domain, terminates TLS with a trusted certificate, and requires no manual DNS or certificate step to publish

## Epic S7: Identity provider and federation

One directory account authenticating to a service through OIDC, with groups arriving as claims. Follows the cluster because it runs inside it.

**FRs covered:** FR-30, FR-31, FR-33 · **Governed by:** AD-2, AD-10, AD-18

### Story S7.1: Identity provider deployed

As the operator,
I want an OIDC authorization server running in the platform,
So that my applications have something real to authenticate against.

**Realizes:** FR-30 (partial)

**Acceptance Criteria:**

**Given** the identity provider
**When** it is deployed
**Then** it runs as a workload with an explicit memory limit rather than default sizing
**And** it is published through the gateway with a platform CA certificate
**And** it publishes a standards-compliant discovery document

**Given** the cluster's own administration
**When** the identity provider is unavailable
**Then** the cluster remains administrable through its static credential, because identity-backed access is an enhancement and never a dependency

### Story S7.2: Federation to the directory

As the operator,
I want the identity provider to consume accounts rather than own them,
So that there is one account store and one place to revoke.

**Realizes:** FR-30

**Acceptance Criteria:**

**Given** the identity provider
**When** federation is configured
**Then** accounts authenticate against the directory and are not duplicated into the provider
**And** the provider stores only sessions, clients, and realm configuration
**And** a directory password change takes effect for provider authentication immediately

**Given** the identity provider is rebuilt from the repository
**When** it returns
**Then** no account data was lost, because it never owned any

### Story S7.3: Group membership as token claims

As the operator,
I want group membership to arrive in tokens,
So that applications can make authorization decisions from claims alone.

**Realizes:** FR-31

**Acceptance Criteria:**

**Given** an authenticated account
**When** a token is issued
**Then** group membership appears in a documented, stable claim
**And** adding the account to a group changes claims on the next token issued
**And** a workload can authorize from claims without querying the directory directly

### Story S7.4: Client registration Procedure

As the operator,
I want registering a new application to be a documented repeatable step,
So that the second application costs no more thought than the first.

**Realizes:** FR-33

**Acceptance Criteria:**

**Given** a new application
**When** it is registered
**Then** the registration is declarative and lives in the repository
**And** authorization code flow with PKCE is supported
**And** integration requires no vendor-specific client library

## Epic S8: Reference application, end to end — SKELETON GATE

The gate. The operator's own code, deployed by reconciliation, authenticating against the identity provider and authorising from claims. Reaching it proves every seam: hypervisor to storage, storage to cluster, directory to provider, provider to cluster, provider to application, repository to running workload.

**FRs covered:** FR-42, FR-44 · **Governed by:** AD-3, AD-14, AD-27

### Story S8.1: Reconciliation from the repository

As the operator,
I want workload state to follow the repository without me deploying,
So that the repository is the source of truth in practice and not just in policy.

**Realizes:** FR-42

**Acceptance Criteria:**

**Given** a workload declaration committed to the repository
**When** the change lands
**Then** it converges within a bounded interval with no operator action
**And** drift introduced directly against the cluster is reverted or reported
**And** current deployed state is determinable from the repository alone

**Given** platform-critical images
**When** a cold start occurs with the internal registry unavailable
**Then** those images resolve from upstream or the node image cache, never from the registry that runs inside the cluster it serves

### Story S8.2: The operator's own application, authenticated

As the operator,
I want an application I wrote running on the platform and authenticating real users,
So that the thing this lab exists for actually works.

**Realizes:** FR-44

**Acceptance Criteria:**

**Given** an empty application repository
**When** the documented path is followed
**Then** one Procedure covers registration with the identity provider, declaration, publication, and reconciliation, with no undocumented manual step
**And** a second application repeats the Procedure without variation

**Given** the deployed application
**When** the operator visits it
**Then** they are redirected to the identity provider, authenticate with the same account used for SSH, and return authenticated
**And** the application makes an authorization decision from group claims in the token

---

# Phase 1 — Deepen

The skeleton proved the seams. These epics add redundancy, observability, and recoverability to layers that already work. Every story remains a Procedure under AD-3.

## Epic D1: Storage depth

Home Directories follow the operator everywhere, and the database sits on storage that suits it.

**FRs covered:** FR-15, FR-18 · **Governed by:** AD-8, AD-25

### Story D1.1: Portable Home Directories

As the operator,
I want the same home directory on every host,
So that I stop caring which machine I am on.

**Realizes:** FR-15

**Acceptance Criteria:**

**Given** a file written under the operator's home on one host
**When** the operator logs into a different Node or Guest
**Then** the file is present, with ownership resolving to the same account
**And** no home directory content is stored on any Node's local disk

**Given** a first login on a newly built host
**When** it completes
**Then** a home directory is provisioned automatically without manual intervention

**Given** the appliance is unavailable
**When** the break-glass account logs in
**Then** its home is unaffected, because it lies outside every path the shared filesystem manages

### Story D1.2: Database storage off the appliance

As the operator,
I want the database on storage matched to its access pattern,
So that its durability guarantees are ones the medium can actually keep.

**Realizes:** FR-18

**Acceptance Criteria:**

**Given** the database workload
**When** its storage is inspected
**Then** its data sits on local NVMe, never on appliance-backed storage by any protocol
**And** the constraint is enforced by configuration in the repository rather than by convention

**Given** database storage pins the workload to a Node
**When** the deployment is designed
**Then** continuous write-ahead archiving to shared storage is configured as a precondition of running at all, not deferred to the backup epic

## Epic D2: Identity depth

Identity survives losing an instance, authorisation is centrally driven, and revocation is bounded rather than indefinite.

**FRs covered:** FR-13, FR-21, FR-22, FR-23, FR-25 · **Governed by:** AD-2, AD-9, AD-10, AD-26

### Story D2.1: Directory replica across fault domains

As the operator,
I want identity to survive losing one instance,
So that patching the directory is not a platform-wide outage.

**Realizes:** FR-25, FR-13

**Acceptance Criteria:**

**Given** two directory instances
**When** either is stopped
**Then** host authentication continues, the identity provider continues issuing tokens, and name resolution still answers
**And** the two do not share a Node, expressed as an enforceable placement constraint

**Given** an account or group change made against one instance
**When** the other is queried
**Then** the change is present

**Given** the replica is built
**When** its roles are inspected
**Then** it carries the certificate and DNS roles explicitly, and the location of the certificate-renewal role, its health check, and its relocation Procedure are named in the repository

### Story D2.2: Central authorization and privilege escalation

As the operator,
I want host access and sudo driven by group membership,
So that granting or removing access is one change in one place.

**Realizes:** FR-21

**Acceptance Criteria:**

**Given** a group membership change in the directory
**When** it is made
**Then** which hosts the account may access changes accordingly, without editing per-host configuration
**And** privilege escalation rules are defined centrally and applied consistently across both OS families

### Story D2.3: Bounded offline credential cache

As the operator,
I want to keep working as myself during a directory outage,
So that routine work does not run through a shared emergency credential.

**Realizes:** FR-23

**Acceptance Criteria:**

**Given** an account that has authenticated to a host before
**When** the directory is unavailable
**Then** login succeeds, with group membership and privilege escalation resolving from cache

**Given** an account that has never authenticated to that host
**When** the directory is unavailable
**Then** login correctly fails

**Given** the cache
**When** its configuration is inspected
**Then** an explicit maximum age is set in the repository rather than left at product default, because an unexpired cache is indistinguishable from a valid account

### Story D2.4: Revocation with recorded bounds

As the operator,
I want disabling one account to end access everywhere within a stated time,
So that revocation is a promise I can actually keep.

**Realizes:** FR-22

**Acceptance Criteria:**

**Given** a disabled account
**When** authentication is attempted on any reachable host
**Then** it fails immediately, with no second list edited to complete the revocation

**Given** a host that cannot reach the directory
**When** the cache expiry elapses
**Then** the disabled account stops authenticating there, bounded rather than indefinite

**Given** the platform's relying parties
**When** their propagation bounds are examined
**Then** each bound is recorded in a per-party table in the repository, and an unrecorded bound is treated as a defect

## Epic D3: Delivery depth

Images built inside the platform from committed source, traceable to their commit, with a way back.

**FRs covered:** FR-43, FR-45 · **Governed by:** AD-4, AD-20, AD-27

### Story D3.1: Internal registry

As the operator,
I want an image registry inside the platform,
So that workloads do not depend on an outbound link that crosses a wireless bridge.

**Realizes:** FR-43 (partial)

**Acceptance Criteria:**

**Given** the registry
**When** it is deployed
**Then** the cluster pulls from it without external dependency, and it is published through the gateway with a platform CA certificate
**And** it declares an explicit memory limit, and the capacity check is recorded in the commit that places it

**Given** a cold start with the registry unavailable
**When** the cluster comes up
**Then** platform-critical images resolve from upstream or the node image cache, and a Procedure verifies this rather than assuming it

### Story D3.2: Images built from committed source

As the operator,
I want images built inside the platform from what is committed,
So that what runs is traceable to what was written.

**Realizes:** FR-43

**Acceptance Criteria:**

**Given** a commit to an application repository
**When** the build runs
**Then** it builds from committed source rather than from a workstation
**And** the resulting image is identifiable back to the commit that produced it
**And** the image is pushed to the internal registry and pullable by the cluster

### Story D3.3: Rollback through the repository

As the operator,
I want to return a workload to a known-good state,
So that a bad deployment is a minor event.

**Realizes:** FR-45

**Acceptance Criteria:**

**Given** a workload in a bad state
**When** rollback is performed
**Then** it happens through the repository, preserving it as the source of truth
**And** the previous state is identifiable without reconstruction from memory
**And** reconciliation converges on the rolled-back state without manual intervention

## Epic D4: Stateful services

A database and a cache workloads can obtain through a documented Procedure, replicated and continuously archived.

**FRs covered:** FR-46, FR-47, FR-48 · **Governed by:** AD-8, AD-19, AD-21, AD-26

### Story D4.1: Replicated database cluster

As the operator,
I want the database to survive losing a Node,
So that node-pinned local storage does not become a single point of failure.

**Realizes:** FR-46 (partial)

**Acceptance Criteria:**

**Given** the database cluster
**When** its placement is inspected
**Then** instances are spread so no two share a Node, expressed as an enforceable constraint
**And** each instance declares an explicit memory limit within the capacity ceiling

**Given** the primary instance's Node is lost
**When** failover occurs
**Then** a replica is promoted automatically and workloads reconnect

### Story D4.2: Database provisioning for workloads

As the operator,
I want to give a workload a database through a documented step,
So that the second application is no harder than the first.

**Realizes:** FR-46

**Acceptance Criteria:**

**Given** a workload needing a database
**When** the provisioning Procedure is followed
**Then** the database and role are created without manual server-side steps outside the Procedure
**And** credentials reach the workload at runtime without appearing in the repository in plaintext
**And** each workload's database is isolated from every other's

### Story D4.3: Continuous archiving and proven restore

As the operator,
I want a database restore I have actually performed,
So that recoverability is evidence rather than configuration.

**Realizes:** FR-47

**Acceptance Criteria:**

**Given** the database
**When** archiving is configured
**Then** write-ahead archiving runs continuously to storage independent of the Node holding the data
**And** backups run on a defined schedule without operator action, with failure detected and recorded, registered as an alert source for D5.5

**Given** the restore Procedure
**When** it is executed
**Then** the database is restored to a prior point and the restored data is verified correct, not merely present
**And** the execution is recorded, because a backup that has never been read does not count as present

### Story D4.4: Cache available to workloads

As the operator,
I want a cache workloads can use,
So that applications have somewhere for ephemeral state.

**Realizes:** FR-48

**Acceptance Criteria:**

**Given** the cache
**When** a workload connects
**Then** authentication is required, and connection details are documented
**And** its persistence behaviour is a documented deliberate choice rather than a default

**Given** the cache is lost
**When** dependent workloads are observed
**Then** they degrade without data loss in the database

## Epic D5: Observability

The operator learns about failures from the platform rather than by noticing.

**FRs covered:** FR-19, FR-36, FR-49, FR-50, FR-51 · **Governed by:** AD-12, AD-19, AD-23

### Story D5.1: Metrics with bounded retention

As the operator,
I want current and historical metrics for everything,
So that I can answer "what changed" during a drill.

**Realizes:** FR-49

**Acceptance Criteria:**

**Given** the metrics stack
**When** it is deployed
**Then** it covers host resources, Cluster health, cluster health, and workload state
**And** a new Guest or workload is discovered without manual registration
**And** retention is a defined bounded period, so storage growth is predictable rather than discovered at exhaustion
**And** its own memory limit is explicit, since retention is the most likely consumer of remaining capacity

### Story D5.2: Centralised searchable logs

As the operator,
I want logs from every host and workload in one place,
So that a log survives the system that produced it.

**Realizes:** FR-50

**Acceptance Criteria:**

**Given** the log store
**When** logs are queried
**Then** they are searchable by host, workload, and time range
**And** logs survive the destruction of the system that produced them
**And** retention is bounded and stated

### Story D5.3: Storage and appliance health visible

As the operator,
I want to know the appliance is unwell before it fails,
So that the one place holding everything is not a blind spot.

**Realizes:** FR-19

**Acceptance Criteria:**

**Given** the appliance
**When** its metrics are collected
**Then** capacity, utilisation, and drive health are reported to the observability system
**And** an alert fires at a defined threshold before capacity is exhausted
**And** a drive failure produces an alert without the operator inspecting the appliance

### Story D5.4: Authentication events recorded

As the operator,
I want to see who authenticated where,
So that identity has an audit trail.

**Realizes:** FR-36

**Acceptance Criteria:**

**Given** authentication activity across relying parties
**When** events are reviewed
**Then** they are visible from one place, identifying account, relying party, and outcome
**And** failed authentication is distinguishable from failed authorization

### Story D5.5: Alerting in three independent tiers

As the operator,
I want to be told about failures without watching a dashboard,
So that I find out from the platform rather than from a broken service.

**Realizes:** FR-51

**Acceptance Criteria:**

**Given** platform failure conditions
**When** they occur
**Then** alerts fire for Node loss, storage exhaustion, approaching certificate expiry, backup failure, and power events, each naming the affected component and condition
**And** notification reaches the operator outside the platform's own interfaces

**Given** an infrastructure alert from the appliance or the power system
**When** it is raised
**Then** it does not route through the cluster, so it survives the cluster being down

**Given** the platform is entirely down
**When** the external dead-man's-switch heartbeat stops
**Then** the operator is alerted from outside infrastructure — the only path that survives a whole-house outage, since the household router cannot be battery-backed

**Given** two components that can fail independently
**When** heartbeats are configured
**Then** each owns its own check, because a shared check stays green while one of them is dead

**Given** detectors registered as alert sources by earlier epics — drift checks, certificate renewal failures, backup failures
**When** this story completes
**Then** every registered source is wired to notification, and the Procedure Index shows no alert source left unwired

## Epic D6: Secrets management

Secrets reach workloads at runtime and are revocable, and everything needed to recover the platform is escrowed outside it.

**FRs covered:** FR-54, FR-55 · **Governed by:** AD-15, AD-24

### Story D6.1: Runtime secret delivery

As the operator,
I want workloads to receive secrets at runtime,
So that rotating one does not mean editing manifests.

**Realizes:** FR-54

**Acceptance Criteria:**

**Given** a workload needing a secret
**When** access is granted
**Then** the secret is delivered at runtime and never baked into an image
**And** rotating it requires no edit to the workload's declaration
**And** the workload's access is revocable

**Given** the secret store
**When** it is deployed
**Then** its unseal material is escrowed outside the platform

### Story D6.2: Escrow completeness

As the operator,
I want an exhaustive list of what lives outside the platform,
So that recovery does not depend on something I forgot to copy.

**Realizes:** FR-55

**Acceptance Criteria:**

**Given** the escrow list
**When** it is reviewed
**Then** it is exhaustive and enumerated rather than illustrative, covering at minimum: break-glass credentials for every Node and Guest, the cluster's static administrative credential, the platform CA root key, the key decrypting repository secrets, secret-store unseal material, the directory superuser credential, the appliance administrative credential, delivery-controller repository credentials, and out-of-band management credentials
**And** every item names where it lives and how it is rotated

**Given** recovery
**When** it is attempted
**Then** it requires no Asgard component running, and no single machine that is not itself escrowed — a key held only on the operator's workstation fails this criterion

## Epic D7: Power continuity

An unattended power failure ends with the platform cleanly down and nothing corrupted — proven by pulling the plug.

**FRs covered:** FR-56, FR-57, FR-58, FR-59, FR-60 · **Governed by:** AD-11, AD-12

### Story D7.1: Battery-backed inventory

As the operator,
I want everything that must act during a power failure to still have power,
So that the shutdown sequence does not lose its own network partway through.

**Realizes:** FR-58

**Acceptance Criteria:**

**Given** the UPS
**When** its outlets are allocated
**Then** all four Nodes, the appliance, and **both** switches are battery-backed
**And** the membership switch is included, since losing it mid-sequence breaks cluster membership while Guests are still shutting down
**And** the allocation is recorded, including that no spare outlet remains

**Given** the household router
**When** its power source is considered
**Then** it is documented as **outside** the UPS boundary, with the consequence recorded: no outbound notification can leave during a whole-house outage

### Story D7.2: UPS signalling to clients

As the operator,
I want the platform to learn that mains power is gone,
So that shutdown begins without me.

**Realizes:** FR-56 (partial)

**Acceptance Criteria:**

**Given** the UPS connected to the appliance
**When** signalling is configured
**Then** the appliance broadcasts UPS state and the Nodes receive it as clients
**And** the client roster fits within the appliance's supported limit, with that limit recorded as a constraint on adding a fifth Node
**And** shutdown begins automatically after a defined time on battery

### Story D7.3: Ordered shutdown by measured margin

As the operator,
I want components to power down in an order that respects what depends on what,
So that nothing is writing when its storage disappears.

**Realizes:** FR-57

**Acceptance Criteria:**

**Given** a sustained power failure
**When** the sequence runs
**Then** workloads drain, then Guests stop, then Nodes stop, then the appliance stops — in that order, with the appliance last to cease serving

**Given** the appliance offers no shutdown handshake and will not wait for clients
**When** ordering is configured
**Then** it is produced by **tuned delay**: the appliance's threshold is set later than the measured completion of all Node shutdowns, by a stated margin
**And** that margin is recorded as a number in the repository, derived from measurement rather than estimation

### Story D7.4: Power events visible and alerted

As the operator,
I want to know the moment we are on battery,
So that a power event is not discovered afterwards.

**Realizes:** FR-59

**Acceptance Criteria:**

**Given** a transfer to battery
**When** it occurs
**Then** an alert is raised, and battery charge and estimated runtime are recorded as metrics
**And** a battery approaching end of service is reported before it fails

### Story D7.5: The power drill

As the operator,
I want to have actually pulled the plug,
So that the margin is proven rather than believed.

**Realizes:** FR-60, FR-56

**Acceptance Criteria:**

**Given** the configured sequence
**When** mains power is physically removed
**Then** the full sequence completes with the appliance last, and no database or appliance corruption results
**And** runtime under real load is measured and recorded rather than taken from the specification sheet
**And** the interval between the last Node completing shutdown and the appliance ceasing to serve is measured, confirming the configured margin holds

**Given** a battery replacement
**When** it is performed
**Then** the drill is repeated

## Epic D8: Backup and verified restore

Every class of data has a restore that has actually been performed.

**FRs covered:** FR-61, FR-62, FR-63 · **Governed by:** AD-21, AD-24

### Story D8.1: Native backup per data class

As the operator,
I want each system backed up by the mechanism it provides,
So that I am not maintaining a general abstraction nobody understands.

**Realizes:** FR-61

**Acceptance Criteria:**

**Given** the platform's data classes
**When** backup is configured
**Then** file data uses appliance snapshots and replication, Guests use hypervisor dumps, and the database uses its operator's own continuous archiving
**And** no general-purpose backup abstraction layer is introduced
**And** backups run on a defined schedule with failure raising an alert

### Story D8.2: Coverage enumerated, exclusions deliberate

As the operator,
I want to know exactly what is and is not protected,
So that gaps are decisions rather than surprises.

**Realizes:** FR-62

**Acceptance Criteria:**

**Given** the backup coverage list
**When** it is reviewed
**Then** it enumerates what is backed up, and anything not backed up is listed as a deliberate exclusion with its reason
**And** loss of any single Node does not lose that Node's backups

**Given** the appliance holds both the data and its backups
**When** the limit is documented
**Then** it is recorded explicitly that appliance loss is unrecoverable for bulk data in v1, mitigated only by the encrypted critical subset held offline

### Story D8.3: Restores executed, not assumed

As the operator,
I want to have restored each class of data at least once,
So that "configured" is never mistaken for "working".

**Realizes:** FR-63

**Acceptance Criteria:**

**Given** each backed-up class — Guests, persistent volumes, the database, and directory data
**When** the restore Procedure is executed
**Then** the restore completes and the restored data is verified correct rather than merely present
**And** each execution is recorded, since a configured-but-untested restore is treated as not present

## Epic D9: Single sign-on breadth

One account and one session reach every administrative interface, including services with no native support.

**FRs covered:** FR-32, FR-34, FR-35, FR-39, FR-52 · **Governed by:** AD-10, AD-14

### Story D9.1: Account-lock mapping — build what does not ship

As the operator,
I want disabling an account in the directory to actually reach the identity provider,
So that revocation is not silently a no-op.

**Realizes:** FR-35

**Acceptance Criteria:**

**Given** the identity provider has no built-in mapper for the directory's account-lock attribute, and the obvious attribute mapper inverts its sense
**When** the mapping is implemented
**Then** a disabled directory account is reflected as disabled at the provider

**Given** a disabled account
**When** the verification is run
**Then** authentication is attempted at each relying party and refused within that party's recorded bound
**And** refresh-token grants fail, and existing provider sessions are terminated rather than left to expire
**And** the verification is part of the Procedure, re-run on change, not a one-time check

### Story D9.2: Cluster access through the identity provider

As the operator,
I want kubectl to authenticate with my directory account,
So that cluster authorization follows the same groups as everything else.

**Realizes:** FR-39

**Acceptance Criteria:**

**Given** the cluster API
**When** OIDC authentication is configured
**Then** kubectl authenticates with a provider-issued token and no static credential is used for routine access
**And** group claims map to cluster authorization rules, and removing an account from a group removes the corresponding access

**Given** the identity provider is unavailable
**When** the operator needs to administer the cluster
**Then** the static administrative credential still works, remaining escrowed outside the platform

### Story D9.3: Administrative interfaces behind one login

As the operator,
I want the hypervisor, appliance, and dashboards to accept my one account,
So that there is no second set of logins to maintain.

**Realizes:** FR-32, FR-52

**Acceptance Criteria:**

**Given** each administrative interface
**When** authentication is configured
**Then** it accepts identity-provider authentication, and one authentication covers subsequent interfaces within the session window
**And** group membership determines view and edit permissions where the product supports it
**And** local administrative accounts remain available for break-glass but are not used routinely

**Given** an interface whose session model cannot honour the platform's target bound — such as one minting its own long-lived ticket with no back-channel logout
**When** its bound is recorded
**Then** its real ceiling is stated in the per-party table and accepted knowingly rather than assumed away

### Story D9.4: Forward-auth for services without native support

As the operator,
I want to put a login in front of a service that has none,
So that no internal service is protected only by nobody knowing its address.

**Realizes:** FR-34

**Acceptance Criteria:**

**Given** a service with no OIDC support
**When** an authenticating proxy is placed in front
**Then** unauthenticated requests are redirected to the identity provider, and identity and group claims are passed to the backing service
**And** the backing service binds only to an address reachable by the proxy, and its published name resolves only to the proxy

**Given** the flat network forecloses enforcement
**When** the limitation is documented
**Then** it is stated plainly that bypass prevention is binding-and-naming convention rather than network enforcement, acceptable only because there is one operator and no inbound path

## Epic D10: Destructive rebuild drill — DOCUMENTATION GATE

The second gate. S8 proved the architecture; this proves the documentation.

**FRs covered:** FR-64 · **Governed by:** AD-3, AD-22, AD-27

### Story D10.1: Full platform rebuild Procedure

As the operator,
I want a written order for rebuilding everything,
So that a catastrophe is a long day rather than an open-ended one.

**Realizes:** FR-64 (partial)

**Acceptance Criteria:**

**Given** the repository, the backups, and escrowed credentials
**When** the rebuild Procedure is written
**Then** it states its order, following the layer sequence, with each layer naming what it needs from below and what it must tolerate being absent from above
**And** it requires no undocumented knowledge and no input beyond those three sources
**And** it states explicitly which failures it does **not** cover, so its limits are known before they are discovered

### Story D10.2: The destructive drill

As the operator,
I want to destroy a Node and bring it back with nothing undocumented,
So that I am willing to break this platform on purpose.

**Realizes:** FR-64

**Acceptance Criteria:**

**Given** a fully working platform
**When** a Node is deliberately destroyed and rebuilt using only the repository and escrowed credentials
**Then** the number of steps required but not documented is **zero**
**And** the rebuilt Node rejoins and resumes its workloads
**And** the Automation reports zero changes against it

**Given** any gap found during the drill
**When** it is discovered
**Then** it is closed in both the Runbook and the Automation before the drill counts as passed, and the repository history shows the correction alongside the execution that found it

**Given** the cold-start path
**When** it is exercised
**Then** a start with both the internal registry and the outbound uplink unavailable succeeds, relying on upstream or cached images