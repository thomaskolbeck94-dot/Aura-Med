import asyncio
import sys
import base64

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from auramed.core.decoder import decode_datamatrix_from_bytes
from auramed.core.ocr import run_ocr_extraction
from auramed.core.database import lookup_pzn
from auramed.core.pzn_validator import is_valid_pzn
from auramed.core.affiliate import generate_refill_link

# Initialize MCP Server
app = Server("auramed-core")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for the Antigravity Agent."""
    return [
        Tool(
            name="scan_datamatrix",
            description="Liest einen GS1-DataMatrix Code aus einem base64-kodierten Bild aus.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Das Bild als base64 encodierter String"}
                },
                "required": ["image_base64"]
            }
        ),
        Tool(
            name="run_ocr_extraction",
            description="Führt OCR-Texterkennung auf einem base64-kodierten Bild aus, um PZN und Ablaufdatum als Fallback zu finden.",
            inputSchema={
                "type": "object",
                "properties": {
                    "image_base64": {"type": "string", "description": "Das Bild als base64 encodierter String"}
                },
                "required": ["image_base64"]
            }
        ),
        Tool(
            name="lookup_pzn_database",
            description="Sucht in der lokalen Datenbank nach Stammdaten für eine PZN (Pharmazentralnummer).",
            inputSchema={
                "type": "object",
                "properties": {
                    "pzn": {"type": "string", "description": "Die 8-stellige PZN"}
                },
                "required": ["pzn"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool execution requests."""
    
    if name == "scan_datamatrix":
        image_b64 = arguments.get("image_base64")
        if not image_b64:
            return [TextContent(type="text", text="Error: image_base64 ist erforderlich.")]
            
        try:
            image_bytes = base64.b64decode(image_b64)
            result = decode_datamatrix_from_bytes(image_bytes)
            if result:
                return [TextContent(type="text", text=f"Erfolgreich dekodiert: {result}")]
            else:
                return [TextContent(type="text", text="Kein DataMatrix Code im Bild gefunden.")]
        except Exception as e:
            return [TextContent(type="text", text=f"Fehler bei der Dekodierung: {str(e)}")]

    elif name == "run_ocr_extraction":
        image_b64 = arguments.get("image_base64")
        if not image_b64:
            return [TextContent(type="text", text="Error: image_base64 ist erforderlich.")]
            
        try:
            image_bytes = base64.b64decode(image_b64)
            ocr_data = run_ocr_extraction(image_bytes)
            return [TextContent(type="text", text=str(ocr_data))]
        except Exception as e:
            return [TextContent(type="text", text=f"Fehler bei OCR: {str(e)}")]

    elif name == "lookup_pzn_database":
        pzn = arguments.get("pzn")
        if not pzn:
            return [TextContent(type="text", text="Error: pzn ist erforderlich.")]
            
        if not is_valid_pzn(pzn):
            return [TextContent(type="text", text="Fehler: Ungültige PZN (Modulo-11 Check fehlgeschlagen).")]
            
        med_info = lookup_pzn(pzn)
        if med_info:
            med_info["refill_link"] = generate_refill_link(pzn)
            return [TextContent(type="text", text=str(med_info))]
        else:
            return [TextContent(type="text", text="PZN nicht in der Datenbank gefunden.")]

    else:
        return [TextContent(type="text", text=f"Error: Tool '{name}' existiert nicht.")]

async def main():
    # Run the server using stdin/stdout streams
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    # Ensure stdout is used only for MCP protocol messages
    asyncio.run(main())
