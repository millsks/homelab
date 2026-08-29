---
title: Project Asgard — Diagram Set
status: draft
created: 2026-08-28
updated: 2026-08-28
companion_to: ARCHITECTURE-SPINE.md
---

# Project Asgard — Diagram Set

Views of the same system at different altitudes. Each carries a rule or a mechanism that prose states less clearly; none is decorative. Where a diagram and the spine disagree, the spine wins.

## 1. Context — who and what touches Asgard

```mermaid
graph TB
  OP["Operator<br/><i>single administrator</i>"]
  HH["Household devices<br/><i>share the LAN, use nothing</i>"]
  GH["GitHub<br/><i>Repository, container base images</i>"]
  PUSH["Push service + dead-man's switch<br/><i>outbound alerting</i>"]
  UP["Upstream packages, images, time"]
  ASG["<b>ASGARD</b><br/>private platform<br/><i>asgard.home.arpa</i>"]

  OP -->|"SSH, kubectl, browser<br/>LAN only"| ASG
  ASG -->|"outbound only"| GH
  ASG -->|"outbound only"| PUSH
  ASG -->|"outbound only"| UP
  HH -.->|"no interaction"| ASG
  PUSH -->|"phone, over cellular"| OP
```

**The rule this carries:** every arrow leaving Asgard is outbound. There is no inbound path — no VPN, no tunnel, no published service. The only route that reaches the operator when the platform is down runs *through* an external service, which is why the dead-man's switch is load-bearing rather than supplementary.

## 2. Physical and network topology

```mermaid
graph LR
  NET(("Internet"))
  RTR["Household router<br/><b>not on UPS</b><br/><i>closet, far side of house</i>"]
  BR["Wireless bridge<br/><i>AP in client mode</i>"]
  DSW["Data switch · 10-port<br/><i>6 of 10 used</i>"]
  MSW["Membership switch · 5-port<br/><b>no uplink, no gateway</b>"]
  N1["odin"]
  N2["thor"]
  N3["heimdall"]
  N4["tyr"]
  NAS["nidavellir<br/><i>DS925+ · SHR-2 · ~28 TB</i>"]

  NET --- RTR
  RTR -. "wireless<br/>outbound only" .- BR
  BR --- DSW
  DSW ---|"2.5 GbE"| N1
  DSW ---|"2.5 GbE"| N2
  DSW ---|"2.5 GbE"| N3
  DSW ---|"2.5 GbE"| N4
  DSW ---|"2.5 GbE"| NAS
  MSW ===|"1 GbE onboard"| N1
  MSW ===|"1 GbE onboard"| N2
  MSW ===|"1 GbE onboard"| N3
  MSW ===|"1 GbE onboard"| N4
```

**The rule this carries:** two traffic classes never share a link *or* a switch. Bold edges are cluster membership on the onboard NICs; thin edges are storage, pods, backups and outbound on the USB 2.5 GbE adapters. The membership switch deliberately connects to nothing else — joining the two switches would return membership to shared fabric and forfeit the separation.

**The trap it shows:** the router sits outside the UPS boundary, so a whole-house power failure severs every outbound path at once.

## 3. Layers and placement

```mermaid
graph TB
  subgraph L5["L5 · Workloads"]
    APP["the operator's applications"]
  end
  subgraph L4["L4 · Platform services — in-cluster"]
    FOR["forseti · IdP"]
    FAF["fafnir · PostgreSQL<br/><i>local NVMe</i>"]
    RAT["ratatoskr · cache"]
    OBS["huginn · muninn · gjallarhorn"]
    SUP["brokkr · sindri · Argo CD"]
    AND["andvari · secrets"]
  end
  subgraph L3["L3 · Yggdrasil"]
    CP["urd · verdandi · skuld<br/><i>one per node</i>"]
    WK["brynhildr · sigrun · gondul"]
    GW["MetalLB + Envoy Gateway"]
  end
  subgraph L2["L2 · Foundation — outside the cluster"]
    MIM["mimir + replica<br/><i>LDAP · Kerberos · DNS · time</i>"]
    DRA["draupnir · platform CA<br/><i>ACME</i>"]
  end
  subgraph L1["L1 · Proxmox cluster"]
    PVE["odin · thor · heimdall · tyr"]
  end
  subgraph L0["L0 · Power and fabric"]
    PHY["UPS · switches · NAS"]
  end

  L5 --> L4 --> L3 --> L2 --> L1 --> L0
  FOR -. "federates<br/>read-mostly" .-> MIM
  L3 -. "OIDC — enhancement only,<br/>static credential is the fallback" .-> FOR
```

**The rule this carries:** solid arrows are permitted dependencies and point only downward. The two dotted arrows are the exceptions that prove it — Keycloak federating *down* to the directory is fine, and Kubernetes using Keycloak is an enhancement with a static-credential fallback, never a dependency. Only two services sit outside the cluster, and each met a named test.

## 4. Identity — one account, two protocols

```mermaid
sequenceDiagram
  autonumber
  actor OP as Operator
  participant H as Node or Guest
  participant M as mimir · Directory
  participant F as forseti · IdP
  participant RP as Relying Party

  Note over M: single authoritative account store

  OP->>H: SSH with directory account
  H->>M: LDAP / Kerberos
  M-->>H: groups, sudo rules
  Note over H: cached, with an explicit maximum age —<br/>an unbounded cache would outlive revocation

  OP->>RP: open service
  RP->>F: OIDC redirect
  F->>M: federate account and groups
  M-->>F: identity
  F-->>RP: token · 15 min · group claims

  rect rgba(200,80,80,0.12)
    Note over M,F: account-lock must be MAPPED into the IdP.<br/>No shipping mapper does this, and the obvious one inverts.<br/>Unmapped, disablement never propagates at all.
  end
```

**The mechanism this carries:** the directory is the only account store; Keycloak holds sessions and clients, never identity, so it can be rebuilt without loss. Revocation is one action with bounded — not instant — propagation.

## 5. Certificates — one protocol, four consumers

```mermaid
graph LR
  DRA["draupnir · step-ca<br/><i>ACME server, outside the cluster</i>"]
  PVE["Proxmox<br/><i>native ACME</i>"]
  CM["cert-manager<br/><i>in-cluster</i>"]
  HOST["Nodes and Guests<br/><i>acme.sh</i>"]
  NAS["nidavellir"]
  GW["Gateway listeners"]
  WL["Workloads"]

  DRA -->|ACME| PVE
  DRA -->|ACME| CM
  DRA -->|ACME| HOST
  DRA -->|ACME| NAS
  CM --> GW
  CM --> WL
```

**The rule this carries:** ACME is the *only* issuance path. Four consumers with nothing else in common all speak it, which turns automatic renewal from four bespoke problems into one. Manual installation is prohibited so the bespoke problems cannot creep back.

## 6. Storage placement by I/O class

```mermaid
graph TB
  Q{"What kind of I/O?"}
  Q -->|"database random I/O"| NVME["<b>Local NVMe</b><br/>guest disks · PostgreSQL<br/><i>via local-path</i>"]
  Q -->|"shared, multi-consumer"| NFS["<b>NFS — default class</b><br/>home directories<br/>general volumes<br/><i>ReadWriteMany</i>"]
  Q -->|"block semantics wanted"| ISCSI["<b>iSCSI — second class</b><br/><i>ReadWriteOnce</i>"]
  NFS --> NAS[("nidavellir<br/>4 × 14 TB spinning<br/>SHR-2")]
  ISCSI --> NAS
  NVME --> LOCAL[("node NVMe<br/>~3 TB usable")]
```

**The rule this carries:** placement follows I/O class, never convenience. The NAS is HDD-only, so *nothing* database-shaped lands there by any protocol — the exclusion is about the medium, not about NFS. Both NAS classes share the same spindles, so iSCSI buys semantics, not speed.

## 7. Ordered shutdown — margin, not handshake

```mermaid
sequenceDiagram
  autonumber
  participant U as UPS
  participant N as nidavellir<br/>(NUT server)
  participant K as Yggdrasil
  participant G as Guests
  participant P as Nodes

  U->>N: mains lost
  N->>P: state broadcast to clients
  Note over N,P: broadcast only — the appliance does not<br/>wait for, or know about, its clients

  K->>K: drain workloads (~60 s)
  G->>G: stop guests (~60 s)
  P->>P: nodes power off (~60 s)
  Note over P: nodes act at ~3 min on battery

  N->>N: enters protective mode at ~10 min
  Note over N: the ~7 min gap IS the safety mechanism.<br/>Measured by drill, recorded as a number, re-measured<br/>after battery replacement.
```

**The mechanism this carries:** there is no coordination to rely on. Ordering is produced by configured delays sized larger than the measured shutdown time — a race engineered to be unlosable. The drill exists to prove the margin, not to confirm a guarantee.

## 8. Build order — walking skeleton

```mermaid
graph LR
  S1["S1<br/>Repository<br/>+ Procedures"] --> S2["S2<br/>Network · Cluster<br/><b>Break-glass</b>"]
  S2 --> S3["S3<br/>Storage"]
  S3 --> S4["S4<br/>Directory · DNS<br/>time · login"]
  S4 --> S5["S5<br/>Platform CA"]
  S5 --> S6["S6<br/>Kubernetes"]
  S6 --> S7["S7<br/>IdP +<br/>federation"]
  S7 --> S8["S8<br/><b>Reference app</b><br/>GATE"]
```

**The constraints this carries:** break-glass precedes directory login, or a lockout has no independent way in. Name resolution is provisional until S4 delivers the resolver that serves the domain. The CA precedes the cluster because it lives outside it; the IdP follows the cluster because it lives inside it. Reaching S8 proves every integration seam while each is still cheap to change.
