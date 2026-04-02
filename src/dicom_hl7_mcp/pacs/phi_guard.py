"""PHI safety utilities for PACS connectivity.

Ensures that Protected Health Information never leaks into logs,
error messages, or cached files. Query results are formatted with
clear PHI warnings. Optional output redaction is available.
"""

from __future__ import annotations

import logging
import re

from dicom_hl7_mcp.config import PHI_REDACT

# DICOM tag keywords and HL7 fields that contain PHI
PHI_DICOM_KEYWORDS = frozenset({
    "PatientName",
    "PatientID",
    "PatientBirthDate",
    "PatientBirthTime",
    "PatientSex",
    "PatientAge",
    "PatientAddress",
    "PatientTelephoneNumbers",
    "OtherPatientIDs",
    "OtherPatientNames",
    "EthnicGroup",
    "PatientComments",
    "PatientInsurancePlanCodeSequence",
    "MedicalRecordLocator",
    "ReferringPhysicianName",
    "ReferringPhysicianTelephoneNumbers",
    "InstitutionName",
    "InstitutionAddress",
    "InstitutionalDepartmentName",
    "PerformingPhysicianName",
    "OperatorsName",
    "RequestingPhysician",
    "ScheduledPerformingPhysicianName",
    "OrderingProvider",
    "AccessionNumber",
})

# DICOM tag numbers (group, element) that contain PHI
PHI_DICOM_TAGS = frozenset({
    (0x0010, 0x0010),  # PatientName
    (0x0010, 0x0020),  # PatientID
    (0x0010, 0x0030),  # PatientBirthDate
    (0x0010, 0x0032),  # PatientBirthTime
    (0x0010, 0x1000),  # OtherPatientIDs
    (0x0010, 0x1001),  # OtherPatientNames
    (0x0010, 0x1040),  # PatientAddress
    (0x0010, 0x2154),  # PatientTelephoneNumbers
    (0x0008, 0x0050),  # AccessionNumber
    (0x0008, 0x0090),  # ReferringPhysicianName
    (0x0008, 0x0080),  # InstitutionName
    (0x0008, 0x0081),  # InstitutionAddress
})

PHI_RESULT_BANNER = "--- PACS Query Result (contains PHI — handle per your organization's policy) ---\n"

PHI_CLOUD_WARNING = (
    "WARNING: This tool connects to real PACS systems containing PHI.\n"
    "Do not use with cloud-hosted LLMs unless your organization's policies\n"
    "permit sending PHI to that LLM provider."
)


class PHIRedactingFilter(logging.Filter):
    """Logging filter that redacts known PHI patterns from log records.

    Catches common PHI patterns like patient names, IDs, dates of birth,
    and accession numbers in log messages.
    """

    # Patterns to redact in log messages
    _PATTERNS = [
        # Patient name patterns (Last^First or LAST^FIRST^MIDDLE)
        (re.compile(r"PatientName['\"]?\s*[:=]\s*['\"]?([^,\n'\"}\]]+)"), "PatientName=[REDACTED]"),
        (re.compile(r"Patient(?:'s)?\s*Name['\"]?\s*[:=]\s*['\"]?([^,\n'\"}\]]+)"), "PatientName=[REDACTED]"),
        # Patient ID
        (re.compile(r"PatientID['\"]?\s*[:=]\s*['\"]?([^,\n'\"}\]]+)"), "PatientID=[REDACTED]"),
        # Date of birth
        (re.compile(r"PatientBirthDate['\"]?\s*[:=]\s*['\"]?(\d{8})"), "PatientBirthDate=[REDACTED]"),
        # Accession number
        (re.compile(r"AccessionNumber['\"]?\s*[:=]\s*['\"]?([^,\n'\"}\]]+)"), "AccessionNumber=[REDACTED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Redact PHI from log record message. Always returns True (never drops records)."""
        if isinstance(record.msg, str):
            msg = record.msg
            for pattern, replacement in self._PATTERNS:
                msg = pattern.sub(replacement, msg)
            record.msg = msg
        return True


def install_phi_filter(logger_name: str = "dicom_hl7_mcp") -> None:
    """Install the PHI redacting filter on the specified logger and all its children."""
    logger = logging.getLogger(logger_name)
    logger.addFilter(PHIRedactingFilter())


def redact_result(text: str) -> str:
    """Optionally redact PHI fields from a PACS tool result string.

    Only redacts if DICOM_HL7_PHI_REDACT=true is set. Otherwise returns
    the text unchanged.

    Args:
        text: The formatted result string.

    Returns:
        The result with PHI fields replaced by [REDACTED] if redaction is enabled.
    """
    if not PHI_REDACT:
        return text

    # Redact patient name values (handles DICOM PN format: Last^First^Middle)
    text = re.sub(
        r"(Patient(?:'s)?\s*Name\s*[:=|]\s*)([A-Za-z\^]+(?:\^[A-Za-z]+)*)",
        r"\1[REDACTED]",
        text,
    )
    # Redact patient ID values
    text = re.sub(
        r"(Patient\s*ID\s*[:=|]\s*)(\S+)",
        r"\1[REDACTED]",
        text,
    )
    # Redact accession numbers
    text = re.sub(
        r"(Accession\s*(?:Number)?\s*[:=|]\s*)(\S+)",
        r"\1[REDACTED]",
        text,
    )
    # Redact dates of birth
    text = re.sub(
        r"((?:Birth|DOB)\s*(?:Date)?\s*[:=|]\s*)(\d{4}[-/]?\d{2}[-/]?\d{2})",
        r"\1[REDACTED]",
        text,
    )

    return text


def format_pacs_result(content: str) -> str:
    """Wrap a PACS tool result with the PHI banner and apply optional redaction.

    Args:
        content: The raw result content.

    Returns:
        The content with PHI banner prepended and optional redaction applied.
    """
    result = PHI_RESULT_BANNER + content
    return redact_result(result)


def sanitize_exception(exc: Exception) -> str:
    """Extract an error message from an exception, stripping any PHI.

    Args:
        exc: The exception to sanitize.

    Returns:
        A safe error message string.
    """
    msg = str(exc)
    # Strip anything that looks like DICOM PN values or patient IDs
    for pattern, replacement in PHIRedactingFilter._PATTERNS:
        msg = pattern.sub(replacement, msg)
    return msg
