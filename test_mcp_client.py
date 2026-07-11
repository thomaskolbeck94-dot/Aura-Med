import asyncio
import json
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_mcp_test():
    # Set path to current Python interpreter
    import sys
    python_exe = sys.executable
    
    server_params = StdioServerParameters(
        command=python_exe,
        args=["src/auramed/mcp_server.py"],
        env=os.environ.copy()
    )

    print("Starte MCP Server über stdio...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n1. Hole Liste aller verfügbaren Tools...")
            tools = await session.list_tools()
            for tool in tools.tools:
                print(f" - Tool gefunden: {tool.name}")
            
            print("\n2. Teste 'lookup_pzn_database' Tool (Mock PZN 00259869)...")
            result = await session.call_tool("lookup_pzn_database", arguments={"pzn": "00259869"})
            print(f"Ergebnis: {result.content[0].text}")

if __name__ == "__main__":
    asyncio.run(run_mcp_test())
