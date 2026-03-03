"""Data models for the Fuzz Gauntlet challenge."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BillResult:
    """Result of a bill calculation."""
    subtotal: float
    discount_total: float
    tax: float
    total: float
    line_items: list[dict]


@dataclass
class Reservation:
    """A restaurant reservation."""
    start: datetime
    end: datetime
    party_size: int
    timezone: str
    name: str


@dataclass
class ScheduleResult:
    """Result of scheduling a reservation."""
    reservations: list[Reservation]
    conflicts: list[tuple[Reservation, Reservation]]


@dataclass
class ParsedOrder:
    """A successfully parsed order."""
    items: list[str]
    quantities: list[int]
    modifiers: list[str]
    raw_text: str


@dataclass
class ParseError:
    """An error encountered while parsing an order."""
    message: str
    position: int


@dataclass
class AuditEntry:
    """A single entry in the reconciliation audit trail."""
    item: str
    sources: dict[str, int]
    resolved_quantity: int
    resolution_method: str


@dataclass
class ReconciledInventory:
    """Result of reconciling inventory from multiple sources."""
    items: dict[str, int]
    audit_trail: list[AuditEntry]
    conflicts: list[str]
