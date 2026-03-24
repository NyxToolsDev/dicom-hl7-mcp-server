"""Field mapping tools between DICOM, HL7, and FHIR (Premium Tier)."""

from __future__ import annotations

from dicom_hl7_mcp.knowledge.dicom_dictionary import DICOM_TAGS
from dicom_hl7_mcp.knowledge.fhir_mappings import DICOM_TO_HL7_MAP, HL7_TO_FHIR_MAP, INTEGRATION_PATTERNS
from dicom_hl7_mcp.knowledge.hl7_segments import HL7_SEGMENTS
from dicom_hl7_mcp.tools.dicom_tags import _find_by_keyword, _parse_tag_input
from dicom_hl7_mcp.utils.formatting import format_dicom_tag, format_hl7_field_ref
from dicom_hl7_mcp.utils.license import require_premium


def map_dicom_to_hl7(tag: str) -> str:
    """Map DICOM tag(s) to equivalent HL7 v2 fields.

    Args:
        tag: DICOM tag identifier(s). Accepts tag number or keyword.
            Separate multiple tags with commas for batch lookup.

    Returns:
        Corresponding HL7 segment.field, mapping notes, data type conversions.
    """
    premium_check = require_premium("map_dicom_to_hl7")
    if premium_check:
        return premium_check

    # Handle multiple tags separated by semicolons
    tags = [t.strip() for t in tag.replace(";", ",").split(",") if t.strip()]
    # But only if they look like separate tags (not a single tag like "0010,0010")
    if len(tags) == 2:
        # Check if this is actually a single DICOM tag in GGGG,EEEE format
        parsed = _parse_tag_input(tag.strip())
        if parsed is not None:
            tags = [tag.strip()]

    results = []
    for single_tag in tags:
        results.append(_map_single_dicom_to_hl7(single_tag))

    return "\n\n".join(results)


def _map_single_dicom_to_hl7(tag: str) -> str:
    """Map a single DICOM tag to HL7."""
    # Resolve the tag
    parsed = _parse_tag_input(tag)
    tag_key = None
    tag_info = None

    if parsed is not None:
        tag_key = parsed
        tag_info = DICOM_TAGS.get(parsed)
    else:
        results = _find_by_keyword(tag)
        if results:
            tag_key, tag_info = results[0]

    if tag_key is None or tag_info is None:
        return f"DICOM tag '{tag}' not found. Use 'lookup_dicom_tag' to find the correct tag."

    mapping = DICOM_TO_HL7_MAP.get(tag_key)
    if not mapping:
        return (
            f"No HL7 mapping found for {format_dicom_tag(*tag_key)} ({tag_info['keyword']}).\n"
            f"This tag may not have a standard HL7 v2 equivalent. Some DICOM-specific "
            f"attributes (acquisition parameters, pixel data characteristics) have no "
            f"direct HL7 representation."
        )

    parts = [
        f"## DICOM -> HL7 Mapping",
        f"",
        f"DICOM Tag:  {format_dicom_tag(*tag_key)}  {tag_info['keyword']}",
        f"DICOM Name: {tag_info['name']}",
        f"DICOM VR:   {tag_info['vr']}",
        f"",
        f"HL7 Field:  {mapping['hl7_field']}",
        f"HL7 Segment: {mapping['hl7_segment']}",
    ]

    if mapping.get("hl7_component"):
        parts.append(f"Component:  {mapping['hl7_component']}")

    parts.extend([
        f"",
        f"Data Type Conversion: {mapping['data_type_conversion']}",
        f"Bidirectional: {'Yes' if mapping['bidirectional'] else 'No (DICOM -> HL7 only)'}",
        f"",
        f"Mapping Notes:",
        f"  {mapping['mapping_notes']}",
    ])

    # Add HL7 field details if available
    seg_id = mapping["hl7_segment"].split(" / ")[0].split(" ")[0]
    seg_info = HL7_SEGMENTS.get(seg_id)
    if seg_info:
        # Try to find the field position from the field reference
        field_ref = mapping["hl7_field"]
        import re
        pos_match = re.search(r"-(\d+)", field_ref)
        if pos_match:
            pos = int(pos_match.group(1))
            for field_def in seg_info.get("fields", []):
                if field_def["position"] == pos:
                    parts.append(f"")
                    parts.append(f"HL7 Field Details:")
                    parts.append(f"  Name: {field_def['name']}")
                    parts.append(f"  Data Type: {field_def['data_type']}")
                    parts.append(f"  Required: {field_def['required']}")
                    if field_def.get("description"):
                        parts.append(f"  Description: {field_def['description']}")
                    break

    return "\n".join(parts)


def map_hl7_to_fhir(field_ref: str) -> str:
    """Map HL7 v2 segments/fields to FHIR R4 resources.

    Args:
        field_ref: HL7 field reference (e.g., "PID-3", "OBR-4", "PV1-7",
            "MSH-9"). Format: SEGMENT-POSITION.

    Returns:
        FHIR resource, element path, ConceptMap reference, and conversion notes.
    """
    premium_check = require_premium("map_hl7_to_fhir")
    if premium_check:
        return premium_check

    field_ref = field_ref.strip().upper()

    # Parse the field reference
    import re
    match = re.match(r"^([A-Z]{2,3})-?(\d+)(?:\.(\d+))?$", field_ref)
    if not match:
        return (
            f"Invalid field reference '{field_ref}'.\n"
            f"Expected format: SEGMENT-POSITION (e.g., 'PID-3', 'OBR-4')."
        )

    segment = match.group(1)
    position = int(match.group(2))
    component = int(match.group(3)) if match.group(3) else None

    # Look up the mapping
    lookup_key = (segment, position, component) if component else (segment, position)
    mapping = HL7_TO_FHIR_MAP.get(lookup_key)

    # If no component-specific mapping, try without component
    if mapping is None and component is not None:
        mapping = HL7_TO_FHIR_MAP.get((segment, position))

    if mapping is None:
        return (
            f"No FHIR mapping found for {field_ref}.\n\n"
            f"This field may not have a standard v2-to-FHIR mapping defined in the "
            f"HL7 v2-to-FHIR Implementation Guide.\n\n"
            f"Mapped fields for {segment}: "
            + ", ".join(
                f"{s}-{p}" for (s, p, *_) in HL7_TO_FHIR_MAP.keys()
                if s == segment
            )
        )

    parts = [
        f"## HL7 v2 -> FHIR R4 Mapping",
        f"",
        f"HL7 Field:     {field_ref}",
    ]

    # Add HL7 field name
    seg_info = HL7_SEGMENTS.get(segment)
    if seg_info:
        for field_def in seg_info.get("fields", []):
            if field_def["position"] == position:
                parts.append(f"HL7 Field Name: {field_def['name']}")
                break

    parts.extend([
        f"",
        f"FHIR Resource: {mapping['fhir_resource']}",
        f"FHIR Path:     {mapping['fhir_path']}",
        f"FHIR Type:     {mapping['fhir_element_type']}",
        f"",
        f"Conversion Type: {mapping['conversion_type']}",
    ])

    if mapping.get("concept_map"):
        parts.append(f"ConceptMap:    {mapping['concept_map']}")

    parts.extend([
        f"",
        f"Mapping Notes:",
        f"  {mapping['notes']}",
    ])

    # Add conversion guidance
    conv_type = mapping["conversion_type"]
    if conv_type == "direct":
        parts.append("")
        parts.append("Conversion Guidance: Direct mapping. Copy the value as-is (with format adjustment if needed).")
    elif conv_type == "transform":
        parts.append("")
        parts.append("Conversion Guidance: Requires data format transformation (e.g., date format, name structure).")
    elif conv_type == "lookup":
        parts.append("")
        parts.append("Conversion Guidance: Requires code/value lookup via ConceptMap or mapping table.")
    elif conv_type == "complex":
        parts.append("")
        parts.append("Conversion Guidance: Complex mapping requiring multiple component extractions and possible resource creation.")

    return "\n".join(parts)


def explain_integration_pattern(pattern_name: str) -> str:
    """Explain common healthcare integration patterns.

    Args:
        pattern_name: Pattern identifier. Examples:
            - "ADT feed" or "adt_feed"
            - "order to result" or "order_to_result"
            - "radiology workflow"
            - "lab interface"
            - "report distribution"
            - "patient merge"
            - "charge posting"

    Returns:
        Message flow diagram, trigger events, expected segments, common pitfalls.
    """
    premium_check = require_premium("explain_integration_pattern")
    if premium_check:
        return premium_check

    # Normalize the pattern name
    normalized = pattern_name.strip().lower().replace(" ", "_").replace("-", "_")

    # Try exact match
    pattern = INTEGRATION_PATTERNS.get(normalized)

    # Try fuzzy match
    if pattern is None:
        for key, val in INTEGRATION_PATTERNS.items():
            if normalized in key or key in normalized:
                pattern = val
                break
            if normalized in val["name"].lower().replace(" ", "_"):
                pattern = val
                break

    if pattern is None:
        available = "\n".join(
            f"  - {key}: {val['name']}" for key, val in INTEGRATION_PATTERNS.items()
        )
        return (
            f"Integration pattern '{pattern_name}' not found.\n\n"
            f"Available patterns:\n{available}"
        )

    parts = [
        f"## {pattern['name']}",
        f"",
        pattern["description"],
        f"",
        f"### Message Flow",
    ]

    for i, step in enumerate(pattern["message_flow"], 1):
        parts.append(f"  {i}. {step}")

    parts.extend([
        f"",
        f"### Trigger Events",
    ])
    for event in pattern["trigger_events"]:
        parts.append(f"  - {event}")

    parts.extend([
        f"",
        f"### Expected Segments",
        f"  {', '.join(pattern['expected_segments'])}",
        f"",
        f"### Common Pitfalls",
    ])
    for pitfall in pattern["common_pitfalls"]:
        parts.append(f"  ! {pitfall}")

    parts.extend([
        f"",
        f"### Best Practices",
    ])
    for practice in pattern["best_practices"]:
        parts.append(f"  * {practice}")

    return "\n".join(parts)
