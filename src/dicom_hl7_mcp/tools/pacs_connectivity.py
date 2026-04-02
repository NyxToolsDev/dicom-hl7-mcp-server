"""PACS connectivity tools (Premium Tier).

Provides tools for querying and interacting with PACS servers
via traditional DICOM (C-FIND/C-MOVE/C-ECHO) or DICOMweb (QIDO-RS/WADO-RS).
"""

from __future__ import annotations

from mcp.types import Tool

from dicom_hl7_mcp.config import PACS_ALLOW_RETRIEVE, get_pacs_protocol, is_pacs_configured
from dicom_hl7_mcp.pacs import require_pacs_deps
from dicom_hl7_mcp.pacs.connection import pacs_echo, pacs_find, pacs_get_metadata, pacs_move
from dicom_hl7_mcp.pacs.models import QueryFilters
from dicom_hl7_mcp.pacs.phi_guard import format_pacs_result, sanitize_exception
from dicom_hl7_mcp.utils.license import require_premium


# ---------------------------------------------------------------
# Tool Definitions (registered in server.py)
# ---------------------------------------------------------------

PACS_TOOLS = [
    Tool(
        name="pacs_echo",
        description=(
            "[Premium] Verify PACS connectivity. Sends a C-ECHO (DIMSE) or HTTP ping (DICOMweb) "
            "to confirm the PACS server is reachable and accepting connections. "
            "Returns success/failure, response time, and connection details."
        ),
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="pacs_query",
        description=(
            "[Premium] Search PACS for studies or series. Supports filtering by patient ID, "
            "patient name, accession number, study date (YYYYMMDD or range), modality, and "
            "study description. Returns up to 50 results. Uses C-FIND (DIMSE) or QIDO-RS (DICOMweb)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "query_level": {
                    "type": "string",
                    "description": "Query level: 'STUDY' or 'SERIES'. Default: STUDY.",
                    "default": "STUDY",
                    "enum": ["STUDY", "SERIES"],
                },
                "patient_id": {
                    "type": "string",
                    "description": "Filter by Patient ID.",
                    "default": "",
                },
                "patient_name": {
                    "type": "string",
                    "description": "Filter by patient name. Supports wildcards (* or ?).",
                    "default": "",
                },
                "accession_number": {
                    "type": "string",
                    "description": "Filter by accession number.",
                    "default": "",
                },
                "study_date": {
                    "type": "string",
                    "description": "Filter by study date. YYYYMMDD for exact, YYYYMMDD-YYYYMMDD for range.",
                    "default": "",
                },
                "modality": {
                    "type": "string",
                    "description": "Filter by modality (CT, MR, US, XR, MG, etc.).",
                    "default": "",
                },
                "study_description": {
                    "type": "string",
                    "description": "Filter by study description (partial match).",
                    "default": "",
                },
                "study_instance_uid": {
                    "type": "string",
                    "description": "Filter by Study Instance UID. Required for SERIES level queries.",
                    "default": "",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results to return (1-50). Default: 10.",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 50,
                },
            },
        },
    ),
    Tool(
        name="pacs_get_metadata",
        description=(
            "[Premium] Retrieve detailed metadata for a study or series from PACS. "
            "Returns DICOM header information including patient, study, series, and equipment details. "
            "Uses WADO-RS metadata (DICOMweb) or series-level C-FIND (DIMSE)."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "study_instance_uid": {
                    "type": "string",
                    "description": "Study Instance UID to retrieve metadata for.",
                },
                "series_instance_uid": {
                    "type": "string",
                    "description": "Optional Series Instance UID for series-level metadata.",
                    "default": "",
                },
            },
            "required": ["study_instance_uid"],
        },
    ),
    Tool(
        name="pacs_retrieve",
        description=(
            "[Premium] Initiate C-MOVE to send images from PACS to a destination AE title. "
            "This moves real images across the network — use with care. "
            "Only available via DIMSE protocol. Requires DICOM_HL7_PACS_ALLOW_RETRIEVE=true."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "study_instance_uid": {
                    "type": "string",
                    "description": "Study Instance UID to retrieve.",
                },
                "destination_ae_title": {
                    "type": "string",
                    "description": "Destination AE title to send images to.",
                },
                "series_instance_uid": {
                    "type": "string",
                    "description": "Optional Series Instance UID for series-level retrieve.",
                    "default": "",
                },
            },
            "required": ["study_instance_uid", "destination_ae_title"],
        },
    ),
]


# ---------------------------------------------------------------
# Tool Dispatch
# ---------------------------------------------------------------

def dispatch_pacs_tool(name: str, arguments: dict) -> str:
    """Dispatch a PACS tool call to the appropriate handler.

    Three-layer gating:
    1. Premium license check
    2. Dependency check (pynetdicom/httpx installed?)
    3. Configuration check (PACS connection configured?)

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        Formatted result string.
    """
    # Layer 1: Premium check
    premium_check = require_premium(name)
    if premium_check:
        return premium_check

    # Layer 2: Dependency check
    protocol = get_pacs_protocol()
    dep_check = require_pacs_deps(protocol)
    if dep_check:
        return dep_check

    # Layer 3: Configuration check (except pacs_echo which gives a helpful error itself)
    if name != "pacs_echo" and not is_pacs_configured():
        return (
            "No PACS connection configured.\n\n"
            "Set environment variables for DIMSE:\n"
            "  DICOM_HL7_PACS_AE_TITLE, DICOM_HL7_PACS_HOST, DICOM_HL7_PACS_PORT\n\n"
            "Or for DICOMweb:\n"
            "  DICOM_HL7_DICOMWEB_URL\n"
        )

    try:
        if name == "pacs_echo":
            return _handle_echo()
        elif name == "pacs_query":
            return _handle_query(arguments)
        elif name == "pacs_get_metadata":
            return _handle_get_metadata(arguments)
        elif name == "pacs_retrieve":
            return _handle_retrieve(arguments)
        else:
            return f"Unknown PACS tool: {name}"
    except Exception as exc:
        return f"Error in {name}: {sanitize_exception(exc)}"


def _handle_echo() -> str:
    """Handle pacs_echo tool call."""
    result = pacs_echo()

    lines = [
        "PACS Connectivity Test",
        "=" * 50,
        f"Status:        {'SUCCESS' if result.success else 'FAILED'}",
        f"Protocol:      {result.protocol}",
        f"Response Time: {result.response_time_ms:.1f} ms",
        f"Message:       {result.message}",
    ]
    if result.remote_ae:
        lines.append(f"Remote AE:     {result.remote_ae}")
    if result.local_ae:
        lines.append(f"Local AE:      {result.local_ae}")

    return "\n".join(lines)


def _handle_query(arguments: dict) -> str:
    """Handle pacs_query tool call."""
    filters = QueryFilters(
        query_level=arguments.get("query_level", "STUDY"),
        patient_id=arguments.get("patient_id", ""),
        patient_name=arguments.get("patient_name", ""),
        accession_number=arguments.get("accession_number", ""),
        study_date=arguments.get("study_date", ""),
        modality=arguments.get("modality", ""),
        study_description=arguments.get("study_description", ""),
        study_instance_uid=arguments.get("study_instance_uid", ""),
        limit=arguments.get("limit", 10),
    )

    results = pacs_find(filters)

    if not results:
        return format_pacs_result("No results found matching the query filters.")

    lines = [f"Found {len(results)} {filters.query_level.lower()}(s):", "=" * 70]

    for i, r in enumerate(results, 1):
        lines.append(f"\n--- Result {i} ---")
        data = r.model_dump()
        for key, value in data.items():
            if value:  # Only show non-empty fields
                label = key.replace("_", " ").title()
                lines.append(f"  {label}: {value}")

    return format_pacs_result("\n".join(lines))


def _handle_get_metadata(arguments: dict) -> str:
    """Handle pacs_get_metadata tool call."""
    study_uid = arguments["study_instance_uid"]
    series_uid = arguments.get("series_instance_uid", "")

    metadata = pacs_get_metadata(study_uid, series_uid)

    if not metadata:
        return format_pacs_result(f"No metadata found for study {study_uid}")

    lines = [
        f"Metadata for Study: {study_uid}",
        "=" * 70,
        f"Retrieved {len(metadata)} metadata object(s)",
    ]

    # Format each metadata object
    for i, item in enumerate(metadata[:10], 1):  # Limit display to 10
        lines.append(f"\n--- Object {i} ---")
        if isinstance(item, dict):
            for key, value in item.items():
                if value:
                    label = key.replace("_", " ").title()
                    lines.append(f"  {label}: {value}")

    if len(metadata) > 10:
        lines.append(f"\n... and {len(metadata) - 10} more objects")

    return format_pacs_result("\n".join(lines))


def _handle_retrieve(arguments: dict) -> str:
    """Handle pacs_retrieve tool call."""
    # Double-gate: check PACS_ALLOW_RETRIEVE
    if not PACS_ALLOW_RETRIEVE:
        return (
            "C-MOVE retrieve is disabled by default for safety.\n\n"
            "This operation moves real DICOM images across the network.\n"
            "To enable, set: DICOM_HL7_PACS_ALLOW_RETRIEVE=true\n\n"
            "Only enable this if you understand the implications and have\n"
            "permission to move images within your environment."
        )

    study_uid = arguments["study_instance_uid"]
    dest_ae = arguments["destination_ae_title"]
    series_uid = arguments.get("series_instance_uid", "")

    result = pacs_move(study_uid, dest_ae, series_uid)

    lines = [
        "PACS Retrieve (C-MOVE)",
        "=" * 50,
        f"Status:      {'SUCCESS' if result.success else 'FAILED'}",
        f"Study UID:   {study_uid}",
        f"Destination: {dest_ae}",
        f"Message:     {result.message}",
    ]
    if result.num_completed:
        lines.append(f"Completed:   {result.num_completed}")
    if result.num_failed:
        lines.append(f"Failed:      {result.num_failed}")
    if result.num_warning:
        lines.append(f"Warnings:    {result.num_warning}")

    return format_pacs_result("\n".join(lines))
