import asyncio

from fastmcp import Client

SERVER_URL = "http://127.0.0.1:8000/mcp"


async def call_check_order_status(client: Client, record_id: str) -> None:
    result = await client.call_tool("check_order_status", {"record_id": record_id})
    print(f"\nMCP call for record_id={record_id!r}:")
    print(f"  Standardized MCP response: {result}")


async def main() -> None:
    async with Client(SERVER_URL) as client:
        tools = await client.list_tools()
        print("Tools discovered on server:", [t.name for t in tools])

        # Call the tool for 2+ different record IDs, per the brief.
        for record_id in ["ORD-0001", "ORD-0002", "ORD-9999"]:  # last one deliberately not found
            await call_check_order_status(client, record_id)


if __name__ == "__main__":
    asyncio.run(main())