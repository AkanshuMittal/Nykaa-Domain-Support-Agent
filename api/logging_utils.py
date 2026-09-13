import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from guardrails import mask_pii  # noqa: E402

LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "requests.jsonl")


def log_request(trace_id: str, raw_query: str, response: dict, duration_ms: float) -> None:
    masked_query, pii_found = mask_pii(raw_query)

    entry = {
        "trace_id": trace_id,
        "timestamp": time.time(),
        "duration_ms": round(duration_ms, 2),
        "query_text": masked_query,  # masked — never the raw text
        "pii_found": pii_found,
        "source": response.get("source"),
        "is_fallback": response.get("is_fallback"),
        "escalation_score": response.get("escalation_score"),
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


if __name__ == "__main__":
    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    fake_response = {"source": "rag", "is_fallback": False, "escalation_score": None}
    log_request(
        "trace-demo-1",
        "Please call me at 9876543210 about my order, card ending in 4417.",
        fake_response,
        duration_ms=123.4,
    )

    print("Logged entry:")
    with open(LOG_FILE) as f:
        print(f.read())

    print("Verifying no raw phone/card digits reached disk:")
    with open(LOG_FILE) as f:
        content = f.read()
        assert "9876543210" not in content, "RAW PHONE LEAKED INTO LOG FILE"
        assert "4417" not in content, "RAW CARD DIGITS LEAKED INTO LOG FILE"
    print("PASS — no raw PII in the log file.")