---
title: "Addendum — Project Asgard"
status: approved
created: 2026-08-28
updated: 2026-08-28
---

# Addendum — Project Asgard

Depth captured during discovery that belongs to the PRD, the architecture spine, or the specs rather than to the brief. Nothing here is decided unless the brief says it is decided.

## 1. Hardware Inventory, Assessed

| Class | Item | Qty | Assessment |
|---|---|---|---|
| Compute | HP EliteDesk 705 G5 Mini - Ryzen 5 PRO 3400GE (4C/8T, 35 W, Zen+), 32 GB RAM, 1 TB NVMe | 4 | Well-matched to a Proxmox cluster. Homogeneous, which matters more than raw speed. **Supports AMD DASH out-of-band management** - corrected from an earlier 'no IPMI' assessment; ships enabled with vendor default credentials, so it is claimed in S2 rather than left. Ships Windows 11 Pro; all four are reimaged. Vega 11 iGPU is idle capacity. |
| Storage | Synology DS925+ (diskless) | 1 | Dual 2.5 GbE. Serves NFS and, via `synology-csi`, iSCSI LUNs. Single point of failure by design decision. |
| Storage | WD Red Pro 14 TB (CMR, 7200 RPM) | 4 | **SHR-2 selected: ~28 TB usable, dual-drive tolerance.** Not on the DS925+ compatibility list, which carries only vendor-branded entries - permitted under the DSM 7.3 reversal, not validated. Requires DSM 7.3 or later. |
| Storage | SanDisk 1 TB Extreme Portable SSD | 1 | Best used as the offline bootstrap seed and out-of-band escrow for break-glass credentials — deliberately not part of the running system. |
| Network | NICGIGA 10-port (2x 10 G RJ45, 8x 2.5 G) | 1 | The data switch. 6 of 10 ports used after the 2.5 GbE adapters land; 4 spare. Unmanaged, so no VLANs even if wanted. |
| **Purchased** | APC Smart-UPS SMT1500C | 1 | 1500 VA / 1000 W, pure sine, 8 outlets all battery-backed, hot-swap battery. Gate: verify against Synology's supported-UPS list before relying on DSM as NUT server. |
| **Purchased** | UGREEN USB-A to 2.5 GbE adapter | 4 | Second interface per Node, carrying bulk traffic. Typically RTL8156-family on the `r8152` driver; Proxmox 8's 6.x kernel supports it. Verify deterministic interface naming on arrival - USB NIC naming is less stable than onboard and the address plan depends on it. |
| **Purchased** | TP-Link Omada ES205G | 1 | The membership switch. 5-port gigabit, easy-managed, fanless, metal chassis, ~2-3 W. Run **standalone** - never adopted into an Omada controller. |
| Network | TP-Link TL-WA3001 AX3000 AP | 1 | **Deployed in client-bridge mode as the platform's only uplink.** Reversed from an earlier decision not to deploy it: the rack has no wired path to the household router - opposite side of the house, no spare ports, no coaxial anywhere - so the bridge is how outbound traffic leaves. Four external antennas suit a through-walls link. Carries outbound traffic only; nothing internal crosses it. |
| Network | GL.iNet GL-BE3600 (Slate 7) travel router | 1 | Genuinely a travel router. Not a lab edge device. Useful as a portable VPN client or an isolated test bench. |

### Identified gaps

- **UPS - RESOLVED, now in scope.** APC Smart-UPS SMT1500C. See section 9 for load math, outlet budget, and shutdown-ordering design.
- **No 2.5 G NICs for the nodes.** USB 3.0 2.5 GbE adapters or M.2 A+E-key NICs would unlock the switch. Low cost, meaningful gain on NFS-heavy workloads. Partly mitigated already: Nidavellir takes a 2.5 GbE port, so the shared side is not the constraint even while each Node caps at 1 GbE.
- **Node wireless is not a fallback.** The EliteDesks' WiFi 6E radios are disabled, not held in reserve. Cluster membership signalling is latency- and jitter-sensitive; wireless variance reads as node loss and produces spurious partitions. A node that silently fails over to wireless destabilises the cluster while appearing healthy.
- **No managed switch.** Forecloses VLAN segmentation, consistent with v1 scope.
- **No dedicated firewall.** Consistent with v1 scope; revisit if anything is ever published.

## 2. Capacity Model

Revised during the PRD review, which found the original model incomplete: it omitted Redis, the registry, CI runners, the secret store, the GitOps controller, forward-auth, and alerting, and understated the Directory at 3 GB per instance. It also used a single-sided metric - unallocated hypervisor memory - which could be satisfied by relocating a service into a Worker Guest while consuming exactly the same capacity. NFR-6 is now bounded from both sides.

vCPU is deliberately oversubscribed against 32 threads; that is normal and appropriate for a lab. RAM is not oversubscribed, because memory pressure is where labs actually fall over.

### Tier 1 - Guests on the hypervisor

| Component | vCPU | RAM |
|---|---:|---:|
| Proxmox VE overhead (4 x ~2 GB) | - | 8 GB |
| Directory primary (`mimir`) | 2 | 4 GB |
| Directory replica | 2 | 4 GB |
| Identity provider (`forseti`), JVM heap capped | 2 | 4 GB |
| Kubernetes control plane, 3 x Norn | 6 | 12 GB |
| Kubernetes workers, 3 x Valkyrie | 18 | 48 GB |
| PostgreSQL (`fafnir`), Off-NFS Store | 4 | 8 GB |
| **Committed** | **34** | **88 GB** |
| NFR-6(a) ceiling | | 90 GB |
| Unallocated of 128 GB physical | | **40 GB** |

### Tier 2 - inside the 48 GB Worker allocation

The components the original model missed are here rather than absent - they run as Workloads, not as their own Guests. That is precisely why a hypervisor-level metric alone was inadequate.

| Workload | RAM |
|---|---:|
| Prometheus (`huginn`) | 6 GB |
| Loki (`muninn`) | 4 GB |
| Grafana | 1 GB |
| Alerting (`gjallarhorn`) | 0.5 GB |
| Redis (`ratatoskr`) | 2 GB |
| Container registry (`sindri`) | 2 GB |
| CI runners (`brokkr`) | 4 GB |
| Secret store (`andvari`) | 1 GB |
| GitOps controller | 2 GB |
| Ingress and forward-auth | 1 GB |
| k3s agent overhead (3 x ~1 GB) | 3 GB |
| **Platform subtotal** | **~26.5 GB** |
| **Schedulable for the operator's own Workloads** | **~21 GB** |

NFR-6(b) requires at least 15 GB schedulable within Yggdrasil; ~21 GB satisfies it with room. NFR-7 requires that losing one Node still run identity, storage, and cluster control: three Nodes provide 96 GB against 88 GB committed, which is why the 90 GB ceiling exists rather than a higher one.

### What will consume the margin

Two components, predictably. **Prometheus retention** grows with both scrape targets and retention window, and is the single most likely cause of a slow squeeze - NFR-8 requires the window be bounded and stated rather than left to grow. **The identity provider's JVM** must have its heap capped explicitly; left to default sizing it will claim a share of whatever the Guest is given. NFR-9 exists for exactly these two cases.

Storage: 4 TB raw NVMe across the Nodes, realistically ~3 TB usable for Guest disks after hypervisor overhead and local volume layout. Bulk data lives on Nidavellir.

## 3. Norse Naming Registry

Principle: **realms name tiers, beings name instances.** Every name carries a reason — a scheme where the names mean something is a scheme that gets remembered and extended correctly.

### Realms — tiers and domains

| Name | Binds to | Rationale |
|---|---|---|
| `asgard` | Platform identity, DNS domain | Realm of the Æsir — the whole works |
| `midgard` | The household LAN the lab sits on | Realm of humans |
| `yggdrasil` | The Kubernetes cluster | The world tree connecting all realms |
| `nidavellir` | Synology / storage tier | Realm of the dwarf-smiths who forge and keep |
| `bifrost` | Ingress and reverse proxy | The bridge between realms, watched by Heimdall |
| `hel` | Backup and archive tier | Where things go to be kept after they die |
| `vanaheim` | Reserved: second environment / staging | A separate realm of separate gods |
| `jotunheim` | Reserved: untrusted / DMZ, should VLANs arrive | Realm of the giants — outside the walls |

### Physical nodes — the Æsir

| Host | Suggested weight | Rationale |
|---|---|---|
| `odin` | Proxmox primary; identity tier | The All-Father — knows everything, gave an eye for knowledge |
| `thor` | Compute / worker-heavy | Raw strength |
| `heimdall` | Edge, ingress, observability | The watchman who sees and hears everything approaching |
| `tyr` | Data services | God of law and oaths — the one who keeps his word, and paid a hand for it |

Roles are weightings, not hard bindings — in a Proxmox cluster guests migrate. Names indicate intent.

### Guests and services

| Name | Role | Rationale |
|---|---|---|
| `urd`, `verdandi`, `skuld` | Kubernetes control plane | The three Norns, who tend Yggdrasil's roots. Exactly three of them, and their job is literally to tend the tree. |
| `brynhildr`, `sigrun`, `gondul` | Kubernetes workers | Valkyries — they carry the fallen to their destination, as workers carry workloads |
| `mimir` | LDAP directory | The well of wisdom; Odin queries Mimir's head for knowledge |
| `forseti` | Keycloak | God of justice who presides over disputes — grants and denies |
| `fafnir` | PostgreSQL | The dragon who guards the hoard |
| `ratatoskr` | Redis | The squirrel who runs messages up and down Yggdrasil — fast, ephemeral, in-transit |
| `huginn` | Prometheus / Grafana | Odin's raven "Thought" — flies out and observes |
| `muninn` | Loki / log retention | Odin's raven "Memory" — retention |
| `draupnir` | Internal certificate authority | Odin's ring that drips eight copies of itself every ninth night — an issuer of copies |
| `andvari` | Vault / secrets | The dwarf who hoarded gold hidden in a cave |
| `brokkr` | CI / build runners | The smith who forged Mjölnir |
| `sindri` | Container registry | Brokkr's brother, the other half of the forge |
| `gjallarhorn` | Alerting / notification | Heimdall's horn, sounded when something is coming |
| `valhalla` | Reserved: long-running app tier | The hall where the einherjar await |
| `einherjar-NN` | Reserved: scale-out ephemeral workers | The countless warriors — for when named workers run out |

Reserve pool for future instances: `baldr`, `frigg`, `vidar`, `bragi`, `njord`, `freyja`, `freyr`, `idunn`, `sif`, `ullr`, `hodr`, `nanna`, `alviss`, `dvalin`, `durin`, `eitri`, `nott`, `dagr`, `skadi`, `aegir`.

## 4. Identity Design Notes

### Why the directory and Keycloak are two things, not one

Linux hosts authenticate over LDAP/Kerberos via SSSD; web services authenticate over OIDC. Nothing speaks both well. The standard resolution is a directory as the authoritative user store with Keycloak federating to it as a read-mostly consumer — one account, two protocols. Keycloak's own database then holds only sessions, clients, and realm config, which makes Keycloak rebuildable without touching user identity.

### Directory options

| Option | Gives | Costs |
|---|---|---|
| **FreeIPA** | LDAP + Kerberos + integrated CA + DNS + sudo rules + host-based access control + a replication story | ~4 GB RAM, opinionated, replication is real work. Highest enterprise fidelity. |
| **LLDAP + SSSD** | Lightweight LDAP, pleasant admin UI, tiny footprint | No Kerberos, no sudo rules, no CA. Least to learn from. |
| **Samba AD DC** | Genuine Active-Directory-compatible domain; closest to what most corporations actually run | Heaviest operationally; Linux integration is workable but less idiomatic |

Given the enterprise-simulator purpose, FreeIPA is the strongest teacher — it delivers the CA (`draupnir`), host-based access control, and centralized sudo rules as part of the same system, which collapses three otherwise-separate epics into one.

### Identity bootstrap — the lockout problem

Centralized login creates a circular dependency: hosts need the directory to authenticate, and the directory runs on those hosts. Four defenses, in order of use:

1. **Local emergency admin on every node**, in the `sudo` group, excluded from directory management, password held in the password manager and escrowed on the portable SSD.
2. **`cache_credentials = true` in SSSD** — any user who has authenticated before can still log in offline. This covers the overwhelming majority of real outages.
3. **Proxmox `root@pam`** — Proxmox's own local realm, unaffected by directory state, and the path to VM consoles when guest authentication is broken.
4. **Physical console** — no IPMI on these nodes, so this is genuinely the floor. Keyboard and monitor.

A **second directory replica** is a should-have. Cost is one small VM; the return is that "the directory is a service with redundancy, not a host" — which is the actual enterprise lesson, and it removes the most likely cause of ever needing defense 4.

### What Keycloak can and cannot cover

| Target | Mechanism | Status |
|---|---|---|
| Operator's own applications | Native OIDC, authorization code + PKCE | The stated primary goal |
| Kubernetes API / `kubectl` | API server `--oidc-issuer-url`, claims → groups → ClusterRoleBindings | The canonical enterprise pattern; high value |
| Proxmox VE | Native OpenID Connect realm | Supported natively |
| Grafana, Argo CD, Harbor, Gitea, Vault | Native OIDC clients | Straightforward |
| Synology DSM | Native OIDC SSO | Supported |
| Services with no auth | `oauth2-proxy` or Authelia forward-auth at the ingress | Replaces per-service passwords |
| Linux console / SSH login | Not OIDC — SSSD against the directory | Shared user store is what unifies them |
| SSH as a first-class OIDC citizen | Vault SSH certificate authority, OIDC-authenticated, issuing short-lived certs | Stretch goal; among the highest-value exercises in the build. Break-glass under FR-24 remains the independent path. |
| VPN / network transport | Moot - remote access was cut from scope entirely. Had it stayed, an IdP-authenticated VPN would have created a circular dependency: Keycloak down means no way in to fix Keycloak. | Out of scope |
| Secret storage | Not Keycloak's job | Password manager persists for break-glass and API tokens |

**On PingFederate fidelity:** for application-side integration, Keycloak is a faithful stand-in. Discovery documents, authorization code + PKCE flow, JWT validation, claims mapping, and scope handling are standards-defined and identical against either. The divergence is in the administrative console, adapter tooling, and policy language — not the part being practiced.

## 5. Storage Design Notes

**Decided:** NFS from `nidavellir` for shared home directories and for Kubernetes persistent volumes. Operator has accepted NAS-reboot impact.

**Decided carve-out:** PostgreSQL does not run on NFS. PostgreSQL's durability model depends on `fsync` semantics and file locking that NFS implements loosely; the failure mode is silent corruption discovered late. Two acceptable answers: a VM on local NVMe with disciplined backups, or an iSCSI block LUN presented through `synology-csi`. The iSCSI route keeps the volume in the Kubernetes storage model and is the better learning exercise.

**Open — RAID level.** SHR-1 gives ~42 TB with single-drive tolerance; SHR-2 gives ~28 TB with dual-drive tolerance. With 14 TB drives, rebuild windows are long, and a second failure during rebuild is the realistic risk rather than a theoretical one.

**Known bottleneck.** Nodes are 1 GbE; NFS throughput caps near 110 MB/s per node regardless of what the NAS or switch can do. Mitigation, if it matters later, is USB 3.0 or M.2 2.5 GbE adapters — cheap, and the switch already has the ports.

**Home directory mechanics.** NFS `/home` with `autofs` on-demand mounting is preferable to hard static mounts: a NAS outage then degrades to "home directory unavailable" rather than "every process on the node hangs in uninterruptible sleep." SSSD's `mkhomedir` handles first-login provisioning.

## 6. Documentation Model

The brief's dual-form requirement, made concrete. Every procedure has three parts:

1. **The runbook** — ordered, human-followable steps with verification checkpoints, stating *why* at each decision point. Written for the operator mid-outage at 2am, not for the operator who just made the decision.
2. **The automation** — the Ansible role, Terraform/OpenTofu module, or Kubernetes manifest that performs the same thing idempotently.
3. **The verification** — how to prove the result is correct, identical whichever path was taken.

The governing invariant: **following the runbook by hand must produce a node the automation then considers already converged.** A drift between the two is a documentation defect, and running the automation against a hand-built node is the test that detects it.

## 7. Candidate Epic Decomposition

Preliminary, for the PRD to confirm or restructure. Ordered by dependency.

| # | Epic | Depends on | Delivers |
|---|---|---|---|
| 0 | Repository, documentation standard, secrets bootstrap | — | The dual-form contract, structure, and how secrets are handled before there is a Vault |
| 1 | Network foundation and DNS | 0 | Addressing plan, `asgard` DNS, name resolution for everything after |
| 2 | Proxmox cluster on 4 nodes | 1 | `odin`, `thor`, `heimdall`, `tyr` clustered; the reimage-and-rejoin runbook |
| 3 | Storage: NAS, NFS exports, backup targets | 1 | `nidavellir` serving shares; `hel` as a backup target |
| 4 | Identity: directory + replica | 2, 3 | `mimir`; network logins working on all four hosts |
| 5 | PKI: internal certificate authority | 4 | `draupnir`; trusted TLS everywhere internal |
| 6 | Keycloak + directory federation | 4, 5 | `forseti`; SSO for the first service |
| 7 | Kubernetes cluster | 2, 3 | `yggdrasil`; Norns and Valkyries; NFS storage class |
| 8 | GitOps and CI | 7 | `brokkr`, `sindri`; deployment from this repository |
| 9 | Stateful services | 7 | `fafnir` (off NFS), `ratatoskr` |
| 10 | Observability | 7 | `huginn`, `muninn`, `gjallarhorn`; SSO-fronted Grafana |
| 11 | Secrets management | 6, 7 | `andvari`; migration off bootstrap secrets |
| 12b | Power protection and ordered shutdown | 2, 3 | UPS on the NAS as NUT server, Proxmox hosts as clients, dependency-ordered shutdown, proven by a live drill |
| 13 | Backup, restore, and destructive rebuild test | all | Success criteria 1 and 6 actually proven, not assumed |
| 14 | Reference application | 6, 8, 9 | Success criterion 3: the operator's own OIDC-protected app, end to end |

Epic 14 is the one that validates the lab's stated purpose. Epic 13 is the one that validates the documentation.

## 8. Deferred and Rejected, With Reasons

| Item | Disposition | Reason |
|---|---|---|
| VLAN segmentation, dedicated firewall | Deferred | Nothing is internet-facing and there is one user; the existing ISP router suffices. Revisit if anything is ever published. |
| Public DNS, ACME certificates | Deferred | An internal CA is sufficient for a LAN/VPN-only lab. Registering a domain now keeps the option open. |
| Ceph / Longhorn node-replicated storage | Rejected for v1 | Operator chose the Synology. Would also compete for the RAM headroom that is the experimentation budget. |
| Service mesh | Deferred | No workload yet justifies it. |
| PostgreSQL HA cluster | Deferred | Cost in RAM is real; the enterprise lesson is available more cheaply elsewhere. Tested restore is the v1 answer. |
| Tailscale/password manager instead of Keycloak | Rejected | Would satisfy convenience but defeats purposes A, B, and D. The identity machinery *is* the point. |
| UPS | **Accepted into scope** | APC Smart-UPS SMT1500C. Sized at ~3.1x the ~320 W load, 8 battery-backed outlets. The value is in the NUT shutdown orchestration, not the battery. |

## 9. Power Protection Design

### Load model

| Load | Estimate |
|---|---:|
| 4x EliteDesk 705 G5 Mini (external bricks, ~50 W avg) | ~200 W |
| DS925+ with 4x WD Red Pro 14 TB | ~90 W |
| NICGIGA data switch | ~15 W |
| 5-port membership switch | ~5 W |
| Household router (and modem, if separate) | ~10 W |
| **Total typical** | **~320 W** |
| **Peak (all Nodes loaded, drives active)** | **~430 W** |

The USB 2.5 GbE adapters draw from the Nodes' own USB ports and are already inside the per-Node figure. The access point is powered as the uplink bridge and is included above.

Against 1000 W the unit runs at roughly a third of capacity. Expected runtime at ~320 W is **an estimated 12-15 minutes, to be measured by Drill rather than assumed** - sufficient for orderly shutdown, insufficient for riding out an outage. Every decision below follows from that distinction.

### Model - SETTLED

**APC Smart-UPS SMT1500C**, 1440 VA / 1000 W, pure sine wave, 8 outlets all battery-backed. (Marketed as a 1500-class unit; the plated rating is 1440 VA. The 1000 W figure the load model uses is the binding one.)

The selection moved twice, and both moves were driven by findings rather than preference. The BX1500M was rejected for its stepped-approximation waveform - workable given that all lab gear runs on external power bricks, but not worth the residual risk sitting underneath the one device holding every byte of persistent state. The BR1500MS2 fixed the waveform but failed on outlet topology: Back-UPS units split their outlets, offering only 5 battery-backed of 10, against a requirement of six devices. That would have forced a non-surge distribution strip onto a battery outlet - workable, but an extra failure point and a standing invitation to plug in a surge suppressor by mistake.

Smart-UPS resolves the topology structurally: every outlet is battery-backed. The line beyond that (line-interactive AVR, hot-swappable battery, longer service life) is worth the premium for a unit running 24/7 beneath the entire platform. Hot-swap in particular matters at year three, when the alternative is a full planned outage to change a battery.

### Outlet budget

Eight battery-backed outlets against eight required devices. The access point's removal and the membership switch's addition cancel out; the household router's addition consumes the last spare.

| Outlet | Load | Why battery-backed |
|---|---|---|
| 1-4 | `odin`, `thor`, `heimdall`, `tyr` | Need time to shut Guests down cleanly |
| 5 | `nidavellir` (Synology DS925+) | Holds all persistent state; ceases serving last |
| 6 | Data switch | Without it, storage and shutdown signalling stop |
| 7 | Membership switch | Losing it mid-sequence breaks cluster membership while Guests are still shutting down |
| 8 | Household router | Without it, FR-59's power alert cannot leave the premises during the event that triggers it |

**One thing to check before racking:** whether the ISP equipment is a single combined modem-router or a separate modem and router. If separate, both need battery power - an outbound alert needs the whole chain - and that is a ninth device against eight outlets. The clean resolution is a **plain distribution strip with no surge suppression** on outlet 8, feeding the two small network devices (roughly 5-10 W each). The earlier objection to a strip does not apply here: it was specifically about cascading *surge suppressors*, not about distributing two trivial loads.

There is now no spare outlet. A fifth Node would require revisiting this, most likely by consolidating the small network devices onto a strip as above.

### Compatibility gate

DSM is the NUT server, so the UPS must appear on Synology's supported-device list. APC USB-HID units are broadly covered and Smart-UPS is the standard case, but this is verified against Synology's list before the design depends on it - it is the one specification whose failure would force a topology change rather than a workaround.

### Shutdown orchestration - the actual deliverable

The battery buys time; the orchestration converts that time into data integrity. The controlling constraint is a dependency inversion:

> **VM storage lives on the NAS, so the NAS must power down last - but the NAS is also the natural NUT server.** The host that signals shutdown must outlive every host it signals.

Topology: UPS connects by USB to the Synology. DSM runs as the network UPS server. The four Proxmox hosts run `upsmon` as clients. **The switch must be on the UPS**, or clients lose the network path before the shutdown signal arrives.

Ordering, which requires explicit configuration rather than defaults:

| Phase | Action | Budget |
|---|---|---:|
| 1 | Cordon and drain Kubernetes workloads | ~60 s |
| 2 | Shut down k8s guests (Valkyries, then Norns) | ~60 s |
| 3 | Clean shutdown of `fafnir` (PostgreSQL), then remaining service VMs | ~60 s |
| 4 | Shut down Proxmox hosts | ~60 s |
| 5 | NAS shuts down last, on a delayed timer | ~30 s |
| | **Target total** | **~5 min** |

A ~5 minute target against an estimated 12-15 minutes of runtime leaves margin for an aged battery, or an outage beginning under full load.

### Verification

The only acceptable proof is a live drill: pull mains power and observe the sequence complete with the NAS last. Runtime under real load is measured, not trusted from the specification sheet, and the drill is repeated after battery replacement. Belongs to Epic 12b; feeds Epic 13 recovery evidence.

## 10. Network Topology

Asgard shares the household LAN and runs **two switches carrying two kinds of traffic**.

```
ISP router ~~wireless bridge~~> data switch (10-port) --+-- odin   2.5 GbE (adapter)
    |                                          +-- thor       2.5 GbE (adapter)
    |                                          +-- heimdall   2.5 GbE (adapter)
    |                                          +-- tyr        2.5 GbE (adapter)
    +-- household devices                      +-- nidavellir 2.5 GbE
                                                   6 of 10 used, 4 spare

         membership switch (5-port, isolated) --+-- odin       1 GbE (onboard)
                                                +-- thor       1 GbE (onboard)
                                                +-- heimdall   1 GbE (onboard)
                                                +-- tyr        1 GbE (onboard)
                                                    4 of 5 used, NO uplink
```

**Why two switches.** Each Node gained a USB 2.5 GbE adapter, doubling its port demand from one to two. Against the 10-port switch that totalled eleven ports required for ten available, and the access point could not simply be dropped to recover one - it is the uplink. A five-port gigabit switch dedicated to membership traffic costs roughly fifteen dollars and returns four spare 2.5 GbE ports on the data switch.

**The uplink is wireless out of necessity.** The rack has no wired path to the household router: it sits in a closet on the opposite side of the house, the router has no spare ports, and there is no coaxial cabling in the building to carry MoCA. The access point therefore runs in client-bridge mode, connecting the data switch to the household wireless network. Only outbound traffic crosses it - package retrieval, image pulls, upstream time, and alerts - so a 100-200 Mbps link is adequate and the bottleneck lands where it does not matter. Cluster membership, storage, Workload and backup traffic never leave the two switches at the rack.

The honest driver is **port headroom**, not fabric contention. The 10-port switch almost certainly has adequate backplane to carry membership signalling alongside storage traffic. Nor does the second switch buy availability - either switch failing disrupts the Cluster. What it buys is growth room and genuine separation, cheaply.

**The membership switch has no uplink.** It is not connected to the data switch or the router. It carries only Node membership traffic on its own subnet, with no gateway and no path to the internet. Connecting the two switches would return membership to shared fabric and forfeit the separation entirely - and the instinct to daisy-chain switches is exactly why this is stated as a constraint rather than left to inference.

**The membership switch runs standalone, never controller-adopted.** The chosen unit (TP-Link Omada ES205G) supports adoption into an Omada controller. It must not be adopted. Doing so would make the configuration of the network carrying cluster membership dependent on controller software - and if that controller ever ran as a Workload on this cluster, the result is a circular dependency in which the cluster's membership network is managed from inside the cluster. Standalone administration via its own web interface keeps the segment inert and independent.

**Three settings decisions on the membership switch**, each deliberate:

| Setting | Decision | Why |
|---|---|---|
| Management IP | Static, on the membership subnet, no gateway | Reachable from a Node, unreachable from the household LAN |
| IGMP snooping | Off | Corosync 3 with knet is unicast, so snooping buys nothing; on an isolated segment with no querier present it can silently break multicast if anything ever uses it. Pure downside. |
| VLANs, QoS, LAG | Unused, left at default | One traffic type between four hosts. Every feature enabled is a novel way for cluster membership to fail. |

An easy-managed switch was chosen over an unmanaged one for a single reason: **port error counters and cable diagnostics on the segment whose failures are hardest to diagnose.** Corosync flapping is intermittent and presents as evicted Nodes with no obvious cause; an unmanaged switch would leave that segment unobservable, which defeats much of the point of isolating it. The cost is that the switch becomes a configuration item under FR-4 and needs a small Procedure - accepted knowingly.

**Energy Efficient Ethernet is a build-time check.** The 802.3az Low Power Idle state adds wake latency, which is the jitter signature corosync is sensitive to. If the ES205G exposes an EEE toggle, disable it. If it does not, monitor corosync latency through the first days after cutover, since that is when such a problem would surface.

**Membership stays on the onboard interfaces, not the adapters.** The adapters are USB-attached, and USB Ethernet is more prone to resets and renumbering than an onboard controller. That is acceptable for bulk traffic that retries; it is not acceptable for the signalling that decides whether a Node is alive. Bulk traffic therefore takes the faster, less reliable path and membership takes the slower, more reliable one - the inverse of the naive allocation.

**Nidavellir takes a 2.5 GbE port** even though each Node's storage path caps near 300 MB/s. Four Nodes can demand several Gbps in aggregate; the faster link on the shared side moves the bottleneck to the individual Node, which is where it belongs.

**No inbound path exists.** Remote access was cut from scope entirely. The data switch's uplink carries outbound traffic only.

Both switches are unmanaged, which forecloses VLANs - consistent with the flat-LAN scope decision. Should segmentation ever be wanted, the data switch is the component to replace.
