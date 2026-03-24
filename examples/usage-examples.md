# Usage Examples

## Free Tier Examples

### 1. Look up a DICOM tag by number
**Prompt:** "What is DICOM tag (0008,0050)?"
**Tool:** `lookup_dicom_tag` with tag="0008,0050"

### 2. Look up a DICOM tag by keyword
**Prompt:** "What DICOM tag stores the patient's name?"
**Tool:** `lookup_dicom_tag` with tag="patient name"

### 3. Explain a DICOM tag in depth
**Prompt:** "Explain how AccessionNumber works and common issues"
**Tool:** `explain_dicom_tag` with tag="AccessionNumber"

### 4. Parse an HL7 message
**Prompt:** "Parse this HL7 message: MSH|^~\\&|RIS|RAD|EMR|HOSP|202403151400||ORU^R01|MSG001|P|2.5.1..."
**Tool:** `parse_hl7_message` with the full message

### 5. Explain an HL7 segment
**Prompt:** "What fields are in the OBR segment?"
**Tool:** `explain_hl7_segment` with segment_name="OBR"

### 6. Look up HL7 table values
**Prompt:** "What are the valid values for Patient Class?"
**Tool:** `lookup_hl7_table` with table_number="0004"

## Premium Tier Examples

### 7. Map DICOM to HL7
**Prompt:** "What HL7 field does DICOM AccessionNumber map to?"
**Tool:** `map_dicom_to_hl7` with tag="AccessionNumber"

### 8. Map HL7 to FHIR
**Prompt:** "How does PID-3 map to FHIR?"
**Tool:** `map_hl7_to_fhir` with field_ref="PID-3"

### 9. Generate Mirth channel
**Prompt:** "Generate a Mirth channel for ADT from Epic to PACS"
**Tool:** `generate_mirth_channel` with source_type="HL7v2", destination_type="HL7v2", use_case="ADT feed from Epic to PACS"

### 10. Validate an HL7 message
**Prompt:** "Validate this HL7 message for correctness"
**Tool:** `validate_hl7_message` with the message

### 11. Explain integration patterns
**Prompt:** "Explain the radiology workflow integration pattern"
**Tool:** `explain_integration_pattern` with pattern_name="radiology workflow"

### 12. Decode private tags
**Prompt:** "What is Siemens private tag (0019,100C)?"
**Tool:** `decode_private_tags` with tag="0019,100C", vendor="Siemens"

### 13. Generate sample messages
**Prompt:** "Generate a sample ADT^A01 message for an emergency CT"
**Tool:** `generate_sample_message` with message_type="ADT^A01", scenario="emergency CT"
