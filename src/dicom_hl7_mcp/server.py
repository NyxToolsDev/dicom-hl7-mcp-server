"""MCP Server for DICOM/HL7 Developer AI Assistant.

Registers all tools and runs the server over stdio transport.
"""

from __future__ import annotations

import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from dicom_hl7_mcp.config import LOG_LEVEL
from dicom_hl7_mcp.tools.dicom_tags import explain_dicom_tag, lookup_dicom_tag
from dicom_hl7_mcp.tools.fhir_converter import (
    decode_private_tags,
    generate_sample_message,
    validate_hl7_message,
)
from dicom_hl7_mcp.tools.field_mapper import (
    explain_integration_pattern,
    map_dicom_to_hl7,
    map_hl7_to_fhir,
)
from dicom_hl7_mcp.tools.hl7_parser import (
    explain_hl7_segment,
    lookup_hl7_table,
    parse_hl7_message,
)
from dicom_hl7_mcp.tools.mirth_generator import generate_mirth_channel
from dicom_hl7_mcp.tools.pacs_combined import PACS_COMBINED_TOOLS, dispatch_pacs_combined_tool
from dicom_hl7_mcp.tools.pacs_connectivity import PACS_TOOLS, dispatch_pacs_tool
from dicom_hl7_mcp.pacs.phi_guard import install_phi_filter

# Configure logging with PHI redaction
logging.basicConfig(level=getattr(logging, LOG_LEVEL, logging.INFO))
logger = logging.getLogger("dicom_hl7_mcp")
install_phi_filter("dicom_hl7_mcp")

# Create the MCP server
app = Server("dicom-hl7-mcp")


# ---------------------------------------------------------------
# Tool Definitions
# ---------------------------------------------------------------

TOOLS = [
    # Free Tier
    Tool(
        name="lookup_dicom_tag",
        description=(
            "Look up any DICOM tag by group/element number or keyword. "
            "Returns tag number, name, VR, VM, description, common values, and usage notes. "
            "Accepts formats: '0010,0010', '(0010,0010)', 'PatientName', 'patient name'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "DICOM tag number (e.g., '0010,0010') or keyword (e.g., 'PatientName', 'patient name').",
                },
            },
            "required": ["tag"],
        },
    ),
    Tool(
        name="explain_dicom_tag",
        description=(
            "Get a detailed explanation of a DICOM tag with context, including what it is, "
            "when it's used, common values, vendor quirks (Philips, GE, Siemens), gotchas, "
            "and related tags."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "DICOM tag identifier (number or keyword).",
                },
            },
            "required": ["tag"],
        },
    ),
    Tool(
        name="parse_hl7_message",
        description=(
            "Parse an HL7 v2.x message into human-readable format. "
            "Returns parsed segments with field names, values, table lookups, and explanations. "
            "Supports MSH, PID, PV1, OBR, OBX, ORC, DG1, AL1, NK1, IN1, and more."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Raw HL7 v2.x message string (pipe-delimited). Segments separated by \\r, \\n, or \\r\\n.",
                },
            },
            "required": ["message"],
        },
    ),
    Tool(
        name="explain_hl7_segment",
        description=(
            "Explain what an HL7 segment does and list all its fields with positions, "
            "data types, optionality, table references, and descriptions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "segment_name": {
                    "type": "string",
                    "description": "HL7 segment identifier (e.g., 'PID', 'OBX', 'MSH', 'ORC').",
                },
            },
            "required": ["segment_name"],
        },
    ),
    Tool(
        name="lookup_hl7_table",
        description=(
            "Look up HL7 table values. Returns the table name and all defined values "
            "with descriptions. Example: Table 0001 = Administrative Sex."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "table_number": {
                    "type": "string",
                    "description": "HL7 table number (e.g., '0001', '0004', '76'). Leading zeros optional.",
                },
            },
            "required": ["table_number"],
        },
    ),

    # Premium Tier
    Tool(
        name="map_dicom_to_hl7",
        description=(
            "[Premium] Map DICOM tags to equivalent HL7 v2 fields. "
            "Returns corresponding HL7 segment.field, mapping notes, and data type conversions."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "DICOM tag identifier (number or keyword). Example: '0010,0010' or 'PatientName'.",
                },
            },
            "required": ["tag"],
        },
    ),
    Tool(
        name="map_hl7_to_fhir",
        description=(
            "[Premium] Map HL7 v2 segments/fields to FHIR R4 resources. "
            "Returns FHIR resource, element path, ConceptMap reference, and conversion notes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "field_ref": {
                    "type": "string",
                    "description": "HL7 field reference in SEGMENT-POSITION format (e.g., 'PID-3', 'OBR-4', 'PV1-7').",
                },
            },
            "required": ["field_ref"],
        },
    ),
    Tool(
        name="generate_mirth_channel",
        description=(
            "[Premium] Generate Mirth Connect channel configuration XML. "
            "Creates a channel skeleton with source/destination connectors, "
            "transformer steps, filter logic, and implementation notes."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "source_type": {
                    "type": "string",
                    "description": "Source data format: 'HL7v2', 'DICOM', 'FHIR', 'Database', or 'File'.",
                },
                "destination_type": {
                    "type": "string",
                    "description": "Destination data format: 'HL7v2', 'FHIR', 'Database', 'File', or 'HTTP'.",
                },
                "use_case": {
                    "type": "string",
                    "description": "Description of the integration use case (e.g., 'ADT feed from Epic to PACS').",
                },
            },
            "required": ["source_type", "destination_type", "use_case"],
        },
    ),
    Tool(
        name="validate_hl7_message",
        description=(
            "[Premium] Validate an HL7 v2.x message against the standard. "
            "Checks required fields, data types, table values, segment structure, "
            "and cross-segment consistency."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Raw HL7 v2.x message string to validate.",
                },
            },
            "required": ["message"],
        },
    ),
    Tool(
        name="explain_integration_pattern",
        description=(
            "[Premium] Explain common healthcare integration patterns including "
            "message flow diagrams, trigger events, expected segments, common pitfalls, "
            "and best practices. Patterns: 'ADT feed', 'order to result', 'radiology workflow', "
            "'lab interface', 'report distribution', 'patient merge', 'charge posting'."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "pattern_name": {
                    "type": "string",
                    "description": "Integration pattern name (e.g., 'ADT feed', 'radiology workflow', 'order to result').",
                },
            },
            "required": ["pattern_name"],
        },
    ),
    Tool(
        name="decode_private_tags",
        description=(
            "[Premium] Decode vendor-specific private DICOM tags. "
            "Returns known private tag meaning for Philips, GE, Siemens, Fuji, Agfa, Canon/Toshiba, Hologic."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "tag": {
                    "type": "string",
                    "description": "Private DICOM tag number (e.g., '0019,100C', '0029,1010').",
                },
                "vendor": {
                    "type": "string",
                    "description": "Optional vendor hint: 'GE', 'Siemens', 'Philips', 'Fuji', 'Agfa', 'Canon', 'Toshiba', 'Hologic'.",
                    "default": "",
                },
            },
            "required": ["tag"],
        },
    ),
    Tool(
        name="generate_sample_message",
        description=(
            "[Premium] Generate realistic sample HL7 messages for testing. "
            "Supports ADT^A01, ADT^A04, ADT^A08, ADT^A03, ADT^A34, ADT^A40, "
            "ORM^O01, ORU^R01, MDM^T02, SIU^S12, DFT^P03."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "message_type": {
                    "type": "string",
                    "description": "HL7 message type (e.g., 'ADT^A01', 'ORM^O01', 'ORU^R01').",
                },
                "scenario": {
                    "type": "string",
                    "description": "Optional scenario description (e.g., 'emergency CT', 'routine MRI', 'outpatient X-ray').",
                    "default": "",
                },
            },
            "required": ["message_type"],
        },
    ),
] + PACS_TOOLS + PACS_COMBINED_TOOLS


# ---------------------------------------------------------------
# MCP Server Handlers
# ---------------------------------------------------------------

@app.list_tools()
async def list_tools() -> list[Tool]:
    """Return the list of available tools."""
    return TOOLS


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Dispatch tool calls to the appropriate handler."""
    logger.debug(f"Tool call: {name} with args: {arguments}")

    try:
        result = _dispatch_tool(name, arguments)
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}", exc_info=True)
        result = f"Error executing {name}: {str(e)}"

    return [TextContent(type="text", text=result)]


def _dispatch_tool(name: str, arguments: dict) -> str:
    """Dispatch to the correct tool function."""
    # Free tier tools
    if name == "lookup_dicom_tag":
        return lookup_dicom_tag(arguments["tag"])
    elif name == "explain_dicom_tag":
        return explain_dicom_tag(arguments["tag"])
    elif name == "parse_hl7_message":
        return parse_hl7_message(arguments["message"])
    elif name == "explain_hl7_segment":
        return explain_hl7_segment(arguments["segment_name"])
    elif name == "lookup_hl7_table":
        return lookup_hl7_table(arguments["table_number"])

    # Premium tier tools
    elif name == "map_dicom_to_hl7":
        return map_dicom_to_hl7(arguments["tag"])
    elif name == "map_hl7_to_fhir":
        return map_hl7_to_fhir(arguments["field_ref"])
    elif name == "generate_mirth_channel":
        return generate_mirth_channel(
            arguments["source_type"],
            arguments["destination_type"],
            arguments["use_case"],
        )
    elif name == "validate_hl7_message":
        return validate_hl7_message(arguments["message"])
    elif name == "explain_integration_pattern":
        return explain_integration_pattern(arguments["pattern_name"])
    elif name == "decode_private_tags":
        return decode_private_tags(
            arguments["tag"],
            arguments.get("vendor", ""),
        )
    elif name == "generate_sample_message":
        return generate_sample_message(
            arguments["message_type"],
            arguments.get("scenario", ""),
        )

    # PACS tools
    elif name.startswith("pacs_study_"):
        return dispatch_pacs_combined_tool(name, arguments)
    elif name.startswith("pacs_"):
        return dispatch_pacs_tool(name, arguments)

    else:
        return f"Unknown tool: {name}"


def main() -> None:
    """Run the MCP server."""
    import asyncio

    async def _run() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await app.run(read_stream, write_stream, app.create_initialization_options())

    asyncio.run(_run())


if __name__ == "__main__":
    main()
