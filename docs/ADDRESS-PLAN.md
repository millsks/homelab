# Address Plan

Governed by **AD-22** and **AD-4**. This is the declaring mechanism for the resource class
[`docs/OWNERSHIP.md`](OWNERSHIP.md) calls *"Address plan (static assignments, membership segment,
DHCP pool boundaries)"*, and the human form of `PROC-ADDRESS-PLAN` in
[`PROCEDURE-INDEX.md`](../PROCEDURE-INDEX.md).

**Addresses are declared here and never discovered from running systems.** A plan reconstructed by
reading what hosts happen to answer is not a plan; it is a description of an accident, and it
survives exactly until the accident changes. Every later story — the hypervisor build, the
directory, the cluster, the gateway — reads addresses out of this file. Nothing writes addresses
back into it from a running system.

Every address in this file is a *commitment*, not an observation. Most of them are not configured
anywhere yet: this story declares, story 2.3 applies. An address that is declared and not yet
configured is normal. An address that is configured and not declared is a defect.

## Why this document exists

Without it, each story invents the addresses it needs, and the first collision is found by a device
that stops working. A plan written after the fact cannot prevent that; it can only describe it.
Writing it first costs one document and turns a whole class of outage into a failing check.

## Scope and boundaries

**Declares:**

- The two network segments, their network addresses, masks, and gateways.
- Every address range in both segments, with its purpose stated and its type declared.
- Every static address assigned today, what holds it, on which physical interface, and what class
  of traffic that interface carries.
- The growth reservations, named — so that a future address comes out of a decision rather than out
  of a gap nobody had noticed.

**Does not declare:**

- **The cabling map** — which cable lands in which switch port. That is `PROC-HYPERVISOR-INSTALL`'s,
  declared in `runbooks/l0-physical/`. This file names the interface *on the host*, which is what
  makes an address traceable to a physical port; it does not name the port at the other end.
- **In-guest and in-host interface configuration** — the files and commands that make a host
  actually carry the address below. That is `PROC-NODE-BUILD`'s (story 2.3, `Ansible`). This story
  declares; it configures nothing.
- **DNS records** — `PROC-DNS-ZONE`'s (story 4.3). The directory does not exist yet, and a name
  cannot be declared against a zone that has not been created.
- **The contents of the load-balancer pool** — `PROC-LB-ADDRESS-POOL`'s (story 6.4). This file
  reserves the range that pool draws from and states its boundaries; which service takes which
  address inside it is in-cluster state.
- **The household DHCP pool's configuration.** The pool boundaries are *recorded* here because
  every static address has to sit outside them; the router that hands out those leases is
  `Runbook`-owned and is not configured from this Repository.

## Confirmed facts

Measured from the live network, not assumed. Everything below is derived from these.

| Fact | Value |
| --- | --- |
| Household LAN | `192.168.86.0/24`, mask `255.255.255.0`, gateway `192.168.86.1` |
| Household DHCP pool | `192.168.86.100` – `192.168.86.200`, leaving `.2`–`.99` and `.201`–`.254` free |
| Membership segment | `172.16.8.0/24`, isolated, no gateway |
| Router and modem location | A closet, and **not** on the UPS |
| Uplink from the rack to the household router | The TL-WA3001 wireless bridge, in client-bridge mode. There is no wired path |

**Why `172.16.8.0/24` and not something more obvious.** It is clear of the Kubernetes
distribution's default pod and service ranges, which live in `10.42/16` and `10.43/16`, and it sits
below the container runtime's default bridge pool at `172.17/16`. A membership segment that
overlaps either would present as intermittent cluster-membership failure whose cause is a routing
table, which is among the least pleasant things to diagnose. The choice is deliberate and is
recorded so a later renumbering knows what it has to preserve.

**The uplink is a wireless bridge, and it is the only one.** The rack sits on the opposite side of the house
from the household router: there is no spare wired path and no coaxial for MoCA, so the TL-WA3001 in
client-bridge mode carries every byte that leaves the platform. It is recorded here as an allocation rather
than as background because it is a single point of failure on the outbound path and because a reader who
believes the rack is wired will mis-diagnose the first outage. It takes a management address from
`data-infrastructure` so that it can be configured and confirmed up.

**The router's location is recorded because it contradicts an assumption made elsewhere.** The
power design allocates UPS outlet 8 to the household router so that an outbound alert can leave the
premises during the event that triggers it. The router is in a closet and is not on the UPS, so
that allocation is currently a plan rather than a fact. It is not this story's to resolve — it is
recorded in the deferred-work ledger and belongs to story 15.1.

## How to read this document

Four tables below are parsed by `pixi run audit`. They are the declaration; the prose around them
explains it and is not read by anything.

- **Segments** — the two networks, and which of them is isolated.
- **Address ranges** — every address in both segments belongs to exactly one range, and every range
  states its purpose. The ranges *tile* their segment: the audit fails on a gap and on an overlap,
  because a gap nobody named is a gap someone fills by accident.
- **Allocations** — every static address assigned today.
- **Kinds** — the closed enumeration the Allocations table's `Kind` column draws from.

### Two conventions worth knowing before reading the tables

**A Node's last octet is identical on both segments.** `odin` is `.11` on the data segment and
`.11` on the membership segment. It costs nothing, makes the plan memorable, and turns a whole
class of transposition mistake into something a reader notices immediately rather than something a
packet capture finds later.

**Membership stays on the onboard interfaces; bulk traffic takes the adapters.** The USB 2.5 GbE
adapters are faster and less reliable — USB Ethernet resets and renumbers in ways an onboard
controller does not. That is acceptable for storage traffic, which retries. It is not acceptable
for the signalling that decides whether a Node is alive. So the faster path carries the traffic that
can tolerate a hiccup, and the slower one carries the traffic that cannot. This is the inverse of
the naive allocation, and it is the reason the `Interface` column is part of the declaration rather
than a note.

## Segments

The `Isolated` column is load-bearing rather than descriptive: the audit reads it, and a segment
marked `yes` that declares a gateway — or that carries an allocation of kind `gateway` — fails the
check. The isolation *is* the point of the second segment, so it is stated in a form a machine can
disagree with.

| Segment | Network | Mask | Gateway | Isolated | Purpose |
| --- | --- | --- | --- | --- | --- |
| `data` | `192.168.86.0/24` | `255.255.255.0` | `192.168.86.1` | no | The household LAN. Carries storage, workload, and outbound traffic. Reached from the rack over the wireless bridge at `192.168.86.2`, which is the platform's only uplink. Shared with household devices, which is why the DHCP pool below is a hard boundary rather than a courtesy. |
| `membership` | `172.16.8.0/24` | `255.255.255.0` | none — no route off-segment | yes | Cluster membership signalling only. No uplink, no gateway, no path to the internet. Connecting it to the data switch would return membership to shared fabric and forfeit the separation entirely. |

## Address ranges

Every address in each segment belongs to exactly one range. Three types:

| Type | Means |
| --- | --- |
| `allocatable` | Addresses may be assigned from here by the story that needs one. |
| `dhcp-pool` | The household router hands these out. **No static address may fall inside one**; an address inside it will eventually be handed to a phone. |
| `reserved` | Held. An address here is not free space — taking one is a decision that edits this table in the same change. Network and broadcast addresses are reserved too, so that they are unassignable by declaration rather than by convention. |

A misspelled `Type` is safe by construction: anything that is neither `allocatable` nor `dhcp-pool`
is treated as `reserved`, so a typo makes the check stricter and never silent. The `Kind` column in
the Allocations table does not have that property, which is why it — and not this one — carries an
enumeration check.

| Range | Segment | First | Last | Type | Purpose |
| --- | --- | --- | --- | --- | --- |
| `data-network` | `data` | `192.168.86.0` | `192.168.86.0` | `reserved` | The network address. Not assignable. |
| `data-edge` | `data` | `192.168.86.1` | `192.168.86.1` | `allocatable` | The household router. Outside the platform's declarative boundary, recorded so it is not mistaken for unowned. |
| `data-infrastructure` | `data` | `192.168.86.2` | `192.168.86.5` | `allocatable` | Network infrastructure sitting between the household router and the hosts. The wireless bridge lives here: it is the platform's only uplink, and it needs a management address both to be configured and to be confirmed up. |
| `data-infrastructure-growth` | `data` | `192.168.86.6` | `192.168.86.9` | `reserved` | Growth: further network equipment that later needs a static address — a managed data switch, a second uplink. |
| `data-physical` | `data` | `192.168.86.10` | `192.168.86.19` | `allocatable` | Physical hosts: the storage appliance, and each Node's bulk-traffic interface. |
| `data-physical-growth` | `data` | `192.168.86.20` | `192.168.86.29` | `reserved` | Growth: a fifth Node, and a second appliance link. Both are constrained by other things — the UPS has no spare outlet and the membership switch caps at five clients — but the address plan must not be a third constraint. |
| `data-guests` | `data` | `192.168.86.30` | `192.168.86.99` | `allocatable` | Guests. Seventy addresses against a capacity model that commits nine Guests. Each Guest's address is assigned by the story that builds it, and lands in this table in the same change. |
| `data-dhcp` | `data` | `192.168.86.100` | `192.168.86.200` | `dhcp-pool` | The household router's DHCP pool, measured from the live network. Recorded here because every static address has to sit outside it. |
| `data-service` | `data` | `192.168.86.201` | `192.168.86.250` | `allocatable` | The Kubernetes load-balancer address pool (story 6.4). This file declares the range and its boundaries; which service takes which address inside it is in-cluster state. |
| `data-service-growth` | `data` | `192.168.86.251` | `192.168.86.254` | `reserved` | Growth: headroom above the load-balancer pool. |
| `data-broadcast` | `data` | `192.168.86.255` | `192.168.86.255` | `reserved` | The broadcast address. Not assignable. |
| `membership-network` | `membership` | `172.16.8.0` | `172.16.8.0` | `reserved` | The network address. Not assignable. |
| `membership-no-gateway` | `membership` | `172.16.8.1` | `172.16.8.1` | `reserved` | **Deliberately empty.** `.1` is where a reader's hand reaches for a gateway. Naming the range keeps that reach from landing on free space, and an allocation here fails the check twice — once as a consumed reservation, and again as a route on an isolated segment if it carries the `gateway` kind. |
| `membership-infrastructure` | `membership` | `172.16.8.2` | `172.16.8.9` | `allocatable` | The membership switch's management address, and anything else that must be reachable on this segment without being a Node. |
| `membership-nodes` | `membership` | `172.16.8.10` | `172.16.8.19` | `allocatable` | Node membership interfaces. Deliberately the same offsets as `data-physical`, so a Node's last octet is identical on both segments. |
| `membership-growth` | `membership` | `172.16.8.20` | `172.16.8.29` | `reserved` | Growth: a fifth Node's membership interface, mirroring `data-physical-growth`. |
| `membership-unused` | `membership` | `172.16.8.30` | `172.16.8.254` | `reserved` | Unused, and expected to stay that way. The segment carries one kind of traffic between at most five hosts; a `/24` is far more space than it needs. Declared as one reserved range rather than left blank so that the segment is fully accounted for. |
| `membership-broadcast` | `membership` | `172.16.8.255` | `172.16.8.255` | `reserved` | The broadcast address. Not assignable. |

## Allocations

One row per static address. The `Interface` column names the interface **on the holder**, which is
what lets a reader go from an address to a physical port without guessing; the port at the other
end of the cable belongs to the cabling map, not here.

| Address | Segment | Holds | Kind | Interface | Traffic class | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `192.168.86.1` | `data` | `household-router` | `gateway` | The router's own LAN interface | Outbound only; the uplink carries no inbound path | Google WiFi. Declared, not configured from this Repository. |
| `192.168.86.2` | `data` | `wireless-bridge` | `network device` | Its own management interface, in client-bridge mode | Every byte that leaves the platform | TP-Link TL-WA3001, client-bridge mode. **The platform's only uplink:** the rack is on the opposite side of the house from the household router, with no spare wired path and no coaxial for MoCA, so this bridge is how outbound traffic leaves. The address exists to configure it and to confirm it is up. |
| `192.168.86.10` | `data` | `nidavellir` | `appliance` | Onboard 2.5 GbE, port 1 | Storage (NFS, iSCSI) | Synology DS925+. Single-homed by design: it is not a cluster member and has no business on the membership segment. |
| `192.168.86.11` | `data` | `odin` | `node` | USB 2.5 GbE adapter | Storage, workload, outbound | |
| `192.168.86.12` | `data` | `thor` | `node` | USB 2.5 GbE adapter | Storage, workload, outbound | |
| `192.168.86.13` | `data` | `heimdall` | `node` | USB 2.5 GbE adapter | Storage, workload, outbound | |
| `192.168.86.14` | `data` | `tyr` | `node` | USB 2.5 GbE adapter | Storage, workload, outbound | |
| `172.16.8.2` | `membership` | `membership-switch` | `network device` | Its own management interface, reachable on any port | Switch management only | TP-Link Omada ES205G, run standalone and never controller-adopted. Reachable from a Node, unreachable from the household LAN. |
| `172.16.8.11` | `membership` | `odin` | `node` | Onboard 1 GbE (RJ45) | Cluster membership only | |
| `172.16.8.12` | `membership` | `thor` | `node` | Onboard 1 GbE (RJ45) | Cluster membership only | |
| `172.16.8.13` | `membership` | `heimdall` | `node` | Onboard 1 GbE (RJ45) | Cluster membership only | |
| `172.16.8.14` | `membership` | `tyr` | `node` | Onboard 1 GbE (RJ45) | Cluster membership only | |

Guests carry no rows yet, and that is the honest state: no Guest exists, and inventing addresses for
hosts whose owning stories are unstarted would produce declarations nobody has committed to. Each
lands in this table in the change that builds it, taking an address from `data-guests`.

## Kinds — a closed enumeration

The `Kind` column is parsed, so it is an enumeration rather than free text, for the same reason the
Owner column of [`docs/OWNERSHIP.md`](OWNERSHIP.md) is. A value outside this set is a defect the
audit names.

The asymmetry with the `Type` column above is deliberate and is why this check exists at all: a
misspelled `Type` makes the range checks *stricter*, but a misspelled `Kind` makes the dual-homing
rule silently skip the row. A typo that weakens a check has to be caught; a typo that strengthens
one does not.

| Kind | Means |
| --- | --- |
| `node` | A Proxmox Node. **Homed on every segment the plan declares: exactly one address on each.** A Node on one segment and not the other is a defect in either direction — both segments or neither. |
| `appliance` | A storage appliance. Single-homed on the data segment; it serves storage and takes no part in cluster membership. |
| `network device` | A switch, bridge, or router carrying an address only so that it can be managed and confirmed up. Single-homed on the segment it serves. Two hold one today, one per segment: the wireless bridge on `data` and the membership switch on `membership`. The switch is why the dual-homing rule is scoped to Nodes rather than to everything on the membership segment — it legitimately lives on that segment alone, and scoping the rule is better than carrying a per-entry exemption for it. |
| `gateway` | The default route off a segment. **Never legal on a segment marked isolated** — the audit fails on one. |
| `guest` | A virtual machine. Single-homed on the data segment. None exist yet; each is added by the story that builds it. |

If a later segment is added that some Nodes legitimately do not join, the `node` rule needs
refining rather than exempting, and the refinement belongs to the change that adds the segment.

## What the check enforces

`pixi run audit` parses the four tables above and reports these classes. Each fails loudly; none is
a warning, and none is auto-resolved — a collision has two claimants and picking one silently is
how the wrong one becomes permanent.

| Defect | Fires when |
| --- | --- |
| `address-plan-collision` | Two allocations claim one address on one segment. Both holders are named. |
| `address-plan-inside-dhcp-pool` | A static address falls inside a `dhcp-pool` range. The address and the pool are named. |
| `address-plan-reservation-consumed` | An allocation falls inside a `reserved` range. The reservation is named. Growth ranges are not free space. |
| `address-plan-node-on-one-segment` | A `node` holder does not carry exactly one address on every declared segment. The host and the missing segment are named. |
| `address-plan-route-on-isolated-segment` | A segment marked isolated declares a gateway, or carries an allocation of kind `gateway`. |
| `address-plan-illegal-kind` | An allocation's `Kind` is outside the closed enumeration above. |
| `address-plan-range-coverage` | The ranges declared for a segment do not tile it exactly — a gap, an overlap, a range outside its own segment, or one whose bounds do not parse or run backwards. |
| `address-plan-address-in-no-declared-range` | An allocation's address does not parse, names a segment this file does not declare, or falls in no declared range. |

## What this document cannot yet verify

[`docs/OWNERSHIP.md`](OWNERSHIP.md) names this class's verification as *declared addresses
reconciled against Directory DNS and against what hosts actually answer*. **Neither half of that is
available today**, and saying so is more useful than quietly implementing something weaker and
calling it done:

- Reconciliation against DNS needs a zone, which story 4.3 creates.
- Reconciliation against what hosts answer needs hosts that answer, which story 2.3 builds.

What is checkable today is **internal consistency**, and that is what the list above enforces. The
reconciliation check belongs to the first story that has something to reconcile against; it is
recorded in the deferred-work ledger against stories 2.3 and 4.3 rather than dropped. Until it
exists, this file's agreement with reality is a human claim — it is checked for self-consistency,
not for truth.

## Changing an address

An address moves by editing this file in the same change that moves the declaration. A commit that
reconfigures a host without updating this table produces exactly the state this file exists to
prevent: an address that is real and undeclared, which the next reader will discover from the
running system and copy back, and the plan stops being the source of truth from that moment on.

Taking an address out of a `reserved` range is the same operation with one extra step: the range is
narrowed, or split, in the same change. The check enforces it — an allocation inside a reservation
fails — which is what makes "growth ranges are not free space" a rule rather than an intention.
