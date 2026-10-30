import os

from fastmcp import Client

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8002/mcp/")
MCP_TOKEN = os.getenv("MCP_SERVER_TOKEN", "")

async def test_authenticated_server():
    # Bearer token authentication
    async with Client(
            MCP_SERVER_URL,
            auth=MCP_TOKEN
    ) as client:
        await client.ping()
        tools = await client.list_tools()
        print(f"Available tools: {[tool.name for tool in tools]}")

    # Test tool call
    async with Client(
            MCP_SERVER_URL,
            auth=MCP_TOKEN) as client:
        try:
            result = await client.call_tool("query_prescription_data", {
                "sql_query": """
                SELECT `제조사`, count(DISTINCT `의약품명`) as `제품수`, sum(`처방금액`) as `총매출`, sum(`처방건수`) as `총처방건수`, round(avg(`약가`), 2) as `평균약가` FROM POC_REAL WHERE `처방년도` = 2025 GROUP BY `제조사` ORDER BY sum(`처방금액`) DESC LIMIT 10
"""

            })
            print(f"Tool result: {result}")
        except Exception as e:
            print(f"Tool call failed: {e}")

import asyncio

if __name__ == "__main__":
    asyncio.run(test_authenticated_server())
