import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dataset import ORDERS  # noqa: E402

ESCALATION_THRESHOLD = 0.6133

_ORDERS_BY_ID = {o["record_id"]: o for o in ORDERS}


def _compute_escalation_score(delayed_shipment: bool, days_since_created: int) -> float:
    delayed_component = 1.0 if delayed_shipment else 0.0
    recency_component = min(days_since_created, 30) / 30
    return round(0.6 * delayed_component + 0.4 * recency_component, 4)


def check_order_status(record_id: str) -> dict:
    """Look up an order by record_id and return its status, value, and a
    designed escalation_score in [0, 1]. Raises KeyError if not found."""
    order = _ORDERS_BY_ID.get(record_id)
    if order is None:
        return {
            "record_id": record_id,
            "found": False,
            "error": f"No order found with record_id={record_id!r}",
        }

    score = _compute_escalation_score(order["delayed_shipment"], order["days_since_created"])

    return {
        "record_id": record_id,
        "found": True,
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "escalation_score": score,
        "recommend_escalation": score > ESCALATION_THRESHOLD,
    }


if __name__ == "__main__":
    for rid in ["ORD-0001", "ORD-0002", "ORD-9999"]:
        print(check_order_status(rid))