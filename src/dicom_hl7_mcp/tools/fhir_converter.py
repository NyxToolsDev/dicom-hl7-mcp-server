"""FHIR conversion, validation, and sample generation tools (Premium Tier)."""

from __future__ import annotations

import re
from datetime import datetime

from dicom_hl7_mcp.knowledge.dicom_dictionary import PRIVATE_TAG_RANGES
from dicom_hl7_mcp.knowledge.hl7_segments import HL7_SEGMENTS, HL7_TABLES, HL7_MESSAGE_TYPES
from dicom_hl7_mcp.utils.license import require_premium


def validate_hl7_message(message: str) -> str:
    """Validate an HL7 v2.x message against the standard."""
    premium_check = require_premium("validate_hl7_message")
    if premium_check:
        return premium_check

    if not message or not message.strip():
        return "Error: Empty message provided."

    segments = _normalize_message(message)
    if not segments:
        return "FATAL: No segments found in message."

    errors: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    # 1. Validate MSH header
    result = _validate_msh(segments[0], errors, warnings)
    if result is None:
        return _format_validation_result(errors, warnings, info)
    field_sep, component_sep, msg_type_str = result

    # 2. Validate segment structure
    segment_ids = [s.split(field_sep)[0] if field_sep in s else s[:3] for s in segments]
    _validate_segment_order(msg_type_str, segment_ids, errors, info)

    # 3. Validate individual segments
    _validate_segments(segments, field_sep, component_sep, errors, warnings, info)

    # 4. Cross-segment validation
    _validate_cross_segments(segments, segment_ids, field_sep, component_sep, errors, warnings, info)

    return _format_validation_result(errors, warnings, info)


def _normalize_message(message: str) -> list[str]:
    """Normalize line endings and split into segments."""
    clean = message.strip()
    clean = clean.replace("\\r\\n", "\n").replace("\\r", "\n").replace("\\n", "\n")
    clean = clean.replace("\r\n", "\n").replace("\r", "\n")
    return [s.strip() for s in clean.split("\n") if s.strip()]


def _validate_msh(
    msh: str, errors: list[str], warnings: list[str],
) -> tuple[str, str, str] | None:
    """Validate MSH segment. Returns (field_sep, component_sep, msg_type_str) or None on fatal error."""
    if not msh.startswith("MSH"):
        errors.append("Message must start with MSH segment.")
        return None

    if len(msh) < 8:
        errors.append("MSH segment too short (missing encoding characters).")
        return None

    field_sep = msh[3]
    component_sep = msh[4]
    msh_fields = _split_msh_fields(msh, field_sep)

    _validate_required_field(msh_fields, 7, "MSH-7 (Date/Time of Message)", errors)
    _validate_required_field(msh_fields, 9, "MSH-9 (Message Type)", errors)
    _validate_required_field(msh_fields, 10, "MSH-10 (Message Control ID)", errors)
    _validate_required_field(msh_fields, 11, "MSH-11 (Processing ID)", errors)
    _validate_required_field(msh_fields, 12, "MSH-12 (Version ID)", errors)

    if len(msh_fields) > 7 and msh_fields[7]:
        dt_str = msh_fields[7].split(component_sep)[0]
        if not re.match(r"^\d{8,14}", dt_str):
            errors.append(f"MSH-7 date/time format invalid: '{dt_str}'. Expected YYYYMMDD[HHMMSS].")

    msg_type_str = _validate_msh_message_type(msh_fields, component_sep, warnings)
    _validate_msh_processing_id(msh_fields, component_sep, errors, warnings)

    return field_sep, component_sep, msg_type_str


def _validate_msh_message_type(
    msh_fields: list[str], component_sep: str, warnings: list[str],
) -> str:
    """Validate MSH-9 message type field. Returns the message type string."""
    if len(msh_fields) <= 9 or not msh_fields[9]:
        return ""
    msg_type_str = msh_fields[9].replace(component_sep, "^")
    if "^" not in msg_type_str:
        warnings.append(f"MSH-9 should contain message type and trigger event (e.g., ADT^A01). Got: '{msg_type_str}'.")
    else:
        parts = msg_type_str.split("^")
        full_type = f"{parts[0]}^{parts[1]}" if len(parts) >= 2 else parts[0]
        if full_type not in HL7_MESSAGE_TYPES and parts[0] not in ("ACK",):
            warnings.append(f"Message type '{full_type}' not found in standard message type table.")
    return msg_type_str


def _validate_msh_processing_id(
    msh_fields: list[str], component_sep: str, errors: list[str], warnings: list[str],
) -> None:
    """Validate MSH-11 processing ID."""
    if len(msh_fields) <= 11 or not msh_fields[11]:
        return
    proc_id = msh_fields[11].split(component_sep)[0]
    if proc_id not in ("P", "D", "T"):
        errors.append(f"MSH-11 Processing ID must be P, D, or T. Got: '{proc_id}'.")
    if proc_id == "D":
        warnings.append("MSH-11 Processing ID is 'D' (Debug). Do not use in production.")
    elif proc_id == "T":
        warnings.append("MSH-11 Processing ID is 'T' (Training). Do not use in production.")


def _validate_segment_order(
    msg_type_str: str, segment_ids: list[str], errors: list[str], info: list[str],
) -> None:
    """Check for required/optional segments based on message type."""
    if not msg_type_str:
        return
    parts = msg_type_str.split("^")
    full_type = f"{parts[0]}^{parts[1]}" if len(parts) >= 2 else parts[0]
    type_info = HL7_MESSAGE_TYPES.get(full_type)
    if not type_info:
        return
    for req_seg in type_info.get("required_segments", []):
        if req_seg not in segment_ids:
            errors.append(f"Required segment {req_seg} is missing for {full_type} message.")
    for opt_seg in type_info.get("optional_segments", []):
        if opt_seg in segment_ids:
            info.append(f"Optional segment {opt_seg} is present.")


def _validate_segments(
    segments: list[str],
    field_sep: str,
    component_sep: str,
    errors: list[str],
    warnings: list[str],
    info: list[str],
) -> None:
    """Validate individual segments against the HL7 standard."""
    for seg_text in segments:
        seg_fields = seg_text.split(field_sep)
        seg_id = seg_fields[0]

        if seg_id == "MSH":
            continue

        seg_info = HL7_SEGMENTS.get(seg_id)
        if seg_info is None:
            if seg_id.startswith("Z"):
                info.append(f"Custom Z-segment found: {seg_id}")
            else:
                warnings.append(f"Unknown segment: {seg_id}")
            continue

        for field_def in seg_info.get("fields", []):
            if field_def["required"] == "R":
                pos = field_def["position"]
                if pos >= len(seg_fields) or not seg_fields[pos]:
                    errors.append(
                        f"{seg_id}-{pos} ({field_def['name']}) is required but empty/missing."
                    )

            if field_def.get("table") and field_def["position"] < len(seg_fields):
                value = seg_fields[field_def["position"]]
                if value:
                    primary_val = value.split(component_sep)[0]
                    if primary_val:
                        table_info = HL7_TABLES.get(field_def["table"])
                        if table_info and primary_val not in table_info["values"]:
                            warnings.append(
                                f"{seg_id}-{field_def['position']} value '{primary_val}' "
                                f"not found in Table {field_def['table']} ({table_info['name']})."
                            )


def _validate_cross_segments(
    segments: list[str],
    segment_ids: list[str],
    field_sep: str,
    component_sep: str,
    errors: list[str],
    warnings: list[str],
    info: list[str],
) -> None:
    """Cross-segment validation (PID, ORC/OBR matching)."""
    if "PID" in segment_ids:
        pid_fields = segments[segment_ids.index("PID")].split(field_sep)
        if len(pid_fields) > 3 and pid_fields[3]:
            info.append(f"Patient ID: {pid_fields[3].split(component_sep)[0]}")
        else:
            errors.append("PID-3 (Patient Identifier List) is empty — this is required.")
        if len(pid_fields) > 5 and pid_fields[5]:
            info.append(f"Patient Name: {pid_fields[5]}")
        else:
            warnings.append("PID-5 (Patient Name) is empty.")

    if "ORC" in segment_ids and "OBR" in segment_ids:
        orc_fields = segments[segment_ids.index("ORC")].split(field_sep)
        obr_fields = segments[segment_ids.index("OBR")].split(field_sep)
        orc_filler = orc_fields[3] if len(orc_fields) > 3 else ""
        obr_filler = obr_fields[3] if len(obr_fields) > 3 else ""
        if orc_filler and obr_filler and orc_filler != obr_filler:
            warnings.append(
                f"ORC-3 ('{orc_filler}') and OBR-3 ('{obr_filler}') Filler Order Numbers don't match."
            )


def _split_msh_fields(msh: str, field_sep: str) -> list[str]:
    """Split MSH segment into fields, accounting for MSH-1."""
    parts = msh.split(field_sep)
    return [parts[0], field_sep] + parts[1:]


def _validate_required_field(fields: list[str], pos: int, name: str, errors: list[str]) -> None:
    """Check if a required field is present and non-empty."""
    if pos >= len(fields) or not fields[pos]:
        errors.append(f"{name} is required but missing/empty.")


def _format_validation_result(errors: list[str], warnings: list[str], info: list[str]) -> str:
    """Format validation results."""
    parts = [
        "=" * 60,
        "HL7 MESSAGE VALIDATION RESULTS",
        "=" * 60,
        "",
    ]

    if not errors and not warnings:
        parts.append("PASS: No errors or warnings found.")
    elif not errors:
        parts.append("PASS WITH WARNINGS: No errors, but warnings noted below.")
    else:
        parts.append(f"FAIL: {len(errors)} error(s) found.")

    parts.append("")

    if errors:
        parts.append(f"ERRORS ({len(errors)}):")
        for i, e in enumerate(errors, 1):
            parts.append(f"  {i}. [ERROR] {e}")
        parts.append("")

    if warnings:
        parts.append(f"WARNINGS ({len(warnings)}):")
        for i, w in enumerate(warnings, 1):
            parts.append(f"  {i}. [WARN] {w}")
        parts.append("")

    if info:
        parts.append(f"INFO ({len(info)}):")
        for i, inf in enumerate(info, 1):
            parts.append(f"  {i}. [INFO] {inf}")

    return "\n".join(parts)


def decode_private_tags(tag: str, vendor: str = "") -> str:
    """Decode vendor-specific private DICOM tags.

    Args:
        tag: Private tag number (e.g., "0019,100C", "0029,1010").
        vendor: Optional vendor hint ("GE", "Siemens", "Philips", "Fuji",
            "Agfa", "Canon", "Toshiba", "Hologic").

    Returns:
        Known private tag meaning, vendor information, and notes.
    """
    premium_check = require_premium("decode_private_tags")
    if premium_check:
        return premium_check

    # Parse the tag
    tag = tag.strip().strip("()")
    match = re.match(r"^([0-9a-fA-F]{4})\s*,\s*([0-9a-fA-F]{4})$", tag)
    if not match:
        return f"Invalid tag format: '{tag}'. Expected: GGGG,EEEE (e.g., '0019,100C')."

    group = int(match.group(1), 16)
    element = int(match.group(2), 16)
    group_hex = f"{group:04X}"

    if group % 2 == 0:
        return f"Tag ({group_hex},{element:04X}) is not a private tag (even group number). Private tags use odd group numbers."

    parts = [
        f"## Private Tag: ({group_hex},{element:04X})",
        "",
    ]

    vendor_norm = vendor.strip().lower()
    vendor_map = {
        "ge": "GE",
        "general electric": "GE",
        "gems": "GE",
        "siemens": "Siemens",
        "philips": "Philips",
        "fuji": "Fuji",
        "fujifilm": "Fuji",
        "agfa": "Agfa",
        "canon": "Canon/Toshiba",
        "toshiba": "Canon/Toshiba",
        "hologic": "Hologic",
    }
    target_vendor = vendor_map.get(vendor_norm) if vendor_norm else None

    found_any = False
    vendors_to_check = [target_vendor] if target_vendor else PRIVATE_TAG_RANGES.keys()

    for v in vendors_to_check:
        vendor_info = PRIVATE_TAG_RANGES.get(v)
        if not vendor_info:
            continue

        # Check if this group belongs to this vendor
        if group_hex.lower() not in [g.lower() for g in vendor_info["common_groups"]]:
            if target_vendor:
                parts.append(f"Group {group_hex} is not a known {v} private group.")
                parts.append(f"Known {v} groups: {', '.join(vendor_info['common_groups'])}")
            continue

        found_any = True
        tag_tuple = (group, element)
        known = vendor_info.get("known_tags", {}).get(tag_tuple)

        parts.append(f"### Vendor: {v}")
        parts.append(f"Known private groups: {', '.join(vendor_info['common_groups'])}")
        parts.append(f"Creator IDs: {', '.join(vendor_info['creator_ids'][:4])}")
        parts.append("")

        if known:
            parts.append(f"Tag Name: {known['name']}")
            parts.append(f"Notes: {known['notes']}")
        else:
            parts.append(f"Tag ({group_hex},{element:04X}) is in the {v} private group range")
            parts.append(f"but is not in our known tags database.")
            parts.append("")
            parts.append("To identify this tag:")
            parts.append(f"  1. Check the Private Creator element at ({group_hex},00{(element >> 8):02X})")
            parts.append(f"  2. Look up the creator ID in {v}'s documentation")
            parts.append(f"  3. The element's low byte ({element & 0xFF:02X}) indexes within that creator's block")

        if vendor_info.get("notes"):
            parts.append("")
            parts.append(f"Vendor Notes: {vendor_info['notes']}")
        parts.append("")

    if not found_any:
        parts.append("No matching vendor found for this private group.")
        parts.append("")
        parts.append("To identify the vendor:")
        parts.append(f"  1. Look at the Private Creator element at ({group_hex},0010) through ({group_hex},00FF)")
        parts.append("  2. The creator ID string will identify the vendor")
        parts.append("")
        parts.append("Known vendor private group ranges:")
        for v, vi in PRIVATE_TAG_RANGES.items():
            parts.append(f"  {v}: groups {', '.join(vi['common_groups'])}")

    return "\n".join(parts)


def generate_sample_message(message_type: str, scenario: str = "") -> str:
    """Generate sample HL7 messages for testing.

    Args:
        message_type: HL7 message type (e.g., "ADT^A01", "ORM^O01", "ORU^R01",
            "ADT^A08", "ADT^A34", "MDM^T02", "SIU^S12", "DFT^P03").
        scenario: Optional description of the scenario (e.g., "emergency CT",
            "routine MRI", "outpatient X-ray").

    Returns:
        Realistic sample HL7 message with meaningful test data.
    """
    premium_check = require_premium("generate_sample_message")
    if premium_check:
        return premium_check

    msg_type = message_type.strip().upper().replace(" ", "")
    if "^" not in msg_type:
        return f"Invalid message type '{msg_type}'. Expected format: TYPE^TRIGGER (e.g., 'ADT^A01')."

    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    msg_ctrl_id = f"MSG{now.strftime('%Y%m%d%H%M%S%f')[:18]}"
    scenario_lower = scenario.lower()

    generators = {
        "ADT^A01": _gen_adt_a01,
        "ADT^A04": _gen_adt_a04,
        "ADT^A08": _gen_adt_a08,
        "ADT^A03": _gen_adt_a03,
        "ADT^A34": _gen_adt_a34,
        "ADT^A40": _gen_adt_a40,
        "ORM^O01": _gen_orm_o01,
        "ORU^R01": _gen_oru_r01,
        "MDM^T02": _gen_mdm_t02,
        "SIU^S12": _gen_siu_s12,
        "DFT^P03": _gen_dft_p03,
    }

    generator = generators.get(msg_type)
    if generator is None:
        available = ", ".join(sorted(generators.keys()))
        return (
            f"Message type '{msg_type}' not supported for sample generation.\n\n"
            f"Supported types: {available}"
        )

    message = generator(timestamp, msg_ctrl_id, scenario_lower)

    parts = [
        f"## Sample {msg_type} Message",
        f"Scenario: {scenario or 'Default test scenario'}",
        f"Generated: {now.isoformat()}",
        "",
        "### Raw Message (copy below):",
        "```",
        message,
        "```",
        "",
        "### Usage Notes:",
        "- Replace test patient data before use in any environment with real patients",
        "- Message Control ID (MSH-10) should be unique per message",
        "- Timestamps should reflect actual date/time",
        "- Processing ID is set to 'T' (Training) — change to 'P' for production",
    ]

    return "\n".join(parts)


def _gen_adt_a01(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A01 (Admit/Visit Notification)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|PACS|MAIN_HOSPITAL|{ts}||ADT^A01^ADT_A01|{ctrl}|T|2.5.1\r"
        f"EVN|A01|{ts}|||JSMITH^Smith^John^^Dr.^MD\r"
        f"PID|1||MRN123456^^^MAIN_HOSP^MR~SSN987654321^^^USSSA^SS||DOE^JOHN^MICHAEL^^MR.||19650315|M|||123 MAIN ST^^ANYTOWN^NY^12345^USA^H||^PRN^PH^^^^^555^5551234|^WPN^PH^^^^^555^5555678|EN|M|CHR|ACCT20240101001|||||||N\r"
        f"PV1|1|I|4EAST^401^A^MAIN_HOSPITAL^^^^4EAST|E||PREV_LOC^^^MAIN_HOSPITAL|1234567^ATTENDING^DOCTOR^A^^DR.^MD^^NPI|9876543^REFERRING^PHYSICIAN^B^^DR.^MD^^NPI||MED|||1||5555555^ADMITTING^DOCTOR^C^^DR.^MD|IP|VN20240101001|||||||||||||||||||MAIN_HOSPITAL|||||{ts}\r"
        f"NK1|1|DOE^JANE^M|SPO|123 MAIN ST^^ANYTOWN^NY^12345|^PRN^PH^^^^^555^5559999\r"
        f"AL1|1|DA|IODINE^Iodinated Contrast|SV|ANAPHYLAXIS|20200101\r"
        f"AL1|2|DA|PENICILLIN^Penicillin|MO|HIVES\r"
        f"DG1|1||R10.9^Unspecified abdominal pain^I10||{ts}|A\r"
        f"IN1|1|BCBS001^Blue Cross Blue Shield|12345^BCBS|||||||||||20240101|20241231|||DOE^JOHN||||||||||||||987654321A"
    )


def _gen_adt_a04(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A04 (Register a Patient)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|RIS|RAD_DEPT|{ts}||ADT^A04^ADT_A01|{ctrl}|T|2.5.1\r"
        f"EVN|A04|{ts}\r"
        f"PID|1||MRN789012^^^MAIN_HOSP^MR||SMITH^JANE^A||19800722|F|||456 OAK AVE^^SOMECITY^CA^90210^USA^H||^PRN^PH^^^^^310^5551234|||||ACCT20240201001\r"
        f"PV1|1|O|RAD^WAITING^01^MAIN_HOSPITAL|R|||1111111^ORDERING^DOCTOR^D^^DR.^MD^^NPI|2222222^REFERRING^DOCTOR^E^^DR.^MD||RAD||||3||||||OP|VN20240201001\r"
        f"DG1|1||M79.3^Soft tissue disorder, unspecified^I10||{ts}|W"
    )


def _gen_adt_a08(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A08 (Update Patient Information)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|PACS|MAIN_HOSPITAL|{ts}||ADT^A08^ADT_A01|{ctrl}|T|2.5.1\r"
        f"EVN|A08|{ts}\r"
        f"PID|1||MRN123456^^^MAIN_HOSP^MR||DOE^JOHN^MICHAEL^^MR.||19650315|M|||789 NEW ADDRESS^^NEWTOWN^NY^12346^USA^H||^PRN^PH^^^^^555^5551234||EN|M|CHR|ACCT20240101001\r"
        f"PV1|1|I|4EAST^401^A^MAIN_HOSPITAL|E|||1234567^ATTENDING^DOCTOR^A^^DR.^MD^^NPI|9876543^REFERRING^PHYSICIAN^B^^DR.^MD||MED||||1||||||IP|VN20240101001"
    )


def _gen_adt_a03(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A03 (Discharge/End Visit)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|PACS|MAIN_HOSPITAL|{ts}||ADT^A03^ADT_A03|{ctrl}|T|2.5.1\r"
        f"EVN|A03|{ts}\r"
        f"PID|1||MRN123456^^^MAIN_HOSP^MR||DOE^JOHN^MICHAEL||19650315|M\r"
        f"PV1|1|I|4EAST^401^A^MAIN_HOSPITAL||||1234567^ATTENDING^DOCTOR^A^^DR.^MD||MED||||||||IP|VN20240101001||||||||||||||||||||||||{ts}"
    )


def _gen_adt_a34(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A34 (Merge Patient Information - Patient ID Only)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|PACS|MAIN_HOSPITAL|{ts}||ADT^A34^ADT_A30|{ctrl}|T|2.5.1\r"
        f"EVN|A34|{ts}\r"
        f"PID|1||MRN123456^^^MAIN_HOSP^MR||DOE^JOHN^MICHAEL||19650315|M\r"
        f"MRG|MRN999999^^^MAIN_HOSP^MR||ACCT_OLD001"
    )


def _gen_adt_a40(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ADT^A40 (Merge Patient - Patient Identifier List)."""
    return (
        f"MSH|^~\\&|ADT_SYSTEM|MAIN_HOSPITAL|PACS|MAIN_HOSPITAL|{ts}||ADT^A40^ADT_A39|{ctrl}|T|2.5.1\r"
        f"EVN|A40|{ts}\r"
        f"PID|1||MRN123456^^^MAIN_HOSP^MR||DOE^JOHN^MICHAEL||19650315|M\r"
        f"MRG|MRN999999^^^MAIN_HOSP^MR\r"
        f"PV1|1|I"
    )


def _gen_orm_o01(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ORM^O01 (Order Message)."""
    # Determine procedure based on scenario
    if "ct" in scenario:
        proc_code = "CTABD"
        proc_desc = "CT ABDOMEN PELVIS WITH CONTRAST"
        modality = "CT"
        body_part = "ABDOMEN"
    elif "mri" in scenario or "mr" in scenario:
        proc_code = "MRBRAIN"
        proc_desc = "MRI BRAIN WITHOUT CONTRAST"
        modality = "MR"
        body_part = "HEAD"
    elif "xr" in scenario or "x-ray" in scenario or "chest" in scenario:
        proc_code = "XRCHEST2"
        proc_desc = "XR CHEST 2 VIEWS"
        modality = "CR"
        body_part = "CHEST"
    elif "us" in scenario or "ultrasound" in scenario:
        proc_code = "USABD"
        proc_desc = "US ABDOMEN COMPLETE"
        modality = "US"
        body_part = "ABDOMEN"
    else:
        proc_code = "CTCHEST"
        proc_desc = "CT CHEST WITH CONTRAST"
        modality = "CT"
        body_part = "CHEST"

    return (
        f"MSH|^~\\&|CPOE|MAIN_HOSPITAL|RIS|RAD_DEPT|{ts}||ORM^O01^ORM_O01|{ctrl}|T|2.5.1\r"
        f"PID|1||MRN456789^^^MAIN_HOSP^MR||JOHNSON^ROBERT^L||19750512|M|||321 ELM ST^^ANYTOWN^CA^90001||(555)555-4321||EN|S||ACCT20240301001\r"
        f"PV1|1|O|ED^TRIAGE^01|E|||3333333^ORDERING^DOCTOR^F^^DR.^MD^^NPI|4444444^REFERRING^DOCTOR^G^^DR.^MD|||RAD||||5\r"
        f"ORC|NW|ORD20240301001^CPOE|ACC20240301001^RIS||SC|||1^^^^^R||{ts}|JNURSE^Nurse^Jenny||3333333^ORDERING^DOCTOR^F^^DR.^MD^^NPI|ED\r"
        f"OBR|1|ORD20240301001^CPOE|ACC20240301001^RIS|{proc_code}^{proc_desc}^L|||{ts}||||||||R10.9^Unspecified abdominal pain^I10|||3333333^ORDERING^DOCTOR^F^^DR.^MD||||||RAD|SC\r"
        f"DG1|1||R10.9^Unspecified abdominal pain^I10||{ts}|W\r"
        f"NTE|1||Clinical History: Patient presents with acute abdominal pain, nausea, and vomiting x 2 days."
    )


def _gen_oru_r01(ts: str, ctrl: str, scenario: str) -> str:
    """Generate ORU^R01 (Unsolicited Observation Result)."""
    report_text = (
        "EXAMINATION: CT Abdomen and Pelvis with IV Contrast\\.br\\"
        "\\.br\\"
        "CLINICAL INDICATION: Acute abdominal pain, nausea, vomiting.\\.br\\"
        "\\.br\\"
        "COMPARISON: None available.\\.br\\"
        "\\.br\\"
        "TECHNIQUE: Helical CT of the abdomen and pelvis was performed after "
        "administration of 100 mL of Omnipaque 350 IV contrast.\\.br\\"
        "\\.br\\"
        "FINDINGS:\\.br\\"
        "Liver: Normal in size and attenuation. No focal lesions.\\.br\\"
        "Gallbladder: Distended with wall thickening measuring 5mm. Pericholecystic "
        "fluid is present. Multiple gallstones identified.\\.br\\"
        "Pancreas: Normal.\\.br\\"
        "Spleen: Normal.\\.br\\"
        "Kidneys: Normal bilaterally. No hydronephrosis or stones.\\.br\\"
        "Adrenals: Normal.\\.br\\"
        "Bowel: Normal caliber. No obstruction or wall thickening.\\.br\\"
        "Appendix: Normal.\\.br\\"
        "No free air. Small amount of free fluid in the right lower quadrant.\\.br\\"
        "Lymph nodes: No pathologic lymphadenopathy.\\.br\\"
        "\\.br\\"
        "IMPRESSION:\\.br\\"
        "1. Acute cholecystitis with gallstones and pericholecystic fluid. "
        "Surgical consultation recommended.\\.br\\"
        "2. Small amount of free fluid in the right lower quadrant, likely reactive."
    )

    return (
        f"MSH|^~\\&|RIS|RAD_DEPT|EMR|MAIN_HOSPITAL|{ts}||ORU^R01^ORU_R01|{ctrl}|T|2.5.1\r"
        f"PID|1||MRN456789^^^MAIN_HOSP^MR||JOHNSON^ROBERT^L||19750512|M\r"
        f"PV1|1|O|ED^TRIAGE^01|E|||3333333^ORDERING^DOCTOR^F^^DR.^MD||||||||||OP|VN20240301001\r"
        f"ORC|RE|ORD20240301001^CPOE|ACC20240301001^RIS||CM\r"
        f"OBR|1|ORD20240301001^CPOE|ACC20240301001^RIS|CTABD^CT ABDOMEN PELVIS WITH CONTRAST^L|||{ts}|||||||R10.9^Abdominal pain|||3333333^ORDERING^DOCTOR^F^^DR.^MD||||||RAD|F||||||5555555^READING^RADIOLOGIST^H^^DR.^MD^^NPI\r"
        f"OBX|1|FT|&GDT^Radiology Report^L||{report_text}||||||F\r"
        f"OBX|2|FT|&IMP^Impression^L||1. Acute cholecystitis with gallstones and pericholecystic fluid. Surgical consultation recommended.\\.br\\2. Small amount of free fluid in the RLQ, likely reactive.||||||F"
    )


def _gen_mdm_t02(ts: str, ctrl: str, scenario: str) -> str:
    """Generate MDM^T02 (Original Document Notification and Content)."""
    return (
        f"MSH|^~\\&|RIS|RAD_DEPT|EMR|MAIN_HOSPITAL|{ts}||MDM^T02^MDM_T02|{ctrl}|T|2.5.1\r"
        f"EVN|T02|{ts}\r"
        f"PID|1||MRN456789^^^MAIN_HOSP^MR||JOHNSON^ROBERT^L||19750512|M\r"
        f"PV1|1|O|ED^TRIAGE^01\r"
        f"TXA|1|RAD|FT|{ts}|5555555^READING^RADIOLOGIST^H^^DR.^MD|{ts}|{ts}||5555555^READING^RADIOLOGIST^H^^DR.^MD|||DOC20240301001||||AU|||||{ts}^5555555^READING^RADIOLOGIST^H\r"
        f"OBX|1|FT|&GDT^Radiology Report^L||Findings as dictated.||||||F"
    )


def _gen_siu_s12(ts: str, ctrl: str, scenario: str) -> str:
    """Generate SIU^S12 (Notification of New Appointment Booking)."""
    sched_time = (datetime.now()).strftime("%Y%m%d%H%M%S")
    return (
        f"MSH|^~\\&|SCHEDULING|MAIN_HOSPITAL|RIS|RAD_DEPT|{ts}||SIU^S12^SIU_S12|{ctrl}|T|2.5.1\r"
        f"SCH|SCH20240301001|ORD20240301001|||||ROUTINE^Routine^HL70277|NORMAL^Normal appointment^HL70278|30|min^Minutes^ISO+|^^30^{sched_time}^{sched_time}\r"
        f"PID|1||MRN789012^^^MAIN_HOSP^MR||SMITH^JANE^A||19800722|F\r"
        f"PV1|1|O|RAD\r"
        f"RGS|1|A\r"
        f"AIS|1|A|CTABD^CT ABDOMEN PELVIS WITH CONTRAST^L|{sched_time}||30|min^Minutes^ISO+"
    )


def _gen_dft_p03(ts: str, ctrl: str, scenario: str) -> str:
    """Generate DFT^P03 (Post Detail Financial Transactions)."""
    return (
        f"MSH|^~\\&|RIS|RAD_DEPT|BILLING|MAIN_HOSPITAL|{ts}||DFT^P03^DFT_P03|{ctrl}|T|2.5.1\r"
        f"EVN|P03|{ts}\r"
        f"PID|1||MRN456789^^^MAIN_HOSP^MR||JOHNSON^ROBERT^L||19750512|M|||321 ELM ST^^ANYTOWN^CA^90001||||||ACCT20240301001\r"
        f"PV1|1|O|ED^TRIAGE^01||||||3333333^ORDERING^DOCTOR^F||RAD||||||||OP|VN20240301001\r"
        f"FT1|1||BATCH001|{ts}||CG|74178^CT ABD & PELVIS WITH CONTRAST^CPT|||1|350.00||||||RAD|||R10.9^Unspecified abdominal pain^I10|5555555^READING^RADIOLOGIST^H|3333333^ORDERING^DOCTOR^F||||74178^CT ABD & PELVIS WITH CONTRAST^CPT\r"
        f"DG1|1||R10.9^Unspecified abdominal pain^I10||{ts}|W"
    )
