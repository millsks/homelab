---
title: Project Asgard — Homelab Platform
status: final
created: 2026-08-28
updated: 2026-08-28
revision: 2 — amended by architecture phase
---

# PRD: Project Asgard

## 0. Document Purpose

This PRD is the requirements contract for Project Asgard, a four-node private cloud built from the hardware inventory in `infrastructure_inventory.txt`. Its readers are the architecture workflow that will turn these requirements into a technical spine, the epic-and-story workflow that will decompose them into executable work, and the operator who will build the thing and later need to know what "done" meant.

It builds on the approved product brief at `_bmad-output/planning-artifacts/briefs/brief-homelab-2026-08-28/` — `brief.md` for purpose, scope, and constraints, `addendum.md` for the capacity model, naming registry, identity design, storage analysis, and power design. This document does not repeat them; where a decision was settled upstream it is cited, not re-argued.

Structure: vocabulary is fixed in the Glossary (§3) and used verbatim everywhere after. Features (§4) group functional requirements, numbered globally as FR-N so downstream artifacts have stable references even if features are reorganized. Cross-cutting non-functional requirements live in §5. Technology choices and mechanism decisions live in `addendum.md`, not here — this document states capabilities and the conditions they must satisfy. Inferences carry inline `[ASSUMPTION]` tags, indexed in §12.

## 1. Vision

Project Asgard is a private cloud small enough to sit on a shelf and honest enough to teach. Four mini PCs, a NAS, and a switch become a Proxmox cluster running Kubernetes, backed by a single identity system where one account authenticates a Linux shell, a `kubectl` call, a Grafana dashboard, and an application the operator wrote that afternoon. It is not a collection of self-hosted services that happen to share a network. It is a platform with a coherent identity plane, a coherent storage plane, and a coherent deployment path.

What separates it from an ordinary homelab is that **it is described, not just built**. Every node, guest, and service exists as configuration in a Git repository, and every procedure exists twice — as a runbook a human follows at a keyboard, and as automation that produces an identical result unattended. Neither form is the summary of the other. The runbook explains why; the automation guarantees how. The governing invariant is that following the runbook by hand must produce a node the automation then considers already converged, which makes drift between the two a detectable defect rather than a slow decay.

That property is what converts the lab from an artifact into an instrument. A platform that can be destroyed and restored from source is a platform that can be experimented on without fear, and fearlessness is the actual deliverable — the operator wanted somewhere to develop OIDC-protected applications against a real authorization server, to practice the patterns a corporate environment would impose, and to break things on a Saturday. All three require a lab you are willing to break.

## 2. Target User

A single operator: an experienced software engineer, building this to develop against, to learn on, and to break deliberately. There are no other human accounts, and the enterprise machinery here exists for **fidelity rather than scale** — a design that would be over-engineering for a household is exactly correct for a simulator.

The secondary reader is the same operator months later, mid-outage, following a procedure they no longer remember writing. Much of the documentation standard in §5 is set by that reader rather than the first one.

### 2.1 Jobs To Be Done

- **Develop applications against a real authorization server.** Practice OIDC and OAuth2 integration — discovery, authorization code with PKCE, JWT validation, claims-to-authorization mapping — against an identity provider that behaves like the PingFederate deployments these applications will meet in production.
- **Practice the patterns a corporation would impose.** Centralized directory, SSO, RBAC, GitOps, observability, backup and restore — at a scale where the whole system fits in one head.
- **Build depth in specific technologies.** Kubernetes, infrastructure-as-code, configuration management, and platform operations, deliberately choosing the instructive option where the trade is affordable.
- **Have somewhere real to run personal software**, with a genuine path from commit to running workload.
- **Break things without consequence.** Destroy a node on purpose, restore it from source, and be bored by the outcome.
- **Stop maintaining infrastructure from memory.** Replace undocumented 11pm decisions with procedures that survive being forgotten.

### 2.2 Non-Users (v1)

- Household members. No family accounts, no shared media services, no consumer-facing surfaces.
- The public internet. Nothing is published; there are no anonymous users to design for.
- Any second administrator. Multi-admin delegation and separation-of-duties are simulated through directory groups and RBAC, not driven by a real second person.

### 2.3 Key User Journeys

Operator journeys, downscaled per the single-role audience. They exist to keep requirements anchored to lived moments rather than to organize the document.

- **UJ-1. Kevin rebuilds a node he deliberately destroyed.**
  Saturday morning. `thor` is wiped to prove the claim that it can be. Kevin installs the base hypervisor, adds the node to inventory in Git, runs the automation, and watches it rejoin the cluster and pick up its share of guests. He consults the runbook only to confirm ordering. **Climax:** the cluster reports four healthy nodes and nothing was reconstructed from memory. **Resolution:** the rebuild procedure is now evidence rather than assertion. **Edge case:** if the automation completes but a manual step was missing from the runbook, the gap is a documentation defect and gets fixed in the same sitting.

- **UJ-2. Kevin takes an application from empty repository to SSO-protected and running.**
  He has written a small web application that needs authenticated users. He registers a client in the identity provider, commits manifests to the platform repository, and lets GitOps converge. He opens the URL, is redirected to the login page, authenticates with the same account he uses for SSH, and lands in the application with his group memberships present as token claims. **Climax:** authorization decisions in his own code are driven by claims issued by a real IdP. **Resolution:** the deployment path is proven and the next application is a repetition, not an expedition.

- **UJ-3. Kevin logs into a node he has never touched.**
  A new guest, or a rebuilt host. He SSHes in with his directory account — no local user was created, no key was copied by hand — and his home directory is present with the contents he left on a different machine. **Climax:** the node is interchangeable. **Resolution:** he stops caring which machine he is on.

- **UJ-4. The power fails at three in the morning.**
  Nobody is awake. The UPS transfers to battery and signals the cluster. Workloads drain, guests shut down in dependency order, the hypervisors follow, and the NAS powers off last. Power returns; the lab comes back. **Climax:** Kevin learns about it from a notification and a clean log, not from a corrupted database. **Edge case:** if power returns mid-shutdown, the sequence completes rather than racing a restart.

- **UJ-5. Kevin revokes access from one place.**
  He disables a single directory account. SSH access to every node stops, `kubectl` stops, every SSO-protected service stops honoring existing sessions within the configured window. **Climax:** there is no second list to remember. **Resolution:** the identity plane is provably central rather than nominally central.

- **UJ-6. Kevin breaks something on purpose to learn how it fails.**
  He snapshots a guest, makes a change he expects to be destructive, observes the failure mode, and rolls back. **Climax:** the experiment cost minutes. **Resolution:** the snapshot discipline is what makes the lab a place to learn rather than a place to be careful.

## 3. Glossary

Downstream workflows and readers use these terms exactly. Introducing a synonym anywhere in this document is a discipline violation.

**Platform and topology**

- **Asgard** — the platform as a whole, and its DNS domain `asgard.home.arpa`. One Asgard.
- **Node** — a physical machine running the hypervisor. Exactly four: `odin`, `thor`, `heimdall`, `tyr`. Named for the Æsir.
- **Guest** — a virtual machine or container running on a Node. Many Guests per Node; a Guest runs on exactly one Node at a time and may migrate.
- **Cluster** — the four Nodes managed as one hypervisor cluster. One Cluster.
- **Yggdrasil** — the Kubernetes cluster running as Guests on the Cluster. Distinct from Cluster; never used interchangeably.
- **Control Plane Guest** — a Yggdrasil server node. Three: `urd`, `verdandi`, `skuld`, named for the Norns.
- **Worker Guest** — a Yggdrasil agent node running Workloads. Named for Valkyries.
- **Workload** — a containerized application deployed to Yggdrasil.
- **Nidavellir** — the NAS. Sole source of shared storage. One Nidavellir.

**Identity**

- **Directory** — the authoritative store of Accounts and Groups (`mimir`). Authenticates Nodes and Guests at the operating-system layer.
- **Identity Provider** (**IdP**) — the OIDC and SAML authorization server (`forseti`). Federates to the Directory for Accounts; issues Tokens to Relying Parties. Does not own Accounts.
- **Account** — one human or service identity. Lives in the Directory. Referenced by the IdP, never duplicated into it.
- **Group** — a collection of Accounts in the Directory, projected into Tokens as claims and consumed as the basis of Authorization.
- **Relying Party** — any system delegating authentication to the IdP. Includes Yggdrasil's API, the hypervisor UI, Nidavellir, and Workloads.
- **Token** — an OIDC ID or access token issued by the IdP, carrying claims including Group membership.
- **Break-glass Account** — a local Account on a Node or Guest, outside the Directory, used only when the Directory is unavailable. Not for routine use.
- **Draupnir** — the internal certificate authority. Sole issuer of TLS certificates within Asgard.

**Operations**

- **Runbook** — the human-followable form of a procedure: ordered steps, verification checkpoints, and the reasoning behind each decision point.
- **Automation** — the machine-executable form of the same procedure, idempotent, stored in the Repository.
- **Procedure** — a Runbook and its Automation together. Neither alone is a Procedure.
- **Converged** — the state in which Automation run against a system makes no changes. The central test: a system built by following the Runbook by hand must be Converged.
- **Repository** — the Git repository holding all Automation, Runbooks, and declarative configuration. Single source of truth.
- **Walking Skeleton** — the thin end-to-end vertical slice built first, exercising every integration seam before any layer is deepened.
- **Drill** — a deliberate destructive test executed to produce evidence that a Procedure works.

**Storage and power**

- **Share** — an NFS export from Nidavellir consumed by Nodes or Guests.
- **Home Directory** — an Account's `/home` directory, served from a Share, identical on every Node and Guest.
- **Persistent Volume** (**PV**) — durable storage attached to a Workload, provisioned from Nidavellir.
- **Off-NFS Store** — block or local storage used where NFS semantics are inadequate. Currently PostgreSQL (`fafnir`) only.
- **NUT Server** — the host owning the UPS connection and signaling Shutdown Sequence participants. Nidavellir.
- **Shutdown Sequence** — the dependency-ordered power-down of the platform on UPS battery, ending with Nidavellir.

## 4. Features

Functional requirements are numbered globally as FR-N and remain stable if features are reorganized. Each states a capability and the testable conditions that prove it. Mechanism — which product, which protocol, which file — belongs to architecture, not here.

### 4.1 Procedure Discipline

**Description:** The property that distinguishes Asgard from an ordinary homelab, and therefore the first feature rather than an afterthought. Every operational activity exists as a Procedure: a Runbook explaining the reasoning and a machine-executable Automation guaranteeing the result. The two are kept honest by a convergence test rather than by intention. Realizes UJ-1.

The operator explicitly chose completeness over speed as the rebuild standard — there is no time target, and requirements here optimize for a Procedure being correct and trustworthy rather than fast.

**Functional Requirements:**

#### FR-1: Every procedure exists in both forms, against an enumerated set

The operator can consult a **Procedure Index** in the Repository that enumerates every Procedure Asgard requires, and find both a Runbook and its corresponding Automation for each entry.

**Consequences (testable):**
- The Procedure Index exists in the Repository and is the authoritative list of what "every operational activity" means. Without it, FR-1 quantifies over an unbounded set and SM-1 and SM-2 have no denominator.
- Every Index entry resolves to both a Runbook and an Automation; an entry missing either is an incomplete Procedure.
- An activity performed but absent from the Index is a defect in the Index, closed under FR-3.
- No operational activity is documented in only one form.
- Each Runbook names the Automation that performs it, and each Automation names the Runbook that explains it.
- Runbooks state the reasoning at each decision point, not only the commands.

#### FR-2: Manual execution produces a converged system

The operator can follow a Runbook by hand and then run its Automation against the result, and the Automation reports no changes.

**Consequences (testable):**
- Running Automation against a Runbook-built system produces zero changes.
- Any difference is recorded as a documentation defect against the Procedure, not accommodated in the Automation.
- Automation is idempotent: a second consecutive run also produces zero changes.

#### FR-3: Documentation defects are resolved at discovery

The operator can record a gap found while executing a Procedure and resolve it before the activity is considered complete. Realizes UJ-1.

**Consequences (testable):**
- A Procedure executed with an undocumented manual step is not complete until that step is added to both forms.
- The Repository history shows the correction alongside the execution that discovered it.

#### FR-4: All configuration originates in the Repository

The operator can identify the Repository as the sole source of truth for the configuration of every Node, Guest, and service.

**Consequences (testable):**
- No configuration required to rebuild any component exists only on a running system.
- A change made directly on a running system is either reflected back into the Repository or reverted by the next Automation run.

#### FR-5: Procedures declare their verification

The operator can, on completing any Procedure, execute a stated verification and get an unambiguous pass or fail.

**Consequences (testable):**
- Every Procedure ends with a verification step whose expected output is stated.
- Verification is identical whether the Runbook or the Automation performed the work.

### 4.2 Hypervisor Foundation

**Description:** Four Nodes running a hypervisor and joined into one Cluster, providing the substrate all Guests run on. Snapshots are treated as a first-class safety mechanism because fearless experimentation is a stated purpose. Realizes UJ-1, UJ-6.

**Functional Requirements:**

#### FR-6: Four Nodes form one Cluster

The operator can manage all four Nodes as a single Cluster from any Node.

**Consequences (testable):**
- Cluster status reports four healthy members.
- Loss of one Node leaves the remaining three operating and manageable.

#### FR-7: A Node can be rebuilt from the Repository

The operator can destroy a Node entirely and restore it to full Cluster membership using only the Repository and documented Procedures. Realizes UJ-1.

**Consequences (testable):**
- Rebuild requires no information held outside the Repository except Break-glass credentials.
- The rebuilt Node is Converged per FR-2.
- The rebuilt Node resumes hosting Guests without manual reconfiguration of storage or network.

#### FR-8: Guests are provisioned declaratively

The operator can define a Guest in the Repository and have it created with the declared resources, storage, and network placement.

**Consequences (testable):**
- Guest specifications are declarative; applying them repeatedly converges rather than duplicates.
- A destroyed Guest is recreated from its declaration.

#### FR-9: Guests can be snapshotted and rolled back

The operator can snapshot a Guest before a change and restore it afterward. Realizes UJ-6.

**Consequences (testable):**
- A snapshot is taken and restored without reinstalling the Guest.
- Restoration returns the Guest to its pre-change state including disk contents.

#### FR-10: The Cluster is manageable when the Directory is unavailable

The operator can authenticate to the Cluster management interface and reach a Guest console using a Break-glass Account.

**Consequences (testable):**
- Cluster management authentication succeeds with the Directory offline.
- Guest consoles are reachable when Guest-level authentication is broken.

### 4.3 Network and Name Resolution

**Description:** Asgard occupies the existing flat LAN behind the household router; no segmentation is in scope. The switch uplinks to the household router, so Node-to-Node and Node-to-Nidavellir traffic stays local to the switch while outbound traffic for updates passes through the router. Asgard's own DNS domain, `asgard.home.arpa`, provides stable names for every Node, Guest, and service, and is the foundation both TLS and identity depend on. Realizes UJ-3.

Two switches carry two kinds of traffic. The **data switch** carries storage, Workload, and outbound traffic and reaches the household router **over a wireless bridge**. The **membership switch** is an isolated island: cluster membership traffic only, its own subnet, no gateway, and deliberately **no uplink to anything**. Connecting the two would return membership to shared fabric and forfeit the separation entirely.

**The uplink is wireless out of necessity.** The rack has no wired path to the household router, which sits in a closet on the opposite side of the house with no spare ports and no coaxial cabling anywhere in the building. The access point is therefore deployed in **client-bridge mode** as the uplink. Only outbound traffic crosses it — package retrieval, image pulls, upstream time, and alerts — so a 100–200 Mbps link is adequate. Cluster membership, storage, Workload, and backup traffic never leave the two switches at the rack.

```
ISP router ~~wireless bridge~~> data switch (10-port) --+-- odin   2.5 GbE (adapter)
    |                                          +-- thor       2.5 GbE (adapter)
    |                                          +-- heimdall   2.5 GbE (adapter)
    |                                          +-- tyr        2.5 GbE (adapter)
    +-- household devices                      +-- nidavellir 2.5 GbE
                                                   6 of 10 ports used

         membership switch (5-port, isolated) --+-- odin       1 GbE (onboard)
                                                +-- thor       1 GbE (onboard)
                                                +-- heimdall   1 GbE (onboard)
                                                +-- tyr        1 GbE (onboard)
                                                    4 of 5 ports used, no uplink
```

Nidavellir takes a 2.5 GbE port because four Nodes can demand several Gbps in aggregate; putting the faster link on the shared side moves the bottleneck to the individual Node, which is where it belongs.

**Functional Requirements:**

#### FR-11: Every Node, Guest, and service is reachable by name

The operator can reach any component by its fully-qualified name within `asgard.home.arpa` without knowing its address.

**Consequences (testable):**
- Forward resolution succeeds for every Node, Guest, and published service.
- Reverse resolution succeeds for every Node and Guest.
- Names follow the Norse registry in the brief addendum.

#### FR-12: Addressing is deterministic and recorded

The operator can determine the address any component will receive before it is built, from the Repository.

**Consequences (testable):**
- Infrastructure components receive stable addresses that survive rebuild.
- The address plan is in the Repository, not discovered from running systems.

#### FR-13: Name resolution survives a single failure

The operator can resolve names within Asgard when any one resolver is unavailable.

**Consequences (testable):**
- More than one resolver answers for the domain.
- Loss of one resolver does not prevent Nodes or Guests from resolving names.

#### FR-65: Nodes are wired, dual-homed, and separate membership traffic from bulk traffic

The operator can confirm every Node reaches the network over two wired interfaces, with cluster membership traffic isolated from storage and Workload traffic, and wireless disabled rather than held in reserve.

**Consequences (testable):**
- All four Nodes and Nidavellir are connected to the switch by cable.
- Wireless interfaces on the Nodes are disabled, not merely unused.
- Each Node presents two interfaces: the onboard 1 GbE and an added 2.5 GbE adapter.
- **Cluster membership traffic uses the onboard interface on an isolated membership switch; storage, Workload, and backup traffic use the 2.5 GbE adapter on the data switch.** The two share neither a link nor a switch.
- The membership switch has no uplink and no gateway; nothing but Node membership traffic reaches it.
- The membership switch is administered standalone. It is **not** adopted into any centralised controller, so that the network carrying cluster membership never depends on software that could run on the cluster it serves.
- The membership switch's configuration lives in the Repository as a Procedure per FR-1 and FR-4, including the deliberate decision to leave optional features disabled.
- Nidavellir is connected at 2.5 GbE.
- Interface naming is deterministic across reboots and recorded in the address plan per FR-12.

**Notes:** Membership signalling is latency- and jitter-sensitive, and ordinary wireless variance is indistinguishable from Node loss — leaving wireless enabled as a fallback is worse than not having it, because silent failover destabilises membership while every Node still appears up. The same argument applies to sharing one link with bulk storage traffic: heavy NFS load can starve membership signalling into a false partition.

Membership stays on the *onboard* interface deliberately. The added adapters are USB-attached, and USB Ethernet is more prone to resets and renumbering than an onboard controller — acceptable for bulk traffic that retries, unacceptable for the signalling that decides whether a Node is alive. Deterministic interface naming is called out because USB device naming is less stable than onboard, and the address plan depends on it.

**Notes:** This is a hard constraint rather than a preference. Cluster membership signalling is latency- and jitter-sensitive; ordinary wireless variance is indistinguishable from node loss and produces spurious partitions and evictions. Leaving wireless enabled as a fallback is worse than not having it, because silent failover destabilises cluster membership while every node still appears up. NFS under FR-15 and FR-17 degrades badly on a lossy link for the same reason.

#### FR-14: Household devices are unaffected

The operator can operate Asgard without changing DNS or DHCP behavior for devices outside it.

**Consequences (testable):**
- Non-Asgard devices continue to use the household router unchanged.
- Asgard does not take over DHCP for the household LAN.

`[ASSUMPTION: the household router will continue serving DHCP for non-Asgard devices, and Asgard can coexist with it without assuming control. Unverified against the specific router.]`

### 4.4 Shared Storage

**Description:** Nidavellir serves Shares that make Nodes and Guests interchangeable — the same Home Directory appears everywhere — and provisions Persistent Volumes for Workloads. One deliberate exception exists: PostgreSQL runs on an Off-NFS Store, because its durability model depends on locking and `fsync` semantics NFS implements loosely. Realizes UJ-3.

**Functional Requirements:**

#### FR-15: Home Directories are identical on every host

The operator can log into any Node or Guest and find the same Home Directory contents. Realizes UJ-3.

**Consequences (testable):**
- A file written on one host is present on another under the same Account.
- No Home Directory content is stored on a Node's local disk.
- First login provisions a Home Directory without manual intervention.

#### FR-16: Storage unavailability degrades rather than hangs

The operator can log into a Node and perform local diagnostics while Nidavellir is unavailable.

**Consequences (testable):**
- Loss of the Share does not leave processes unkillable in uninterruptible sleep.
- A Break-glass Account can log in and operate without the Share.
- Recovery on Share return requires no Node reboot.

#### FR-17: Workloads obtain Persistent Volumes on demand

The operator can declare storage for a Workload and have a Persistent Volume provisioned automatically from Nidavellir.

**Consequences (testable):**
- A storage claim results in a bound, writable volume without manual provisioning.
- Two storage classes are offered: an NFS default class supporting ReadWriteMany, and an iSCSI class supporting ReadWriteOnce block volumes.
- Data survives Workload restart and rescheduling to a different Worker Guest.
- Volumes can be attached by more than one Workload where the class supports it.

`[ASSUMPTION: Nidavellir's capacity is sufficient for Home Directories and all Persistent Volumes for the foreseeable term; no storage tiering is needed in v1.]`

#### FR-18: PostgreSQL does not run on NFS

The operator can confirm that PostgreSQL data resides on an Off-NFS Store.

**Consequences (testable):**
- PostgreSQL data is on local NVMe, never a Share and never NAS-backed block storage.
- The constraint is enforced by configuration in the Repository, not by convention.
- Nidavellir is HDD-only, so the constraint covers any protocol reaching it — the exclusion is about the medium, not about NFS specifically.

#### FR-19: Storage capacity and health are visible

The operator can see capacity, utilization, and drive health for Nidavellir, and be alerted before exhaustion.

**Consequences (testable):**
- Utilization and drive health are reported to the observability system.
- An alert fires at a defined threshold before capacity is exhausted.
- Drive failure produces an alert without the operator inspecting the NAS.

### 4.5 Identity and Directory

**Description:** One Directory holds every Account and Group and authenticates Nodes and Guests at the operating-system layer. It is authoritative: the IdP federates to it and never duplicates Accounts. Because centralized login creates a circular dependency — hosts need the Directory, and the Directory runs on those hosts — deliberate escape hatches are requirements, not caveats. Realizes UJ-3, UJ-5.

**Functional Requirements:**

#### FR-20: One Account authenticates to every host

The operator can log into any Node or Guest with a single Directory Account. Realizes UJ-3.

**Consequences (testable):**
- No per-host local account is created for routine access.
- A password or key change takes effect everywhere without per-host action.
- Group membership resolves consistently on every host.

#### FR-21: Authorization is driven by Group membership

The operator can grant or remove access to hosts and privilege escalation by changing Group membership in the Directory.

**Consequences (testable):**
- Which Accounts may access which hosts is determined centrally, not by per-host configuration.
- Privilege escalation rules are defined centrally and applied consistently.

#### FR-22: Disabling an Account revokes host access within a bounded window

The operator can disable one Account and lose the ability to authenticate to any Node or Guest with it, within a bounded and stated window. Realizes UJ-5.

**Consequences (testable):**
- Authentication fails on every reachable host immediately after the Account is disabled.
- Cached offline credentials expire after a configured maximum age, so a host that cannot reach the Directory stops honouring a disabled Account within that bound rather than indefinitely.
- The offline expiry bound is stated in configuration in the Repository, not left at product default.
- Revocation requires editing the Directory only — no per-host list is maintained.

**Notes:** FR-23's credential cache is what makes an unbounded version of this requirement false: a cache with no expiry lets a disabled Account keep authenticating for as long as the Directory is unreachable. The two requirements are reconciled by bounding the cache, not by choosing between them.

#### FR-23: Hosts authenticate during a Directory outage for known Accounts

The operator can log into a host they have previously authenticated to while the Directory is unavailable, using their own Account rather than a Break-glass Account.

**Consequences (testable):**
- Credential caching permits login for a previously-authenticated Account with the Directory offline.
- Group membership and privilege escalation resolve from cache during the outage.
- A never-before-seen Account correctly fails.

**Notes:** See also FR-24, whose local-home requirement is what makes Break-glass usable during a storage outage. This is not a defense layer weighed against FR-24 — it is a single configuration setting with no ongoing cost. Its value is that routine work during an outage continues under the operator's own Account instead of a shared emergency credential, and that Guests losing the Directory keep functioning rather than becoming unreachable.

The cache trades directly against FR-22: an unexpired cache is indistinguishable from a valid Account. The expiry bound is therefore a required setting, and choosing it is choosing how long a disabled Account may survive an outage.

#### FR-24: Break-glass access exists on every host and survives storage loss

The operator can access any Node or Guest using a Break-glass Account independent of both the Directory and Nidavellir.

**Consequences (testable):**
- Every Node and Guest has a Break-glass Account with privilege escalation.
- **The Break-glass Account's home directory is local to the host, never served from a Share** — so a login during a storage outage lands in a working shell.
- **The Break-glass home directory path lies outside any NFS-managed path.** A local home nested under the Share's mount point is shadowed by the mount while it is active and unreachable while it hangs; under an automounted path it is not visible at all. Being local is necessary but not sufficient — the path must also be one NFS never manages.
- Break-glass Accounts are not managed by, and do not depend on, the Directory.
- The Break-glass Account is a named local account, not the root account directly; direct remote root login remains disabled.
- Break-glass credentials are stored outside Asgard and recorded as such.

#### FR-25: The Directory survives loss of one instance

The operator can continue to authenticate, and the IdP can continue to issue Tokens, when one Directory instance is unavailable.

**Consequences (testable):**
- More than one Directory instance answers authentication requests.
- Account and Group changes made against one instance appear on the other.
- The IdP continues to authenticate Accounts when either instance is unavailable.
- A Directory instance can be patched and restarted without interrupting authentication to any Relying Party.

**Notes:** The justification is service availability, not administrative access — FR-24 already guarantees the operator can get in. The Directory is a runtime dependency of the IdP and therefore of every Relying Party, so a single instance makes every Directory upgrade a platform-wide SSO outage. Sequenced into the deepen phase rather than the Walking Skeleton, so it remains a clean single cut if deferred to v2.

#### FR-26: Accounts are defined in the Repository

The operator can rebuild the Directory's Account and Group structure from the Repository.

**Consequences (testable):**
- Account and Group definitions exist as declarative configuration.
- Secret material is not stored in the Repository in plaintext.

### 4.6 Certificate Authority

**Description:** Draupnir issues every TLS certificate inside Asgard. Because nothing is internet-facing, an internal authority is sufficient and avoids public DNS and ACME entirely — but only if its trust is distributed automatically, since a certificate authority nobody trusts produces warnings rather than security.

**Functional Requirements:**

#### FR-27: One authority issues all internal certificates

The operator can obtain a TLS certificate for any internal service from Draupnir.

**Consequences (testable):**
- Every internal TLS endpoint presents a certificate chaining to Draupnir.
- No service presents a self-signed certificate outside that chain.

#### FR-28: Trust is distributed automatically

The operator can reach any internal service from any Node or Guest without a certificate warning.

**Consequences (testable):**
- The Draupnir trust anchor is installed on every Node and Guest by Automation.
- Command-line tools and Workloads validate internal certificates without per-host manual steps.

#### FR-29: Certificates renew without manual action

The operator can rely on certificates renewing before expiry without intervention.

**Consequences (testable):**
- Certificates renew automatically ahead of expiry.
- Renewal failure raises an alert before the certificate expires.

### 4.7 Single Sign-On and Federation

**Description:** The IdP federates to the Directory and issues Tokens to every Relying Party in Asgard — the Kubernetes API, the hypervisor UI, Nidavellir, the observability stack, and the operator's own Workloads. This is the feature the platform exists to exercise: it must behave like a production authorization server, because its purpose is to be developed against. Services with no native OIDC support are fronted rather than exempted. Realizes UJ-2, UJ-5.

**Functional Requirements:**

#### FR-30: The IdP federates to the Directory

The operator can authenticate to the IdP using a Directory Account without that Account being duplicated in the IdP.

**Consequences (testable):**
- Accounts are not created directly in the IdP.
- A Directory password change takes effect for IdP authentication immediately.
- The IdP can be rebuilt without loss of Account data.

#### FR-31: Group membership appears in Tokens as claims

The operator can receive a Token containing Group memberships and use them for authorization decisions. Realizes UJ-2.

**Consequences (testable):**
- Tokens carry Group membership in a documented, stable claim.
- Adding an Account to a Group changes claims on the next Token issued.
- A Workload can make authorization decisions from claims alone.

#### FR-32: Administrative interfaces authenticate through the IdP

The operator can log into the hypervisor UI, the observability interface, and Nidavellir using the same Account and a single sign-on session.

**Consequences (testable):**
- Each named interface accepts IdP authentication.
- One authentication covers subsequent interfaces within the session window.
- Local administrative accounts remain available for break-glass but are not used routinely.

`[ASSUMPTION: the hypervisor UI, Nidavellir, and the observability stack each support OIDC against a self-hosted provider at the versions in use. This must be verified in architecture before FR-32 is relied upon — it is the assumption whose failure would most reshape §4.7.]`

#### FR-33: Workloads can be registered as Relying Parties

The operator can register a new Workload with the IdP and integrate it using standard OIDC flows. Realizes UJ-2.

**Consequences (testable):**
- Registration is declarative and lives in the Repository.
- The IdP publishes a standards-compliant discovery document.
- Authorization code flow with PKCE is supported.
- Integration requires no vendor-specific client library.

#### FR-34: Services without native OIDC are fronted

The operator can place an authenticating proxy in front of a service that has no OIDC support, and reach it only after authenticating.

**Consequences (testable):**
- Unauthenticated requests are redirected to the IdP.
- Identity and Group claims are passed to the backing service.
- The backing service binds only to an address reachable by the proxy, and its published name resolves only to the proxy.

**Notes:** Bypass is prevented by binding and naming convention, not by network enforcement — §6 rules out the segmentation that would make it enforceable, so anyone on the flat LAN who learns the backing address can still reach it directly. The limitation is stated rather than papered over; it is acceptable only because Asgard has one operator and no inbound path (NFR-14).

#### FR-35: Account disablement propagates to Relying Parties within stated, per-party bounds

The operator can disable an Account and have every Relying Party stop honoring it within a bound stated for that party. 15 minutes is the target and the default; parties that cannot honour it declare their actual ceiling. Realizes UJ-5.

**Consequences (testable):**
- Access tokens issued by the IdP are valid for no more than 15 minutes.
- **The Directory's account-lock attribute is mapped into the IdP**, so a disabled Account is reflected as disabled at the IdP rather than remaining enabled in its imported copy. Without this mapping, disablement in the Directory does not reach the IdP at all and the rest of this requirement is void.
- Refresh-token grants fail after disablement.
- Existing IdP sessions for a disabled Account are terminated, not left to expire.
- Each Relying Party's actual propagation bound is recorded in a table in the Repository. Parties whose session model cannot honour 15 minutes — notably the hypervisor UI, which issues its own long-lived ticket after OIDC login and offers no back-channel logout — state their real ceiling, and that ceiling is accepted knowingly rather than assumed away.

**Notes:** The uniform "15 minutes everywhere" claim was false in three independent places: cached host credentials (FR-22), the Directory-to-IdP account-lock gap addressed above, and the hypervisor's self-issued ticket. Revocation remains centrally driven from one Account; it is not instantaneous and not uniform, and the per-party table is what keeps that honest.

#### FR-36: Authentication events are recorded

The operator can review authentication successes and failures across Relying Parties from one place.

**Consequences (testable):**
- The IdP emits authentication events to the observability system.
- Failed authentication is distinguishable from failed authorization.
- Events identify the Account, the Relying Party, and the outcome.

### 4.8 Kubernetes Platform

**Description:** Yggdrasil runs as Guests on the Cluster and is where Workloads live. It authenticates through the IdP like every other Relying Party, so `kubectl` access is governed by the same Account and Groups as an SSH session. Its storage comes from Nidavellir. Realizes UJ-2.

**Functional Requirements:**

#### FR-37: Yggdrasil survives loss of one Control Plane Guest

The operator can continue to schedule and manage Workloads when one Control Plane Guest is unavailable.

**Consequences (testable):**
- Three Control Plane Guests participate in a quorum.
- Loss of one leaves the API served and Workloads schedulable.
- The lost Control Plane Guest rejoins without cluster rebuild.

#### FR-38: Control Plane Guests are distributed across Nodes

The operator can lose any single Node without losing Yggdrasil.

**Consequences (testable):**
- No two Control Plane Guests share a Node.
- Node loss removes at most one Control Plane Guest.

#### FR-39: `kubectl` authenticates through the IdP

The operator can run `kubectl` authenticated by a Token from the IdP, with permissions determined by Group membership. Realizes UJ-2, UJ-5.

**Consequences (testable):**
- No static administrative credential is used for routine access.
- Group claims map to cluster authorization rules.
- Removing an Account from a Group removes the corresponding access.
- A static administrative credential remains available for break-glass and is stored outside Asgard.

#### FR-40: Yggdrasil is rebuildable from the Repository

The operator can destroy and recreate Yggdrasil from the Repository, and restore Workloads without manual reconstruction.

**Consequences (testable):**
- Cluster composition and configuration are declared in the Repository.
- Workloads return by reconciliation, not manual reapplication.
- Persistent Volume data survives cluster rebuild.

#### FR-41: Workloads reach the network by stable name

The operator can reach a Workload from the LAN by a name in `asgard.home.arpa` over TLS.

**Consequences (testable):**
- Published Workloads are reachable by hostname without port memorization.
- Publication uses Gateway API resources only; Ingress resources are not used, so one routing model exists rather than two.
- A single load-balancer address serves as the ingress point, and names resolve to it.
- Certificates are issued by Draupnir per FR-27, obtained over ACME.
- Publishing a new Workload requires no manual DNS or certificate step.

### 4.9 Continuous Delivery

**Description:** The path from committed source to running Workload. Deployment is reconciliation from the Repository rather than an imperative push, which makes the Repository's status as source of truth (FR-4) enforced rather than declared. Realizes UJ-2.

**Functional Requirements:**

#### FR-42: Workload state reconciles from the Repository

The operator can change a Workload declaration in the Repository and observe the change applied without manual deployment.

**Consequences (testable):**
- Committed changes converge within a bounded interval without operator action.
- Drift introduced directly against Yggdrasil is reverted or reported.
- Current deployed state is determinable from the Repository.

#### FR-43: Container images are built and stored within Asgard

The operator can build a container image from source and store it in an internal registry that Yggdrasil can pull from.

**Consequences (testable):**
- Images are built from committed source, not a workstation.
- Yggdrasil pulls from the internal registry without external dependency.
- Images are identifiable back to the commit that produced them.

#### FR-44: A new application reaches production by a documented path

The operator can take a new application from empty repository to running, SSO-protected Workload following one Procedure. Realizes UJ-2.

**Consequences (testable):**
- The Procedure covers registration with the IdP, image build, declaration, and publication.
- No step requires undocumented manual configuration.
- A second application repeats the Procedure without variation.

#### FR-45: Deployments can be rolled back

The operator can return a Workload to a previous known-good state. Realizes UJ-6.

**Consequences (testable):**
- Rollback is performed through the Repository, preserving FR-4.
- The previous state is identifiable without reconstruction from memory.

### 4.10 Stateful Services

**Description:** PostgreSQL (`fafnir`) and Redis (`ratatoskr`), available to Workloads and to the platform itself. PostgreSQL carries the Off-NFS constraint from FR-18. These are shared platform services rather than per-application instances, so their availability and backup requirements are stricter than any single Workload's.

**Functional Requirements:**

#### FR-46: Workloads can obtain a database

The operator can provision a PostgreSQL database and credentials for a Workload through a documented Procedure.

**Consequences (testable):**
- Databases and roles are created without manual server-side steps outside the Procedure.
- Credentials are delivered to the Workload without appearing in the Repository in plaintext.
- Each Workload's database is isolated from others'.

#### FR-47: PostgreSQL is backed up and restorable

The operator can restore PostgreSQL to a prior point and verify the restored data.

**Consequences (testable):**
- Backups run on a defined schedule without operator action.
- A restore has been performed and verified, not merely configured.
- Backups are stored off the host running PostgreSQL.

#### FR-48: Redis is available to Workloads

The operator can make a Redis instance available to a Workload with documented connection details and access control.

**Consequences (testable):**
- Redis requires authentication.
- Loss of Redis degrades dependent Workloads without data loss in PostgreSQL.
- Persistence behavior is a documented, deliberate choice.

### 4.11 Observability

**Description:** Huginn observes and Muninn remembers — metrics and logs for Nodes, Guests, Yggdrasil, and Workloads, with dashboards behind SSO. Its purpose is that the operator learns about failures from the platform rather than from a user, and can answer "what changed" during a Drill.

**Functional Requirements:**

#### FR-49: Platform metrics are collected and retained

The operator can view current and historical metrics for every Node, Guest, and Workload.

**Consequences (testable):**
- Metrics cover host resources, Cluster health, Yggdrasil health, and Workload state.
- Retention is a defined period, bounded so storage growth is predictable.
- A new Guest or Workload is discovered without manual registration.

#### FR-50: Logs are centralized and searchable

The operator can search logs across Nodes, Guests, and Workloads from one interface.

**Consequences (testable):**
- Logs are queryable by host, Workload, and time range.
- Logs survive the destruction of the system that produced them.
- Retention is bounded and defined.

#### FR-51: Failures generate alerts

The operator can be notified of a defined failure condition without watching a dashboard.

**Consequences (testable):**
- Alerts fire for Node loss, storage exhaustion, certificate expiry approach, backup failure, and UPS events.
- Notifications reach the operator outside the platform's own interfaces.
- An alert names the affected component and the condition.

#### FR-52: Dashboards authenticate through the IdP

The operator can reach observability dashboards using the same Account and session as other Relying Parties.

**Consequences (testable):**
- Access requires IdP authentication per FR-32.
- Group membership determines view and edit permissions.

### 4.12 Secrets Management

**Description:** Credentials, keys, and tokens the platform needs to operate, and the bootstrap problem of holding them before a secret store exists. Because FR-4 makes the Repository the source of truth, this feature defines how secret material coexists with a Repository that will be pushed to GitHub.

**Functional Requirements:**

#### FR-53: No plaintext secret is committed

The operator can push the Repository to a remote without exposing usable credentials.

**Consequences (testable):**
- No plaintext credential, key, or token exists in the Repository or its history.
- Encrypted secret material in the Repository is unusable without a key held outside it.
- A check prevents a plaintext secret from being committed.

#### FR-54: Workloads obtain secrets without manual injection

The operator can grant a Workload access to a secret without placing it in a manifest by hand.

**Consequences (testable):**
- Secrets are delivered at runtime, not baked into images.
- Rotating a secret does not require editing Workload declarations.
- A Workload's access to a secret is revocable.

#### FR-55: Break-glass credentials are held outside Asgard

The operator can recover Break-glass credentials when the entire platform is unavailable. Realizes UJ-1.

**Consequences (testable):**
- Break-glass credentials for every Node, plus the Yggdrasil static administrative credential and the Draupnir trust anchor, are stored outside Asgard.
- Recovery does not require any Asgard component to be running.
- The store's location and contents are documented in the Repository without exposing the credentials themselves.

### 4.13 Power Continuity

**Description:** The UPS buys an estimated twelve to fifteen minutes — a figure FR-60 requires be measured rather than assumed; the orchestration converts that time into data integrity. The design's controlling constraint is a dependency inversion: Nidavellir must power down last because everything's storage depends on it, yet it is the NUT Server that signals the others.

**A correction the architecture must carry.** Nidavellir's operating system offers no shutdown handshake with its clients — it enters a protective mode on its own timer and does not know or wait for whether dependent hosts have finished. Ordering here is therefore **achieved by tuned delay, not by coordination**: Nodes act at one battery threshold, Nidavellir at a later one, with the interval deliberately sized larger than the measured Node shutdown time. This is a race engineered to be unlosable, and FR-60's Drill exists to prove the margin rather than to confirm a guarantee that does not exist. Requirements below are written to that reality.

**Functional Requirements:**

#### FR-56: The platform shuts down cleanly on sustained power loss

The operator can lose mains power unattended and find the platform powered down without corruption. Realizes UJ-4.

**Consequences (testable):**
- Shutdown begins automatically after a defined time on battery.
- The Shutdown Sequence completes within the battery's proven runtime, with margin.
- No PostgreSQL or Nidavellir corruption results.

`[ASSUMPTION: measured battery runtime at the real ~320 W load exceeds the Shutdown Sequence duration with margin. FR-60 requires this be measured by Drill rather than taken from the specification sheet.]`

#### FR-57: Shutdown order is achieved by tuned delay, with proven margin

The operator can confirm the Shutdown Sequence powers components down in an order respecting their storage dependencies, achieved through configured delays rather than inter-host coordination. Realizes UJ-4.

**Consequences (testable):**
- Workloads drain, then Guests stop, then Nodes stop, then Nidavellir stops — in that order.
- Nidavellir's protective-mode threshold is configured later than the measured completion time of all Node shutdowns, by a stated margin.
- The margin is recorded as a number in the Repository, derived from Drill measurement rather than estimation.
- No Guest is terminated while its storage is already unavailable.
- Nidavellir is the last device to cease serving storage.

**Notes:** The absence of a handshake is the reason the margin must be measured and recorded. A margin that is merely assumed is the single most likely cause of the corruption FR-56 exists to prevent.

#### FR-58: All shutdown participants remain powered until they act

The operator can confirm every component required to execute the Shutdown Sequence is on battery power.

**Consequences (testable):**
- All four Nodes, Nidavellir, **both switches**, and the household router are on battery-backed outlets.
- The membership switch is battery-backed: losing it mid-sequence would break cluster membership while Guests are still shutting down.
- **The household router cannot be battery-backed.** It sits in a closet on the opposite side of the house, on a circuit outside the operator's control. In a whole-house outage it loses power, and no outbound notification can leave the premises regardless of what generates it.
- **Consequence:** FR-51's external dead-man's-switch tier is the only alerting path that survives a whole-house outage, and is therefore load-bearing rather than supplementary. It alerts from external infrastructure over cellular when the heartbeat stops.
- A small independent UPS in the router closet would restore the direct path; not in v1 scope.
- Loss of mains does not interrupt the network path carrying shutdown signals.

#### FR-59: Power events are visible and alerted

The operator can see transfer to battery, battery state, and shutdown progress, and be notified of each.

**Consequences (testable):**
- Transfer to battery raises an alert per FR-51.
- Battery charge and estimated runtime are recorded as metrics.
- A battery requiring replacement is reported before it fails.

#### FR-60: The Shutdown Sequence is proven by Drill

The operator can produce evidence that the Shutdown Sequence works, from an executed Drill rather than configuration review.

**Consequences (testable):**
- A Drill has been performed by removing mains power.
- Measured runtime under real load is recorded, not taken from the specification sheet.
- The Drill is repeated after battery replacement.
- The Drill measures the interval between the last Node completing shutdown and Nidavellir ceasing to serve, confirming the FR-57 margin holds under real load.

### 4.14 Backup and Recovery

**Description:** What makes destruction safe, and therefore what makes the lab usable for its stated purpose. A backup that has never been restored is an assumption; this feature exists to convert assumptions into evidence.

**Functional Requirements:**

#### FR-61: Platform state is backed up automatically

The operator can rely on Guests, Persistent Volumes, databases, and Directory data being backed up without manual action.

**Consequences (testable):**
- Backups run on a defined schedule.
- Coverage is enumerated in the Repository; anything not backed up is listed as a deliberate exclusion.
- Backup failure raises an alert per FR-51.

#### FR-62: Backups survive loss of any single Node

The operator can restore after losing the Node that produced the backup.

**Consequences (testable):**
- Backups are stored on Nidavellir, independent of the Node whose data they hold.
- Loss of any single Node does not lose that Node's backups.
- Backup integrity is verified on Nidavellir, not assumed from a successful write.

**Out of Scope:**
- Independence from Nidavellir itself. Nidavellir is both the sole bulk backup target and the source of Home Directories and Persistent Volumes, so its loss is currently unrecoverable.

**Notes:** `[NOTE FOR PM]` This is a knowingly accepted gap, not an oversight. The v1 inventory contains no second bulk storage device, and the operator has deferred purchasing one. Until that target exists, **loss of Nidavellir is total data loss** for Persistent Volumes and Home Directories, and the §10 risk register records it as accepted rather than mitigated. Acquiring an independent target is the single highest-value addition to v2, at which point this requirement returns to its stronger form.

#### FR-63: Restores are verified, not assumed

The operator can point to an executed and verified restore for each backed-up class of data.

**Consequences (testable):**
- A restore has been performed for Guests, Persistent Volumes, PostgreSQL, and Directory data.
- Restored data is verified correct, not merely present.
- Each restore is a documented Procedure.

#### FR-64: The platform can be rebuilt from Repository and backups

The operator can rebuild Asgard from the Repository plus backups plus Break-glass credentials, with no other input, provided Nidavellir survives. Realizes UJ-1.

**Consequences (testable):**
- A full rebuild Procedure exists and states its order.
- The Procedure requires no undocumented knowledge.
- A destructive Drill on at least one Node has proven it.
- The Procedure states explicitly which failures it does *not* cover, so its limits are known before they are discovered.

**Notes:** Inherits FR-62's boundary — rebuild is proven against Node loss, not against Nidavellir loss.

## 5. Cross-Cutting Non-Functional Requirements

### 5.1 Documentation Quality

The differentiating quality attribute, and the one most likely to erode quietly.

- **NFR-1.** Every Procedure is executable by the operator six months later with no recall of building it. Ambiguity is a defect.
- **NFR-2.** Runbooks state reasoning, not only commands. A step whose purpose is unstated cannot be evaluated when conditions differ.
- **NFR-3.** Automation is idempotent without exception. Any Automation that fails on a second run is defective.
- **NFR-4.** Procedures are versioned with the systems they describe; a change to a system and to its Procedure land together.
- **NFR-5.** Where a Runbook and its Automation disagree, the Automation is authoritative for *what* and the Runbook for *why*, and the disagreement is a defect to be closed rather than tolerated.

### 5.2 Capacity

- **NFR-6.** Capacity is bounded from two sides so it cannot be satisfied by relocating a service. **(a)** Total committed Guest memory across the Cluster does not exceed 90 GB of the 128 GB physical, and **(b)** at least 15 GB remains schedulable within Yggdrasil. Measuring only unallocated hypervisor memory is insufficient — moving a service from its own Guest into a Worker Guest would satisfy such a metric while consuming the same capacity.
- **NFR-7.** Loss of any one Node leaves sufficient capacity to run all identity, storage, and Yggdrasil control functions, though not necessarily all Workloads. NFR-6's 90 GB ceiling exists to make this achievable: three Nodes provide 96 GB.
- **NFR-8.** Observability retention is bounded so storage growth is predictable rather than discovered at exhaustion.
- **NFR-9.** Guests declare explicit memory limits; no component relies on unbounded default sizing.

### 5.3 Security

- **NFR-10.** No credential, key, or token exists in plaintext in the Repository or its history.
- **NFR-11.** Every HTTPS and OIDC endpoint in Asgard presents a certificate chaining to Draupnir, and no such endpoint is served over plaintext HTTP. Named exclusions, which use their own transport security rather than Draupnir certificates: SSH (host keys), NFS Shares (unencrypted on the trusted LAN), Redis (authenticated, unencrypted), and cluster membership traffic. The exclusions are deliberate and bounded by NFR-14's no-inbound-path position; a blanket "all traffic" claim would be false.
- **NFR-12.** Direct remote root login is disabled on every Node and Guest; privilege escalation is through a named Account.
- **NFR-13.** Break-glass credentials are unique per host, not shared.
- **NFR-14.** No Asgard service is reachable from the internet, and no inbound path from outside the LAN exists. Access requires presence on the local network.
- **NFR-15.** Authentication events are recorded and retained per FR-36 and FR-50.

### 5.4 Reliability

- **NFR-16.** Identity, storage, and Yggdrasil control tolerate loss of one Node without operator intervention.
- **NFR-17.** No unattended failure results in data corruption. Availability may be sacrificed; integrity may not.
- **NFR-18.** Every recovery Procedure is proven by execution before being relied upon. Configured-but-untested is treated as not present.
- **NFR-19.** Failure conditions are detected and alerted rather than discovered during use.

### 5.5 Operability

- **NFR-20.** The operator can determine current platform state from the Repository and the observability system without logging into individual hosts.
- **NFR-21.** Routine operations require no Break-glass credential.
- **NFR-22.** Adding a Node, Guest, or Workload follows an existing Procedure rather than requiring a new one.
- **NFR-23.** Snapshot-before-change is available for every Guest, so experimentation is cheap by default.

## 6. Non-Goals

- **Not a household service platform.** No family accounts, no media services, no consumer surfaces. Adding one changes the availability and UX requirements of the whole system.
- **Not internet-facing.** No public DNS, no ACME certificates, no inbound exposure, no anonymous users. This is what permits an internal certificate authority and a modest security posture.
- **Not a high-availability production system.** HA is taken where it is cheap and instructive. Integrity is non-negotiable; uptime is not a goal in itself.
- **Not a Kubernetes-only platform.** Guests running outside Yggdrasil are legitimate. "Everything in the cluster" is not an objective — but neither is the reverse: placement follows a stated test rather than preference, and a service runs outside only when it meets one. The Directory and the platform CA are the deliberate examples; PostgreSQL is not, having been placed inside the cluster on that test.
- **Not segmented.** VLANs, a dedicated firewall, and network zoning are out. The lab shares the household LAN.
- **Not remotely accessible.** No VPN, no tunnel, no inbound path from outside the LAN. Operating Asgard means being on the local network. This removes the plane in which an identity-dependent remote path could lock the operator out, and it is the strictest interpretation of the no-exposure position.
- **Not optimized for build speed.** Completeness and correctness of Procedures govern; no rebuild time target exists, and none should be inferred.
- **Not multi-tenant.** One operator, one trust domain. Group-based authorization simulates separation; it does not enforce isolation between real parties.
- **Not a hardware upgrade project.** The platform targets the existing inventory plus the UPS. Faster networking and additional nodes are possible futures, not requirements.

## 7. MVP Scope

### 7.1 In Scope

- Proxmox Cluster across four Nodes, declaratively provisioned
- `asgard.home.arpa` with resilient name resolution and a recorded address plan
- Nidavellir serving Home Directories and Persistent Volumes; PostgreSQL on an Off-NFS Store
- Directory with replica, network login on every host, Break-glass access with local home directories
- Draupnir issuing all internal TLS, trust distributed automatically
- Forseti federated to the Directory, fronting Yggdrasil, the hypervisor UI, Nidavellir, observability, and Workloads
- Yggdrasil with three Control Plane Guests spread across Nodes, OIDC-authenticated `kubectl`, name-and-TLS Workload publication
- GitOps reconciliation, internal image build and registry
- PostgreSQL and Redis as shared platform services
- Metrics, logs, and alerting with SSO-protected dashboards
- Secrets management with no plaintext in the Repository and off-platform break-glass escrow
- UPS with dependency-ordered Shutdown Sequence, proven by Drill
- Automated backup with verified restores for every backed-up class
- Every one of the above as a Procedure — Runbook plus Automation — in the Repository
- A reference application: the operator's own code, deployed by GitOps, authorizing from IdP claims

### 7.2 Out of Scope for MVP

- **VLAN segmentation, dedicated firewall** — no internet exposure and one user; the existing router suffices. Deferred, not rejected.
- **Public DNS and ACME certificates** — an internal authority is sufficient for a LAN-only platform with no inbound path.
- **Node-replicated storage (Ceph, Longhorn)** — Nidavellir is the storage answer for v1. Would also consume the headroom NFR-6 protects.
- **Service mesh** — deferred until a Workload requires it.
- **Formal PostgreSQL high-availability targets** — no RTO or RPO is committed. Note this is *weaker* than what the architecture actually delivers: running PostgreSQL under a Kubernetes operator brings streaming replication and automatic failover as a property of the chosen mechanism rather than as a requirement. What stays out of scope is *promising* availability numbers and testing against them; a verified restore remains the v1 recovery answer.
- **A backup destination independent of Nidavellir** — deferred to v2 by operator decision. `[NOTE FOR PM]` this is the accepted gap behind FR-62's narrowing, and the consequence is that Nidavellir loss is currently unrecoverable. Highest-value v2 purchase.
- **Multi-cluster or staging Yggdrasil** — `vanaheim` is reserved in the naming registry for this, not built.
- **Automated bare-metal provisioning (PXE, autoinstall)** — deliberately excluded given completeness was chosen over rebuild speed. Hypervisor installation may be manual provided it is fully documented.
- **Remote access of any kind** — no VPN, no inbound path. The operator works from the LAN. `[NOTE FOR PM]` this removes an entire plane from the design; it can be reintroduced later without disturbing anything else, since nothing depends on it.
- **GPU workloads** — the Vega iGPUs are idle capacity, not a v1 requirement.
- **Additional hardware** — beyond the UPS and, optionally, 2.5 GbE adapters.

## 8. Success Metrics

The rebuild standard is completeness, not speed. Metrics are stated so that a passing result is evidence rather than opinion.

**Primary**

- **SM-1: Zero undocumented steps.** A Node is destroyed and rebuilt using only the Repository and Break-glass credentials, and the number of steps required but not documented is zero. Measured by Drill. Validates FR-1, FR-3, FR-7, FR-64.
- **SM-2: Convergence holds.** Automation run against a system built by hand from its Runbook reports zero changes, for every Procedure. Validates FR-2, FR-5.
- **SM-3: One Account, everywhere; one action to revoke it.** A single Directory Account authenticates SSH to every host, `kubectl`, the hypervisor UI, Nidavellir, and observability. Disabling that one Account — with no second system edited — removes access from every Relying Party within its stated bound: 15 minutes for OIDC parties, the offline-cache expiry for unreachable hosts, and the hypervisor's declared ticket ceiling. Measured against the per-party table required by FR-35. Validates FR-20, FR-22, FR-32, FR-35, FR-39.
- **SM-4: The application proof.** An application written by the operator, deployed through GitOps, authenticates users against Forseti and makes authorization decisions from Token claims. Validates FR-31, FR-33, FR-42, FR-44.
- **SM-5: Restores are evidence.** Every backed-up class of data has an executed, verified restore on record. Validates FR-47, FR-63.
- **SM-6: Unattended power loss is uneventful.** A Drill with mains removed produces a completed Shutdown Sequence, Nidavellir last, no corruption. Validates FR-56, FR-57, FR-60.

**Secondary**

- **SM-7: Home Directory portability.** Contents written on one host are present on every other. Validates FR-15.
- **SM-8: Trust is silent.** No certificate warning appears anywhere in normal use. Validates FR-28.
- **SM-9: Failures announce themselves.** Every Drill-induced failure produced an alert before it was noticed by hand. Validates FR-51.
- **SM-10: The second application is boring.** Deploying a second SSO-protected Workload requires no new Procedure. Validates FR-33, FR-44, NFR-22.

**Counter-metrics (do not optimize)**

- **SM-C1: Automation coverage at the expense of comprehension.** Automating a Procedure so thoroughly that its Runbook no longer explains the reasoning defeats NFR-2. Counterbalances SM-1 and SM-2.
- **SM-C2: Uptime.** This platform exists to be broken. A long uninterrupted uptime is a sign of insufficient experimentation, not of success. Counterbalances SM-6.
- **SM-C3: Service count.** Running more services is not progress. Depth in the stated stack beats breadth. Counterbalances nothing directly; it guards the purpose.
- **SM-C4: Time to rebuild.** Explicitly not a target. Optimizing it would trade away the documentation completeness SM-1 measures.

## 9. Delivery Plan

Sequenced as a **Walking Skeleton** followed by deepening, per the operator's decision. The skeleton is deliberately thin at every layer — its purpose is to exercise every integration seam while each is cheap to change, because integration seams are where this class of build fails. Nothing in the skeleton is redundant, resilient, or complete; all of that arrives in the deepen phase.

### Phase 0 — Walking Skeleton

| # | Epic | Delivers |
|---|---|---|
| S1 | Repository and Procedure standard | The dual-form contract, the Procedure Index, repository structure, secret handling before a secret store exists |
| S2 | Network, the Cluster, **and Break-glass** | Address plan, dual-homed interfaces, four Nodes clustered, Break-glass Accounts with local homes on every Node, out-of-band management credentials changed, first rebuild Runbook. **Name resolution is provisional here** — hosts files or the household router — because the Directory that serves `asgard.home.arpa` does not exist until S4 |
| S3 | Shared storage, one Share | Nidavellir exporting; a Guest consuming it |
| S4 | Directory, DNS, time, and network login | `mimir`, single instance; `asgard.home.arpa` becomes real; the time authority begins; one Account logging into all four Nodes. Provisional resolution from S2 is retired here |
| S5 | Draupnir, the platform CA | Internal CA with ACME, trust distributed to every Node and Guest. Sequenced before the cluster because it runs **outside** it, and the cluster's own published endpoints need it |
| S6 | Yggdrasil, minimal | A working Kubernetes cluster with storage from Nidavellir, MetalLB, and a gateway terminating TLS from `draupnir` |
| S7 | Forseti and federation | The IdP, federated to the Directory, with one Relying Party working. **Sequenced after S6 because the IdP now runs inside the cluster.** Thin form permitted: an embedded database, migrating to `fafnir` in D5 |
| S8 | Reference application, end to end | **Skeleton gate:** the operator's own code, deployed from the Repository, authenticating via Forseti with claims-based authorization. Thin form permitted: the image may be built and pushed by hand, with automated build arriving in D4 |

**Three ordering constraints are not negotiable**, and two of them were found by review after the first draft had the order wrong.

**Break-glass moves into S2, ahead of S4.** Enabling Directory-backed login before an independent way in exists risks a lockout. The Nodes do carry out-of-band management, which softens this — but that interface ships with vendor default credentials, so changing and escrowing them is part of the same epic rather than a later hardening task.

**Name resolution is provisional until S4.** The original order had S2 delivering `asgard.home.arpa` while the Directory that serves it arrived two epics later. S2 now uses hosts files or the household router and retires them in S4.

**The IdP follows the cluster, not the other way round.** The original order put the IdP in S5, before Yggdrasil existed — an artefact of when it was to be a Guest. Once placement moved it inside the cluster it necessarily follows S6. The platform CA moves to S5 in its place, which is correct on its own merits: it runs outside the cluster, and the cluster's published endpoints need it.

The thin forms named above are what make the skeleton genuinely thin rather than a full build in disguise. Each names the deepen-phase epic that replaces it, so no thin form becomes permanent by accident.

`[ASSUMPTION: the Walking Skeleton can reach S8 without any deepen-phase capability. Partly falsified in review — the IdP needed a cluster that did not exist and S2 promised a domain before its resolver — and resolved by reordering plus explicit thin forms rather than by moving the phase boundary.]`

Reaching S8 proves every seam in the design: hypervisor to storage, storage to Kubernetes, Directory to IdP, IdP to Kubernetes, IdP to application, Repository to running Workload. Anything wrong with the architecture surfaces here rather than in month four.

### Phase 1 — Deepen

| # | Epic | Delivers |
|---|---|---|
| D1 | Storage depth | Home Directories everywhere, on-demand mounting, dynamic Persistent Volumes, Off-NFS Store for PostgreSQL |
| D2 | Identity depth | Directory replica, credential caching, Break-glass with local homes on every host, Group-driven authorization |
| D3 | Yggdrasil depth | Three Control Plane Guests spread across Nodes, OIDC `kubectl`, ingress with Draupnir TLS |
| D4 | Delivery depth | Image build from source, internal registry, rollback |
| D5 | Stateful services | `fafnir` on the Off-NFS Store, `ratatoskr`, provisioning Procedure |
| D6 | Observability | `huginn`, `muninn`, `gjallarhorn`; SSO-protected dashboards; alerting |
| D7 | Secrets management | `andvari`, runtime secret delivery, commit-time plaintext prevention |
| D8 | Power continuity | UPS, NUT topology, ordered Shutdown Sequence, **proven by Drill** |
| D9 | Backup and recovery | Automated backup, off-source storage, **verified restore per data class** |
| D10 | SSO breadth | Hypervisor UI, Nidavellir, observability, forward-auth for services without native OIDC |
| D11 | Destructive rebuild Drill | **Final gate:** SM-1 proven — a Node destroyed and restored with zero undocumented steps |

D11 validates the documentation; S8 validates the architecture. They are the two epics that cannot be skipped.

## 10. Risks

| Risk | Impact | Response |
|---|---|---|
| Nidavellir is a single point of failure under Home Directories, Persistent Volumes **and backups** | **Total, unrecoverable data loss** if Nidavellir fails — not merely disruption | **Knowingly accepted for v1.** FR-16 bounds the blast radius of an *outage* to degradation, but there is no mitigation for *loss*: no second bulk storage device exists and its purchase is deferred to v2. FR-62 is narrowed to Node-loss protection accordingly. This is the largest accepted risk in the design and the highest-value v2 purchase. |
| Directory outage disables all SSO and therefore all Relying Parties | Total loss of service access | FR-25 replica; FR-24 Break-glass preserves administrative access throughout. |
| No remote access at all | Every repair requires physical presence | Accepted deliberately. Removing the remote plane also removes the circular dependency in which an identity-dependent VPN would make IdP failure unrecoverable from outside. |
| Documentation drift as the platform outlives enthusiasm | The stated deliverable silently decays | FR-2 convergence test makes drift detectable; NFR-4 versions Procedures with systems. |
| Capacity exhaustion from observability retention and JVM sizing | Headroom disappears; experimentation stops | NFR-6 floor, NFR-8 bounded retention, NFR-9 explicit limits. |
| 1 GbE nodes bottleneck all storage traffic | Slow Workloads, slow rebuilds | Accepted for v1. FR-65 puts Nidavellir on 2.5 GbE so the shared side is not the constraint; per-Node adapters are a cheap remedy if it becomes real. |
| Out-of-band management ships with vendor default credentials | A credentialed remote power, boot, firmware and console interface reachable by anyone on the flat LAN | **Reversed finding.** The Nodes do have out-of-band management, which improves lockout recovery — but it is an unmanaged attack surface until claimed. Credentials are changed and escrowed in S2, and the interface's enabled/disabled state is declared rather than inherited. |
| A backup that has never been restored | False confidence, discovered at the worst time | NFR-18: configured-but-untested is treated as not present. FR-63 requires executed restores. |
| Account revocation is neither instant nor uniform | A disabled Account retains access longer than expected | FR-35's per-party table makes each real bound explicit; FR-22 bounds the offline credential cache. The residual — the hypervisor's self-issued ticket — is accepted knowingly rather than assumed away. |
| Shutdown ordering rests on tuned delay, not coordination | Storage withdrawn beneath a Guest still shutting down | FR-57 requires the margin be measured and recorded, not estimated; FR-60's Drill proves it under real load and repeats after battery replacement. |
| Directory CA renewal role is a single unrecoverable point | The Directory's own certificates expire silently, well after the fault | **Resolved (§11.6).** The Directory's CA issues only its own internal certificates; the platform CA is separate and runs outside the cluster. Blast radius is contained to the Directory. Its renewal-role location, health check and relocation Procedure are named in the Repository. |

## 11. Resolved by Architecture

All eight open questions were closed during the architecture phase. Resolutions are binding; the reasoning lives in the architecture spine's decision log.

| # | Question | Resolution | Governed by |
| --- | --- | --- | --- |
| 1 | Directory product | **FreeIPA.** Delivers FR-21, FR-25, §4.6 PKI and §4.3 DNS as one system. LLDAP eliminated on requirements — no replication, so FR-25 is unmeetable. Samba AD DC rejected for having no integrated CA. | AD-2, AD-17 |
| 2 | Off-NFS Store mechanism | **Neither original option.** PostgreSQL runs as **CloudNativePG in Yggdrasil on local-path NVMe** — same NVMe speed as the VM option, stays in the Kubernetes model, and survives Node loss via operator-managed streaming replication, which the VM did not. iSCSI rejected: Nidavellir is HDD-only, so it would place database random I/O on spinning disks. | AD-8, AD-18 |
| 3 | Nidavellir RAID level | **SHR-2** (~28 TB, dual-drive tolerance). With no independent backup, array redundancy is the only protection against total loss, and 14 TB rebuild windows run 26–40 hours with material read-error probability across the surviving set. | AD-8 |
| 4 | Yggdrasil ingress | **Replaced.** Bundled ingress and load balancer are disabled; **MetalLB (L2) + Envoy Gateway on Gateway API**. The originally-chosen ingress-nginx was found end-of-life as of 2026-03-24 — read-only repository, no CVE patches — during architecture version verification. Gateway API is the only north-south routing model; Ingress resources are not used. | AD-14 |
| 5 | UPS compatibility gate | **Still a build-time gate, not a design question.** The SMT1500C must appear on Synology's supported list before the design depends on DSM as NUT Server. | AD-11 |
| 6 | Directory CA role placement | **Split.** The Directory's integrated CA issues only the Directory's own internal certificates. `draupnir` (step-ca) is the platform CA for everything else, and runs **outside Yggdrasil** because hosts and the hypervisor depend on it. ACME is the only issuance protocol. The renewal role's location, health check and relocation Procedure are named in the Repository. | AD-5, AD-18 |
| 7 | Independent backup target | **Deferred to v2, with an interim.** No second bulk device exists. The Repository is already off-platform on GitHub; Directory data, PostgreSQL dumps, the platform CA root key and Break-glass credentials go encrypted to the owned SanDisk 1 TB. This does not close FR-62 — a dead Nidavellir still costs bulk volumes — but identity, CA and databases survive. | FR-62 notes |
| 8 | Alert delivery path | **Pushover, in three independent tiers:** platform alerts from Yggdrasil; infrastructure alerts (UPS, NAS) direct from the appliances, bypassing Yggdrasil; and an external dead-man's-switch heartbeat. The third is **load-bearing rather than optional** — see the amendment to FR-58. | AD-12 |

### Remaining build-time gates

1. **UPS on Synology's supported-device list** — verify before purchase.
2. **DSM 7.3 or later** — required for WD Red Pro support following Synology's compatibility-policy reversal.
3. **ISP equipment: combined gateway or separate modem and router** — determines the outlet count.
4. **USB 2.5 GbE adapter interface naming** — must be deterministic across reboots; the address plan depends on it.
5. **Energy Efficient Ethernet on the membership switch** — disable if exposed, otherwise monitor cluster-membership latency after cutover.

## 12. Assumptions Index

- **§4.3 / FR-14** — The household router will continue serving DHCP for non-Asgard devices, and Asgard can coexist without assuming control of it.
- **§4.4 / FR-17** — Nidavellir's storage is sufficient for both Home Directories and all Persistent Volumes for the foreseeable term; no tiering is needed in v1.
- **§4.7 / FR-32** — ~~Unverified~~ **Resolved during review:** all three do support OIDC against a self-hosted provider, with per-product caveats carried into FR-35's per-party bounds. The hypervisor's inability to honour a 15-minute ceiling is the material one.
- **§4.13 / FR-56** — Measured battery runtime at the real ~320 W load will exceed the Shutdown Sequence duration with margin. The Drill measures rather than assumes this.
- **§5.2 / NFR-6** — **Restated during review.** The prior single-sided 20 GB metric was gameable by relocating a service into a Worker Guest, and the model behind it omitted Redis, the registry, CI runners, the secret store, the GitOps controller, forward-auth, and alerting. Now bounded from both sides; the revised model is in the brief addendum.
- **§9** — **Partly falsified during review.** The IdP required a cluster that did not yet exist, and S2 promised a domain its resolver had not yet delivered; both were fixed by reordering. Thin forms cover the rest. Resolved by naming explicit thin forms with the deepen-phase epic that replaces each, rather than by moving the phase boundary.

### Deferred-item callouts

`[NOTE FOR PM]` markers placed in the document, surfaced here so deferrals stay visible rather than dissolving into the scope list:

- **§7.2 / Formal PostgreSQL high-availability targets** — no RTO/RPO committed, though the chosen mechanism delivers replication and failover regardless. Revisit if a Workload becomes something the operator would genuinely miss.
- **§7.2 / Independent backup target** — deferred to v2 by operator decision; the consequence is that Nidavellir loss is unrecoverable in v1. See FR-62.
- **§7.2 / Remote access** — cut entirely rather than deferred, but recorded because it removes a whole plane from the design. Reintroducible later without disturbing anything else, since no requirement depends on it.

## 13. Amendment Record

Changes made to this PRD after it was finalised, arising from the architecture phase. Recorded rather than silently applied, so the reasoning behind each reversal survives.

| § | Was | Now | Why |
| --- | --- | --- | --- |
| §11 | Eight open questions | Eight resolutions plus five build-time gates | All closed in architecture; see the spine's decision log |
| §11 Q2, §4.10, FR-18 | PostgreSQL as a Guest on local NVMe, or an iSCSI LUN | **CloudNativePG in Yggdrasil on local-path NVMe** | Operator directed infrastructure services into Kubernetes where sound. This is strictly better than the Guest option — same NVMe speed, and it survives Node loss through operator-managed replication, which the single Guest did not. iSCSI stayed rejected once Nidavellir was confirmed HDD-only. |
| §11 Q4, FR-41 | Retain or replace the bundled ingress | **MetalLB + Envoy Gateway on Gateway API**; Ingress resources not used | The originally-selected ingress-nginx reached end-of-life 2026-03-24 — read-only repository, no CVE patches, migration recommended by the Kubernetes Steering and Security Response Committees. Found during architecture version verification. The transferability argument that justified it had inverted. |
| §4.3, FR-58 | Access point not deployed; data switch uplinks by cable to the household router; router on a battery-backed outlet | **Access point redeployed in client-bridge mode as the sole uplink**; router cannot be battery-backed | The rack has no wired path to the router — opposite side of the house, no spare ports, no coaxial cabling. Only outbound traffic crosses the bridge, so the bandwidth cost lands where it does not matter. But the router is beyond the UPS's reach, which promotes FR-51's dead-man's-switch tier from supplementary to load-bearing. |
| FR-17 | One storage class implied | **Two classes**: NFS default (ReadWriteMany) and iSCSI (ReadWriteOnce) | Block semantics wanted for some Workloads. Both land on the same spinning disks — the second class buys semantics, not speed. |
| FR-18 | "not on a Share" | "not on any NAS-backed medium" | Nidavellir is HDD-only, so the exclusion is about the storage medium rather than about NFS specifically. |
| §6, §7.2, §12 | PostgreSQL cited as an example of a service living outside the cluster; PostgreSQL HA listed as out of scope | PostgreSQL cited as an example of a service placed *inside*; the exclusion narrowed to formal availability *targets* | Consequential to the CloudNativePG move. The operator-managed mechanism supplies replication and failover as a property, so a blanket "no HA" exclusion understated what is actually being built. What remains out of scope is committing to RTO/RPO numbers. |

Decisions this PRD made that architecture **upheld unchanged**: no inbound path; Break-glass independence including the local-home-outside-NFS requirement; bounded rather than instant revocation; shutdown ordering by measured margin; the dual-form Procedure contract and its convergence test; the Norse naming registry; and FR-62's narrowing to Node-loss protection.
