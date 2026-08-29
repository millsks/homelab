---
title: 'Story 2.1 — Address plan and interface allocation'
type: 'feature'
created: '2026-08-29'
status: 'done'
review_loop_iteration: 0
baseline_commit: 'e62d656f908b9a39f7bdd1882de4a5ca7c424415'
context:
  - _bmad-output/implementation-artifacts/epic-1-context.md
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Nothing records what address anything will have. Every later story — the hypervisor build, the directory, the cluster, the gateway — needs addresses that are decided in advance and survive a rebuild, and the requirement is explicit that they are declared rather than discovered from running systems. Without the plan first, each story invents its own and the first collision is found by a device that stops working.

**Approach:** Declare the complete allocation for both network segments as a committed record, with every range's purpose stated, and add a check that the declaration is internally consistent — no collisions, nothing inside the DHCP pool, every host on the membership segment also present on the data segment.

## Boundaries & Constraints

**Always:**
- Two segments, and they never mix: the household LAN carries storage, workload, and outbound traffic; the isolated membership segment carries cluster membership only, with no gateway and no route anywhere else.
- Every static address sits **outside** the household DHCP pool. An address inside it will eventually be handed to a phone.
- Every entry names what holds it and which interface, so a reader can go from an address to a physical port without guessing.
- Ranges are reserved for growth explicitly, not left as accidental gaps — a gap nobody named is a gap someone fills by accident.
- The record is the source of truth. Addresses are never discovered from running systems and copied back.
- A node's identity is consistent across both segments, so the same host is recognisable on either.

**Ask First:**
- Any address inside the DHCP pool.
- Any route or gateway on the membership segment.
- Changing either segment's network address.

**Never:**
- Do not configure any interface — this story declares, it does not apply. Configuration is story 2.3.
- Do not create DNS records; the directory does not exist until story 4.3.
- Do not weaken the harness or its existing checks.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|---|---|---|---|
| Address lookup | A host or service name | One address per segment, with its interface named | N/A |
| Collision | Two entries claiming one address | Check fails, both named | Never auto-resolved |
| Inside the DHCP pool | A static in `.100`–`.200` | Check fails, address and pool named | N/A |
| Membership host absent from LAN | A node on one segment only | Check fails, host named | Both segments or neither |
| Gateway on the membership segment | A route declared there | Check fails | The isolation is the point |
| Reserved range consumed | An address inside a named reservation | Check fails, reservation named | Growth ranges are not free space |

</frozen-after-approval>

## Code Map

- `PROCEDURE-INDEX.md` -- `PROC-ADDRESS-PLAN`, story 2.1, `manual-by-decision`, Runbook path `docs/ADDRESS-PLAN.md`, no Automation half; a forward reference this story resolves
- `docs/OWNERSHIP.md` -- the address-plan row: `docs/ record`, "never discovered from running systems", verification is reconciliation against DNS and against what hosts answer
- `src/asgard_harness/checks_index.py` -- the pattern for a document-parsing detector; the address-plan consistency check follows it
- `src/asgard_harness/selfcheck.py` -- every new defect class needs a fixture proving it fires
- `_bmad-output/planning-artifacts/briefs/brief-homelab-2026-08-28/addendum.md` -- section 10 carries the topology this plan assigns addresses to
- `runbooks/TEMPLATE.md` -- shape for the human form

**Read-only:** `_bmad/`, `.claude/`, `.agents/`, `.bmad-loop/`.

## Confirmed facts

Measured from the live network, not assumed:

- Household LAN `192.168.86.0/24`, mask `255.255.255.0`, gateway `192.168.86.1`
- DHCP pool `192.168.86.100` – `192.168.86.200`, leaving `.2`–`.99` and `.201`–`.254` free
- Membership segment `172.16.8.0/24`, isolated, no gateway. Clear of the Kubernetes distribution's pod and service ranges and below the container runtime's default pool
- Router and modem are in a closet and are **not** on the UPS

## Tasks & Acceptance

**Execution:**
- [x] `docs/ADDRESS-PLAN.md` -- the allocation for both segments, every range's purpose named, growth reservations explicit -- the story's substance and the record every later story reads
- [x] `src/asgard_harness/checks_address_plan.py` -- parse the plan and detect collisions, addresses inside the DHCP pool, hosts present on one segment only, and consumed reservations -- a declaration nothing checks drifts the moment a story needs an address
- [x] `src/asgard_harness/selfcheck.py` -- a fixture per new defect class -- the discipline established in story 1.3
- [x] `tests/` -- unit tests per detector, each proving it fires -- coverage stays at the project threshold
- [x] `PROCEDURE-INDEX.md` -- resolve the forward reference, move `PROC-ADDRESS-PLAN` to its true status, update Totals, register the new check as an alert source
- [x] `docs/OWNERSHIP.md` -- resolve the address-plan forward-reference row

**Acceptance Criteria:**
- Given the plan, when any node is looked up, then it has one address on each segment, each naming its interface and traffic class.
- Given every static address, when compared against the DHCP pool, then none falls inside it.
- Given the membership segment, when its entries are read, then no gateway or route off-segment is declared.
- Given a collision, a pool overlap, a one-segment host, or a consumed reservation, when the check runs, then it exits non-zero and names the offending address or host.
- Given the check against the committed plan, when it runs, then it passes and reports what it examined.
- Given `pixi run ci`, `pixi run audit`, and `pixi run selfcheck`, when they run, then all pass.

## Design Notes

**Keep a node's last octet identical on both segments.** A node at `.11` on the data segment should be `.11` on the membership segment. It costs nothing, makes the plan memorable, and turns a whole class of transposition mistake into something a reader notices immediately.

**Reserve for growth explicitly.** The UPS has no spare outlet and the membership switch's client roster caps at five, so a fifth node is already constrained by other things — but the address plan should not be the thing that blocks it. Name the reserved ranges so they are decisions rather than gaps.

**The full verification is not available yet.** The ownership table says this plan is verified by reconciliation against DNS and against what hosts actually answer — neither exists until stories 4.3 and 2.3. What is checkable today is internal consistency, and that is what this story builds. The reconciliation check belongs to the story that first has something to reconcile against, and should be recorded as such rather than quietly dropped.

## Verification

**Commands:**
- `pixi run ci`, `pixi run audit`, `pixi run selfcheck` -- expected: all exit 0
- Inject each defect class in turn -- expected: non-zero exit naming the offending address or host; repository restored afterwards

**Manual checks:**
- Confirm every declared static sits outside `192.168.86.100`–`192.168.86.200`.
- Confirm no gateway appears anywhere in the membership segment's entries.
