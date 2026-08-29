---
title: Coverage Review — Architecture Spine vs PRD
type: architecture-review
target: ARCHITECTURE-SPINE.md
against: _bmad-output/planning-artifacts/prds/prd-homelab-2026-08-28/prd.md
created: 2026-08-28
---

# Coverage Review — Project Asgard Spine vs PRD

**Verdict.** The spine is structurally strong where it engages — AD-1, AD-3, AD-5, AD-7, AD-9, AD-10, AD-11, AD-15 and AD-18 are real, load-bearing invariants that would keep a build coherent. But it engages unevenly. Three whole PRD feature areas (backup and recovery, SSO breadth to administrative interfaces, and observability collection) reach the Capability Map with rows that name no governing rule, and one design decision the spine made — moving `forseti` and `fafnir` inside Yggdrasil under AD-18 — silently breaks NFR-6(b), the one requirement the PRD deliberately made two-sided precisely to catch that move. The spine is not ready to build D9, D10 or D6 from, and S5 cannot be sequenced as the PRD orders it.

**Headline counts:** 11 FRs and 8 NFRs with nothing in the spine governing them; 2 of the PRD's 8 open questions still unresolved and 3 more answered only in the memlog; 18 PRD lines now stale.

---

## Check 1 — FR Coverage

Legend: **G** = governed by a named AD, convention, stack entry, or map row that actually constrains how it is built. **P** = partially governed; some testable consequences have no rule. **U** = nothing in the spine governs it.

| FR | Requirement | Status | Governing element (or gap) |
|---|---|---|---|
| FR-1 | Procedure Index, dual form | G | AD-3; repo shape `PROCEDURE-INDEX.md` |
| FR-2 | Manual execution converges | G | AD-3; convention *Automation* |
| FR-3 | Defects resolved at discovery | G | AD-3 |
| FR-4 | Repository sole source of truth | G | AD-4 |
| FR-5 | Procedures declare verification | P | Convention *Runbook shape* covers the stated-output half; nothing states verification is **identical** whether Runbook or Automation ran |
| FR-6 | Four Nodes, one Cluster | P | L1 layer row + map row only. No invariant on cluster formation, quorum with an even node count, or fencing |
| FR-7 | Node rebuilt from Repository | G | AD-4, AD-17 (per-family host-build Runbook), AD-3 |
| FR-8 | Guests provisioned declaratively | G | Convention *Declarative provisioning* (OpenTofu/Ansible boundary at first boot) |
| FR-9 | Snapshot and rollback | **U** | No AD, convention, stack entry or map row mentions snapshots. Map row for FR-6–10 points at AD-4/AD-9/AD-17, none of which touch this |
| FR-10 | Cluster manageable, Directory down | G | AD-9 |
| FR-11 | Everything reachable by name | G | AD-16, AD-13, convention *Host and service naming* |
| FR-12 | Deterministic recorded addressing | G | AD-7, convention *Addressing* |
| FR-13 | Resolution survives one failure | P | AD-13 is cited in the map but governs exposure, not resolver redundancy. Only `mimir` Guest (×2) in the placement table implies it; open question 6 (DNS role on the replica) is unresolved |
| FR-65 | Dual-homed, membership separated | G | AD-7 |
| FR-14 | Household devices unaffected | P | Convention *Addressing* ("outside the household DHCP pool") covers non-takeover; nothing governs DNS coexistence |
| FR-15 | Identical Home Directories | P | AD-8 (NFS default class for home directories). First-login home provisioning is not governed |
| FR-16 | Storage loss degrades, not hangs | **U** | AD-8 governs *placement*, not mount semantics. Nothing anywhere specifies soft/intr mounts or an automounter, and "no reboot on Share return" has no rule |
| FR-17 | PVs on demand | G | AD-8; stack `csi-driver-nfs`, `synology-csi` |
| FR-18 | PostgreSQL off NFS | G | AD-8 ("local NVMe for … database data") |
| FR-19 | Storage capacity and health visible | P | AD-12 governs the NAS alert path. Nothing governs utilisation/SMART collection or the alert threshold |
| FR-20 | One Account, every host | G | AD-2, AD-6 |
| FR-21 | Group-driven authorization | P | AD-2 puts Groups in the Directory but no rule states host access and privilege escalation are defined centrally. FreeIPA HBAC + central sudo is a memlog decision that never reached the spine |
| FR-22 | Bounded revocation window | G | AD-10 (explicit offline cache max age) |
| FR-23 | Offline auth during outage | P | AD-10 establishes the cache and its bound; "groups and sudo resolve from cache" is ungoverned |
| FR-24 | Break-glass on every host | G | AD-9 |
| FR-25 | Directory survives one instance loss | P | Only `mimir` Guest (×2) in the placement table. No invariant on multi-master replication, on either instance serving authentication, or on patching one without an outage |
| FR-26 | Accounts defined in Repository | G | AD-4, AD-15 |
| FR-27 | One authority issues internal certs | G | AD-5 |
| FR-28 | Trust distributed automatically | **U** | AD-5 governs *issuance and renewal* over ACME and escrows the root key (AD-9). Nothing governs installing the Draupnir trust anchor on every Node and Guest — the requirement SM-8 measures |
| FR-29 | Certificates renew unattended | G | AD-5 (ACME only, manual installation prohibited) |
| FR-30 | IdP federates to Directory | G | AD-2 |
| FR-31 | Groups appear as claims | P | AD-2 + identity flow diagram. The claim name is not fixed as a convention, so "documented, stable claim" has no anchor |
| FR-32 | Admin interfaces authenticate via IdP | **U** | Map row cites AD-2/AD-10/AD-14; none governs SSO breadth. Nothing in the spine states that the hypervisor UI, Nidavellir and observability are Relying Parties. This is SM-3's core and epic D10 |
| FR-33 | Workloads registered as RPs | P | AD-4 generically. No rule or stack entry for declarative Keycloak client registration |
| FR-34 | Non-OIDC services fronted | P | AD-14 covers binding and bypass honestly, but no forward-auth component appears in the stack or placement table |
| FR-35 | Disablement propagates, bounded | G | AD-2 (account-lock mapping), AD-10 (per-party table) |
| FR-36 | Authentication events recorded | **U** | Convention *Logging* covers shipping logs generally. Nothing requires the IdP to emit authentication events, nor distinguishes failed authn from failed authz |
| FR-37 | Survives one Control Plane loss | P | Three Norns appear as a diagram label; no invariant on quorum |
| FR-38 | Control Planes spread across Nodes | **U** | "one per Node" is a mermaid node caption in the Structural Seed, not a rule. No anti-affinity or placement-spread AD exists, so nothing prevents OpenTofu landing two Norns on one Node |
| FR-39 | `kubectl` via IdP | G | AD-1 (static credential makes OIDC an enhancement), AD-9 (escrow) |
| FR-40 | Yggdrasil rebuildable | P | AD-4 + convention *Workload delivery*. "PV data survives cluster rebuild" needs a reclaim-policy rule that does not exist |
| FR-41 | Workloads reachable by name over TLS | G | AD-14, AD-5 |
| FR-42 | Reconciliation from Repository | G | Convention *Workload delivery*; stack Argo CD |
| FR-43 | Images built and stored in Asgard | G | Convention *Images*; placement table `sindri`, `brokkr`; AD-18 registry caveat |
| FR-44 | Documented path to production | G | AD-3 |
| FR-45 | Deployments roll back | P | Implied by AD-4 + *Workload delivery*; no rule names how a previous known-good state is identified |
| FR-46 | Workloads obtain a database | P | AD-8 is cited but governs placement. No rule for declarative database/role provisioning or credential delivery |
| FR-47 | PostgreSQL backed up and restorable | **U** | Map row says "Native per system" and names no mechanism. CNPG/barman is memlog-only. No schedule, no off-host rule, no restore-verification rule |
| FR-48 | Redis available to Workloads | **U** | `ratatoskr` appears in the placement table and as an NFR-11 TLS exclusion. Nothing governs authentication or the persistence choice the PRD requires be deliberate |
| FR-49 | Metrics collected and retained | P | Convention *Logging* covers logs and cites NFR-8. Metrics retention and auto-discovery of new Guests/Workloads are ungoverned |
| FR-50 | Logs centralized and searchable | G | Convention *Logging* |
| FR-51 | Failures generate alerts | G | AD-12 |
| FR-52 | Dashboards authenticate via IdP | **U** | Same gap as FR-32; nothing makes Grafana a Relying Party or maps Groups to view/edit |
| FR-53 | No plaintext secret committed | G | AD-15; stack SOPS + age |
| FR-54 | Runtime secret delivery | P | AD-15 states the rule; no component delivers it — External Secrets Operator and the `andvari` product are memlog-only |
| FR-55 | Break-glass held outside Asgard | G | AD-9 |
| FR-56 | Clean shutdown on power loss | G | AD-11 |
| FR-57 | Order by tuned delay, proven margin | G | AD-11 |
| FR-58 | All participants stay powered | **Contradicted** | AD-11 battery-backs Nodes, Nidavellir and both switches and **omits the household router**; AD-12 states the router is beyond the UPS's reach. See Check 5 |
| FR-59 | Power events visible and alerted | G | AD-12, AD-11 |
| FR-60 | Shutdown proven by Drill | G | AD-11 |
| FR-61 | Platform state backed up automatically | **U** | Map row "Native per system → AD-4, AD-8". Neither AD governs backup. No schedule, no coverage enumeration, no failure alerting rule |
| FR-62 | Backups survive Node loss | P | Deferred section states the Nidavellir gap and alludes to "the encrypted critical subset held offline", but never names the device, contents, schedule or integrity check |
| FR-63 | Restores verified, not assumed | **U** | Nothing in the spine requires an executed restore per data class. This is SM-5 and the D9 gate |
| FR-64 | Rebuild from Repository and backups | P | AD-3/AD-4 govern the Procedure's *form*; no rule requires a stated rebuild order or an explicit statement of what the Procedure does not cover |

**Totals: 34 G · 20 P · 11 U** (FR-58 counted separately as contradicted).

### Findings

- **[critical]** Backup and recovery has no governing invariant at all — FR-61, FR-63 uncovered; FR-47, FR-62, FR-64 partial. The Capability Map's row reads "Backup and recovery (FR-61–64) | Native per system | AD-4, AD-8". "Native per system" names no mechanism, and neither AD-4 nor AD-8 constrains backup. The memlog carries a full decision (Synology Btrfs snapshots + Hyper Backup for NFS data, Proxmox `vzdump` for Guests, CloudNativePG barman for PostgreSQL, all landing on Nidavellir, Velero deliberately excluded) that never reached the spine. Epic D9 is unbuildable from this document. *Fix:* add an AD — "Backup uses each system's native mechanism; no new abstraction layer" — carrying the four named mechanisms, the Nidavellir landing zone, the enumerated-coverage rule (anything not backed up is a listed exclusion), and the invariant that a restore Procedure is not complete until executed and verified per data class.
- **[critical]** SSO breadth (FR-32, FR-52) is uncovered — the requirement the platform exists to exercise. The PRD's §12 records the OIDC-support assumption as resolved with per-product caveats, and SM-3 measures one Account across the hypervisor UI, Nidavellir, observability and `kubectl`. The spine names none of these as Relying Parties. AD-10 records the hypervisor's ticket ceiling but never establishes that the hypervisor is fronted by the IdP in the first place. Epic D10 has no invariants. *Fix:* add an AD enumerating the Relying Party set, stating that a service with native OIDC is registered directly and one without is fronted per AD-14, and add a forward-auth component to the stack and placement table.
- **[high]** FR-9 and NFR-23 (snapshot before change) are uncovered. Fearless experimentation is a stated purpose (UJ-6, §4.2) and the PRD makes snapshots first-class, yet the word does not appear in the spine. *Fix:* add a convention row — snapshot-before-change is available for every Guest, taken by a named Procedure, with a stated retention/cleanup rule so snapshots do not silently consume the local NVMe that also holds CNPG data.
- **[high]** FR-16 (storage unavailability degrades rather than hangs) is uncovered. AD-8 decides *where* volumes live and says nothing about *how* they are mounted; hard NFS mounts would put processes in uninterruptible sleep and violate the requirement while fully satisfying AD-8. AD-9 handles the break-glass half only. *Fix:* extend AD-8 or add a convention row fixing mount semantics (soft/`intr` or automounted, with the recovery-without-reboot property stated) and note that this is what makes AD-9's local break-glass home sufficient rather than merely necessary.
- **[high]** FR-38 (no two Control Plane Guests share a Node) survives only as a mermaid caption. "urd · verdandi · skuld — control plane, one per Node" is diagram text, not a rule; NFR-16 has the same problem. There is no anti-affinity invariant, so nothing in the governing layer stops OpenTofu placing two Norns on `odin`. *Fix:* add an AD — "single-Node loss removes at most one instance of any replicated component" — binding FR-25, FR-37, FR-38, NFR-7, NFR-16, and covering the Directory pair, the three Norns, and CNPG replicas together.
- **[medium]** FR-28 (trust anchor distribution) is uncovered. AD-5 governs issuance and renewal thoroughly and stops at the point where a certificate has to be *believed*. SM-8 ("no certificate warning appears anywhere in normal use") has nothing behind it. *Fix:* extend AD-5's rule with anchor distribution by Automation to every Node and Guest, and name the OS-family difference AD-17 implies.
- **[medium]** FR-21's central authorization mechanism is memlog-only. The memlog resolves it (FreeIPA HBAC plus central sudo, and that combination is a stated reason FreeIPA won). AD-2 records only that Groups live in the Directory. *Fix:* add the HBAC/central-sudo rule to AD-2 so per-host `sudoers` editing is prohibited rather than merely discouraged.
- **[medium]** FR-25's replication properties are unstated. The placement table's "(×2)" is the only trace. The PRD requires bidirectional change propagation, either instance serving the IdP, and patching one without interrupting authentication — none is an invariant. Compounded by open question 6 remaining unresolved. *Fix:* fold into the replicated-component AD above and state the FreeIPA replication agreement plus which roles the replica must be built with.
- **[medium]** FR-36 / NFR-15 (authentication event recording) uncovered. The *Logging* convention ships logs; nothing makes the IdP emit authentication events or requires authn/authz failures be distinguishable. *Fix:* add a bullet to AD-12 or the Logging convention naming the IdP event stream as a required source with that distinction.
- **[medium]** FR-48 (Redis) uncovered. `ratatoskr` appears twice as a name and never as a constraint, despite the PRD requiring authentication and a *deliberate, documented* persistence choice. *Fix:* one convention row: Redis requires authentication; persistence mode is stated in the Repository with its rationale; dependent Workloads degrade without PostgreSQL data loss.
- **[medium]** FR-54's delivery mechanism is memlog-only. AD-15 states the rule; the stack lists SOPS + age (the FR-53 half) but not External Secrets Operator or OpenBao, and `andvari` in the placement table is a name with no product. Epic D7 is half-specified. *Fix:* add both to the Stack table with the memlog's BSL/OpenBao caveat.
- **[medium]** FR-6 has no cluster-formation invariant. The spine asserts a four-Node Proxmox cluster in the layer table and never governs quorum behaviour, which matters with an even node count and matters more given AD-7 puts membership on a physically separate switch with no uplink. *Fix:* state the quorum expectation and the membership-switch failure mode (what happens to the Cluster if the membership switch dies) as part of AD-7.
- **[low]** FR-5's identical-verification property is unstated — the convention covers verification existing, not being the same for both forms. *Fix:* one clause in AD-3.
- **[low]** FR-31's claim name is not fixed. "Documented, stable claim" needs an anchor if Workloads are to be written against it. *Fix:* name the claim in the Consistency Conventions table.
- **[low]** FR-40's PV-survives-rebuild property needs a reclaim-policy rule in AD-8. *Fix:* state the reclaim policy for each storage class.

---

## Check 2 — NFR Coverage

| NFR | Status | Governing element (or gap) |
|---|---|---|
| NFR-1 six-month executability | G | AD-3, convention *Runbook shape* |
| NFR-2 reasoning not only commands | G | Convention *Runbook shape* |
| NFR-3 idempotent without exception | G | Convention *Automation* |
| NFR-4 versioned with their systems | **U** | Nothing requires a system change and its Procedure change to land together. AD-3 binds NFR-1–5 but its rule never addresses this |
| NFR-5 Automation authoritative for *what* | P | AD-3 makes disagreement a defect; the precedence rule itself (Automation for what, Runbook for why) is absent |
| NFR-6 two-sided capacity bound | **U + violated** | No AD, convention or table governs memory. See the capacity analysis below |
| NFR-7 one-Node loss leaves capacity | **U** | Nothing governs. AD-18 decides placement on layering grounds only and never consults capacity |
| NFR-8 bounded observability retention | P | Cited in the *Logging* convention for logs; metrics retention — the addendum's named largest consumer — is ungoverned |
| NFR-9 explicit Guest memory limits | **U** | Nothing requires declared limits. The addendum names the Keycloak JVM heap as one of two components that will eat the margin, and `forseti` is now a Workload where an uncapped heap is even easier to miss |
| NFR-10 no plaintext in Repository | G | AD-15 |
| NFR-11 TLS everywhere, named exclusions | P | AD-5 + convention *Certificates* govern issuance. The "no endpoint over plaintext HTTP" half and the four named exclusions are not restated as an invariant |
| NFR-12 no direct remote root | G | AD-9 |
| NFR-13 break-glass unique per host | G | AD-9 |
| NFR-14 no inbound path | G | AD-13 |
| NFR-15 authn events recorded and retained | **U** | Same gap as FR-36 |
| NFR-16 one-Node tolerance for identity/storage/control | P | AD-7 is cited but governs traffic separation, not placement spread. The property lives only in diagram captions |
| NFR-17 no unattended corruption | P | AD-11 covers the power case thoroughly; the general integrity-over-availability principle is not an invariant |
| NFR-18 recovery proven by execution | **U** | Nothing. This is the rule that would make FR-63 and SM-5 enforceable |
| NFR-19 detected and alerted, not discovered | G | AD-12 |
| NFR-20 state determinable without host login | **U** | Nothing governs. AD-4 makes the Repository authoritative for *desired* state; nothing covers observed state |
| NFR-21 routine ops need no break-glass | P | AD-9 frames break-glass as the emergency path; the prohibition on routine use is not stated |
| NFR-22 additions follow existing Procedures | P | AD-3's Index and AD-18's "adding a service means adding a row" get close; the no-new-Procedure property is not stated |
| NFR-23 snapshot-before-change everywhere | **U** | Same gap as FR-9 |

**Totals: 8 G · 7 P · 8 U.**

### NFR-6 capacity check — the spine does not fit inside it

The PRD made NFR-6 two-sided specifically so it "cannot be satisfied by relocating a service" (§5.2, line 864). AD-18 relocates two services. Adding up what the spine actually puts where, against the addendum's capacity model:

**Side (a) — committed Guest memory ≤ 90 GB.** The addendum budgets `forseti` at 4 GB and `fafnir` at 8 GB as Tier-1 Guests. AD-18 places both inside Yggdrasil, so they leave Tier 1. The spine also adds `draupnir` as an L2 Guest, which the capacity model never budgeted.

| Guest | Addendum | Under the spine |
|---|---:|---:|
| Proxmox overhead (4 × ~2 GB) | 8 | 8 |
| `mimir` + replica | 8 | 8 |
| `forseti` | 4 | **0 — moved into Yggdrasil** |
| `fafnir` | 8 | **0 — moved into Yggdrasil** |
| `draupnir` (step-ca) | **not budgeted** | ~2 |
| Control plane, 3 × Norn | 12 | 12 |
| Workers, 3 × Valkyrie | 48 | 48 |
| **Committed** | **88** | **~78** |

Side (a) passes with 12 GB of headroom against the 90 GB ceiling, and 50 GB unallocated of 128 GB physical.

**Side (b) — ≥ 15 GB schedulable within Yggdrasil. This fails.** The addendum's Tier-2 platform subtotal is ~26.5 GB inside the 48 GB worker allocation, leaving ~21 GB schedulable. The spine adds `forseti` (4 GB) and `fafnir` (8 GB) to that subtotal, and its Tier-2 line item "Ingress and forward-auth, 1 GB" now has to cover Envoy Gateway's control plane and proxies, MetalLB, cert-manager and two CSI drivers — components the model never itemised.

| | RAM |
|---|---:|
| Addendum Tier-2 platform subtotal | 26.5 |
| `forseti` (Keycloak, JVM) — relocated | +4.0 |
| `fafnir` (CloudNativePG) — relocated | +8.0 |
| **Platform subtotal under the spine** | **38.5** |
| Worker allocation | 48.0 |
| **Schedulable for the operator's own Workloads** | **~9.5 GB** |
| NFR-6(b) floor | 15.0 |

~9.5 GB against a 15 GB floor — and that is before the ungoverned Envoy Gateway / MetalLB / cert-manager / CSI delta, which pushes it toward 8 GB. The relocations are individually well-reasoned (the memlog's CNPG rationale is genuinely stronger than the VM proposal), but their combined capacity consequence was never carried back into the model.

- **[critical]** AD-18's placement decisions break NFR-6(b): ~9.5 GB schedulable against a 15 GB floor. Moving `forseti` and `fafnir` into Yggdrasil is exactly the relocation NFR-6 was rewritten to catch, and the spine performs it without recomputing. The addendum's capacity model (Tier-1 rows for `forseti` and `fafnir`, and the "~21 GB schedulable" conclusion) is now stale, so the model would report a pass. *Fix:* the headroom exists — side (a) has 12 GB of slack. Raise the Valkyries from 16 GB to 20 GB each (workers 60 GB, committed ~90 GB, schedulable ~21.5 GB), or cut Harbor for a plain OCI registry as the memlog already flags as the first optional cut. Then add an AD binding NFR-6/7/9 that makes recomputing both sides a mandatory step of any AD-18 placement change, and update the addendum's §2 tables.
- **[high]** NFR-7 and NFR-9 are uncovered, and both are what make the NFR-6 ceiling meaningful. Nothing requires Guests to declare explicit memory limits, and nothing checks that three Nodes can carry identity, storage and cluster control. *Fix:* fold into the capacity AD above — explicit limits on every Guest and every platform Workload, with the JVM heap cap called out by name.
- **[high]** NFR-18 is uncovered — "configured-but-untested is treated as not present". This is the rule the PRD's risk register leans on for the never-restored-backup risk, and it is the enforcement behind FR-63 and SM-5. *Fix:* state it in the backup AD and in AD-3 (a recovery Procedure's Index entry is incomplete until a Drill record exists alongside it).
- **[medium]** NFR-1–5: only NFR-1, 2 and 3 are genuinely governed. NFR-4 (Procedure versioned with its system, landing in the same change) is absent despite being the specific mechanism against the documentation-drift risk in §10, and NFR-5's precedence rule is absent. AD-3 declares it binds NFR-1–5 without covering them. *Fix:* two clauses in AD-3 — a system change and its Procedure change land in the same commit; where the two forms disagree the Automation is authoritative for *what* and the Runbook for *why*.
- **[medium]** NFR-20–23 (operability) are the weakest-governed block: 20 and 23 uncovered, 21 and 22 partial. NFR-20 is notable because the spine already has the pieces (AD-4 for desired state, AD-12 and the Logging convention for observed) and never joins them into the property the operator actually needs. *Fix:* one convention row stating that current platform state is answerable from the Repository plus the observability system, which makes host login an escalation rather than a routine step, and gives NFR-21 its teeth.
- **[low]** NFR-8's metrics half is ungoverned while its logs half is fine, even though the addendum names Prometheus retention as the single most likely cause of a slow capacity squeeze. *Fix:* extend the Logging convention to metrics with a stated window.
- **[low]** NFR-11's plaintext-HTTP prohibition and its four named exclusions (SSH, NFS, Redis, membership traffic) are not restated in the spine, so the exclusion list — which the PRD went to some trouble to bound honestly — has no home in the governing document. *Fix:* add the exclusion list to AD-5's rule.

---

## Check 3 — The PRD's 8 Open Questions

| # | Question | Status |
|---|---|---|
| 1 | Directory product | **Resolved in the spine** |
| 2 | Off-NFS Store mechanism | **Resolved in the spine** (by a third option) |
| 3 | Nidavellir RAID level | **Memlog only** — spine carries the answer as a diagram label |
| 4 | Yggdrasil ingress | **Resolved in the spine**, with a build-critical step memlog-only |
| 5 | UPS / DSM compatibility gate | **Still open** |
| 6 | Directory CA renewal-role placement | **Still open** — delegated, not answered |
| 7 | Independent backup target | **Memlog only** for the interim mitigation |
| 8 | Alert delivery path | **Memlog only** for the channel |

**1. Directory product — resolved.** FreeIPA 4.12.5 on Rocky Linux 10 in the Stack, with AD-17 carrying the mixed-OS consequence and AD-2/AD-6 carrying the role. Fully in the spine.

**2. Off-NFS Store mechanism — resolved.** AD-8 places database data on local NVMe; the Stack names CloudNativePG 1.29.1. Answered with a third option neither PRD alternative listed: in-cluster CNPG on local-path NVMe PVs rather than a Guest or an iSCSI LUN. The rejection of iSCSI on the HDD-only grounds is in AD-8's closing sentence, which is good. The PRD's OQ2 text is now stale (Check 5).

**3. Nidavellir RAID level — memlog only in substance.** "DS925+ SHR-2" appears as a mermaid node caption in the topology diagram. That is a label, not a decision: nothing states the ~28 TB usable figure, the two-drive tolerance, or the reasoning (the memlog's point that with no independent backup the array's redundancy is the only protection against total loss, and that 14 TB rebuild windows run 26–40 hours with material URE probability). A reader of the spine alone cannot tell whether SHR-2 was chosen or inherited.

**4. Yggdrasil ingress — resolved, with a gap.** AD-14 makes Gateway API the only north-south model; the Stack names Envoy Gateway and MetalLB 0.16.x. But the memlog's operative build instruction — **Traefik and ServiceLB must be disabled at k3s install time** — appears nowhere in the spine. A build following the spine gets k3s defaults and two routing models coexisting, which is the exact outcome AD-14 exists to prevent. The ingress-nginx EOL finding that drove the reversal is also memlog-only, so the decision reads as arbitrary preference.

**5. UPS compatibility gate — still open, and not carried anywhere.** The PRD calls this "the one specification whose failure would force a topology change rather than a workaround". The memlog confirms the NUT *topology* (DSM as server, Nodes as clients, ordering by tuned delay, with starting values of ~3 min and ~10 min for the Drill) but never records the gate itself as checked. AD-11 asserts "Nidavellir signals UPS state" as settled fact with no precondition attached. If the SMT1500C is not on Synology's supported list, AD-11 is unbuildable and D8 needs a different topology.

**6. Directory CA renewal-role placement — not resolved; delegated.** AD-5's closing sentence reads: "The Directory CA renewal role's location, health check, and relocation Procedure are named in the Repository." That defers the answer to an artefact that does not exist yet. The PRD asked architecture to *state* where the role lives — the risk register (§10) calls it "a single unrecoverable point" whose failure mode is the Directory's own certificates expiring silently well after the fault. The companion half is also missing: the replica must be built with CA and DNS roles explicitly, or FR-13, FR-25 and FR-27 each fail quietly. Nothing in the spine or the memlog says which roles the replica carries. The split-CA decision (AD-5) *contains* the trap to FreeIPA's own certificates, which is real mitigation, but it does not locate or verify the role.

**7. Independent backup target — the interim answer is memlog-only.** The Deferred section states the gap honestly and alludes to "the encrypted critical subset held offline". The memlog carries the actual decision: the Repository is already off-platform on GitHub, and FreeIPA directory data, PostgreSQL dumps, the step-ca root key and Break-glass credentials go encrypted to the owned SanDisk 1 TB portable SSD (already designated as bootstrap seed and credential escrow). None of the device, contents, schedule or verification reaches the spine, so the mitigation is unbuildable from it.

**8. Alert delivery path — the channel is memlog-only.** AD-12 gets the *structure* right and is one of the stronger ADs: three independent paths, infrastructure alerts bypassing Yggdrasil, all outbound-only, and the dead-man's switch correctly identified as the only path surviving a whole-house outage. But it names no channel. The memlog resolves it: Pushover for the first two tiers, healthchecks.io for the dead-man's switch. AD-12 also under-states what the memlog establishes — that because the router is beyond the UPS's reach, the dead-man's switch is **load-bearing rather than a nice extra**, alerting from external infrastructure over cellular when the heartbeat stops.

- **[critical]** Open question 5 (UPS/DSM compatibility) is unresolved and the spine treats its favourable answer as settled. AD-11 and the whole of D8 rest on DSM being the NUT server. *Fix:* record the gate in AD-11 as an explicit precondition with its verification step and the fallback topology if it fails, and make it a blocking item on the D8 epic rather than a purchase-time check.
- **[critical]** Open question 6 (Directory CA renewal role) is delegated rather than answered. AD-5 points at a Repository artefact that does not exist; the replica's CA and DNS roles are unstated, which is what makes FR-13 and FR-25 quietly fail. *Fix:* state in AD-5 which instance holds the renewal role, that the replica is installed with `--setup-ca --setup-dns`, the health check that detects an offline role-holder before certificates expire, and the relocation Procedure — then let the Repository hold the detail.
- **[high]** The k3s bundled-component disable step is memlog-only, and without it AD-14 is violated at install time. *Fix:* add it to the Stack row for k3s or as a Consistency Convention.
- **[medium]** The alert channel (Pushover, healthchecks.io) is memlog-only, and AD-12 understates the dead-man's switch as covering "total silence" when the memlog establishes it as the only path out during the outage class the platform is most likely to see. *Fix:* name both channels in AD-12 and restate the load-bearing status.
- **[medium]** The interim critical-subset escrow (SanDisk SSD) is memlog-only. It is the only thing standing between the accepted Nidavellir risk and losing identity, CA and databases too. *Fix:* promote it from the Deferred section's allusion to a named rule with contents and cadence.
- **[low]** SHR-2 appears only as a diagram caption with no rationale. *Fix:* one line in the Stack or Deferred section carrying the usable capacity, the tolerance, and the rebuild-window reasoning.

---

## Check 4 — Epic Coverage

| Epic | Buildable from the spine? | Governing invariants |
|---|---|---|
| S1 Repository and Procedure standard | Yes | AD-3, AD-4, AD-15; repo shape; conventions |
| S2 Network, DNS, Cluster, Break-glass | **Partly — DNS blocked** | AD-7, AD-9, AD-16, *Addressing* |
| S3 Shared storage, one Share | Partly | AD-8; FR-16 mount semantics missing |
| S4 Directory and network login | Yes | AD-2, AD-6, AD-17 |
| S5 Draupnir and Forseti | **Blocked — ordering broken** | AD-5, AD-14 |
| S6 Yggdrasil, minimal | Partly | AD-1, AD-8; disable step memlog-only |
| S7 Reference application | Yes | AD-14, AD-2, *Workload delivery*, registry caveat |
| D1 Storage depth | Partly | AD-8; FR-16 gap |
| D2 Identity depth | **Partly — blocked by OQ6** | AD-2, AD-9, AD-10 |
| D3 Yggdrasil depth | Partly | AD-1, AD-14; no anti-affinity rule |
| D4 Delivery depth | Yes | *Images*, *Workload delivery*, placement table |
| D5 Stateful services | Partly | AD-8; Redis ungoverned |
| D6 Observability | **Thin** | AD-12 (alerting only) |
| D7 Secrets management | Partly | AD-15; `andvari` product unnamed |
| D8 Power continuity | **Partly — blocked by OQ5** | AD-11, AD-12 |
| D9 Backup and recovery | **No invariants** | — |
| D10 SSO breadth | **No invariants** | — |
| D11 Destructive rebuild Drill | Yes | AD-3, AD-4, AD-9 |

- **[critical]** S5 cannot be built in the PRD's order. The PRD sequences S5 (Draupnir and Forseti, with minimal TLS ingress) before S6 (Yggdrasil). AD-18 places `forseti` inside Yggdrasil, and AD-14's TLS ingress is Envoy Gateway plus MetalLB — also inside Yggdrasil. So S5 depends on S6 in three places while the PRD orders it first, and the PRD's non-negotiable constraint ("S5 must deliver minimal TLS ingress, because an OIDC redirect requires a working HTTPS endpoint; without it S7 cannot complete") is unsatisfiable as written. The spine never notices. *Fix:* pick one and record it — either swap S5 and S6 (Yggdrasil minimal first, then CA and IdP on it), or split S5 into S5a (`draupnir`, a Guest, buildable early) and S5b (`forseti`, after S6). The second preserves more of the PRD's intent since `draupnir` is L2 and genuinely does come first.
- **[critical]** S2 promises `asgard.home.arpa` before any resolver exists. The PRD's S2 delivers the address plan and DNS domain; the spine's only DNS is FreeIPA integrated DNS in `mimir`, which arrives in S4. Between S2 and S4 nothing answers for the domain, and FR-13 has no second resolver at any point in the skeleton. *Fix:* state the skeleton's DNS story explicitly — either a thin form for S2 (hosts file or the household router's resolver, named as thin with S4 as its replacement, matching the pattern the PRD already uses for S5 and S7) or move basic DNS into S4 and adjust S2's scope.
- **[critical]** D9 has no governing invariants — see Check 1. It is the epic delivering SM-5, and it is the only Phase-1 epic the spine gives nothing to build from.
- **[critical]** D10 has no governing invariants — see Check 1. It delivers SM-3, one of the two primary metrics the platform exists to prove.
- **[high]** D6 is governed only for alerting. AD-12 is strong on alert *routing* and silent on metric collection, log shipping targets (the Logging convention is one row), retention numbers, auto-discovery of new Guests and Workloads (FR-49), and dashboard SSO (FR-52). Three of D6's four FRs are partial or uncovered. *Fix:* add an observability AD covering collection, bounded retention with a stated window, discovery without manual registration, and Grafana as a Relying Party.
- **[high]** D8 rests on an unverified precondition and contradicts FR-58 on the router. See Checks 3 and 5.
- **[medium]** D2 cannot be completed without open question 6. "Directory replica" is the epic's first deliverable and the roles it must carry are unstated.
- **[medium]** D3's headline deliverable — three Control Plane Guests spread across Nodes — has no invariant behind it (FR-38). *Fix:* the replicated-component AD from Check 1.
- **[medium]** S6 will produce a cluster that violates AD-14 unless the k3s disable step is carried into the spine.
- **[low]** S3 and D1 inherit the FR-16 mount-semantics gap; the first Share can be built, but the degradation property S3 is meant to establish cannot be verified.

---

## Check 5 — Contradictions and Stale PRD Lines

### Live contradictions

- **[critical]** FR-58 vs AD-11/AD-12 — the household router. FR-58 requires "All four Nodes, Nidavellir, **both switches**, and the household router are on battery-backed outlets" (prd.md:776) and repeats it as an emphasised bullet (prd.md:778). AD-11 lists only "All Nodes, Nidavellir, and both switches", and AD-12 states plainly that "the household router is beyond the UPS's reach". The memlog explains why: the Google router sits in a closet across the house on a circuit the operator does not control, making FR-58's router clause unachievable. The addendum's outlet budget still allocates outlet 8 to it. This is a direct, unreconciled contradiction, and it changes FR-59's guarantee — during a whole-house outage nothing outbound leaves except the dead-man's switch's *absence*. *Fix:* amend FR-58 to drop the router clause and state the consequence, amend FR-59 to record that in-event notification is not guaranteed and that the external heartbeat is the compensating control, and record the optional remedy (a small UPS in the router closet) as a deferred item.
- **[high]** PostgreSQL placement — the PRD's Non-Goals now assert something false. prd.md:897 reads "Guests running outside Yggdrasil are legitimate — the identity servers and PostgreSQL are deliberate examples." PostgreSQL is no longer an example; AD-18 places `fafnir` inside Yggdrasil with "Test met: none". The PRD is stale here, not the spine. *Fix:* replace the example with `draupnir`, which the spine does place outside on a named test.
- **[high]** PostgreSQL HA — the PRD's out-of-scope claim is now false. prd.md:930 puts PostgreSQL high availability out of MVP scope ("a verified restore is the v1 answer"), repeated at prd.md:1045. The memlog's CNPG decision explicitly cites surviving Node loss via CNPG-managed streaming replication with automatic failover, and the spine's Deferred section says "CloudNativePG failover is the answer; formal HA targets are not set." The PRD deferred a capability the architecture then delivered. *Fix:* rewrite both lines — replication and automatic failover come free with CNPG; what remains deferred is a formal HA target, not the capability.
- **[medium]** The access point — the PRD asserts it is not deployed; the spine's topology depends on it. prd.md:240 states "The wireless access point is not deployed — it served household coverage, never Asgard, and removing it frees a port without affecting any requirement." The spine's topology diagram shows `RTR -.->|wireless bridge, TL-WA3001 client mode| DSW`, and AD-13 states "The uplink is a wireless bridge carrying outbound traffic only." The memlog records the reversal and its cause: the rack has no wired path to the router (opposite side of the house, Google WiFi with no spare ports, no coax). Every consequence in the PRD's §4.3 narrative — the port count, the "uplinks to the household router" phrasing, the ASCII diagram's wired uplink — is now wrong. AD-6 depends on this too: the Directory is the time authority *because* the uplink is a wireless bridge. *Fix:* rewrite §4.3's topology block and narrative; the FR-65 requirement text itself is unaffected, since Node wireless stays disabled and the bridge is a separate device.
- **[medium]** FR-19 vs AD-12 — a reconcilable tension the spine leaves unstated. FR-19 requires Nidavellir utilisation and drive health be "reported to the observability system"; AD-12 requires that NAS alerts "must not route through Yggdrasil", where the observability system lives. Both are satisfiable — metrics flow in for dashboards, alerts flow out independently — but nothing says so, and a builder reading AD-12 alone would reasonably omit the metrics path. *Fix:* one clause in AD-12 distinguishing telemetry ingestion from alert routing.
- **[low]** The spine claims `binds: [… S1-S7, D1-D11]` in its frontmatter while leaving D9 and D10 with no governing invariant. *Fix:* either bind them or narrow the claim.
- **[low]** The Stack table lists "Envoy Gateway | Gateway API" in a version column. *Fix:* pin an actual version, as every other row does.

### Stale PRD lines — 18 requiring update

| # | Line | Currently says | Should say |
|---|---|---|---|
| 1 | prd.md:221 | "The switch uplinks to the household router" | Uplink is a wireless bridge (TL-WA3001, client mode), outbound-only |
| 2 | prd.md:226–238 | ASCII topology showing a wired `ISP router --uplink--> data switch` | Redraw with the wireless bridge |
| 3 | prd.md:231 | "6 of 10 ports used" | 7 of 10 — the bridge consumes one |
| 4 | prd.md:240 | "The wireless access point is not deployed … removing it frees a port without affecting any requirement" | Redeployed as the platform's sole uplink in wireless-bridge mode; the outbound path now depends on it |
| 5 | prd.md:776 | FR-58: "…both switches, and the household router are on battery-backed outlets" | Drop the router — it is on an uncontrolled circuit across the house |
| 6 | prd.md:778 | FR-58 bullet: router and modem on battery-backed outlets | Replace with the consequence: no outbound path during a whole-house outage; the external heartbeat is the compensating control |
| 7 | prd.md:897 | Non-Goals: "the identity servers and PostgreSQL are deliberate examples" | PostgreSQL now runs in-cluster; use `draupnir` as the example |
| 8 | prd.md:930 | §7.2: PostgreSQL HA out of scope, "a verified restore is the v1 answer" | CNPG provides replication and automatic failover; only a formal HA target is deferred |
| 9 | prd.md:1045 | Deferred callout repeating the PostgreSQL HA deferral | Same correction |
| 10 | prd.md:977 | S5: "the IdP may run on an embedded database … migrating to `fafnir` in D5" | `forseti` now runs inside Yggdrasil (S6); the thin form and its ordering need restating |
| 11 | prd.md:981 | S5 ordering constraint: "S5 must deliver minimal TLS ingress" | Unsatisfiable before S6 under AD-14; restate per the S5a/S5b split |
| 12 | prd.md:993 | D3: "ingress with Draupnir TLS" | Gateway API — AD-14 prohibits Ingress resources, so the term now means the wrong thing |
| 13 | prd.md:995 | D5: "`fafnir` on the Off-NFS Store" | `fafnir` as CloudNativePG on local-NVMe PVs; still off NFS, no longer a Guest |
| 14 | prd.md:1023 | OQ1: "Resolved in architecture" without naming the answer | FreeIPA 4.12.5 on Rocky Linux 10; mixed-OS consequence per AD-17 |
| 15 | prd.md:1024 | OQ2: "A Guest with local NVMe, or an iSCSI LUN" | Resolved by a third option: in-cluster CloudNativePG on local-path NVMe PVs; iSCSI rejected because Nidavellir is HDD-only |
| 16 | prd.md:1025 | OQ3: RAID level open | Resolved: SHR-2, ~28 TB, dual-drive tolerance |
| 17 | prd.md:1026 | OQ4: "Retain the distribution's bundled ingress controller and load balancer, or replace them" | Resolved: bundled Traefik and ServiceLB disabled at install; MetalLB L2 plus Envoy Gateway on Gateway API; ingress-nginx eliminated on an EOL finding |
| 18 | prd.md:1030 | OQ8: alert delivery path open | Resolved: Pushover for platform and infrastructure tiers, healthchecks.io dead-man's switch as the load-bearing external path |

Two further PRD lines are not stale but are now **falsified by the spine's own decisions** and need a decision rather than a text edit: prd.md:864 (NFR-6, which AD-18's placement breaks on side (b)) and prd.md:1027 (OQ5, the UPS gate, which remains genuinely open).

Outside the PRD, the brief addendum needs the same treatment: §2's Tier-1 rows for `forseti` and `fafnir` (addendum.md:48, 51, 52), the Tier-2 subtotal and "~21 GB schedulable" conclusion (addendum.md:73–74), the "Not deployed" access point row (addendum.md:24), and the outlet-budget row assigning outlet 8 to the household router (addendum.md:272).

---

## Summary of Findings by Severity

**Critical (7)** — AD-18 placement breaks NFR-6(b); backup and recovery ungoverned (D9); SSO breadth ungoverned (D10); S5 unbuildable in the PRD's order; S2 has no resolver; open question 5 (UPS gate) unresolved and assumed favourable; open question 6 (CA renewal role) delegated rather than answered. Plus the FR-58 router contradiction.

**High (9)** — FR-9/NFR-23 snapshots; FR-16 storage degradation; FR-38/NFR-16 no anti-affinity invariant; NFR-7/NFR-9 capacity enforcement; NFR-18 proven-by-execution; D6 observability thin; k3s disable step memlog-only; PostgreSQL placement and HA lines stale in the PRD.

**Medium (14)** and **low (7)** as listed inline.

**Recommended sequence:** resolve the NFR-6(b) capacity break and the S5/S6 ordering first — both are decisions, not documentation, and both change what gets built. Then add the three missing ADs (backup, SSO breadth, replicated-component spread), promote the six memlog-only decisions into the spine, and land the 18 PRD line edits as a single amendment so the PRD stops contradicting the architecture it produced.
