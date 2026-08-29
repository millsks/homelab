---
title: Project Asgard — Solution Design
status: draft
created: 2026-08-28
updated: 2026-08-28
companion_to: ARCHITECTURE-SPINE.md
---

# Project Asgard — Solution Design

The spine states *what must be true*. This document explains *how the pieces fit and why they were chosen*, for the reader six months from now who needs to change something and wants to know what they will break. Where the two disagree, the spine wins — it is the contract; this is the commentary.

## 1. What this is

Four HP EliteDesk mini PCs, a Synology DS925+, two switches and a UPS, assembled into a private cloud that behaves like a corporate environment rather than a pile of self-hosted containers. It runs Kubernetes for applications, a set of shared backing services, and a single identity plane where one account authenticates a Linux shell, a `kubectl` call, a Grafana dashboard, and an application written that afternoon.

It exists for three overlapping reasons: to be a faithful small-scale enterprise environment to practise on and break; to build depth in Kubernetes, infrastructure-as-code, and OIDC; and to give the operator's own software somewhere real to live with a genuine authorization server to develop against.

The distinguishing property is not the services. It is that **every procedure exists twice** — as a runbook a human follows and as automation that produces the identical result — with a convergence test that makes drift between them detectable rather than gradual.

## 2. The one idea

Everything else follows from a single rule: **no layer may require a higher layer in order to start or to authenticate.**

Six layers, each depending only downward:

| | Layer | What lives here |
| --- | --- | --- |
| L0 | Physical | Power, network fabric, rack |
| L1 | Hypervisor | Proxmox on four nodes |
| L2 | Foundation | Directory, DNS, Kerberos, time, platform CA |
| L3 | Platform | Kubernetes, storage classes, gateway |
| L4 | Platform services | IdP, databases, cache, registry, CI, observability, secrets |
| L5 | Workloads | The operator's own applications |

This sounds abstract until you notice how many concrete failures it prevents. A VPN authenticated by the identity provider means you cannot get in remotely to fix the identity provider. A switch whose configuration is managed by a controller running on the cluster whose membership that switch carries. A directory inside the Kubernetes cluster that Kubernetes nodes need for name resolution. A certificate authority inside the cluster, issuing the certificates the hypervisor below it depends on. Each of these was proposed during design and each was rejected by the same rule.

The corollary is **AD-18's placement test**, which decides where a service runs without argument. Default is inside the cluster. A service moves outside only if the cluster needs it to start or authenticate, if a lower layer depends on it across cluster loss, if it needs host-level identity semantics a pod cannot provide, or if recovering the cluster requires it. Applied across the whole platform, only two services qualify: the directory and the platform CA.

## 3. Walking the layers

### L0 — Physical

Four nodes, each dual-homed. The onboard gigabit interface carries **only cluster membership**, on its own switch with no uplink and no gateway. The added 2.5 GbE USB adapter carries everything else — storage, pods, backups, outbound traffic — on the data switch.

The allocation is deliberately counterintuitive: the faster link gets the bulk traffic and the slower one gets the heartbeats. USB Ethernet resets and renumbers in ways an onboard controller does not. That is tolerable for traffic that retries, and intolerable for the signalling that decides whether a node is alive. Cluster membership is latency-sensitive, not bandwidth-hungry; it wants reliability, and reliability is what the onboard NIC has.

The uplink to the internet is a **wireless bridge**, because the rack has no wired path to the household router — wrong side of the house, no spare ports, no coax. This matters less than it appears: only outbound traffic crosses it. Package retrieval, image pulls, upstream time, and alerts. Nothing internal ever leaves the two switches.

Power is a single UPS with all eight outlets allocated and no spare. The router cannot be on it — it is in a closet on a circuit outside the operator's control — which has one important consequence covered in §7.

### L1 — Hypervisor

Proxmox on all four nodes, clustered. Guest root disks live on **local NVMe**, not the NAS, which keeps a node's ability to shut itself down independent of shared storage.

The nodes support out-of-band management. Its state is unknown until verified, because that interface lives in firmware and is untouched by the operating-system reinstalls these machines have had. It gets claimed or disabled during the node build, never left inherited.

### L2 — Foundation

**FreeIPA** as the directory, on Rocky Linux, with a replica. It was chosen because it delivers four requirement families as one system — LDAP and Kerberos for host authentication, DNS for `asgard.home.arpa`, host-based access control and centralised sudo for authorization, and a replication story. The alternatives each meant assembling three or four components instead.

The cost is a deliberately **mixed-OS platform**: Debian-family for the hypervisor, RHEL-family for the directory guests, because the FreeIPA server is only genuinely supported there. Automation is written OS-family-aware from the first role rather than retrofitted.

FreeIPA is also the **time authority**. Kerberos fails outright at roughly five minutes of clock skew, and external time arrives over a wireless bridge that may be down. So every host synchronises to the directory, and the directory alone synchronises upstream when it can. Internal time stays coherent regardless of the uplink.

**step-ca** is the platform CA, and it lives here rather than in the cluster because the hypervisor and every host depend on it. FreeIPA's own integrated CA is scoped down to issuing only FreeIPA's internal certificates, which contains a known trap: a certificate-renewal role holder that goes merely *offline* rather than being properly decommissioned is never automatically replaced, after which the directory's own certificates expire silently.

### L3 — Platform

k3s with three control-plane guests, one per node, spread by enforceable placement rules rather than by intention. Bundled ingress and load-balancing are disabled in favour of MetalLB and Envoy Gateway.

That last choice was a reversal. The original selection was ingress-nginx, on transferability grounds — until version verification found it reached end-of-life in March 2026, repository read-only, no CVE patches. The transferability argument inverted: it became a dead skill and an unpatched surface. **Gateway API** is the successor standard, and Envoy Gateway is the vendor-neutral implementation whose data plane knowledge transfers furthest.

Two storage classes, both from the NAS: **NFS as the default** with ReadWriteMany, and **iSCSI as a second class** with block semantics. Both land on the same four spinning disks, so the second buys semantics rather than speed.

### L4 — Platform services

Everything else runs here as workloads: Keycloak, PostgreSQL under CloudNativePG, Redis, Harbor, Argo CD, the observability stack, and the secret store.

PostgreSQL is worth dwelling on, because its placement moved twice. NFS was excluded early — a database's durability model depends on precisely the locking and `fsync` guarantees NFS implements loosely. iSCSI looked like the fix until the NAS turned out to be HDD-only, which would have put database random I/O on spinning disks. The answer is **local-path NVMe inside the cluster**, managed by an operator that supplies streaming replication and automatic failover. Faster than the NAS, survives node loss, and stays in the Kubernetes model.

Its consequence: pods are pinned to nodes by local storage, which makes continuous write-ahead archiving to shared storage a precondition of running the database at all, not a backup concern to address later.

### L5 — Workloads

The operator's applications, deployed by reconciliation from the repository, published through Gateway API, authenticating against Keycloak with authorization driven by group claims. This is the layer the whole platform exists to serve.

## 4. Identity, end to end

One account, two protocols, one revocation.

The directory holds every account and group. Hosts authenticate against it over LDAP and Kerberos through SSSD. Keycloak federates to it read-mostly and holds only sessions, clients, and realm configuration — which means Keycloak can be rebuilt without touching identity data, and creating an account directly in Keycloak is prohibited.

Everything else becomes a relying party: the Kubernetes API, the hypervisor UI, the NAS, Grafana, Argo CD, and the operator's own applications. Services with no native OIDC support get an authenticating proxy in front rather than an exemption.

**Revocation is where honesty was required.** The appealing claim — disable one account, lose access everywhere, instantly — is false in three independent places:

- Cached host credentials let a disabled account keep authenticating while the directory is unreachable, so the cache needs an explicit maximum age
- The directory's account-lock attribute is **not mapped into Keycloak by any shipping mechanism**, and the obvious attribute mapper inverts its sense — so this must be built and tested, and until it is, disablement never reaches the IdP at all
- The hypervisor mints its own ticket lasting roughly two hours after OIDC login, with no back-channel logout

So revocation stays driven by one action against one account, but propagation is **bounded rather than immediate**, with each bound recorded per relying party. A bound that is not written down is a defect.

## 5. Storage and its one exception

The NAS serves home directories over NFS — the same `/home` on every host, which is what makes nodes interchangeable — and provisions persistent volumes in both classes.

Mounts are `hard`, so an interruption blocks rather than silently corrupting; integrity outranks availability. The requirement that storage loss degrade rather than hang is met by **automounting**, so shares are absent rather than wedged when unreachable, and by keeping break-glass home directories outside every NFS-managed path.

That last point is subtle enough to have been a genuine defect earlier in design. A break-glass account whose home sits under the NFS mount is shadowed while the mount is active and unreachable while it hangs — so emergency access fails during precisely the emergency it exists for. Local is necessary but not sufficient; the path must be one NFS never manages.

Numeric identity is pinned in the repository. NFS authorises by UID, not by name, so a rebuilt directory issuing different numbers would leave every home directory and volume intact but unreachable — a failure that surfaces long after the rebuild was declared successful.

## 6. Certificates

One issuance protocol: **ACME**, everywhere. The hypervisor supports it natively, cert-manager speaks it, hosts and the NAS use standard clients. That single choice turns "renew certificates automatically across four very different consumers" from a per-consumer chore into a solved problem, and manual certificate installation is prohibited precisely so nobody reintroduces the chore.

## 7. What happens when things fail

The most useful section for the reader who is mid-incident.

**The NAS dies.** The worst case, and the largest knowingly accepted risk. It holds home directories, persistent volumes, *and* the backups — so its loss is unrecoverable for bulk data. Mitigated only partially: the repository is on GitHub, and directory data, database dumps, the CA root key and break-glass credentials are held encrypted on an offline SSD. Identity, CA and databases survive; volumes do not. **The independent backup target is the highest-value v2 purchase.**

**The directory dies.** SSO stops, so every relying party stops — `kubectl`, Grafana, the hypervisor UI, applications. Administrative access survives: break-glass accounts on every host with local homes, the hypervisor's own local realm, cached credentials for anyone who has logged in before. The replica exists so that patching the directory is not a platform-wide outage.

**A node dies.** Three remain, which is why total committed memory is capped at 90 GB of 128 — three nodes provide 96. Control-plane members and directory replicas are placed so no two share a node, enforced in configuration rather than by convention.

**Kubernetes dies.** Identity, DNS, time and certificates continue, because they are below it. The cluster remains administrable through its static credential. Applications are down; the platform is not.

**Power fails.** The UPS gives an estimated twelve to fifteen minutes. Ordering is achieved by **tuned delay, not coordination** — the storage appliance signals UPS state but does not wait for its clients. Workloads drain, guests stop, nodes stop, the NAS last, with a margin measured by drill and recorded as a number. And because the router is beyond the UPS's reach, no outbound notification can leave during a whole-house outage — which promotes the external dead-man's switch from a nicety to the only alerting path that survives.

**The uplink dies.** Nothing internal is affected. Package updates and image pulls stop; internal time stays coherent because the directory is the authority; alerts cannot leave.

## 8. Build sequence

A **walking skeleton** first — a thin vertical slice exercising every integration seam while each is still cheap to change, because integration seams are where this class of build fails. Nothing in the skeleton is redundant or complete.

| | Epic | Note |
| --- | --- | --- |
| S1 | Repository and procedure standard | The dual-form contract and the Procedure Index |
| S2 | Network, cluster, break-glass | Break-glass comes *before* directory login; firmware management claimed here. Name resolution is provisional |
| S3 | Shared storage, one share | |
| S4 | Directory, DNS, time, network login | `asgard.home.arpa` becomes real; provisional resolution retired |
| S5 | Platform CA | Before the cluster, because it runs outside it |
| S6 | Kubernetes, minimal | |
| S7 | IdP and federation | After the cluster, because it runs inside it |
| S8 | Reference application | **Gate:** the operator's own code, deployed from the repository, authorizing from token claims |

Reaching S8 proves every seam: hypervisor to storage, storage to Kubernetes, directory to IdP, IdP to Kubernetes, IdP to application, repository to running workload.

Then eleven deepening epics add redundancy, observability, secrets, power orchestration, backup with verified restores, and SSO breadth — ending with a **destructive rebuild drill** that proves the documentation rather than the architecture.

## 9. Decisions worth remembering

Four reversals, each driven by a finding rather than a preference:

**ingress-nginx → Envoy Gateway.** Discovered end-of-life during version verification. The lesson recorded as AD-20: component maintenance status is a design input, checked before an epic depends on one, not an incident discovered later.

**PostgreSQL: VM → in-cluster.** Two constraints in sequence — NFS semantics, then HDD-only storage — eliminated the obvious options until the operator-managed local-NVMe answer proved better than the original on every axis.

**Access point: cut → redeployed as the uplink.** Removed as a redundant household device, then reinstated as the platform's only path to the internet when the physical topology turned out to forbid a cable.

**Out-of-band management: absent → present but unverified.** Believed missing, then found supported, then correctly challenged on whether an OS reinstall had cleared it. It had not — that interface lives in firmware — so the rule became positive verification rather than inference in either direction.

## 10. Accepted gaps

Recorded so they are decisions rather than oversights:

- **No backup independent of the NAS.** The largest risk in the design. Deferred to v2.
- **No network segmentation.** Both switches are flat; gateway bypass prevention is convention, not enforcement.
- **No remote access.** Every repair requires physical presence. Cut deliberately, and it removed a whole class of circular dependency with it.
- **Drives permitted, not validated.** Absent from the appliance's compatibility list; no vendor support path for a drive fault, which raises the value of tested restores.
- **A fifth node is blocked** before capacity by two limits: no spare UPS outlet, and the appliance's UPS-client roster caps at five.
