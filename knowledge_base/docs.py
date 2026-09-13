DOCUMENTS = [
    {
        "doc_id": "return_window",
        "title": "Return Window by Product Category",
        "text": (
            "Nykaa allows returns within 7 days of delivery for Beauty and "
            "personal-care items, provided the product is unopened and the "
            "seal is intact. Apparel and Footwear can be returned within 15 "
            "days as long as tags are attached and the item is unworn. "
            "Electronics and Home appliances carry a shorter 10-day return "
            "window because these items are checked for physical damage "
            "before a return is approved. Items marked 'Final Sale' during "
            "clearance events are not eligible for return under any category."
        ),
    },
    {
        "doc_id": "cod_refund",
        "title": "Cash-on-Delivery (COD) Refund Timelines",
        "text": (
            "Since COD orders have no prepaid payment method to refund to, "
            "the refund is issued to the customer's bank account or Nykaa "
            "wallet after they share verified account details through the "
            "app. Bank-account refunds for COD orders typically settle "
            "within 7-9 business days after the returned item passes quality "
            "check. Wallet credit for COD refunds is faster and usually "
            "reflects within 24 hours of the return being approved."
        ),
    },
    {
        "doc_id": "delivery_sla",
        "title": "Delivery SLAs",
        "text": (
            "Standard delivery to metro cities is committed within 3-5 "
            "business days of order confirmation, while non-metro and "
            "remote pin codes are given a 5-8 business day window. Express "
            "delivery, where available, promises next-day delivery for an "
            "additional fee. An order is treated as delayed once it crosses "
            "its SLA date without a 'Delivered' status update, which is the "
            "trigger our support tooling uses to flag shipments for review."
        ),
    },
    {
        "doc_id": "reverse_pickup",
        "title": "Reverse-Pickup Eligibility",
        "text": (
            "Reverse pickup, where a courier collects the returned item from "
            "the customer's address, is available only in serviceable pin "
            "codes listed in our logistics partner's coverage map. If "
            "reverse pickup isn't available for a pin code, the customer "
            "must self-ship the item to the returns warehouse and upload the "
            "courier receipt to claim a refund. Reverse pickup is not "
            "offered for items above 5 kg in weight; those always require "
            "self-shipping regardless of pin code."
        ),
    },
    {
        "doc_id": "warranty_terms",
        "title": "Warranty Terms by Category",
        "text": (
            "Electronics such as hair styling tools and grooming appliances "
            "carry a manufacturer warranty of 6-12 months depending on the "
            "brand, covering manufacturing defects but not accidental damage. "
            "Beauty products are not warrantied in the traditional sense but "
            "are covered by the return window if found defective or "
            "damaged on arrival. Home category items like diffusers or small "
            "appliances typically carry a 12-month warranty, and the "
            "warranty card included in the box must be retained as proof."
        ),
    },
    {
        "doc_id": "order_cancellation",
        "title": "Order-Cancellation Policy",
        "text": (
            "Orders can be cancelled free of charge any time before they "
            "reach 'Shipped' status, directly from the order-details screen "
            "in the app. Once an order is 'Shipped', it can no longer be "
            "cancelled outright; the customer must instead refuse delivery "
            "or wait for delivery and initiate a return. Prepaid orders "
            "cancelled before shipping are refunded to the original payment "
            "method within 5-7 business days."
        ),
    },
    {
        "doc_id": "loyalty_points",
        "title": "Loyalty-Points Redemption Policy",
        "text": (
            "Nykaa Prive loyalty points are earned at a fixed rate per "
            "rupee spent and can be redeemed against future orders once a "
            "customer crosses a minimum balance of 100 points. Points can "
            "cover up to 20% of a single order's value and cannot be "
            "combined with certain promotional discounts. Redeemed points "
            "are reversed back to the customer's account if the order they "
            "were used on is later cancelled or fully refunded."
        ),
    },
    {
        "doc_id": "payment_failure",
        "title": "Payment-Failure and Retry Policy",
        "text": (
            "If a payment fails during checkout, the order is held in a "
            "'Payment Pending' state for 15 minutes, during which the "
            "customer can retry payment using the same or a different "
            "method without re-entering their cart. If payment is not "
            "completed within that window, the order is automatically "
            "cancelled and the cart items are released back to inventory. "
            "Any amount debited but not confirmed by the payment gateway "
            "during a failed attempt is auto-reversed by the bank within "
            "5-7 business days, independent of Nykaa's own refund process."
        ),
    },
    {
        "doc_id": "size_exchange",
        "title": "Size-Exchange Policy",
        "text": (
            "Apparel and Footwear orders are eligible for a one-time free "
            "size exchange within 15 days of delivery, subject to the "
            "requested size being in stock at the time of the exchange "
            "request. If the requested size is unavailable, the system "
            "automatically offers a refund instead of an exchange. A second "
            "size-exchange request on the same order is not permitted and is "
            "instead routed to the standard return flow."
        ),
    },
    {
        "doc_id": "damaged_item",
        "title": "Damaged-Item Claim Process",
        "text": (
            "Customers must report a damaged or defective item within 48 "
            "hours of delivery, along with photos of the product and "
            "packaging, through the app's 'Report an Issue' flow. Claims "
            "raised after this 48-hour window are evaluated case by case "
            "and are not guaranteed approval. Once a damaged-item claim is "
            "approved, Nykaa offers either a free replacement, if the same "
            "item is in stock, or a full refund, and does not require the "
            "customer to pay for return shipping in either case."
        ),
    },
    {
        "doc_id": "international_shipping",
        "title": "International Shipping Restrictions",
        "text": (
            "Nykaa currently ships internationally only to a limited set of "
            "countries, and international orders are restricted to the "
            "Beauty and Apparel categories due to customs regulations on "
            "electricals and liquids. International orders cannot use COD "
            "and must be fully prepaid at checkout. Import duties and taxes "
            "levied by the destination country are the customer's "
            "responsibility and are not included in the displayed order "
            "price."
        ),
    },
    {
        "doc_id": "escalation_matrix",
        "title": "Customer-Support Escalation Matrix",
        "text": (
            "Standard queries are handled by first-line chat or phone "
            "support and are expected to be resolved within 24 hours. "
            "Queries involving a delayed shipment past its SLA, a "
            "high-value order above ₹10,000, or a repeat complaint from the "
            "same customer are automatically escalated to a senior support "
            "specialist. Escalations that remain unresolved after 72 hours "
            "are further escalated to the operations manager for that "
            "region, who has authority to approve compensation or expedited "
            "resolution."
        ),
    },
]


if __name__ == "__main__":
    print(f"Total documents: {len(DOCUMENTS)}")
    for d in DOCUMENTS:
        print(f"  - {d['doc_id']}: {len(d['text'].split())} words")