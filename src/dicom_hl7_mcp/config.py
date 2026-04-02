"""Configuration for the DICOM/HL7 MCP Server."""

import os
from pathlib import Path


# ---------------------------------------------------------------
# License
# ---------------------------------------------------------------

# License key for premium features (optional)
DICOM_HL7_LICENSE_KEY: str | None = os.environ.get("DICOM_HL7_LICENSE_KEY")

# Premium license validation endpoint
LICENSE_VALIDATION_URL: str = os.environ.get(
    "DICOM_HL7_LICENSE_URL",
    "https://api.gumroad.com/v2/licenses/verify",
)

# Cache directory for license validation results
CACHE_DIR: Path = Path(os.environ.get("DICOM_HL7_CACHE_DIR", Path.home() / ".dicom-hl7-mcp"))

# ---------------------------------------------------------------
# General
# ---------------------------------------------------------------

# Logging level
LOG_LEVEL: str = os.environ.get("DICOM_HL7_LOG_LEVEL", "INFO")

# Path to a custom dictionary file (JSON) that extends the built-in knowledge base
CUSTOM_DICTIONARY_PATH: str | None = os.environ.get("DICOM_HL7_CUSTOM_DICTIONARY")

# ---------------------------------------------------------------
# PACS — Traditional DICOM (C-FIND / C-MOVE / C-ECHO)
# ---------------------------------------------------------------

PACS_AE_TITLE: str = os.environ.get("DICOM_HL7_PACS_AE_TITLE", "")
PACS_HOST: str = os.environ.get("DICOM_HL7_PACS_HOST", "")
PACS_PORT: int = int(os.environ.get("DICOM_HL7_PACS_PORT", "0"))
LOCAL_AE_TITLE: str = os.environ.get("DICOM_HL7_LOCAL_AE_TITLE", "DICOM_HL7_MCP")

# ---------------------------------------------------------------
# PACS — DICOMweb (QIDO-RS / WADO-RS)
# ---------------------------------------------------------------

DICOMWEB_URL: str = os.environ.get("DICOM_HL7_DICOMWEB_URL", "")
DICOMWEB_AUTH_TYPE: str = os.environ.get("DICOM_HL7_DICOMWEB_AUTH", "none")  # none | bearer | basic
DICOMWEB_TOKEN: str = os.environ.get("DICOM_HL7_DICOMWEB_TOKEN", "")
DICOMWEB_USERNAME: str = os.environ.get("DICOM_HL7_DICOMWEB_USERNAME", "")
DICOMWEB_PASSWORD: str = os.environ.get("DICOM_HL7_DICOMWEB_PASSWORD", "")

# ---------------------------------------------------------------
# PACS — Protocol and Safety
# ---------------------------------------------------------------

# auto | dimse | dicomweb — "auto" prefers DICOMweb if configured, falls back to DIMSE
PACS_PROTOCOL: str = os.environ.get("DICOM_HL7_PACS_PROTOCOL", "auto")

# C-MOVE is double-gated: requires premium AND this must be "true"
PACS_ALLOW_RETRIEVE: bool = os.environ.get("DICOM_HL7_PACS_ALLOW_RETRIEVE", "false").lower() == "true"

# When true, replaces patient name/ID in tool output with [REDACTED]
PHI_REDACT: bool = os.environ.get("DICOM_HL7_PHI_REDACT", "false").lower() == "true"


# ---------------------------------------------------------------
# Derived helpers
# ---------------------------------------------------------------

def is_premium_enabled() -> bool:
    """Check whether premium features are enabled.

    Returns True if a valid license key is configured. In the initial
    release this performs a simple presence check. Future versions will
    validate the key against the Gumroad API.
    """
    return DICOM_HL7_LICENSE_KEY is not None and len(DICOM_HL7_LICENSE_KEY) > 0


def get_pacs_protocol() -> str:
    """Determine which PACS protocol to use.

    Returns 'dicomweb', 'dimse', or 'none'.
    In 'auto' mode, prefers DICOMweb if configured, falls back to DIMSE.
    """
    if PACS_PROTOCOL != "auto":
        return PACS_PROTOCOL
    if DICOMWEB_URL:
        return "dicomweb"
    if PACS_HOST and PACS_PORT:
        return "dimse"
    return "none"


def is_pacs_configured() -> bool:
    """Return True if any PACS connection is configured."""
    return get_pacs_protocol() != "none"
