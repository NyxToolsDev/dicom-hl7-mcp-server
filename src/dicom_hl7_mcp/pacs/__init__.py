"""PACS connectivity module.

Provides C-FIND/C-MOVE (via pynetdicom) and DICOMweb (via httpx) support.
These are optional dependencies — install with: pip install dicom-hl7-mcp[pacs]
"""

_HAS_PYNETDICOM = False
_HAS_HTTPX = False

try:
    import pynetdicom  # noqa: F401

    _HAS_PYNETDICOM = True
except ImportError:
    pass

try:
    import httpx  # noqa: F401

    _HAS_HTTPX = True
except ImportError:
    pass

PACS_INSTALL_HINT = (
    "PACS connectivity requires additional dependencies.\n"
    "Install with:\n"
    "  pip install dicom-hl7-mcp[pacs]\n"
    "Or with uvx:\n"
    "  uvx --with 'dicom-hl7-mcp[pacs]' dicom-hl7-mcp"
)


def require_pacs_deps(protocol: str = "auto") -> str | None:
    """Return an error message if needed dependencies are missing, None if OK.

    Args:
        protocol: 'dimse', 'dicomweb', or 'auto'.

    Returns:
        Error message string if deps are missing, None if all deps available.
    """
    if protocol == "dimse":
        if not _HAS_PYNETDICOM:
            return f"pynetdicom is required for DIMSE operations.\n\n{PACS_INSTALL_HINT}"
        return None

    if protocol == "dicomweb":
        if not _HAS_HTTPX:
            return f"httpx is required for DICOMweb operations.\n\n{PACS_INSTALL_HINT}"
        return None

    # auto — need at least one
    if not _HAS_PYNETDICOM and not _HAS_HTTPX:
        return PACS_INSTALL_HINT

    return None
