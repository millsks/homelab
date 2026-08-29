---
title: "Product Brief: Project Asgard — Homelab Platform"
status: approved
created: 2026-08-28
updated: 2026-08-28
---

# Product Brief: Project Asgard

## Executive Summary

Project Asgard turns four HP EliteDesk mini PCs, a Synology NAS, and a 10-port switch into a small but architecturally honest private cloud — one that behaves like a corporate environment rather than a pile of self-hosted containers. It runs a Kubernetes cluster for containerized applications, a set of stateful backing services (PostgreSQL, Redis, Grafana), and a centralized identity plane where a single directory backs both Linux network logins and OIDC single sign-on for every service and application.

The distinguishing goal is not the running services. It is the **reproducibility of the whole thing**. Every node, VM, and service is described by configuration stored in GitHub, and every build step exists twice: as a runbook a human can follow at a keyboard, and as automation that produces the identical result unattended. A node that fails, or that gets deliberately destroyed to prove the point, returns to service from source control.

That dual-form documentation is what makes the lab a durable learning instrument rather than a fragile artifact. The operator can rebuild it, break it on purpose, and — most importantly — develop applications against an identity provider that behaves like the PingFederate deployments those applications will eventually meet in production.

## Purpose

This lab exists for three overlapping reasons, and the mix matters because it settles trade-offs downstream:

- **Enterprise simulator.** A faithful small-scale copy of a corporate environment — centralized directory, SSO, RBAC, GitOps, observability — to practice on and break safely. When a choice arises between the convenient answer and the answer a real organization would give, this purpose argues for the latter.
- **Skills investment.** Deliberate, hands-on depth in Kubernetes, GitOps, infrastructure-as-code, OIDC/OAuth2, and platform operations. This purpose sometimes argues for choosing the *harder* option on purpose.
- **Application platform.** A production-shaped home for the operator's own software, with a real CI/CD path and, critically, a real authorization server to develop against.

Keycloak is the clearest expression of all three at once: it is the OIDC/PingFed stand-in the operator's applications need, it is the enterprise SSO pattern worth learning, and it is the piece that binds every other service into one coherent identity story.

## The Problem

Ordinary homelabs accrete. A service gets installed by hand at 11pm, works, and is never documented. Six months later nobody remembers which config file was edited, credentials live in a text file, and every service has its own local password. The lab becomes something to be afraid of rather than something to experiment on — precisely inverting its purpose.

Three specific pains follow:

1. **No reproducibility.** A failed disk or a bad upgrade means archaeology, not recovery. Fear of breaking things suppresses the experimentation the lab was built for.
2. **Fragmented identity.** Every node has its own local users; every service has its own login. There is no way to practice the authentication and authorization patterns that real applications require, because there is nothing to practice against.
3. **Fragmented storage.** Home directories and working data are pinned to whichever node they were created on, so nodes are not interchangeable and work cannot follow the operator between machines.

## The Solution

Four layers, built in dependency order:

**Foundation.** Proxmox VE on all four EliteDesks, clustered. Kubernetes nodes, service VMs, and the identity servers all become guests. This buys snapshots before every risky change, and it makes "rebuild a node" a routine operation rather than an ordeal — which is the stated goal, so the foundation is chosen to serve it.

**Identity.** An LDAP directory as the single user store, federated into Keycloak. Linux hosts authenticate against it via SSSD; every service authenticates against Keycloak via OIDC. One account, one password, one place to disable it. This deliberately extends past application login: the Kubernetes API server, Proxmox, Grafana, Argo CD, and the NAS itself all become OIDC clients, and services with no native auth get an `oauth2-proxy` forward-auth gate in front of them.

**Storage.** The Synology serves NFS for shared home directories — so any node presents the same `/home` — and provisions Kubernetes persistent volumes. One documented exception: PostgreSQL does not run on NFS, because Postgres depends on precisely the locking and `fsync` durability guarantees NFS is loosest about. It gets local NVMe or an iSCSI block LUN.

**Platform.** A Kubernetes cluster for containerized applications, GitOps-driven from this repository, with an observability stack and a CI path from source to running workload.

Wrapping all four: documentation where every procedure appears as both a human runbook and the automation that performs it, with the automation treated as the source of truth and the runbook as its readable explanation.

## Who This Serves

A single operator — an experienced software engineer building the lab to develop against, to learn on, and to break. There are no other human users, and that is deliberate: the enterprise machinery here exists for **fidelity**, not for scale. A design that would be over-engineering for a household is exactly right for a simulator.

The secondary consumer is the operator six months from now, mid-outage, who needs the rebuild procedure to be correct and complete. Much of the documentation standard is set by that reader rather than the first one.

## Naming Convention

Norse mythology, applied as a system rather than a list: **realms name tiers, beings name instances.** The scheme must survive growth, so it is defined with room for expansion rather than exactly enough names for today's four nodes. `asgard` is the platform and DNS domain; the Æsir name physical hosts; the Norns name the Kubernetes control plane they tend; Valkyries carry workloads. Full registry in the addendum.

## Success Criteria

1. **Rebuild from source.** Any node can be destroyed and restored to full cluster membership from GitHub-stored configuration, with no undocumented manual steps. Verified by actually doing it, not by believing it.
2. **One identity.** A single directory account logs into every node over SSH and into every service via SSO. Disabling that one account revokes all of it.
3. **Application proof.** An application the operator wrote, deployed to Kubernetes through the GitOps path, authenticates users against Keycloak via OIDC and enforces authorization from token claims.
4. **Portable home.** The same `/home` contents appear on every node.
5. **Dual-form documentation.** Every build procedure exists as both a runbook and its automation, and following the runbook by hand produces a node the automation would consider already converged.
6. **Survivable.** The lab can be recovered from backup after a deliberate destructive test, and the operator can still get in when the directory is down.

## Scope

**In scope for v1:**

- Proxmox VE cluster across all four nodes
- LDAP directory + Keycloak, with SSSD-based network login on every host
- NFS home directories and Kubernetes persistent volumes from the Synology
- A Kubernetes cluster with GitOps-driven deployment
- PostgreSQL, Redis, Grafana, and a metrics/logging stack
- Internal certificate authority for TLS
- Secrets management, with break-glass credentials held outside the lab
- Backups, with a tested restore
- UPS with NUT-orchestrated ordered shutdown, verified by a live power-loss drill
- Wired-only networking for all Nodes and the NAS, wireless disabled
- The full documentation set: runbooks plus automation, in this repository

**Explicitly out of scope for v1:**

- **VLAN segmentation and a dedicated firewall.** The existing ISP router stays; the lab lives on the flat LAN. Deferred, not rejected.
- **Anything internet-facing, and remote access of any kind.** No public DNS, no ACME certificates, no inbound exposure, no VPN. Operating Asgard means being on the local network. This keeps the security surface minimal, lets an internal CA suffice, and removes the circular dependency in which an identity-dependent VPN would make an IdP failure unrecoverable from outside.
- **High availability as a goal in itself.** Where HA is cheap and instructive it is taken; where it costs a second Postgres cluster it is not.
- **Ceph or other node-replicated storage.** The Synology is the storage answer for v1.
- **Service mesh.** Deferred until there is an application that needs one.
- **Hardware purchases**, beyond the acknowledged gaps below.

## Constraints and Known Risks

| | Detail |
|---|---|
| **Compute ceiling** | 16 cores / 32 threads, 128 GB RAM total across four 35 W nodes. The stated stack fits with roughly 25–30 GB headroom. Prometheus retention and Keycloak's JVM are the two things that will consume it. |
| **Network ceiling** | Nodes are 1 GbE onboard, so all storage traffic caps near 110 MB/s. The switch's 2.5 G and 10 G ports are unusable without added NICs. |
| **Out-of-band management, state unverified** | Corrected during architecture review: the EliteDesks support AMD DASH (remote power, boot, firmware, console), so lockout recovery is better than first assessed. Its current state is unknown and cannot be inferred — the interface lives in firmware and is untouched by the OS reinstalls these machines have had. Verified by port probe and firmware screen during the node build, then either claimed with escrowed credentials or deliberately disabled. |
| **Storage single point of failure** | Home directories and Kubernetes volumes both depend on one NAS. Accepted knowingly. |
| **Identity bootstrap** | Centralized login means the directory can lock the operator out of the hosts that run it. Mitigated by local emergency accounts, SSSD credential caching, and Proxmox's local realm. |
| **Power runtime** | UPS in scope (~320 W load, estimated ~12-15 min runtime, measured by Drill). That is a graceful-shutdown budget, not a ride-out budget. The full stack must power down inside ~5 min, NAS last. |
| **Nodes ship Windows** | All four are reimaged. Nothing on them is preserved. |
| **Drives permitted, not validated** | The WD Red Pro drives are absent from the DS925+ compatibility list, which carries only vendor-branded entries. The DSM 7.3 policy reversal permits third-party drives; it does not validate these. Consequence: no vendor support path for a drive-related fault, which raises the value of tested restores. |

## Vision

Two to three years out, Asgard is the place the operator's software is born. New applications get a repository, a pipeline, an OIDC client, and a URL without anyone thinking about infrastructure. The lab is trusted enough to be broken on purpose — a node wiped on a Saturday and rebuilt from GitHub before lunch — because that operation has been proven often enough to be boring.

The documentation outlives the hardware. When the EliteDesks are replaced, the runbooks and automation carry forward to whatever comes next, because they describe a platform rather than four specific machines.

## Resolved Foundation Decisions

Settled during discovery; these are inputs to the PRD, not open items.

| Decision | Choice | Note |
|---|---|---|
| DNS domain | `asgard.home.arpa` | RFC 8375-reserved for home networks. No registration, no leakage to public DNS. Internal CA (`draupnir`) issues all TLS. |
| Kubernetes distribution | **k3s** | Low overhead on 32 GB nodes, HA via 3 embedded-etcd servers. Bundled Traefik and ServiceLB are a deliberate keep-or-replace decision for architecture. |
| Configuration management | **Ansible** | Node and VM configuration; the automation half of every runbook. |
| Infrastructure provisioning | **OpenTofu** | Proxmox VM and resource provisioning. |
| Power protection | **APC Smart-UPS SMT1500C** | 1440 VA / 1000 W, pure sine wave, 8 outlets all battery-backed, hot-swappable battery. ~320 W load, ~3.1x headroom, ~12-15 min runtime. All 8 outlets allocated, no spare. |

### Deferred to architecture

1. **Directory product** - FreeIPA, LLDAP + SSSD, or Samba AD DC. Leaning FreeIPA: it collapses LDAP, Kerberos, the internal CA, host-based access control, and centralized sudo rules into one system.
2. **PostgreSQL placement** - VM on local NVMe, or iSCSI LUN via `synology-csi`. Both satisfy the off-NFS carve-out.
3. **Synology RAID level** - SHR-1 (~42 TB, single-drive tolerance) or SHR-2 (~28 TB, dual-drive). With 14 TB drives, a second failure during a long rebuild is a realistic risk, not a theoretical one.
4. **k3s ingress** - keep bundled Traefik or replace it.
