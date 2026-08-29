"""A parsed `docs/ADDRESS-PLAN.md`.

The address plan states its own closed enumerations — the segment set, the range types, the
allocation kinds — and this module reads all of them out of the document rather than restating them
in Python. The one thing hardcoded here is the *shape* of the four tables, because a parser has to
know what it is looking for; every value it judges comes from the document.

Addresses are parsed with `ipaddress` rather than with a regular expression. A regex that accepts
`192.168.86.300` would hand every downstream detector a subject it cannot compare, and the checks
would then pass over an address that does not exist — the quiet version of reporting a pass.
"""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass
from pathlib import Path

from asgard_harness.markdown import find_table, find_tables, parse_tables

SEGMENT_HEADERS = ("Segment", "Network", "Mask", "Gateway", "Isolated", "Purpose")
RANGE_HEADERS = ("Range", "Segment", "First", "Last", "Type", "Purpose")
ALLOCATION_HEADERS = ("Address", "Segment", "Holds", "Kind", "Interface", "Traffic class", "Notes")
KIND_HEADERS = ("Kind", "Means")

NO_ROUTE_LITERAL = "none — no route off-segment"
"""What an isolated segment's Gateway cell must say. It is not an address, and it is not blank.

A blank cell is indistinguishable from an unfinished row; this literal is a positive statement that
the absence is a decision, in the same way `none — by decision` is in the Procedure Index.
"""

NODE_KIND = "node"
"""The one kind the dual-homing rule applies to. See the Kinds table in the document for why."""

GATEWAY_KIND = "gateway"
"""The kind that constitutes a route off a segment, and is therefore illegal on an isolated one."""

DHCP_POOL_TYPE = "dhcp-pool"
ALLOCATABLE_TYPE = "allocatable"

Address = ipaddress.IPv4Address | ipaddress.IPv6Address
Network = ipaddress.IPv4Network | ipaddress.IPv6Network


def parse_address(text: str) -> Address | None:
    """Parse an address cell.

    Args:
        text: The cell value as the document writes it.

    Returns:
        The address, or `None` when the cell is not one. The caller reports the `None`; it never
        treats an unparseable cell as absent.
    """
    try:
        return ipaddress.ip_address(text.strip())
    except ValueError:
        return None


def parse_network(text: str) -> Network | None:
    """Parse a network cell in CIDR form.

    Args:
        text: The cell value as the document writes it.

    Returns:
        The network, or `None` when the cell is not one.
    """
    try:
        return ipaddress.ip_network(text.strip(), strict=True)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class Segment:
    """One row of the Segments table.

    Attributes:
        name: The segment identifier the other tables join on.
        network_cell: The Network cell, verbatim.
        mask: The Mask cell.
        gateway: The Gateway cell, verbatim — an address, or the no-route literal.
        isolated_cell: The Isolated cell, verbatim.
        purpose: The Purpose cell.
        line: 1-based line number of the row.
    """

    name: str
    network_cell: str
    mask: str
    gateway: str
    isolated_cell: str
    purpose: str
    line: int

    @property
    def network(self) -> Network | None:
        """The parsed network.

        Returns:
            The network, or `None` when the Network cell is not a CIDR block.
        """
        return parse_network(self.network_cell)

    @property
    def is_isolated(self) -> bool | None:
        """Whether the segment is declared isolated.

        Returns:
            True for `yes`, False for `no`, `None` when the cell states neither and so records
            nothing checkable.
        """
        value = self.isolated_cell.strip().casefold()
        if value == "yes":
            return True
        if value == "no":
            return False
        return None

    @property
    def declares_gateway(self) -> bool:
        """Whether the Gateway cell names a route rather than declaring there is none.

        Returns:
            True when the cell is anything other than the no-route literal.
        """
        return self.gateway.strip() != NO_ROUTE_LITERAL


@dataclass(frozen=True, slots=True)
class AddressRange:
    """One row of the Address ranges table.

    Attributes:
        name: The range's stable name, used when a finding has to name a reservation.
        segment: The segment the range belongs to.
        first_cell: The First cell, verbatim.
        last_cell: The Last cell, verbatim.
        type: The range type, drawn from the document's own three-value set.
        purpose: The Purpose cell.
        line: 1-based line number of the row.
    """

    name: str
    segment: str
    first_cell: str
    last_cell: str
    type: str
    purpose: str
    line: int

    @property
    def first(self) -> Address | None:
        """The first address in the range.

        Returns:
            The address, or `None` when the cell does not parse.
        """
        return parse_address(self.first_cell)

    @property
    def last(self) -> Address | None:
        """The last address in the range.

        Returns:
            The address, or `None` when the cell does not parse.
        """
        return parse_address(self.last_cell)

    @property
    def is_dhcp_pool(self) -> bool:
        """Whether the router hands these addresses out.

        Returns:
            True when the declared type is the pool type.
        """
        return self.type.strip() == DHCP_POOL_TYPE

    @property
    def is_allocatable(self) -> bool:
        """Whether an address may be assigned from this range.

        Returns:
            True when the declared type is the allocatable type.
        """
        return self.type.strip() == ALLOCATABLE_TYPE

    @property
    def is_reserved(self) -> bool:
        """Whether the range is held rather than free.

        Anything that is neither allocatable nor a pool counts as reserved, so a misspelled type
        makes the check stricter rather than silent. That asymmetry is stated in the document.

        Returns:
            True when nothing may be assigned from this range.
        """
        return not self.is_allocatable and not self.is_dhcp_pool

    def contains(self, address: Address) -> bool:
        """Whether an address falls inside this range.

        Args:
            address: The address to test.

        Returns:
            True when the range's bounds parse, agree in family, and enclose the address.
        """
        first, last = self.first, self.last
        if first is None or last is None or first.version != address.version:
            return False
        return int(first) <= int(address) <= int(last)

    @property
    def label(self) -> str:
        """A human-readable identification of the range, for findings.

        Returns:
            The name and bounds, so a reader never has to look the range up to act on the finding.
        """
        return f"{self.name} ({self.first_cell}-{self.last_cell})"


@dataclass(frozen=True, slots=True)
class Allocation:
    """One row of the Allocations table.

    Attributes:
        address_cell: The Address cell, verbatim.
        segment: The segment the address sits on.
        holds: What holds the address — the join key for the dual-homing rule.
        kind: The holder's kind, drawn from the document's closed enumeration.
        interface: The interface on the holder that carries the address.
        traffic_class: What that interface carries.
        notes: The Notes cell.
        line: 1-based line number of the row.
    """

    address_cell: str
    segment: str
    holds: str
    kind: str
    interface: str
    traffic_class: str
    notes: str
    line: int

    @property
    def address(self) -> Address | None:
        """The parsed address.

        Returns:
            The address, or `None` when the cell is not one.
        """
        return parse_address(self.address_cell)


@dataclass(frozen=True, slots=True)
class AddressPlan:
    """Everything the harness reads out of `docs/ADDRESS-PLAN.md`.

    Attributes:
        segments: Every declared segment, in document order.
        ranges: Every declared address range, in document order.
        allocations: Every static allocation, in document order.
        legal_kinds: The closed Kind enumeration, read from the document.
        path: Where the document was read from.
    """

    segments: tuple[Segment, ...]
    ranges: tuple[AddressRange, ...]
    allocations: tuple[Allocation, ...]
    legal_kinds: frozenset[str]
    path: Path

    def segment(self, name: str) -> Segment | None:
        """Look one segment up by name.

        Args:
            name: The segment identifier.

        Returns:
            The segment, or `None` when the plan declares no such segment.
        """
        for segment in self.segments:
            if segment.name == name:
                return segment
        return None

    def ranges_for(self, segment: str) -> tuple[AddressRange, ...]:
        """Every range declared for one segment.

        Args:
            segment: The segment identifier.

        Returns:
            The ranges, in document order.
        """
        return tuple(entry for entry in self.ranges if entry.segment == segment)

    def containing_ranges(self, allocation: Allocation) -> tuple[AddressRange, ...]:
        """Every range of the allocation's own segment that encloses its address.

        Args:
            allocation: The allocation to place.

        Returns:
            The enclosing ranges, empty when the address does not parse or lands in none.
        """
        address = allocation.address
        if address is None:
            return ()
        return tuple(entry for entry in self.ranges_for(allocation.segment) if entry.contains(address))


def parse_address_plan(text: str, path: Path) -> AddressPlan:
    """Parse an address plan document.

    Args:
        text: The whole document.
        path: Where it was read from, used for reporting locations.

    Returns:
        The parsed plan.
    """
    tables = parse_tables(text)

    segments = tuple(
        Segment(
            name=row.cell(0),
            network_cell=row.cell(1),
            mask=row.cell(2),
            gateway=row.cell(3),
            isolated_cell=row.cell(4),
            purpose=row.cell(5),
            line=row.line,
        )
        for table in find_tables(tables, SEGMENT_HEADERS)
        for row in table.rows
        if row.cell(0)
    )

    ranges = tuple(
        AddressRange(
            name=row.cell(0),
            segment=row.cell(1),
            first_cell=row.cell(2),
            last_cell=row.cell(3),
            type=row.cell(4),
            purpose=row.cell(5),
            line=row.line,
        )
        for table in find_tables(tables, RANGE_HEADERS)
        for row in table.rows
        if row.cell(0)
    )

    allocations = tuple(
        Allocation(
            address_cell=row.cell(0),
            segment=row.cell(1),
            holds=row.cell(2),
            kind=row.cell(3),
            interface=row.cell(4),
            traffic_class=row.cell(5),
            notes=row.cell(6),
            line=row.line,
        )
        for table in find_tables(tables, ALLOCATION_HEADERS)
        for row in table.rows
        if row.cell(0)
    )

    kind_table = find_table(tables, KIND_HEADERS)
    legal_kinds = frozenset(row.cell(0) for row in (kind_table.rows if kind_table else ()) if row.cell(0))

    return AddressPlan(
        segments=segments,
        ranges=ranges,
        allocations=allocations,
        legal_kinds=legal_kinds,
        path=path,
    )


def load_address_plan(path: Path) -> AddressPlan:
    """Read and parse an address plan.

    Args:
        path: Path to `docs/ADDRESS-PLAN.md`.

    Returns:
        The parsed plan. A missing file yields an empty plan; the detectors report the emptiness as
        a SKIP rather than as a pass over nothing.
    """
    if not path.is_file():
        return AddressPlan(segments=(), ranges=(), allocations=(), legal_kinds=frozenset(), path=path)
    return parse_address_plan(path.read_text(encoding="utf-8"), path)
