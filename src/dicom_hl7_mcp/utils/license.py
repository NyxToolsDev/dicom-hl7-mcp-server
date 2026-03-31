"""License management for premium features."""

import json
import logging
import time
from pathlib import Path

from dicom_hl7_mcp.config import (
    CACHE_DIR,
    DICOM_HL7_LICENSE_KEY,
    is_premium_enabled,
)

logger = logging.getLogger(__name__)

# Cache duration: 24 hours
LICENSE_CACHE_TTL = 86400

PREMIUM_UPGRADE_MESSAGE = (
    "This is a premium feature. To unlock it, subscribe at "
    "https://nyxtools.gumroad.com\n\n"
    "Set your license key as an environment variable:\n"
    "  export DICOM_HL7_LICENSE_KEY=your-key-here\n\n"
    "Premium features include:\n"
    "  - DICOM-to-HL7 field mapping\n"
    "  - HL7-to-FHIR resource mapping\n"
    "  - Mirth Connect channel generation\n"
    "  - HL7 message validation\n"
    "  - Integration pattern explanations\n"
    "  - Vendor private tag decoding\n"
    "  - Sample message generation\n"
)


def require_premium(tool_name: str) -> str | None:
    """Check if premium is enabled. Returns an error message if not, or None if OK.

    Args:
        tool_name: Name of the premium tool being accessed.

    Returns:
        Error message string if premium is not enabled, None if access is granted.
    """
    if not is_premium_enabled():
        return (
            f"'{tool_name}' is a premium feature.\n\n"
            f"{PREMIUM_UPGRADE_MESSAGE}"
        )

    # In production, validate the license key against the Lemon Squeezy API.
    # For now, we check that a key is present.
    if not _validate_license_key():
        return (
            f"Your license key appears to be invalid or expired for '{tool_name}'.\n\n"
            "Please check your DICOM_HL7_LICENSE_KEY environment variable.\n"
            "If you believe this is an error, contact support@nyxtools.dev"
        )

    return None


def _validate_license_key() -> bool:
    """Validate the license key.

    In the initial release, this performs a simple format check and caches
    the result. Future versions will validate against the Lemon Squeezy API.

    Returns:
        True if the license key is valid.
    """
    key = DICOM_HL7_LICENSE_KEY
    if not key:
        return False

    # Check cache first
    cached = _read_cache()
    if cached is not None:
        return cached

    # Basic format validation (will be replaced with API call)
    is_valid = len(key) >= 8

    # Cache the result
    _write_cache(is_valid)

    return is_valid


def _cache_file() -> Path:
    """Get the path to the license cache file."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR / "license_cache.json"


def _read_cache() -> bool | None:
    """Read cached license validation result.

    Returns:
        True/False if cache is valid, None if cache is expired or missing.
    """
    try:
        cache_path = _cache_file()
        if not cache_path.exists():
            return None

        data = json.loads(cache_path.read_text())
        if time.time() - data.get("timestamp", 0) > LICENSE_CACHE_TTL:
            return None

        return data.get("valid", None)
    except Exception:
        logger.debug("Failed to read license cache", exc_info=True)
        return None


def _write_cache(is_valid: bool) -> None:
    """Write license validation result to cache."""
    try:
        cache_path = _cache_file()
        data = {
            "valid": is_valid,
            "timestamp": time.time(),
        }
        cache_path.write_text(json.dumps(data))
    except Exception:
        logger.debug("Failed to write license cache", exc_info=True)
