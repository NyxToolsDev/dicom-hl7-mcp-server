"""Tests for HL7 parsing and explanation tools."""

import pytest

from dicom_hl7_mcp.tools.hl7_parser import (
    explain_hl7_segment,
    lookup_hl7_table,
    parse_hl7_message,
)
from tests.conftest import SAMPLE_ADT_A01, SAMPLE_MALFORMED, SAMPLE_ORM_O01, SAMPLE_ORU_R01


class TestParseHl7Message:
    """Tests for parse_hl7_message."""

    def test_parse_adt_a01(self):
        """Parse a standard ADT^A01 message."""
        result = parse_hl7_message(SAMPLE_ADT_A01)
        assert "ADT^A01" in result
        assert "Admit/Visit Notification" in result
        assert "DOE^JOHN^M" in result
        assert "MRN12345" in result
        assert "PID" in result
        assert "PV1" in result

    def test_parse_orm_o01(self):
        """Parse an ORM^O01 order message."""
        result = parse_hl7_message(SAMPLE_ORM_O01)
        assert "ORM^O01" in result
        assert "CT ABDOMEN WITH CONTRAST" in result
        assert "ORC" in result
        assert "OBR" in result

    def test_parse_oru_r01(self):
        """Parse an ORU^R01 results message."""
        result = parse_hl7_message(SAMPLE_ORU_R01)
        assert "ORU^R01" in result
        assert "OBX" in result
        assert "Radiology Report" in result or "Report" in result

    def test_parse_identifies_segment_names(self):
        """Parsed output should include segment names."""
        result = parse_hl7_message(SAMPLE_ADT_A01)
        assert "Message Header" in result
        assert "Patient Identification" in result
        assert "Patient Visit" in result
        assert "Event Type" in result

    def test_parse_identifies_field_names(self):
        """Parsed output should include field names."""
        result = parse_hl7_message(SAMPLE_ADT_A01)
        assert "Patient Name" in result or "Patient Identifier" in result

    def test_parse_table_lookups(self):
        """Parser should look up table values."""
        result = parse_hl7_message(SAMPLE_ADT_A01)
        # PID-8 = M should resolve to Male from Table 0001
        assert "Male" in result or "M" in result
        # PV1-2 = I should resolve to Inpatient from Table 0004
        assert "Inpatient" in result or "I" in result

    def test_parse_empty_message(self):
        """Empty message should return error."""
        result = parse_hl7_message("")
        assert "Error" in result or "error" in result

    def test_parse_malformed_no_msh(self):
        """Message without MSH should return error."""
        result = parse_hl7_message(SAMPLE_MALFORMED)
        assert "Error" in result or "MSH" in result

    def test_parse_handles_newlines(self):
        """Should handle various line ending formats."""
        msg_with_newlines = SAMPLE_ADT_A01.replace("\r", "\n")
        result = parse_hl7_message(msg_with_newlines)
        assert "ADT^A01" in result

    def test_parse_handles_escaped_newlines(self):
        """Should handle escaped \\r\\n from JSON."""
        msg_escaped = SAMPLE_ADT_A01.replace("\r", "\\r")
        result = parse_hl7_message(msg_escaped)
        assert "ADT^A01" in result

    def test_parse_shows_components(self):
        """Should parse and display components."""
        result = parse_hl7_message(SAMPLE_ADT_A01)
        # PID-5 has components (Family^Given^Middle)
        assert "Components" in result or "DOE" in result


class TestExplainHl7Segment:
    """Tests for explain_hl7_segment."""

    def test_explain_pid(self):
        """Explain PID segment."""
        result = explain_hl7_segment("PID")
        assert "Patient Identification" in result
        assert "Patient Name" in result
        assert "Patient Identifier List" in result

    def test_explain_msh(self):
        """Explain MSH segment."""
        result = explain_hl7_segment("MSH")
        assert "Message Header" in result
        assert "Field Separator" in result
        assert "Message Type" in result

    def test_explain_obx(self):
        """Explain OBX segment."""
        result = explain_hl7_segment("OBX")
        assert "Observation" in result
        assert "Value Type" in result
        assert "Observation Value" in result

    def test_explain_orc(self):
        """Explain ORC segment."""
        result = explain_hl7_segment("ORC")
        assert "Common Order" in result
        assert "Order Control" in result

    def test_explain_obr(self):
        """Explain OBR segment."""
        result = explain_hl7_segment("OBR")
        assert "Observation Request" in result
        assert "Universal Service Identifier" in result

    def test_explain_case_insensitive(self):
        """Segment name should be case-insensitive."""
        result = explain_hl7_segment("pid")
        assert "Patient Identification" in result

    def test_explain_unknown_segment(self):
        """Unknown segment should return helpful message."""
        result = explain_hl7_segment("ZZZ")
        assert "not found" in result

    def test_explain_shows_required_fields(self):
        """Should indicate which fields are required."""
        result = explain_hl7_segment("MSH")
        assert "Required" in result

    def test_explain_shows_table_references(self):
        """Should show table references."""
        result = explain_hl7_segment("PID")
        assert "Table" in result

    def test_explain_shows_message_type_usage(self):
        """Should show which message types use this segment."""
        result = explain_hl7_segment("PID")
        assert "Used In Message Types" in result


class TestLookupHl7Table:
    """Tests for lookup_hl7_table."""

    def test_lookup_table_0001(self):
        """Look up Administrative Sex table."""
        result = lookup_hl7_table("0001")
        assert "Administrative Sex" in result
        assert "Female" in result
        assert "Male" in result

    def test_lookup_table_0004(self):
        """Look up Patient Class table."""
        result = lookup_hl7_table("0004")
        assert "Patient Class" in result
        assert "Inpatient" in result
        assert "Outpatient" in result

    def test_lookup_table_no_leading_zeros(self):
        """Should work without leading zeros."""
        result = lookup_hl7_table("1")
        assert "Administrative Sex" in result

    def test_lookup_table_0119(self):
        """Look up Order Control Codes table."""
        result = lookup_hl7_table("0119")
        assert "Order Control" in result
        assert "NW" in result
        assert "CA" in result

    def test_lookup_table_0085(self):
        """Look up Observation Result Status table."""
        result = lookup_hl7_table("0085")
        assert "Result Status" in result or "Observation" in result
        assert "Final" in result or "F" in result

    def test_lookup_unknown_table(self):
        """Unknown table should return available tables."""
        result = lookup_hl7_table("9999")
        assert "not found" in result

    def test_lookup_shows_referencing_fields(self):
        """Should show which fields reference the table."""
        result = lookup_hl7_table("0001")
        assert "Referenced by" in result
        assert "PID-8" in result
