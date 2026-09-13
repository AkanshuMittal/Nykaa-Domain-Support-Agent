import random

SEED = 42
NUM_RECORDS = 60  # comfortably above the required minimum of 40

CATEGORIES = ["Apparel", "Electronics", "Home", "Footwear", "Beauty"]
STATUSES = ["Placed", "Shipped", "Delivered", "Returned", "Refunded"]

# Weighted so every status appears, but the funnel skews toward
# "in progress" / "closed" rather than everything sitting at "Placed".
STATUS_WEIGHTS = {
    "Placed": 0.15,
    "Shipped": 0.25,
    "Delivered": 0.35,
    "Returned": 0.15,
    "Refunded": 0.10,
}

ORDER_VALUE_MIN_INR = 150
ORDER_VALUE_MAX_INR = 12000

DELAYED_SHIPMENT_PROB = 0.18  # tuned to land inside the required 10-30% band


def _weighted_choice(rng: random.Random, options_with_weights: dict) -> str:
    options = list(options_with_weights.keys())
    weights = list(options_with_weights.values())
    return rng.choices(options, weights=weights, k=1)[0]


def generate_orders(seed: int = SEED, n: int = NUM_RECORDS) -> list[dict]:
    rng = random.Random(seed)
    orders = []

    # Guarantee every category appears at least 3 times by seeding the first
    # len(CATEGORIES) * 3 records round-robin, then filling the rest randomly.
    guaranteed = []
    for cat in CATEGORIES:
        guaranteed.extend([cat] * 3)
    remaining_slots = n - len(guaranteed)
    random_categories = [rng.choice(CATEGORIES) for _ in range(remaining_slots)]
    category_sequence = guaranteed + random_categories
    rng.shuffle(category_sequence)

    # Guarantee every status appears at least once the same way, then fill
    # the rest using STATUS_WEIGHTS.
    guaranteed_statuses = STATUSES.copy()
    remaining_status_slots = n - len(guaranteed_statuses)
    random_statuses = [
        _weighted_choice(rng, STATUS_WEIGHTS) for _ in range(remaining_status_slots)
    ]
    status_sequence = guaranteed_statuses + random_statuses
    rng.shuffle(status_sequence)

    for i in range(n):
        record_id = f"ORD-{i + 1:04d}"
        category = category_sequence[i]
        status = status_sequence[i]
        order_value_inr = rng.randint(ORDER_VALUE_MIN_INR, ORDER_VALUE_MAX_INR)
        days_since_created = rng.randint(0, 30)
        delayed_shipment = rng.random() < DELAYED_SHIPMENT_PROB

        orders.append(
            {
                "record_id": record_id,
                "category": category,
                "status": status,
                "order_value_inr": order_value_inr,
                "days_since_created": days_since_created,
                "delayed_shipment": delayed_shipment,
            }
        )

    return orders


ORDERS = generate_orders()


def _report(orders: list[dict]) -> None:
    print(f"Total records: {len(orders)}\n")

    print("Count per category:")
    for cat in CATEGORIES:
        count = sum(1 for o in orders if o["category"] == cat)
        flag = "OK" if count >= 3 else "FAIL (< 3)"
        print(f"  {cat:12s}: {count:3d}  [{flag}]")

    print("\nCount per status:")
    for status in STATUSES:
        count = sum(1 for o in orders if o["status"] == status)
        flag = "OK" if count >= 1 else "FAIL (< 1)"
        print(f"  {status:12s}: {count:3d}  [{flag}]")

    delayed_count = sum(1 for o in orders if o["delayed_shipment"])
    delayed_pct = 100 * delayed_count / len(orders)
    band_flag = "OK (within 10-30%)" if 10 <= delayed_pct <= 30 else "FAIL (outside 10-30%)"
    print(f"\ndelayed_shipment=True: {delayed_count}/{len(orders)} = {delayed_pct:.1f}%  [{band_flag}]")


if __name__ == "__main__":
    _report(ORDERS)
    print("\nSample record:")
    print(ORDERS[0])