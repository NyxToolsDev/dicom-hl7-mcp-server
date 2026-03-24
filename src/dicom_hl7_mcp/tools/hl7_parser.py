"""HL7 v2.x message parsing and explanation tools (Free Tier)."""

from __future__ import annotations

from dicom_hl7_mcp.knowledge.hl7_segments import HL7_SEGMENTS, HL7_TABLES, HL7_MESSAGE_TYPES


def parse_hl7_message(message: str) -> str:
    """Parse an HL7 v2.x message into human-readable format.

    Args:
        message: Raw HL7 message string (pipe-delimited). Segments can be
            separated by \\r, \\n, or \\r\\n.

    Returns:
        Parsed segments with field names, values, and explanations.
    """
    if not message or not message.strip():
        return "Error: Empty message provided."

    # Normalize line endings and split into segments
    clean = message.strip()
    # Handle escaped newlines from JSON input
    clean = clean.replace("\\r\\n", "\n").replace("\\r", "\n").replace("\\n", "\n")
    # Handle actual carriage returns
    clean = clean.replace("\r\n", "\n").replace("\r", "\n")
    segments = [s.strip() for s in clean.split("\n") if s.strip()]

    if not segments:
        return "Error: No segments found in message."

    # Validate MSH segment
    first_seg = segments[0]
    if not first_seg.startswith("MSH"):
        return (
            "Error: Message must start with MSH segment.\n"
            f"First segment starts with: '{first_seg[:10]}...'"
        )

    # Parse encoding characters from MSH
    if len(first_seg) < 8:
        return "Error: MSH segment too short to contain encoding characters."

    field_sep = first_seg[3]  # Usually '|'
    encoding_chars = first_seg[4:8] if len(first_seg) >= 8 else "^~\\&"
    component_sep = encoding_chars[0] if len(encoding_chars) > 0 else "^"
    repetition_sep = encoding_chars[1] if len(encoding_chars) > 1 else "~"
    escape_char = encoding_chars[2] if len(encoding_chars) > 2 else "\\"
    subcomponent_sep = encoding_chars[3] if len(encoding_chars) > 3 else "&"

    # Parse message header to get message type
    msh_fields = _split_msh(first_seg, field_sep)
    msg_type = msh_fields[8] if len(msh_fields) > 8 else "Unknown"
    msg_type_clean = msg_type.split(component_sep)[0] + "^" + msg_type.split(component_sep)[1] if component_sep in msg_type else msg_type

    # Build output
    parts = [
        "=" * 70,
        f"HL7 MESSAGE PARSE RESULT",
        f"=" * 70,
        f"Message Type: {msg_type_clean}",
    ]

    # Look up message type info
    type_info = HL7_MESSAGE_TYPES.get(msg_type_clean)
    if type_info:
        parts.append(f"Description:  {type_info['name']}")
        parts.append(f"              {type_info['description']}")
    parts.append("")

    # Parse each segment
    for seg_text in segments:
        seg_id = seg_text.split(field_sep)[0] if field_sep in seg_text else seg_text[:3]

        if seg_id == "MSH":
            fields = _split_msh(seg_text, field_sep)
        else:
            fields = seg_text.split(field_sep)

        parts.append("-" * 70)
        seg_info = HL7_SEGMENTS.get(seg_id)
        if seg_info:
            parts.append(f"Segment: {seg_id} — {seg_info['name']}")
            parts.append(f"         {seg_info['description']}")
        else:
            parts.append(f"Segment: {seg_id} (not in standard dictionary — may be Z-segment or custom)")
        parts.append("")

        # Parse fields
        for i, value in enumerate(fields):
            if i == 0:
                continue  # Skip segment ID

            if not value:
                continue  # Skip empty fields

            field_name = "Unknown"
            field_desc = ""
            table_ref = None

            if seg_info:
                field_def = _get_field_def(seg_info, i)
                if field_def:
                    field_name = field_def["name"]
                    field_desc = field_def.get("description", "")
                    table_ref = field_def.get("table")

            # Format the field output
            display_value = value
            if len(value) > 120:
                display_value = value[:120] + "..."

            parts.append(f"  {seg_id}-{i}: {field_name}")
            parts.append(f"    Value: {display_value}")

            # Look up table values if applicable
            if table_ref and value:
                table_lookup = _lookup_table_value(table_ref, value, component_sep)
                if table_lookup:
                    parts.append(f"    Table {table_ref}: {table_lookup}")

            # Parse components for complex fields
            if component_sep in value and len(value.split(component_sep)) > 1:
                components = value.split(component_sep)
                non_empty = [(j, c) for j, c in enumerate(components, 1) if c]
                if len(non_empty) > 1:
                    parts.append(f"    Components:")
                    for comp_idx, comp_val in non_empty:
                        parts.append(f"      .{comp_idx}: {comp_val}")

            parts.append("")

    parts.append("=" * 70)
    return "\n".join(parts)


def _split_msh(msh_text: str, field_sep: str) -> list[str]:
    """Split MSH segment handling the special MSH-1/MSH-2 fields.

    MSH-1 IS the field separator character. MSH-2 is the encoding characters.
    The split needs to account for MSH-1 being the delimiter itself.
    """
    # MSH|^~\\&|SendApp|... -> fields[0]="MSH", fields[1]="|", fields[2]="^~\\&", ...
    parts = msh_text.split(field_sep)
    # Insert the field separator as MSH-1
    result = [parts[0], field_sep]
    if len(parts) > 1:
        result.extend(parts[1:])
    return result


def _get_field_def(seg_info: dict, position: int) -> dict | None:
    """Get field definition by position."""
    for field in seg_info.get("fields", []):
        if field["position"] == position:
            return field
    return None


def _lookup_table_value(table: str, value: str, component_sep: str) -> str:
    """Look up a table value, handling component separators."""
    # Get the primary value (before any component separator)
    primary_value = value.split(component_sep)[0] if component_sep in value else value

    table_info = HL7_TABLES.get(table)
    if not table_info:
        return ""

    meaning = table_info["values"].get(primary_value)
    if meaning:
        return f"{primary_value} = {meaning}"

    return ""


def explain_hl7_segment(segment_name: str) -> str:
    """Explain what an HL7 segment does and list all its fields.

    Args:
        segment_name: Segment identifier (e.g., "PID", "OBX", "MSH").

    Returns:
        Detailed explanation of the segment with all field positions and descriptions.
    """
    segment_name = segment_name.strip().upper()

    seg_info = HL7_SEGMENTS.get(segment_name)
    if not seg_info:
        # Try to find partial match
        matches = [k for k in HL7_SEGMENTS if segment_name in k]
        if matches:
            return (
                f"Segment '{segment_name}' not found. Did you mean one of these?\n"
                + "\n".join(f"  - {m}: {HL7_SEGMENTS[m]['name']}" for m in matches)
            )
        available = ", ".join(sorted(HL7_SEGMENTS.keys()))
        return (
            f"Segment '{segment_name}' not found in dictionary.\n\n"
            f"Available segments: {available}"
        )

    parts = [
        f"## {segment_name} — {seg_info['name']}",
        "",
        seg_info["description"],
        "",
    ]

    # List all fields
    parts.append(f"### Fields ({len(seg_info['fields'])} defined)")
    parts.append("")
    parts.append(f"{'Pos':<5} {'Required':<10} {'Data Type':<10} {'Name'}")
    parts.append(f"{'---':<5} {'--------':<10} {'---------':<10} {'----'}")

    for field in seg_info["fields"]:
        req = field["required"]
        req_str = {
            "R": "Required",
            "RE": "Req/Empty",
            "O": "Optional",
            "C": "Conditnl",
            "B": "Backward",
        }.get(req, req)

        repeat = " (repeating)" if field.get("repeating") else ""
        table = f" [Table {field['table']}]" if field.get("table") else ""

        parts.append(
            f"{field['position']:<5} {req_str:<10} {field['data_type']:<10} "
            f"{field['name']}{repeat}{table}"
        )
        if field.get("description"):
            parts.append(f"{'':>30}{field['description']}")
        parts.append("")

    # Notes
    if seg_info.get("notes"):
        parts.append("### Notes")
        parts.append(seg_info["notes"])
        parts.append("")

    # Show which message types use this segment
    used_in = []
    for msg_type, msg_info in HL7_MESSAGE_TYPES.items():
        all_segs = msg_info.get("required_segments", []) + msg_info.get("optional_segments", [])
        if segment_name in all_segs:
            req = "required" if segment_name in msg_info.get("required_segments", []) else "optional"
            used_in.append(f"  - {msg_type} ({msg_info['name']}) [{req}]")

    if used_in:
        parts.append(f"### Used In Message Types")
        parts.extend(used_in[:15])
        if len(used_in) > 15:
            parts.append(f"  ... and {len(used_in) - 15} more")

    return "\n".join(parts)


def lookup_hl7_table(table_number: str) -> str:
    """Look up HL7 table values.

    Args:
        table_number: Table number (e.g., "0001", "0004", "76"). Leading zeros
            are optional.

    Returns:
        Table name and all defined values with descriptions.
    """
    # Normalize table number to 4-digit zero-padded string
    table_number = table_number.strip().lstrip("0") or "0"
    table_key = table_number.zfill(4)

    table_info = HL7_TABLES.get(table_key)
    if not table_info:
        # Try without padding
        for key in HL7_TABLES:
            if key.lstrip("0") == table_number.lstrip("0"):
                table_info = HL7_TABLES[key]
                table_key = key
                break

    if not table_info:
        available = sorted(HL7_TABLES.keys())
        return (
            f"Table {table_key} not found in dictionary.\n\n"
            f"Available tables: {', '.join(available)}"
        )

    parts = [
        f"## HL7 Table {table_key} — {table_info['name']}",
        "",
        f"{'Value':<10} {'Description'}",
        f"{'-----':<10} {'-----------'}",
    ]

    for value, description in sorted(table_info["values"].items()):
        parts.append(f"{value:<10} {description}")

    parts.append("")
    parts.append(f"Total: {len(table_info['values'])} values")

    # Show which fields reference this table
    referencing_fields = []
    for seg_id, seg_info in HL7_SEGMENTS.items():
        for field in seg_info.get("fields", []):
            if field.get("table") == table_key:
                referencing_fields.append(f"  - {seg_id}-{field['position']} ({field['name']})")

    if referencing_fields:
        parts.append("")
        parts.append("Referenced by:")
        parts.extend(referencing_fields[:10])

    return "\n".join(parts)
