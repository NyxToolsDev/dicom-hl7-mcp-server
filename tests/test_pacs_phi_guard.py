"""Tests for PHI safety utilities."""

import logging

from dicom_hl7_mcp.pacs.phi_guard import (
    PHIRedactingFilter,
    format_pacs_result,
    redact_result,
    sanitize_exception,
)


class TestPHIRedactingFilter:
    """Tests for the logging filter."""

    def test_redacts_patient_name(self):
        """Should redact PatientName from log messages."""
        f = PHIRedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Query returned PatientName='DOE^JOHN' for study",
            args=(), exc_info=None,
        )
        f.filter(record)
        assert "DOE^JOHN" not in record.msg
        assert "REDACTED" in record.msg

    def test_redacts_patient_id(self):
        """Should redact PatientID from log messages."""
        f = PHIRedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="Found PatientID=MRN12345 in response",
            args=(), exc_info=None,
        )
        f.filter(record)
        assert "MRN12345" not in record.msg

    def test_redacts_birth_date(self):
        """Should redact PatientBirthDate from log messages."""
        f = PHIRedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="PatientBirthDate=19800115",
            args=(), exc_info=None,
        )
        f.filter(record)
        assert "19800115" not in record.msg

    def test_allows_non_phi_through(self):
        """Non-PHI messages should pass through unchanged."""
        f = PHIRedactingFilter()
        msg = "C-FIND completed with 5 results"
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg=msg, args=(), exc_info=None,
        )
        f.filter(record)
        assert record.msg == msg

    def test_always_returns_true(self):
        """Filter should never drop records."""
        f = PHIRedactingFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0,
            msg="anything", args=(), exc_info=None,
        )
        assert f.filter(record) is True


class TestFormatPacsResult:
    """Tests for result formatting."""

    def test_adds_phi_banner(self):
        """Should prepend the PHI warning banner."""
        result = format_pacs_result("some content")
        assert "PACS Query Result" in result
        assert "PHI" in result
        assert "some content" in result

    def test_empty_content(self):
        """Should handle empty content."""
        result = format_pacs_result("")
        assert "PACS Query Result" in result


class TestSanitizeException:
    """Tests for exception sanitization."""

    def test_strips_patient_name_from_exception(self):
        """Should remove PHI from exception messages."""
        exc = Exception("Error processing PatientName='DOE^JOHN' in dataset")
        result = sanitize_exception(exc)
        assert "DOE^JOHN" not in result

    def test_preserves_non_phi_error(self):
        """Non-PHI exception messages should pass through."""
        exc = Exception("Connection refused on port 104")
        result = sanitize_exception(exc)
        assert "Connection refused" in result


class TestRedactResult:
    """Tests for optional output redaction."""

    def test_no_redaction_by_default(self, monkeypatch):
        """When PHI_REDACT is False, text passes through unchanged."""
        monkeypatch.setattr("dicom_hl7_mcp.pacs.phi_guard.PHI_REDACT", False)
        text = "Patient Name: DOE^JOHN"
        assert redact_result(text) == text

    def test_redacts_when_enabled(self, monkeypatch):
        """When PHI_REDACT is True, patient identifiers are replaced."""
        monkeypatch.setattr("dicom_hl7_mcp.pacs.phi_guard.PHI_REDACT", True)
        text = "Patient Name: DOE^JOHN\nPatient ID: MRN001\nAccession Number: ACC123"
        result = redact_result(text)
        assert "DOE^JOHN" not in result
        assert "MRN001" not in result
        assert "ACC123" not in result
        assert "[REDACTED]" in result
