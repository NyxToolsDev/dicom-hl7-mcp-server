"""Formatting utilities for consistent output across tools."""


def format_dicom_tag(group: int, element: int) -> str:
    """Format a DICOM tag as (GGGG,EEEE)."""
    return f"({group:04X},{element:04X})"


def format_dicom_tag_short(group: int, element: int) -> str:
    """Format a DICOM tag as GGGG,EEEE (without parentheses)."""
    return f"{group:04X},{element:04X}"


def format_vr_description(vr: str) -> str:
    """Return a human-readable description of a DICOM Value Representation."""
    vr_descriptions = {
        "AE": "Application Entity (max 16 chars)",
        "AS": "Age String (format: nnnD/W/M/Y)",
        "AT": "Attribute Tag (4 bytes)",
        "CS": "Code String (max 16 chars, uppercase, no special chars)",
        "DA": "Date (YYYYMMDD)",
        "DS": "Decimal String (max 16 chars)",
        "DT": "Date Time (YYYYMMDDHHMMSS.FFFFFF&ZZXX)",
        "FL": "Floating Point Single (4 bytes)",
        "FD": "Floating Point Double (8 bytes)",
        "IS": "Integer String (max 12 chars)",
        "LO": "Long String (max 64 chars)",
        "LT": "Long Text (max 10240 chars)",
        "OB": "Other Byte",
        "OD": "Other Double",
        "OF": "Other Float",
        "OL": "Other Long",
        "OW": "Other Word",
        "PN": "Person Name (Family^Given^Middle^Prefix^Suffix)",
        "SH": "Short String (max 16 chars)",
        "SL": "Signed Long (4 bytes)",
        "SQ": "Sequence of Items",
        "SS": "Signed Short (2 bytes)",
        "ST": "Short Text (max 1024 chars)",
        "TM": "Time (HHMMSS.FFFFFF)",
        "UC": "Unlimited Characters",
        "UI": "Unique Identifier (max 64 chars, UID format)",
        "UL": "Unsigned Long (4 bytes)",
        "UN": "Unknown",
        "UR": "Universal Resource Identifier/Locator",
        "US": "Unsigned Short (2 bytes)",
        "UT": "Unlimited Text",
    }
    return vr_descriptions.get(vr, vr)


def format_hl7_field_ref(segment: str, position: int, component: int | None = None) -> str:
    """Format an HL7 field reference (e.g., PID-3.1)."""
    if component is not None:
        return f"{segment}-{position}.{component}"
    return f"{segment}-{position}"


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def indent_text(text: str, spaces: int = 2) -> str:
    """Indent each line of text."""
    prefix = " " * spaces
    return "\n".join(prefix + line for line in text.split("\n"))


def format_mapping_arrow(source: str, target: str) -> str:
    """Format a mapping as source -> target."""
    return f"{source} -> {target}"
