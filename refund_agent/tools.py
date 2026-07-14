"""Mock backend tools for the refund agent.

Each tool simulates a real service call. `issue_refund` is irreversible:
calling it twice for the same order double-charges the company, which is
exactly the failure mode the reliability gate must catch.
"""

from __future__ import annotations

# A tiny in-memory "orders database".
ORDERS: dict[str, dict] = {
    "ORD-1042": {"amount": 49.99, "status": "delivered", "days_since_delivery": 6},
    "ORD-2001": {"amount": 250.00, "status": "delivered", "days_since_delivery": 45},
    "ORD-377": {"amount": 12.50, "status": "shipped", "days_since_delivery": 0},
}

REFUND_WINDOW_DAYS = 30


def lookup_order(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return {"found": False, "order_id": order_id}
    return {"found": True, "order_id": order_id, **order}


def check_refund_eligibility(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return {"eligible": False, "reason": "order not found"}
    if order["status"] != "delivered":
        return {"eligible": False, "reason": "order not delivered yet"}
    if order["days_since_delivery"] > REFUND_WINDOW_DAYS:
        return {"eligible": False, "reason": "outside 30-day refund window"}
    return {"eligible": True, "reason": "within refund window"}


def issue_refund(order_id: str, amount: float) -> dict:
    """Irreversible: really moves money in production."""
    return {"refunded": True, "order_id": order_id, "amount": amount}


def send_confirmation(order_id: str, message: str) -> dict:
    return {"sent": True, "order_id": order_id}
