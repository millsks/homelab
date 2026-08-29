"""Detectors for the defect classes `docs/ADDRESS-PLAN.md` defines.

Each function here implements exactly one class from § "What the check enforces", in the order that
section lists them. The plan is a `docs/ record`: nothing executes it, so the only thing a machine
can say about it today is whether it agrees with itself. That is a real and narrow claim, and it is
stated as such — the plan's other verification, reconciliation against DNS and against what hosts
answer, needs a directory and running hosts that do not exist until stories 4.3 and 2.3.

**No detector here auto-resolves anything.** A collision has two claimants and picking one silently
is how the wrong one becomes permanent; the audit names both and stops.
"""

from __future__ import annotations

from collections import defaultdict

from asgard_harness import defects
from asgard_harness.address_plan_document import (
    GATEWAY_KIND,
    NO_ROUTE_LITERAL,
    NODE_KIND,
    Address,
    AddressPlan,
    Network,
)
from asgard_harness.findings import CheckResult, Finding, result, skipped


def _at(plan: AddressPlan, line: int) -> str:
    return f"{plan.path.name}:{line}"


def _addr(network: Network, value: int) -> Address:
    """Render an integer address back into its own family, relative to a network.

    Args:
        network: The network the value sits inside.
        value: The integer form of the address.

    Returns:
        The address. Indexing the network keeps the family right without the caller choosing
        between the two address classes.
    """
    return network[value - int(network.network_address)]


def _no_plan(name: str, defect: str, noun: str, plan: AddressPlan) -> CheckResult:
    return skipped(
        name,
        defect,
        noun,
        f"{plan.path.name} declares no segments, so there is no address space to judge anything "
        "against; a check with nothing to examine reports a SKIP, never a pass",
    )


def check_kind_enumeration(plan: AddressPlan) -> CheckResult:
    """Illegal kind: an allocation's `Kind` outside the plan's own closed set.

    This check exists because of an asymmetry the document states: a misspelled range `Type` makes
    the range checks stricter, but a misspelled `Kind` makes the dual-homing rule skip the row
    silently. A typo that weakens a check has to be caught.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.legal_kinds:
        return skipped(
            "Allocation kind enumeration",
            defects.ADDRESS_PLAN_ILLEGAL_KIND,
            "allocations",
            f"{plan.path.name} states no closed Kind enumeration, so no kind can be judged legal",
        )
    findings = [
        Finding(
            defect=defects.ADDRESS_PLAN_ILLEGAL_KIND,
            subject=f"{allocation.address_cell} ({allocation.holds})",
            detail=f"kind {allocation.kind!r} is outside the closed set {sorted(plan.legal_kinds)}",
            location=_at(plan, allocation.line),
        )
        for allocation in plan.allocations
        if allocation.kind not in plan.legal_kinds
    ]
    return result(
        "Allocation kind enumeration",
        defects.ADDRESS_PLAN_ILLEGAL_KIND,
        len(plan.allocations),
        "allocations",
        findings,
    )


def check_collisions(plan: AddressPlan) -> CheckResult:
    """Collision: two allocations claiming one address on one segment.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.allocations:
        return _no_plan("Address collisions", defects.ADDRESS_PLAN_COLLISION, "allocations", plan)
    claimed: defaultdict[tuple[str, str], list[tuple[str, int]]] = defaultdict(list)
    for allocation in plan.allocations:
        claimed[(allocation.segment, allocation.address_cell.strip())].append((allocation.holds, allocation.line))
    findings: list[Finding] = []
    for (segment, address), claimants in sorted(claimed.items()):
        if len(claimants) < 2:
            continue
        holders = [holder for holder, _ in claimants]
        lines = [line for _, line in claimants]
        findings.append(
            Finding(
                defect=defects.ADDRESS_PLAN_COLLISION,
                subject=f"{address} on segment {segment}",
                detail=f"claimed by {holders} at lines {lines}; the audit names both and picks neither",
                location=_at(plan, lines[0]),
            )
        )
    return result(
        "Address collisions",
        defects.ADDRESS_PLAN_COLLISION,
        len(plan.allocations),
        "allocations",
        findings,
    )


def check_dhcp_pool(plan: AddressPlan) -> CheckResult:
    """Inside the DHCP pool: a static address the household router will eventually hand out.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    pools = [entry for entry in plan.ranges if entry.is_dhcp_pool]
    if not pools:
        return skipped(
            "Statics outside the DHCP pool",
            defects.ADDRESS_PLAN_IN_DHCP_POOL,
            "allocations",
            f"{plan.path.name} declares no range of type 'dhcp-pool', so no pool boundary exists to "
            "compare a static address against",
        )
    findings = [
        Finding(
            defect=defects.ADDRESS_PLAN_IN_DHCP_POOL,
            subject=f"{allocation.address_cell} ({allocation.holds})",
            detail=f"falls inside the DHCP pool {entry.label}; an address inside it is eventually handed to a phone",
            location=_at(plan, allocation.line),
        )
        for allocation in plan.allocations
        for entry in plan.containing_ranges(allocation)
        if entry.is_dhcp_pool
    ]
    return result(
        "Statics outside the DHCP pool",
        defects.ADDRESS_PLAN_IN_DHCP_POOL,
        len(plan.allocations),
        "allocations",
        findings,
        note=f"{len(pools)} declared pool(s): {[entry.label for entry in pools]}",
    )


def check_reservations(plan: AddressPlan) -> CheckResult:
    """Reserved range consumed: an allocation inside a range that is held rather than free.

    Growth ranges are not free space. Taking an address from one is a decision that narrows the
    reservation in the same change; a check that tolerated it would make the reservation a comment.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    reserved = [entry for entry in plan.ranges if entry.is_reserved]
    if not plan.ranges:
        return _no_plan("Reservations not consumed", defects.ADDRESS_PLAN_RESERVATION_CONSUMED, "allocations", plan)
    findings = [
        Finding(
            defect=defects.ADDRESS_PLAN_RESERVATION_CONSUMED,
            subject=f"{allocation.address_cell} ({allocation.holds})",
            detail=f"falls inside the reserved range {entry.label} — {entry.purpose}",
            location=_at(plan, allocation.line),
        )
        for allocation in plan.allocations
        for entry in plan.containing_ranges(allocation)
        if entry.is_reserved
    ]
    return result(
        "Reservations not consumed",
        defects.ADDRESS_PLAN_RESERVATION_CONSUMED,
        len(plan.allocations),
        "allocations",
        findings,
        note=f"{len(reserved)} reserved range(s) held",
    )


def check_node_homing(plan: AddressPlan) -> CheckResult:
    """A `node` holder carries exactly one address on every declared segment — both or neither.

    Scoped to the `node` kind rather than to everything on the membership segment, because the
    membership switch legitimately lives on that segment alone. The document states that scoping,
    and states that a new segment some Nodes do not join needs the rule refined rather than
    exempted.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.segments:
        return _no_plan("Nodes homed on every segment", defects.ADDRESS_PLAN_NODE_ON_ONE_SEGMENT, "hosts", plan)
    declared = [segment.name for segment in plan.segments]
    homes: defaultdict[str, defaultdict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    lines: dict[str, int] = {}
    for allocation in plan.allocations:
        if allocation.kind != NODE_KIND:
            continue
        homes[allocation.holds][allocation.segment].append(allocation.address_cell)
        lines.setdefault(allocation.holds, allocation.line)
    findings: list[Finding] = []
    for host in sorted(homes):
        for segment in declared:
            addresses = homes[host].get(segment, [])
            if len(addresses) == 1:
                continue
            detail = (
                f"has no address on segment {segment!r}; a Node is on both segments or neither"
                if not addresses
                else f"has {len(addresses)} addresses {addresses} on segment {segment!r}; a Node carries exactly one"
            )
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_NODE_ON_ONE_SEGMENT,
                    subject=host,
                    detail=detail,
                    location=_at(plan, lines[host]),
                )
            )
        for segment in sorted(set(homes[host]) - set(declared)):
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_NODE_ON_ONE_SEGMENT,
                    subject=host,
                    detail=f"is homed on segment {segment!r}, which {plan.path.name} does not declare",
                    location=_at(plan, lines[host]),
                )
            )
    return result(
        "Nodes homed on every segment",
        defects.ADDRESS_PLAN_NODE_ON_ONE_SEGMENT,
        len(homes),
        f"{NODE_KIND} hosts",
        findings,
        note=f"{len(declared)} declared segment(s): {declared}",
    )


def check_isolated_segments(plan: AddressPlan) -> CheckResult:
    """No gateway and no route off a segment declared isolated. The isolation is the point.

    Two shapes count as a route: the segment's own Gateway cell naming one, and an allocation of
    kind `gateway` sitting on it. A segment whose Isolated cell states neither `yes` nor `no`
    records nothing checkable and is reported too.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.segments:
        return _no_plan("Isolated segments carry no route", defects.ADDRESS_PLAN_ROUTE_ON_ISOLATED, "segments", plan)
    findings: list[Finding] = []
    for segment in plan.segments:
        if segment.is_isolated is None:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_ROUTE_ON_ISOLATED,
                    subject=segment.name,
                    detail=f"Isolated cell {segment.isolated_cell!r} states neither 'yes' nor 'no'",
                    location=_at(plan, segment.line),
                )
            )
            continue
        if not segment.is_isolated:
            continue
        if segment.declares_gateway:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_ROUTE_ON_ISOLATED,
                    subject=segment.name,
                    detail=(
                        f"is declared isolated but its Gateway cell is {segment.gateway!r}; "
                        f"an isolated segment must carry the literal {NO_ROUTE_LITERAL!r}"
                    ),
                    location=_at(plan, segment.line),
                )
            )
        for allocation in plan.allocations:
            if allocation.segment != segment.name or allocation.kind != GATEWAY_KIND:
                continue
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_ROUTE_ON_ISOLATED,
                    subject=f"{allocation.address_cell} ({allocation.holds})",
                    detail=f"declares a {GATEWAY_KIND!r} on segment {segment.name!r}, which is declared isolated",
                    location=_at(plan, allocation.line),
                )
            )
    isolated = sum(1 for segment in plan.segments if segment.is_isolated)
    return result(
        "Isolated segments carry no route",
        defects.ADDRESS_PLAN_ROUTE_ON_ISOLATED,
        len(plan.segments),
        "segments",
        findings,
        note=f"{isolated} declared isolated",
    )


def check_range_coverage(plan: AddressPlan) -> CheckResult:
    """The declared ranges tile their segment exactly: no gap, no overlap, nothing outside.

    A gap nobody named is a gap someone fills by accident, so the requirement is total coverage
    rather than merely non-overlapping coverage. Network and broadcast addresses are covered too —
    a range declaring them unassignable is a declaration; leaving them out is an omission.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.segments:
        return _no_plan("Address ranges tile their segment", defects.ADDRESS_PLAN_RANGE_COVERAGE, "segments", plan)
    findings: list[Finding] = []
    for segment in plan.segments:
        network = segment.network
        if network is None:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                    subject=segment.name,
                    detail=f"Network cell {segment.network_cell!r} is not a CIDR block, so nothing can tile it",
                    location=_at(plan, segment.line),
                )
            )
            continue
        usable: list[tuple[int, int, str]] = []
        for entry in plan.ranges_for(segment.name):
            first, last = entry.first, entry.last
            if first is None or last is None:
                findings.append(
                    Finding(
                        defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                        subject=entry.name,
                        detail=f"bounds {entry.first_cell!r}-{entry.last_cell!r} do not both parse as addresses",
                        location=_at(plan, entry.line),
                    )
                )
                continue
            if int(first) > int(last):
                findings.append(
                    Finding(
                        defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                        subject=entry.name,
                        detail=f"runs backwards: first {first} is above last {last}",
                        location=_at(plan, entry.line),
                    )
                )
                continue
            if first not in network or last not in network:
                findings.append(
                    Finding(
                        defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                        subject=entry.name,
                        detail=f"{first}-{last} is not inside segment {segment.name}'s network {network}",
                        location=_at(plan, entry.line),
                    )
                )
                continue
            usable.append((int(first), int(last), entry.name))
        expected = int(network.network_address)
        end = int(network.broadcast_address)
        for first_value, last_value, name in sorted(usable):
            if first_value > expected:
                findings.append(
                    Finding(
                        defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                        subject=segment.name,
                        detail=(
                            f"nothing declares {_addr(network, expected)}-{_addr(network, first_value - 1)}, "
                            f"the gap below range {name}"
                        ),
                        location=_at(plan, segment.line),
                    )
                )
            elif first_value < expected:
                findings.append(
                    Finding(
                        defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                        subject=name,
                        detail=f"overlaps the range below it: it starts at or before "
                        f"{_addr(network, expected - 1)}, which is already declared",
                        location=_at(plan, segment.line),
                    )
                )
            expected = max(expected, last_value + 1)
        if expected <= end:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_RANGE_COVERAGE,
                    subject=segment.name,
                    detail=(
                        f"nothing declares {_addr(network, expected)}-{network.broadcast_address}, "
                        "the tail of the segment"
                    ),
                    location=_at(plan, segment.line),
                )
            )
    return result(
        "Address ranges tile their segment",
        defects.ADDRESS_PLAN_RANGE_COVERAGE,
        len(plan.ranges),
        "declared ranges",
        findings,
        note=f"across {len(plan.segments)} segment(s)",
    )


def check_allocations_are_declared(plan: AddressPlan) -> CheckResult:
    """Every allocation parses, names a declared segment, and lands in a declared range.

    Without this, an unparseable address or a mistyped segment name would be skipped by every other
    detector here — each of them would report a pass over a row it could not place, which is the
    quiet version of not checking it at all.

    Args:
        plan: The parsed address plan.

    Returns:
        The check result.
    """
    if not plan.segments:
        return _no_plan(
            "Allocations land in a declared range", defects.ADDRESS_PLAN_UNDECLARED_ADDRESS, "allocations", plan
        )
    declared = {segment.name for segment in plan.segments}
    findings: list[Finding] = []
    for allocation in plan.allocations:
        subject = f"{allocation.address_cell} ({allocation.holds})"
        if allocation.address is None:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_UNDECLARED_ADDRESS,
                    subject=subject,
                    detail=f"Address cell {allocation.address_cell!r} is not an IP address",
                    location=_at(plan, allocation.line),
                )
            )
            continue
        if allocation.segment not in declared:
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_UNDECLARED_ADDRESS,
                    subject=subject,
                    detail=f"names segment {allocation.segment!r}, which {plan.path.name} does not declare",
                    location=_at(plan, allocation.line),
                )
            )
            continue
        if not plan.containing_ranges(allocation):
            findings.append(
                Finding(
                    defect=defects.ADDRESS_PLAN_UNDECLARED_ADDRESS,
                    subject=subject,
                    detail=(
                        f"falls in no range declared for segment {allocation.segment!r}; "
                        "an address in no named range is an address nobody accounted for"
                    ),
                    location=_at(plan, allocation.line),
                )
            )
    return result(
        "Allocations land in a declared range",
        defects.ADDRESS_PLAN_UNDECLARED_ADDRESS,
        len(plan.allocations),
        "allocations",
        findings,
    )


def run_address_plan_checks(plan: AddressPlan) -> list[CheckResult]:
    """Run every address-plan detector, in the order the document lists them.

    Args:
        plan: The parsed address plan.

    Returns:
        One result per detector.
    """
    return [
        check_collisions(plan),
        check_dhcp_pool(plan),
        check_reservations(plan),
        check_node_homing(plan),
        check_isolated_segments(plan),
        check_kind_enumeration(plan),
        check_range_coverage(plan),
        check_allocations_are_declared(plan),
    ]
