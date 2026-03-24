"""Tests for DICOM tag lookup and explanation tools."""

import pytest

from dicom_hl7_mcp.tools.dicom_tags import explain_dicom_tag, lookup_dicom_tag


class TestLookupDicomTag:
    """Tests for lookup_dicom_tag."""

    def test_lookup_by_number_comma_format(self):
        """Look up a tag by GGGG,EEEE format."""
        result = lookup_dicom_tag("0010,0010")
        assert "PatientName" in result
        assert "Patient's Name" in result
        assert "PN" in result

    def test_lookup_by_number_parentheses(self):
        """Look up a tag with parentheses."""
        result = lookup_dicom_tag("(0010,0010)")
        assert "PatientName" in result

    def test_lookup_by_number_no_comma(self):
        """Look up a tag as 8 hex digits."""
        result = lookup_dicom_tag("00100010")
        assert "PatientName" in result

    def test_lookup_by_number_with_0x(self):
        """Look up a tag with 0x prefix."""
        result = lookup_dicom_tag("0x00100010")
        assert "PatientName" in result

    def test_lookup_by_keyword_exact(self):
        """Look up by exact keyword."""
        result = lookup_dicom_tag("PatientName")
        assert "(0010,0010)" in result
        assert "PN" in result

    def test_lookup_by_keyword_case_insensitive(self):
        """Keywords should be case-insensitive."""
        result = lookup_dicom_tag("patientname")
        assert "PatientName" in result

    def test_lookup_by_name_with_spaces(self):
        """Look up by descriptive name with spaces."""
        result = lookup_dicom_tag("patient name")
        assert "PatientName" in result

    def test_lookup_by_partial_keyword(self):
        """Partial keyword should return multiple results."""
        result = lookup_dicom_tag("Modality")
        assert "Modality" in result

    def test_lookup_accession_number(self):
        """Look up AccessionNumber — critical integration field."""
        result = lookup_dicom_tag("0008,0050")
        assert "AccessionNumber" in result
        assert "SH" in result

    def test_lookup_study_instance_uid(self):
        """Look up StudyInstanceUID."""
        result = lookup_dicom_tag("StudyInstanceUID")
        assert "(0020,000D)" in result
        assert "UI" in result

    def test_lookup_unknown_tag(self):
        """Unknown tag should return informative message."""
        result = lookup_dicom_tag("9999,9999")
        assert "not found" in result

    def test_lookup_unknown_keyword(self):
        """Unknown keyword should return informative message."""
        result = lookup_dicom_tag("nonexistenttag12345")
        assert "not found" in result or "No DICOM tags found" in result

    def test_lookup_private_tag(self):
        """Private (odd group) tags should be identified as private."""
        result = lookup_dicom_tag("0019,100C")
        assert "private" in result.lower() or "PRIVATE" in result

    def test_lookup_sop_class_uid(self):
        """Look up SOPClassUID."""
        result = lookup_dicom_tag("0008,0016")
        assert "SOPClassUID" in result
        assert "CT Image Storage" in result or "SOP Class" in result

    def test_lookup_pixel_data(self):
        """Look up Pixel Data tag."""
        result = lookup_dicom_tag("7FE0,0010")
        assert "PixelData" in result

    def test_lookup_transfer_syntax(self):
        """Look up Transfer Syntax UID."""
        result = lookup_dicom_tag("0002,0010")
        assert "TransferSyntaxUID" in result
        assert "JPEG" in result or "transfer syntax" in result.lower()

    def test_multiple_results_limited(self):
        """Multiple matches should be listed."""
        result = lookup_dicom_tag("Date")
        assert "Found" in result
        # Should match StudyDate, SeriesDate, AcquisitionDate, etc.


class TestExplainDicomTag:
    """Tests for explain_dicom_tag."""

    def test_explain_patient_name(self):
        """Explain PatientName should have detailed context."""
        result = explain_dicom_tag("PatientName")
        assert "What It Is" in result
        assert "When It's Used" in result
        assert "Value Representation" in result

    def test_explain_accession_number(self):
        """AccessionNumber explanation should mention RIS/PACS matching."""
        result = explain_dicom_tag("AccessionNumber")
        assert "RIS" in result or "order" in result.lower()

    def test_explain_by_number(self):
        """Should work with tag number input."""
        result = explain_dicom_tag("0008,0060")
        assert "Modality" in result
        assert "What It Is" in result

    def test_explain_unknown_tag(self):
        """Unknown tag should return appropriate message."""
        result = explain_dicom_tag("nonexistent")
        assert "not found" in result.lower()

    def test_explain_includes_related_tags(self):
        """Explanation should include related tags."""
        result = explain_dicom_tag("StudyDate")
        # Should mention SeriesDate, AcquisitionDate, etc.
        assert "Related Tags" in result

    def test_explain_includes_vr_details(self):
        """Should explain the VR in detail."""
        result = explain_dicom_tag("PatientID")
        assert "Value Representation" in result
