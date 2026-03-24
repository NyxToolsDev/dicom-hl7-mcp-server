"""DICOM tag lookup and explanation tools (Free Tier)."""

from __future__ import annotations

import re

from dicom_hl7_mcp.knowledge.dicom_dictionary import (
    DICOM_TAGS,
    PRIVATE_TAG_RANGES,
    SOP_CLASSES,
    TRANSFER_SYNTAXES,
)
from dicom_hl7_mcp.utils.formatting import format_dicom_tag, format_vr_description


def _parse_tag_input(tag: str) -> tuple[int, int] | None:
    """Parse a tag input string into (group, element) tuple.

    Accepts formats:
        - "0010,0010" or "0010, 0010"
        - "(0010,0010)" or "(0010, 0010)"
        - "00100010"
        - "0x00100010"
    """
    tag = tag.strip().strip("()")

    # Try GGGG,EEEE format
    match = re.match(r"^([0-9a-fA-F]{4})\s*,\s*([0-9a-fA-F]{4})$", tag)
    if match:
        return (int(match.group(1), 16), int(match.group(2), 16))

    # Try GGGGEEEE format (8 hex digits)
    match = re.match(r"^(?:0x)?([0-9a-fA-F]{8})$", tag)
    if match:
        val = int(match.group(1), 16)
        return (val >> 16, val & 0xFFFF)

    return None


def _find_by_keyword(keyword: str) -> list[tuple[tuple[int, int], dict]]:
    """Find DICOM tags by keyword or name (case-insensitive partial match)."""
    keyword_lower = keyword.lower().replace(" ", "").replace("_", "").replace("'", "")
    results = []

    for tag_key, tag_info in DICOM_TAGS.items():
        tag_keyword = tag_info["keyword"].lower().replace("_", "")
        tag_name = tag_info["name"].lower().replace(" ", "").replace("'", "")

        # Exact keyword match
        if keyword_lower == tag_keyword:
            results.insert(0, (tag_key, tag_info))
        # Name match without spaces
        elif keyword_lower == tag_name:
            results.insert(0, (tag_key, tag_info))
        # Partial match
        elif keyword_lower in tag_keyword or keyword_lower in tag_name:
            results.append((tag_key, tag_info))

    return results


def lookup_dicom_tag(tag: str) -> str:
    """Look up a DICOM tag by group/element number or keyword.

    Args:
        tag: Tag identifier. Accepts:
            - Tag number: "0010,0010", "(0010,0010)", "00100010"
            - Keyword: "PatientName", "patient name", "Patient's Name"

    Returns:
        Formatted string with tag information.
    """
    # Try parsing as a numeric tag
    parsed = _parse_tag_input(tag)
    if parsed is not None:
        info = DICOM_TAGS.get(parsed)
        if info:
            return _format_tag_result(parsed, info)

        # Check if it's in a private tag range
        group, element = parsed
        if group % 2 == 1:  # Odd group = private
            return _format_private_tag_info(group, element)

        return (
            f"Tag {format_dicom_tag(*parsed)} not found in the dictionary.\n\n"
            f"This could be:\n"
            f"- A less common standard tag not in our database\n"
            f"- A private tag (odd group numbers are private)\n"
            f"- An incorrect tag number\n\n"
            f"Try searching by keyword instead, or check the DICOM PS3.6 Data Dictionary."
        )

    # Try keyword search
    results = _find_by_keyword(tag)
    if not results:
        return (
            f"No DICOM tags found matching '{tag}'.\n\n"
            f"Tips:\n"
            f"- Try a different keyword (e.g., 'patient' instead of 'pt')\n"
            f"- Use the tag number format: '0010,0010'\n"
            f"- Keywords are searched case-insensitively"
        )

    if len(results) == 1:
        return _format_tag_result(results[0][0], results[0][1])

    # Multiple results
    output_parts = [f"Found {len(results)} tags matching '{tag}':\n"]
    for tag_key, tag_info in results[:15]:  # Limit to 15 results
        retired = " [RETIRED]" if tag_info.get("retired") else ""
        output_parts.append(
            f"  {format_dicom_tag(*tag_key)}  {tag_info['keyword']}  "
            f"VR: {tag_info['vr']}  — {tag_info['name']}{retired}"
        )

    if len(results) > 15:
        output_parts.append(f"\n  ... and {len(results) - 15} more. Try a more specific keyword.")

    return "\n".join(output_parts)


def _format_tag_result(tag_key: tuple[int, int], info: dict) -> str:
    """Format a single DICOM tag result."""
    retired_str = "  **[RETIRED]**" if info.get("retired") else ""
    parts = [
        f"DICOM Tag: {format_dicom_tag(*tag_key)}{retired_str}",
        f"Keyword:   {info['keyword']}",
        f"Name:      {info['name']}",
        f"VR:        {info['vr']} — {format_vr_description(info['vr'])}",
        f"VM:        {info['vm']}",
        f"",
        f"Description:",
        f"  {info['description']}",
    ]

    if info.get("common_values"):
        parts.append("")
        parts.append("Common Values:")
        for val in info["common_values"]:
            parts.append(f"  - {val}")

    if info.get("notes"):
        parts.append("")
        parts.append("Notes:")
        parts.append(f"  {info['notes']}")

    return "\n".join(parts)


def _format_private_tag_info(group: int, element: int) -> str:
    """Provide information about a private tag."""
    group_hex = f"{group:04X}"
    parts = [
        f"Tag ({group_hex},{element:04X}) is a PRIVATE tag (odd group number).",
        "",
        "Private tags are vendor-specific and not part of the DICOM standard.",
        "",
    ]

    # Check known vendor ranges
    found_vendor = False
    for vendor, vendor_info in PRIVATE_TAG_RANGES.items():
        if group_hex.lower() in [g.lower() for g in vendor_info["common_groups"]]:
            found_vendor = True
            parts.append(f"Group {group_hex} is commonly used by: {vendor}")
            parts.append(f"  Known creator IDs: {', '.join(vendor_info['creator_ids'][:3])}")

            # Check for specific known tag
            tag_tuple = (group, element)
            if tag_tuple in vendor_info.get("known_tags", {}):
                known = vendor_info["known_tags"][tag_tuple]
                parts.append(f"  Known tag: {known['name']}")
                parts.append(f"  Notes: {known['notes']}")

            if vendor_info.get("notes"):
                parts.append(f"  Vendor notes: {vendor_info['notes']}")
            parts.append("")

    if not found_vendor:
        parts.append("This private group is not in our vendor database.")
        parts.append("Check the Private Creator element at (GGGG,0010-00FF) to identify the vendor.")

    parts.append("")
    parts.append("Use 'decode_private_tags' with a vendor hint for more details (premium feature).")

    return "\n".join(parts)


def explain_dicom_tag(tag: str) -> str:
    """Get a detailed explanation of a DICOM tag with context.

    Args:
        tag: Tag identifier (number or keyword).

    Returns:
        Detailed explanation including usage context, vendor quirks, and gotchas.
    """
    # Resolve the tag
    parsed = _parse_tag_input(tag)
    info = None
    tag_key = None

    if parsed is not None:
        info = DICOM_TAGS.get(parsed)
        tag_key = parsed
    else:
        results = _find_by_keyword(tag)
        if results:
            tag_key, info = results[0]

    if info is None:
        return f"Tag '{tag}' not found. Use 'lookup_dicom_tag' to search by keyword or number."

    parts = [
        f"## {info['name']}",
        f"Tag: {format_dicom_tag(*tag_key)}  |  Keyword: {info['keyword']}  |  VR: {info['vr']}  |  VM: {info['vm']}",
        "",
    ]

    # What is it?
    parts.append("### What It Is")
    parts.append(info["description"])
    parts.append("")

    # When is it used?
    parts.append("### When It's Used")
    parts.append(_get_usage_context(tag_key, info))
    parts.append("")

    # Common values
    if info.get("common_values"):
        parts.append("### Common Values")
        for val in info["common_values"]:
            parts.append(f"  - {val}")
        parts.append("")

    # VR details
    parts.append("### Value Representation Details")
    parts.append(f"VR: {info['vr']} — {format_vr_description(info['vr'])}")
    parts.append(_get_vr_notes(info["vr"]))
    parts.append("")

    # Practical notes and vendor quirks
    if info.get("notes"):
        parts.append("### Practical Notes & Vendor Quirks")
        parts.append(info["notes"])
        parts.append("")

    # Related tags
    related = _get_related_tags(tag_key, info)
    if related:
        parts.append("### Related Tags")
        for rel_key, rel_info in related:
            parts.append(f"  {format_dicom_tag(*rel_key)}  {rel_info['keyword']} — {rel_info['name']}")
        parts.append("")

    # SOP Class context
    sop_context = _get_sop_context(tag_key)
    if sop_context:
        parts.append("### SOP Class Context")
        parts.append(sop_context)

    return "\n".join(parts)


def _get_usage_context(tag_key: tuple[int, int], info: dict) -> str:
    """Generate usage context based on the tag's group."""
    group = tag_key[0]
    contexts = {
        0x0002: "File Meta Information. Present only in DICOM Part 10 files (not in network transfers). Contains information about how the file is encoded.",
        0x0008: "Study/Series identification and general metadata. These tags are fundamental to DICOM object identification and are used in virtually every DICOM operation (C-FIND queries, C-STORE, C-MOVE).",
        0x0010: "Patient demographics. These tags contain PHI and must be handled according to HIPAA requirements. Used for patient matching between RIS, PACS, and HIS systems.",
        0x0018: "Acquisition parameters. Equipment and protocol settings at the time of image acquisition. Critical for dose tracking, quality assurance, and clinical interpretation.",
        0x0020: "Relationship (spatial and hierarchical). Position and orientation data for images. Critical for 3D reconstruction, multiplanar reformats, and image fusion.",
        0x0028: "Image presentation parameters. Pixel data characteristics and display settings. Must be correct for proper image rendering.",
        0x0032: "Study-level request information. Contains data from the original imaging order/request.",
        0x0038: "Visit/encounter information. Links imaging studies to patient visits/admissions.",
        0x0040: "Procedure and worklist information. Used in Modality Worklist (MWL) and Modality Performed Procedure Step (MPPS). Also contains Structured Report content items.",
        0x0054: "Nuclear Medicine / PET specific parameters.",
        0x0070: "Presentation State and annotation parameters.",
        0x0088: "Storage and media management.",
        0x7FE0: "Pixel data. Contains the actual image data. This is typically the largest element in a DICOM file.",
    }
    return contexts.get(group, f"Group {group:04X} tags. Refer to the DICOM standard for specific context.")


def _get_vr_notes(vr: str) -> str:
    """Get practical notes about a VR."""
    notes = {
        "PN": "Person Name format: Family^Given^Middle^Prefix^Suffix. Three component groups separated by '=': Alphabetic=Ideographic=Phonetic. DICOM PN is very similar to HL7 XPN.",
        "DA": "Date format YYYYMMDD with no separators. Range matching uses '-' (e.g., '20230101-20231231' for C-FIND queries).",
        "TM": "Time format HHMMSS.FFFFFF. Fractional seconds are optional. Vendors differ in precision provided.",
        "UI": "UID format: dot-separated numeric components (e.g., 1.2.840.10008.5.1.4.1.1.2). Max 64 characters. Root should be registered.",
        "CS": "Code String: uppercase letters, digits, spaces, underscore only. Max 16 characters. No leading/trailing spaces.",
        "DS": "Decimal String: ASCII representation of a decimal number. Max 16 characters. May have leading/trailing spaces.",
        "IS": "Integer String: ASCII representation of an integer. Max 12 characters. +-digits only.",
        "LO": "Long String: max 64 characters. No backslash or control characters (except ESC).",
        "SQ": "Sequence of Items: contains zero or more items, each of which contains a set of DICOM attributes. Used for nested/repeating data structures.",
        "SH": "Short String: max 16 characters. Commonly used for identifiers and codes.",
    }
    return notes.get(vr, "")


def _get_related_tags(tag_key: tuple[int, int], info: dict) -> list[tuple[tuple[int, int], dict]]:
    """Find tags related to the given tag."""
    related = []
    keyword_lower = info["keyword"].lower()
    group = tag_key[0]

    # Find tags in the same group with related names
    for other_key, other_info in DICOM_TAGS.items():
        if other_key == tag_key:
            continue

        other_keyword = other_info["keyword"].lower()

        # Same concept in different contexts (e.g., StudyDate/SeriesDate/AcquisitionDate)
        # Or paired tags (e.g., WindowCenter/WindowWidth, Rows/Columns)
        shared_root = _shared_root(keyword_lower, other_keyword)
        if shared_root and len(shared_root) >= 5:
            related.append((other_key, other_info))
        elif other_key[0] == group and abs(other_key[1] - tag_key[1]) <= 3:
            # Nearby tags in the same group
            related.append((other_key, other_info))

    return related[:8]  # Limit to 8 related tags


def _shared_root(a: str, b: str) -> str:
    """Find the longest shared prefix between two strings."""
    prefix = []
    for ca, cb in zip(a, b):
        if ca == cb:
            prefix.append(ca)
        else:
            break
    return "".join(prefix)


def _get_sop_context(tag_key: tuple[int, int]) -> str:
    """Get SOP Class context for a tag."""
    group = tag_key[0]
    if group == 0x0018:
        return "Acquisition parameters vary by SOP Class (modality). CT-specific tags may not be present in MR images and vice versa."
    if group == 0x0054:
        return "Nuclear Medicine and PET-specific tags. Present only in NM/PET SOP Classes."
    if group == 0x0040 and tag_key[1] >= 0xA000:
        return "Structured Report content item tags. Present in SR SOP Classes (Basic Text SR, Enhanced SR, Comprehensive SR, etc.)."
    return ""
