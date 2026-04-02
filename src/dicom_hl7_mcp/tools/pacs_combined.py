"""Combined PACS + interoperability tools (Premium Tier).

The differentiator: query a real study from PACS and instantly show
its DICOM→HL7→FHIR mapping with a generated HL7 message skeleton.
"""

from __future__ import annotations

from mcp.types import Tool

from dicom_hl7_mcp.config import get_pacs_protocol, is_pacs_configured
from dicom_hl7_mcp.pacs import require_pacs_deps
from dicom_hl7_mcp.pacs.connection import pacs_find
from dicom_hl7_mcp.pacs.models import QueryFilters, StudyResult
from dicom_hl7_mcp.pacs.phi_guard import format_pacs_result, sanitize_exception
from dicom_hl7_mcp.utils.license import require_premium


# ---------------------------------------------------------------
# Tool Definition
# ---------------------------------------------------------------

PACS_COMBINED_TOOLS = [
    Tool(
        name="pacs_study_summary",
        description=(
            "[Premium] Query a study from PACS and show its complete interoperability mapping. "
            "Returns: (1) study metadata from PACS, (2) DICOM-to-HL7 field mapping for key fields, "
            "(3) HL7-to-FHIR resource mapping, (4) a generated HL7 ORM^O01 message skeleton "
            "pre-filled with the study's actual data. This is the bridge between 'what's in PACS' "
            "and 'how do I represent it in HL7/FHIR'. "
            "Search by Study Instance UID or accession number."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "study_instance_uid": {
                    "type": "string",
                    "description": "Study Instance UID to look up.",
                    "default": "",
                },
                "accession_number": {
                    "type": "string",
                    "description": "Accession number to look up (alternative to UID).",
                    "default": "",
                },
            },
        },
    ),
]


# ---------------------------------------------------------------
# Key DICOM fields to map (tag keyword -> (group, element))
# ---------------------------------------------------------------

_KEY_STUDY_FIELDS = [
    ("PatientName", "0010,0010", "PID-5"),
    ("PatientID", "0010,0020", "PID-3"),
    ("PatientBirthDate", "0010,0030", "PID-7"),
    ("PatientSex", "0010,0040", "PID-8"),
    ("AccessionNumber", "0008,0050", "OBR-18"),
    ("StudyDate", "0008,0020", "OBR-7"),
    ("StudyDescription", "0008,1030", "OBR-4"),
    ("ReferringPhysicianName", "0008,0090", "PV1-8"),
    ("InstitutionName", "0008,0080", "MSH-4"),
    ("ModalitiesInStudy", "0008,0061", "OBR-24"),
]


def dispatch_pacs_combined_tool(name: str, arguments: dict) -> str:
    """Dispatch a combined PACS tool call.

    Args:
        name: Tool name.
        arguments: Tool arguments.

    Returns:
        Formatted result string.
    """
    # Premium check
    premium_check = require_premium(name)
    if premium_check:
        return premium_check

    # Dependency check
    protocol = get_pacs_protocol()
    dep_check = require_pacs_deps(protocol)
    if dep_check:
        return dep_check

    # Configuration check
    if not is_pacs_configured():
        return (
            "No PACS connection configured.\n\n"
            "Set environment variables for DIMSE:\n"
            "  DICOM_HL7_PACS_AE_TITLE, DICOM_HL7_PACS_HOST, DICOM_HL7_PACS_PORT\n\n"
            "Or for DICOMweb:\n"
            "  DICOM_HL7_DICOMWEB_URL\n"
        )

    try:
        if name == "pacs_study_summary":
            return _handle_study_summary(arguments)
        return f"Unknown combined tool: {name}"
    except Exception as exc:
        return f"Error in {name}: {sanitize_exception(exc)}"


def _handle_study_summary(arguments: dict) -> str:
    """Query a study from PACS and generate a complete interoperability summary."""
    study_uid = arguments.get("study_instance_uid", "")
    accession = arguments.get("accession_number", "")

    if not study_uid and not accession:
        return "Provide either study_instance_uid or accession_number to look up a study."

    # Step 1: Query PACS for the study
    filters = QueryFilters(limit=1)
    if study_uid:
        filters.study_instance_uid = study_uid
    elif accession:
        filters.accession_number = accession

    results = pacs_find(filters)

    if not results:
        search_term = study_uid or accession
        return format_pacs_result(f"No study found matching: {search_term}")

    study = results[0]
    if not isinstance(study, StudyResult):
        return format_pacs_result("Unexpected result type from PACS query.")

    # Step 2: Build the interoperability summary
    lines = [
        "PACS Study Interoperability Summary",
        "=" * 70,
        "",
        "SECTION 1: STUDY METADATA (from PACS)",
        "-" * 40,
    ]

    # Display study metadata
    study_data = study.model_dump()
    for key, value in study_data.items():
        if value:
            label = key.replace("_", " ").title()
            lines.append(f"  {label}: {value}")

    # Step 3: DICOM → HL7 mapping
    lines.extend([
        "",
        "SECTION 2: DICOM → HL7 v2 FIELD MAPPING",
        "-" * 40,
        f"  {'DICOM Tag':<25} {'Value':<25} {'HL7 Field':<15}",
        f"  {'─' * 25} {'─' * 25} {'─' * 15}",
    ])

    for field_name, dicom_tag, hl7_field in _KEY_STUDY_FIELDS:
        value = study_data.get(_camel_to_snake(field_name), "")
        if value:
            lines.append(f"  {field_name:<25} {str(value)[:25]:<25} {hl7_field:<15}")

    # Step 4: HL7 → FHIR mapping
    lines.extend([
        "",
        "SECTION 3: HL7 v2 → FHIR R4 RESOURCE MAPPING",
        "-" * 40,
        f"  {'HL7 Field':<15} {'FHIR Resource':<25} {'FHIR Path':<30}",
        f"  {'─' * 15} {'─' * 25} {'─' * 30}",
    ])

    # Map the key HL7 fields to FHIR
    _hl7_to_fhir_quick = {
        "PID-3": ("Patient", "Patient.identifier"),
        "PID-5": ("Patient", "Patient.name"),
        "PID-7": ("Patient", "Patient.birthDate"),
        "PID-8": ("Patient", "Patient.gender"),
        "PV1-8": ("Encounter", "Encounter.participant"),
        "OBR-4": ("ServiceRequest", "ServiceRequest.code"),
        "OBR-7": ("ServiceRequest", "ServiceRequest.occurrenceDateTime"),
        "OBR-18": ("ServiceRequest", "ServiceRequest.identifier"),
        "OBR-24": ("ImagingStudy", "ImagingStudy.modality"),
        "MSH-4": ("MessageHeader", "MessageHeader.source.endpoint"),
    }

    for _, _, hl7_field in _KEY_STUDY_FIELDS:
        if hl7_field in _hl7_to_fhir_quick:
            fhir_resource, fhir_path = _hl7_to_fhir_quick[hl7_field]
            lines.append(f"  {hl7_field:<15} {fhir_resource:<25} {fhir_path:<30}")

    # Step 5: Generate HL7 ORM^O01 skeleton
    lines.extend([
        "",
        "SECTION 4: GENERATED HL7 ORM^O01 MESSAGE",
        "-" * 40,
        "  (Pre-filled with study data from PACS)",
        "",
    ])

    orm_message = _generate_orm(study)
    for seg in orm_message:
        lines.append(f"  {seg}")

    # Step 6: Integration pattern reference
    lines.extend([
        "",
        "SECTION 5: INTEGRATION CONTEXT",
        "-" * 40,
        "  Pattern: Radiology Order-to-Result Workflow (IHE SWF)",
        "  This study would typically flow through:",
        "    1. HIS/EHR sends ORM^O01 → Integration Engine",
        "    2. Integration Engine → RIS (order creation)",
        "    3. RIS → Modality Worklist (MWL C-FIND)",
        "    4. Modality acquires images → PACS (C-STORE)",
        "    5. RIS sends ORU^R01 (report) → Integration Engine → EHR",
        "",
        "  Use 'explain_integration_pattern' with 'radiology workflow' for full details.",
    ])

    return format_pacs_result("\n".join(lines))


def _generate_orm(study: StudyResult) -> list[str]:
    """Generate an HL7 ORM^O01 message skeleton pre-filled with study data.

    Args:
        study: The study result from PACS.

    Returns:
        List of HL7 segment strings.
    """
    # Format patient name for HL7 (DICOM uses ^ separator already)
    patient_name = study.patient_name.replace("^", "^") if study.patient_name else ""

    # Format study date for HL7 timestamp
    study_datetime = study.study_date
    if study.study_time:
        study_datetime += study.study_time[:4]  # HHMM

    segments = [
        f"MSH|^~\\&|PACS_MCP|{study.institution_name or 'FACILITY'}|RECEIVING_APP|RECEIVING_FAC|"
        f"{study.study_date or ''}||ORM^O01^ORM_O01|MSG001|P|2.5.1",

        f"PID|||{study.patient_id or ''}^^^FACILITY^MR||{patient_name}||"
        f"{study.patient_birth_date or ''}|{study.patient_sex or ''}",

        f"PV1||I|||||{study.referring_physician_name or ''}",

        "ORC|NW|ORD001|FILL001||CM",

        f"OBR|1|ORD001|FILL001|{study.study_description or 'IMAGING'}^^^LOCAL||"
        f"{study_datetime}|||||||||{study.referring_physician_name or ''}||||"
        f"{study.accession_number or ''}||||{study.modalities_in_study or ''}",
    ]

    return segments


def _camel_to_snake(name: str) -> str:
    """Convert CamelCase to snake_case."""
    result = []
    for i, char in enumerate(name):
        if char.isupper() and i > 0:
            result.append("_")
        result.append(char.lower())
    return "".join(result)
