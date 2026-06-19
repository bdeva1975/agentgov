"""Drive the governed MCP server in-memory and show AgentGov decisions.

The AgentGov proxy MUST be running on :8000:
    uvicorn proxy.app:app --reload --port 8000
Run from project root:  python tests\\test_mcp.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastmcp import Client
from mcpserver.server import mcp


def text_of(result):
    data = getattr(result, "data", None)
    if data is not None:
        return data
    content = getattr(result, "content", None)
    if content:
        return content[0].text
    return str(result)


async def main():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("MCP tools exposed:", [t.name for t in tools])
        print()

        # 1. ALLOW — research agent reads a doc (low sensitivity)
        r = await client.call_tool("read_document",
              {"agent_id": "agent_research_01", "doc_id": "DOC-1234"})
        print("read_document (research):", text_of(r))

        # 2. ESCALATE — anyone moving funds needs a human
        r = await client.call_tool("transfer_funds",
              {"agent_id": "agent_finance_01", "to_account": "ACME-001", "amount": 500})
        print("transfer_funds (finance):", text_of(r))

        # 3. DENY — rogue agent on a high-sensitivity tool
        r = await client.call_tool("send_email",
              {"agent_id": "agent_rogue_01", "to": "x@example.com", "subject": "hi"})
        print("send_email (rogue):      ", text_of(r))


if __name__ == "__main__":
    asyncio.run(main())