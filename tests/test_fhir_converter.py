"""Tests for FHIR converter and HL7 validation tools."""

from __future__ import annotations

import os

# Must be set before any imports that read config
os.environ["DICOM_HL7_LICENSE_KEY"] = "test-key-for-testing"

import pytest

from dicom_hl7_mcp.tools.fhir_converter import validate_hl7_message


VALID_ADT_A01 = (
    "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|20260326120000||ADT^A01|MSG001|P|2.5\r"
    "EVN|A01|20260326120000\r"
    "PID|||12345^^^HOSP^MR||DOE^JOHN^A||19800115|M|||123 MAIN ST^^CITY^ST^12345\r"
    "PV1||I|ICU^101^A|E|||1234^SMITH^JANE^^^DR|||MED||||A|||1234^SMITH^JANE^^^DR|IP"
)

VALID_ORM_O01 = (
    "MSH|^~\\&|RIS|HOSP|PACS|HOSP|20260326120000||ORM^O01|MSG002|P|2.5\r"
    "PID|||67890^^^HOSP^MR||SMITH^JANE||19750520|F\r"
    "ORC|NW|ORD001|FILL001||SC\r"
    "OBR||ORD001|FILL001|71020^XRAY CHEST PA AND LATERAL^CPT4"
)


class TestValidateHL7Message:
    def test_empty_message(self):
        result = validate_hl7_message("")
        assert "Empty message" in result

    def test_no_msh_segment(self):
        result = validate_hl7_message("PID|||12345")
        assert "must start with MSH" in result

    def test_msh_too_short(self):
        result = validate_hl7_message("MSH|^~")
        assert "too short" in result

    def test_valid_adt_a01(self):
        result = validate_hl7_message(VALID_ADT_A01)
        assert "VALIDATION RESULTS" in result
        # Should not have critical errors for a well-formed message
        assert "FATAL" not in result

    def test_valid_orm_o01(self):
        result = validate_hl7_message(VALID_ORM_O01)
        assert "VALIDATION RESULTS" in result

    def test_missing_required_msh_fields(self):
        msg = "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|||||||"
        result = validate_hl7_message(msg)
        assert "MSH-7" in result  # Date/time missing
        assert "MSH-9" in result  # Message type missing

    def test_invalid_processing_id(self):
        msg = "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|20260326120000||ADT^A01|MSG001|X|2.5"
        result = validate_hl7_message(msg)
        assert "Processing ID must be P, D, or T" in result

    def test_debug_processing_id_warning(self):
        msg = "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|20260326120000||ADT^A01|MSG001|D|2.5"
        result = validate_hl7_message(msg)
        assert "Debug" in result

    def test_custom_z_segment_info(self):
        msg = (
            "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|20260326120000||ADT^A01|MSG001|P|2.5\r"
            "ZPI|CUSTOM|DATA"
        )
        result = validate_hl7_message(msg)
        assert "Custom Z-segment" in result

    def test_handles_escaped_newlines(self):
        msg = "MSH|^~\\&|EPIC|HOSP|LAB|HOSP|20260326120000||ADT^A01|MSG001|P|2.5\\rPID|||12345^^^HOSP^MR"
        result = validate_hl7_message(msg)
        assert "VALIDATION RESULTS" in result

    def test_orc_obr_filler_mismatch(self):
        msg = (
            "MSH|^~\\&|RIS|HOSP|PACS|HOSP|20260326120000||ORM^O01|MSG001|P|2.5\r"
            "PID|||12345^^^HOSP^MR||DOE^JOHN||19800115|M\r"
            "ORC|NW|ORD001|FILL_A||SC\r"
            "OBR||ORD001|FILL_B|71020^XRAY^CPT4"
        )
        result = validate_hl7_message(msg)
        assert "don't match" in result
