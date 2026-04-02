"""Tests for PACS connectivity tools.

Tests tool dispatch, premium gating, dependency gating, and
result formatting using mocked connection manager.
"""

from unittest.mock import patch

import pytest

from dicom_hl7_mcp.pacs.models import EchoResult, QueryFilters, StudyResult
from dicom_hl7_mcp.tools.pacs_connectivity import dispatch_pacs_tool


@pytest.fixture()
def premium_enabled(monkeypatch):
    """Enable premium features for the test."""
    monkeypatch.setenv("DICOM_HL7_LICENSE_KEY", "test-license-key-12345")
    monkeypatch.setattr("dicom_hl7_mcp.config.DICOM_HL7_LICENSE_KEY", "test-license-key-12345")
    monkeypatch.setattr("dicom_hl7_mcp.utils.license.DICOM_HL7_LICENSE_KEY", "test-license-key-12345")


@pytest.fixture()
def pacs_configured(monkeypatch):
    """Configure a fake PACS connection."""
    monkeypatch.setattr("dicom_hl7_mcp.config.PACS_HOST", "127.0.0.1")
    monkeypatch.setattr("dicom_hl7_mcp.config.PACS_PORT", 4242)
    monkeypatch.setattr("dicom_hl7_mcp.config.PACS_AE_TITLE", "TESTPACS")
    monkeypatch.setattr("dicom_hl7_mcp.tools.pacs_connectivity.is_pacs_configured", lambda: True)
    monkeypatch.setattr("dicom_hl7_mcp.tools.pacs_connectivity.get_pacs_protocol", lambda: "dimse")


class TestPremiumGating:
    """All PACS tools should require premium license."""

    def test_echo_requires_premium(self):
        result = dispatch_pacs_tool("pacs_echo", {})
        assert "premium" in result.lower()

    def test_query_requires_premium(self):
        result = dispatch_pacs_tool("pacs_query", {})
        assert "premium" in result.lower()

    def test_get_metadata_requires_premium(self):
        result = dispatch_pacs_tool("pacs_get_metadata", {"study_instance_uid": "1.2.3"})
        assert "premium" in result.lower()

    def test_retrieve_requires_premium(self):
        result = dispatch_pacs_tool("pacs_retrieve", {
            "study_instance_uid": "1.2.3",
            "destination_ae_title": "WORKSTATION",
        })
        assert "premium" in result.lower()


class TestConfigurationGating:
    """PACS tools should check for configuration."""

    def test_query_requires_config(self, premium_enabled, monkeypatch):
        monkeypatch.setattr("dicom_hl7_mcp.tools.pacs_connectivity.is_pacs_configured", lambda: False)
        monkeypatch.setattr("dicom_hl7_mcp.tools.pacs_connectivity.get_pacs_protocol", lambda: "none")
        result = dispatch_pacs_tool("pacs_query", {})
        assert "No PACS connection configured" in result


class TestRetrieveGating:
    """C-MOVE should be double-gated."""

    def test_retrieve_disabled_by_default(self, premium_enabled, pacs_configured, monkeypatch):
        monkeypatch.setattr("dicom_hl7_mcp.tools.pacs_connectivity.PACS_ALLOW_RETRIEVE", False)
        result = dispatch_pacs_tool("pacs_retrieve", {
            "study_instance_uid": "1.2.3",
            "destination_ae_title": "WORKSTATION",
        })
        assert "disabled" in result.lower()


class TestEchoFormatting:
    """Test echo result formatting."""

    def test_formats_success(self, premium_enabled, pacs_configured):
        mock_result = EchoResult(
            success=True,
            protocol="dimse",
            message="C-ECHO successful",
            response_time_ms=42.5,
            remote_ae="TESTPACS",
            local_ae="DICOM_HL7_MCP",
        )
        with patch("dicom_hl7_mcp.tools.pacs_connectivity.pacs_echo", return_value=mock_result):
            result = dispatch_pacs_tool("pacs_echo", {})
            assert "SUCCESS" in result
            assert "42.5 ms" in result

    def test_formats_failure(self, premium_enabled, pacs_configured):
        mock_result = EchoResult(
            success=False,
            protocol="dimse",
            message="Connection refused",
            response_time_ms=100.0,
        )
        with patch("dicom_hl7_mcp.tools.pacs_connectivity.pacs_echo", return_value=mock_result):
            result = dispatch_pacs_tool("pacs_echo", {})
            assert "FAILED" in result


class TestQueryFormatting:
    """Test query result formatting."""

    def test_formats_study_results(self, premium_enabled, pacs_configured):
        mock_results = [
            StudyResult(
                study_instance_uid="1.2.3",
                patient_name="DOE^JOHN",
                patient_id="MRN001",
                study_date="20260401",
                modalities_in_study="CT",
                study_description="CT CHEST",
            ),
        ]
        with patch("dicom_hl7_mcp.tools.pacs_connectivity.pacs_find", return_value=mock_results):
            result = dispatch_pacs_tool("pacs_query", {"study_date": "20260401"})
            assert "Found 1" in result
            assert "DOE^JOHN" in result or "REDACTED" in result
            assert "CT CHEST" in result

    def test_formats_no_results(self, premium_enabled, pacs_configured):
        with patch("dicom_hl7_mcp.tools.pacs_connectivity.pacs_find", return_value=[]):
            result = dispatch_pacs_tool("pacs_query", {"study_date": "99990101"})
            assert "No results" in result
