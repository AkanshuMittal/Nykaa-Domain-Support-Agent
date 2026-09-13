import jsonschema

AGENT_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string"},
        "source": {"type": "string", "enum": ["rag", "order_lookup", "guardrail_blocked"]},
        "answer": {"type": "string"},
        "is_fallback": {"type": "boolean"},
        "escalation_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
        "retrieved_doc_ids": {"type": "array", "items": {"type": "string"}},
        "trace_id": {"type": "string"},
    },
    "required": ["query", "source", "answer", "is_fallback", "retrieved_doc_ids", "trace_id"],
    "additionalProperties": False,
}


def validate_response(response: dict) -> tuple[bool, str | None]:
    """Returns (is_valid, error_message). error_message is None if valid."""
    try:
        jsonschema.validate(instance=response, schema=AGENT_RESPONSE_SCHEMA)
        return True, None
    except jsonschema.exceptions.ValidationError as e:
        return False, str(e)


if __name__ == "__main__":
    good = {
        "query": "test",
        "source": "rag",
        "answer": "some answer",
        "is_fallback": False,
        "escalation_score": None,
        "retrieved_doc_ids": ["return_window"],
        "trace_id": "abc-123",
    }
    bad = {"query": "test", "answer": "missing required fields"}

    print("Valid response check:", validate_response(good))
    print("Invalid response check:", validate_response(bad))