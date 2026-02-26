"""Pydantic models for the restaurant ordering API."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY = "ready"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderItem(BaseModel):
    """A single item in an order."""
    name: str = Field(..., min_length=1, max_length=100)
    quantity: int
    unit_price: float = Field(..., gt=0)
    notes: Optional[str] = None


class OrderCreate(BaseModel):
    """Request body for creating a new order."""
    customer_name: str = Field(..., min_length=1, max_length=200)
    items: list[OrderItem]
    table_number: Optional[int] = Field(None, ge=1, le=100)
    special_instructions: Optional[str] = None


class OrderResponse(BaseModel):
    """Response body for an order."""
    id: int
    customer_name: str
    items: list[OrderItem]
    table_number: Optional[int] = None
    special_instructions: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    created_at: str


class OrderSummary(BaseModel):
    """Summary of an order including calculated totals."""
    id: int
    customer_name: str
    item_count: int
    total_items_quantity: int
    subtotal: float
    tax: float
    total: float
    average_item_price: float
    status: OrderStatus


class PaginatedOrders(BaseModel):
    """Paginated list of orders."""
    orders: list[OrderResponse]
    page: int
    limit: int
    total: int
    total_pages: int
