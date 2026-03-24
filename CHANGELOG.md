# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-03-23

### Added
- Initial release
- **Free Tier Tools:**
  - `lookup_dicom_tag` — Look up DICOM tags by number or keyword
  - `explain_dicom_tag` — Detailed DICOM tag explanations with vendor notes
  - `parse_hl7_message` — Parse HL7 v2.x messages into human-readable format
  - `explain_hl7_segment` — Explain HL7 segment fields and usage
  - `lookup_hl7_table` — Look up HL7 table values
- **Premium Tier Tools:**
  - `map_dicom_to_hl7` — Map DICOM tags to HL7 v2 fields
  - `map_hl7_to_fhir` — Map HL7 v2 fields to FHIR R4 resources
  - `generate_mirth_channel` — Generate Mirth Connect channel configs
  - `validate_hl7_message` — Validate HL7 messages against standard
  - `explain_integration_pattern` — Explain healthcare integration patterns
  - `decode_private_tags` — Decode vendor private DICOM tags
  - `generate_sample_message` — Generate sample HL7 messages for testing
- **Knowledge Base:**
  - ~200 common DICOM tags with accurate metadata
  - Common SOP Classes and Transfer Syntaxes
  - Private tag ranges for GE, Siemens, Philips, Fuji, Agfa, Canon/Toshiba, Hologic
  - HL7 v2.x segment definitions (MSH, EVN, PID, PV1, PV2, ORC, OBR, OBX, DG1, AL1, NK1, IN1, GT1, TXA, FT1)
  - HL7 table values for 20+ commonly referenced tables
  - HL7-to-FHIR R4 mappings per the v2-to-FHIR IG
  - DICOM-to-HL7 field mappings
  - 7 healthcare integration patterns with flow diagrams and best practices
