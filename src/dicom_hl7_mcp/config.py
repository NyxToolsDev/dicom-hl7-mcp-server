"""Configuration for the DICOM/HL7 MCP Server."""

import os
from pathlib import Path


# License key for premium features (optional)
DICOM_HL7_LICENSE_KEY: str | None = os.environ.get("DICOM_HL7_LICENSE_KEY")

# Logging level
LOG_LEVEL: str = os.environ.get("DICOM_HL7_LOG_LEVEL", "INFO")

# Path to a custom dictionary file (JSON) that extends the built-in knowledge base
CUSTOM_DICTIONARY_PATH: str | None = os.environ.get("DICOM_HL7_CUSTOM_DICTIONARY")

# Premium license validation endpoint
LICENSE_VALIDATION_URL: str = os.environ.get(
    "DICOM_HL7_LICENSE_URL",
    "https://api.lemonsqueezy.com/v1/licenses/validate",
)

# Cache directory for license validation results
CACHE_DIR: Path = Path(os.environ.get("DICOM_HL7_CACHE_DIR", Path.home() / ".dicom-hl7-mcp"))


def is_premium_enabled() -> bool:
    """Check whether premium features are enabled.

    Returns True if a valid license key is configured. In the initial
    release this performs a simple presence check. Future versions will
    validate the key against the Lemon Squeezy API.
    """
    return DICOM_HL7_LICENSE_KEY is not None and len(DICOM_HL7_LICENSE_KEY) > 0
