import os
import sys

from fastmcp import FastMCP

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "agent"))
from tools import check_order_status as _check_order_status  # noqa: E402

mcp = FastMCP("nykaa-order-status-server")


@mcp.tool
def check_order_status(record_id: str) -> dict:
    """Look up a Nykaa order by its record_id (e.g. 'ORD-0001') and return
    its status, order value in INR, and a designed escalation_score in
    [0, 1] indicating how urgently the order may need human review."""
    return _check_order_status(record_id)


if __name__ == "__main__":
    # Default transport serves over HTTP at /mcp on port 8000.
    mcp.run(transport="http", host="127.0.0.1", port=8000)