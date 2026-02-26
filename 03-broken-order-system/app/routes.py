"""API routes for the restaurant ordering API."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query

from .models import (
    OrderCreate,
    OrderItem,
    OrderResponse,
    OrderStatus,
    OrderSummary,
    PaginatedOrders,
)
from .utils import (
    calculate_average_item_price,
    calculate_subtotal,
    calculate_tax,
    calculate_total,
    calculate_total_pages,
    calculate_total_quantity,
)

router = APIRouter()

# In-memory storage for orders
orders_db: list[dict] = []
next_order_id: int = 1


def reset_db():
    """Reset the in-memory database. Used for testing."""
    global orders_db, next_order_id
    orders_db = []
    next_order_id = 1


@router.post("/orders")
def create_order(order: OrderCreate):
    """Create a new restaurant order.

    Validates the order data and stores it in the in-memory database.
    Returns the created order with its assigned ID.
    """
    global next_order_id

    items_data = [
        {
            "name": item.name,
            "quantity": item.quantity,
            "unit_price": item.unit_price,
            "notes": item.notes,
        }
        for item in order.items
    ]

    order_record = {
        "id": next_order_id,
        "customer_name": order.customer_name,
        "items": items_data,
        "table_number": order.table_number,
        "special_instructions": order.special_instructions,
        "status": OrderStatus.PENDING,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    orders_db.append(order_record)
    next_order_id += 1

    response = OrderResponse(
        id=order_record["id"],
        customer_name=order_record["customer_name"],
        items=[OrderItem(**item) for item in order_record["items"]],
        table_number=order_record["table_number"],
        special_instructions=order_record["special_instructions"],
        status=order_record["status"],
        created_at=order_record["created_at"],
    )

    return response


@router.get("/orders", response_model=PaginatedOrders)
def list_orders(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """List all orders with pagination.

    Returns a paginated list of orders. Page numbers start at 1.
    """
    total = len(orders_db)
    total_pages = calculate_total_pages(total, limit)

    offset = page * limit
    end = offset + limit

    page_orders = orders_db[offset:end]

    orders = [
        OrderResponse(
            id=o["id"],
            customer_name=o["customer_name"],
            items=[OrderItem(**item) for item in o["items"]],
            table_number=o["table_number"],
            special_instructions=o["special_instructions"],
            status=o["status"],
            created_at=o["created_at"],
        )
        for o in page_orders
    ]

    return PaginatedOrders(
        orders=orders,
        page=page,
        limit=limit,
        total=total,
        total_pages=total_pages,
    )


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int):
    """Get a specific order by ID.

    Returns the order if found, or 404 if not.
    """
    for order in orders_db:
        if order["id"] == order_id:
            return OrderResponse(
                id=order["id"],
                customer_name=order["customer_name"],
                items=[OrderItem(**item) for item in order["items"]],
                table_number=order["table_number"],
                special_instructions=order["special_instructions"],
                status=order["status"],
                created_at=order["created_at"],
            )

    raise HTTPException(status_code=404, detail=f"Order {order_id} not found")


@router.get("/orders/{order_id}/summary", response_model=OrderSummary)
def get_order_summary(order_id: int):
    """Get a summary of a specific order including totals and tax.

    Calculates subtotal, tax, total, and average item price.
    """
    order = None
    for o in orders_db:
        if o["id"] == order_id:
            order = o
            break

    if order is None:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")

    items = order["items"]
    subtotal = calculate_subtotal(items)
    tax = calculate_tax(subtotal)
    total = calculate_total(subtotal, tax)
    total_quantity = calculate_total_quantity(items)
    average_price = calculate_average_item_price(items)

    return OrderSummary(
        id=order["id"],
        customer_name=order["customer_name"],
        item_count=len(items),
        total_items_quantity=total_quantity,
        subtotal=subtotal,
        tax=tax,
        total=total,
        average_item_price=average_price,
        status=order["status"],
    )
