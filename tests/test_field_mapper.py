"""Tests for field mapping tools (DICOM->HL7, HL7->FHIR)."""

import pytest

from dicom_hl7_mcp.tools.field_mapper import (
    explain_integration_pattern,
    map_dicom_to_hl7,
    map_hl7_to_fhir,
)


class TestMapDicomToHl7:
    """Tests for map_dicom_to_hl7."""

    def test_requires_premium(self):
        """Should require premium license."""
        result = map_dicom_to_hl7("0010,0010")
        assert "premium" in result.lower() or "Premium" in result

    def test_maps_patient_name(self, premium_enabled):
        """Map PatientName to PID-5."""
        result = map_dicom_to_hl7("0010,0010")
        assert "PID-5" in result
        assert "Patient Name" in result or "PatientName" in result

    def test_maps_patient_id(self, premium_enabled):
        """Map PatientID to PID-3."""
        result = map_dicom_to_hl7("PatientID")
        assert "PID-3" in result

    def test_maps_accession_number(self, premium_enabled):
        """Map AccessionNumber to OBR-3/ORC-3."""
        result = map_dicom_to_hl7("0008,0050")
        assert "OBR-3" in result or "ORC-3" in result
        assert "Filler Order Number" in result or "Accession" in result

    def test_maps_referring_physician(self, premium_enabled):
        """Map ReferringPhysicianName to PV1-8."""
        result = map_dicom_to_hl7("0008,0090")
        assert "PV1-8" in result or "OBR-16" in result

    def test_maps_study_date(self, premium_enabled):
        """Map StudyDate to OBR-7."""
        result = map_dicom_to_hl7("0008,0020")
        assert "OBR-7" in result

    def test_maps_admission_id(self, premium_enabled):
        """Map AdmissionID to PV1-19."""
        result = map_dicom_to_hl7("0038,0010")
        assert "PV1-19" in result

    def test_no_mapping_found(self, premium_enabled):
        """Tags without HL7 equivalent should say so."""
        result = map_dicom_to_hl7("0028,0010")  # Rows — no HL7 equivalent
        assert "No HL7 mapping found" in result

    def test_unknown_tag(self, premium_enabled):
        """Unknown tags should return helpful message."""
        result = map_dicom_to_hl7("nonexistent_tag_xyz")
        assert "not found" in result

    def test_shows_data_type_conversion(self, premium_enabled):
        """Should show data type conversion info."""
        result = map_dicom_to_hl7("0010,0010")
        assert "Data Type Conversion" in result
        assert "PN" in result

    def test_shows_bidirectional_info(self, premium_enabled):
        """Should indicate if mapping is bidirectional."""
        result = map_dicom_to_hl7("0010,0010")
        assert "Bidirectional" in result


class TestMapHl7ToFhir:
    """Tests for map_hl7_to_fhir."""

    def test_requires_premium(self):
        """Should require premium license."""
        result = map_hl7_to_fhir("PID-3")
        assert "premium" in result.lower() or "Premium" in result

    def test_maps_pid3_to_patient_identifier(self, premium_enabled):
        """PID-3 should map to Patient.identifier."""
        result = map_hl7_to_fhir("PID-3")
        assert "Patient" in result
        assert "identifier" in result

    def test_maps_pid5_to_patient_name(self, premium_enabled):
        """PID-5 should map to Patient.name."""
        result = map_hl7_to_fhir("PID-5")
        assert "Patient" in result
        assert "name" in result

    def test_maps_pid7_to_birthdate(self, premium_enabled):
        """PID-7 should map to Patient.birthDate."""
        result = map_hl7_to_fhir("PID-7")
        assert "Patient" in result
        assert "birthDate" in result

    def test_maps_pid8_to_gender(self, premium_enabled):
        """PID-8 should map to Patient.gender."""
        result = map_hl7_to_fhir("PID-8")
        assert "Patient" in result
        assert "gender" in result

    def test_maps_pv1_2_to_encounter_class(self, premium_enabled):
        """PV1-2 should map to Encounter.class."""
        result = map_hl7_to_fhir("PV1-2")
        assert "Encounter" in result
        assert "class" in result

    def test_maps_obr4_to_service_request_code(self, premium_enabled):
        """OBR-4 should map to ServiceRequest.code."""
        result = map_hl7_to_fhir("OBR-4")
        assert "ServiceRequest" in result
        assert "code" in result

    def test_maps_obr25_to_diagnostic_report_status(self, premium_enabled):
        """OBR-25 should map to DiagnosticReport.status."""
        result = map_hl7_to_fhir("OBR-25")
        assert "DiagnosticReport" in result
        assert "status" in result

    def test_maps_al1_to_allergy_intolerance(self, premium_enabled):
        """AL1 fields should map to AllergyIntolerance."""
        result = map_hl7_to_fhir("AL1-3")
        assert "AllergyIntolerance" in result

    def test_maps_dg1_to_condition(self, premium_enabled):
        """DG1-3 should map to Condition.code."""
        result = map_hl7_to_fhir("DG1-3")
        assert "Condition" in result

    def test_no_mapping_for_unknown_field(self, premium_enabled):
        """Unknown fields should return helpful message."""
        result = map_hl7_to_fhir("ZZZ-1")
        assert "No FHIR mapping found" in result

    def test_invalid_field_reference(self, premium_enabled):
        """Invalid field format should return error."""
        result = map_hl7_to_fhir("not-a-field")
        assert "Invalid field reference" in result

    def test_shows_conversion_type(self, premium_enabled):
        """Should show the conversion type."""
        result = map_hl7_to_fhir("PID-3")
        assert "Conversion Type" in result

    def test_shows_fhir_resource_and_path(self, premium_enabled):
        """Should show FHIR resource and element path."""
        result = map_hl7_to_fhir("PID-5")
        assert "FHIR Resource" in result
        assert "FHIR Path" in result


class TestExplainIntegrationPattern:
    """Tests for explain_integration_pattern."""

    def test_requires_premium(self):
        """Should require premium license."""
        result = explain_integration_pattern("ADT feed")
        assert "premium" in result.lower() or "Premium" in result

    def test_adt_feed(self, premium_enabled):
        """Should explain ADT feed pattern."""
        result = explain_integration_pattern("ADT feed")
        assert "ADT" in result
        assert "Message Flow" in result
        assert "Common Pitfalls" in result
        assert "Best Practices" in result

    def test_order_to_result(self, premium_enabled):
        """Should explain order-to-result pattern."""
        result = explain_integration_pattern("order to result")
        assert "Order" in result or "order" in result
        assert "Message Flow" in result

    def test_radiology_workflow(self, premium_enabled):
        """Should explain radiology workflow pattern."""
        result = explain_integration_pattern("radiology workflow")
        assert "Radiology" in result or "radiology" in result
        assert "MWL" in result or "worklist" in result.lower()

    def test_patient_merge(self, premium_enabled):
        """Should explain patient merge pattern."""
        result = explain_integration_pattern("patient merge")
        assert "Merge" in result or "merge" in result
        assert "A34" in result or "A40" in result

    def test_unknown_pattern(self, premium_enabled):
        """Unknown pattern should list available patterns."""
        result = explain_integration_pattern("nonexistent_pattern")
        assert "not found" in result
        assert "Available" in result
