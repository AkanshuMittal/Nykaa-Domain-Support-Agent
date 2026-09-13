TEST_QUERIES = [
    {"query": "How long do I have to return a beauty product?", "type": "in_scope", "topic": "return_window"},
    {"query": "When will my COD refund reach my bank account?", "type": "in_scope", "topic": "cod_refund"},
    {"query": "How many days does standard delivery take to a metro city?", "type": "in_scope", "topic": "delivery_sla"},
    {"query": "Is reverse pickup available for my pin code?", "type": "in_scope", "topic": "reverse_pickup"},
    {"query": "Does my hair straightener come with a warranty?", "type": "in_scope", "topic": "warranty_terms"},
    {"query": "Can I cancel my order after it has shipped?", "type": "in_scope", "topic": "order_cancellation"},
    {"query": "How do I redeem my Nykaa Prive loyalty points?", "type": "in_scope", "topic": "loyalty_points"},
    {"query": "What happens if my payment fails during checkout?", "type": "in_scope", "topic": "payment_failure"},
    {"query": "Can I exchange my shoes for a different size?", "type": "in_scope", "topic": "size_exchange"},
    {"query": "My product arrived damaged, how do I report it?", "type": "in_scope", "topic": "damaged_item"},
    {"query": "Can I place an international order from the US?", "type": "in_scope", "topic": "international_shipping"},
    {"query": "When does my complaint get escalated to a manager?", "type": "in_scope", "topic": "escalation_matrix"},
    {"query": "What is the capital of France?", "type": "out_of_scope", "topic": None},
    {"query": "How do I train a neural network from scratch?", "type": "out_of_scope", "topic": None},
    {"query": "returns?", "type": "edge_case", "topic": "return_window"},
]

assert len(TEST_QUERIES) == 15
assert sum(1 for q in TEST_QUERIES if q["type"] == "in_scope") == 12
assert sum(1 for q in TEST_QUERIES if q["type"] == "out_of_scope") == 2