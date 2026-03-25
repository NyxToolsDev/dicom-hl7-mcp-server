# DICOM/HL7 Developer AI Assistant

<!-- mcp-name: io.github.NyxToolsDev/dicom-hl7-mcp-server -->

An MCP (Model Context Protocol) server that gives your AI assistant deep knowledge of DICOM, HL7 v2, and FHIR standards. Built by a healthcare IT engineer with 19 years of PACS, RIS, and integration experience.

**Stop Googling tag numbers. Stop guessing at field mappings. Ask your AI.**

## What It Does

| Tool | Tier | Description |
|------|------|-------------|
| `lookup_dicom_tag` | Free | Look up any DICOM tag by number or keyword |
| `explain_dicom_tag` | Free | Detailed tag explanation with vendor quirks and gotchas |
| `parse_hl7_message` | Free | Parse HL7 v2.x messages into human-readable format |
| `explain_hl7_segment` | Free | Explain segment fields, data types, and usage |
| `lookup_hl7_table` | Free | Look up HL7 table values (Administrative Sex, Patient Class, etc.) |
| `map_dicom_to_hl7` | Premium | Map DICOM tags to HL7 v2 fields with conversion notes |
| `map_hl7_to_fhir` | Premium | Map HL7 v2 fields to FHIR R4 resources |
| `generate_mirth_channel` | Premium | Generate Mirth Connect channel configurations |
| `validate_hl7_message` | Premium | Validate HL7 messages against the standard |
| `explain_integration_pattern` | Premium | Explain healthcare integration patterns with flow diagrams |
| `decode_private_tags` | Premium | Decode vendor private DICOM tags (GE, Siemens, Philips, etc.) |
| `generate_sample_message` | Premium | Generate realistic sample HL7 messages for testing |

## Installation

```bash
pip install dicom-hl7-mcp
```

Or install from source:

```bash
git clone https://github.com/nyxtools/dicom-hl7-mcp.git
cd dicom-hl7-mcp
pip install -e .
```

## Configure with Claude Desktop

Add to your Claude Desktop configuration file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

### Free Tier (no license key needed)

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "dicom-hl7-mcp"
    }
  }
}
```

### Premium Tier

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "dicom-hl7-mcp",
      "env": {
        "DICOM_HL7_LICENSE_KEY": "your-license-key-here"
      }
    }
  }
}
```

### Using uvx (no install needed)

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "uvx",
      "args": ["dicom-hl7-mcp"]
    }
  }
}
```

## Usage Examples

### Look up a DICOM tag

> "What is DICOM tag (0008,0050)?"

Returns: AccessionNumber — SH — RIS-generated number that identifies the order. THE key field for matching RIS orders to PACS studies.

> "What DICOM tag stores the patient's weight?"

Returns: (0010,1030) PatientWeight — DS — Weight in kilograms.

### Explain a tag with context

> "Explain the Transfer Syntax UID tag and common issues"

Returns detailed explanation including what Implicit VR vs Explicit VR means, common vendor defaults (GE uses Implicit, Philips uses Explicit), JPEG compression options, and troubleshooting tips for "unable to decode" errors.

### Parse an HL7 message

> "Parse this HL7 message and explain what it does:"
> ```
> MSH|^~\&|RIS|RAD|EMR|HOSP|20240315140000||ORU^R01|MSG003|P|2.5.1
> PID|1||MRN12345^^^HOSP^MR||DOE^JOHN||19650315|M
> OBR|1|ORD001|ACC001|CTABD^CT Abdomen^L|||20240315130000||||||||||||||||RAD|F||||||5555^SMITH^RAD
> OBX|1|FT|&GDT^Report||FINDINGS: Normal CT.||||||F
> ```

Returns: Each segment parsed with field names, values, table lookups, and contextual explanations.

### Map DICOM to HL7 (Premium)

> "What HL7 field does DICOM Accession Number map to?"

Returns: OBR-3 / ORC-3 (Filler Order Number) with data type conversion notes (SH -> EI) and mapping considerations.

### Map HL7 to FHIR (Premium)

> "How does PID-3 (Patient Identifier List) map to FHIR R4?"

Returns: Patient.identifier with detailed conversion guidance — CX.1->Identifier.value, CX.4->Identifier.system, CX.5->Identifier.type.

### Generate Mirth Connect Channel (Premium)

> "Generate a Mirth channel for receiving ADT messages and writing to a FHIR server"

Returns: Complete channel XML with MLLP source listener, FHIR HTTP destination, transformer steps for HL7-to-FHIR conversion, ADT event filtering, and implementation notes.

### Explain Integration Patterns (Premium)

> "Explain the radiology workflow integration pattern"

Returns: The complete IHE Scheduled Workflow profile — 15-step message flow from order placement through MWL query, image acquisition, MPPS, report dictation, and final result delivery. Includes common pitfalls (MWL AE Title mismatch, unmatched studies, MPPS not implemented) and best practices.

### Validate HL7 Messages (Premium)

> "Validate this HL7 message for errors"

Returns: Errors (required fields missing, invalid values), warnings (non-standard table values, deprecated fields), and informational notes (optional segments present, patient identifiers found).

### Decode Private Tags (Premium)

> "What is Siemens private tag (0019,100C)?"

Returns: B Value (Siemens) — Diffusion b-value, critical for DWI/ADC maps.

### Generate Sample Messages (Premium)

> "Generate a sample ORM^O01 for a CT abdomen order"

Returns: Complete, realistic HL7 message with patient demographics, ordering physician, procedure code, clinical history, and diagnosis code — ready for testing.

## Knowledge Base Coverage

### DICOM Dictionary
- ~200 most common DICOM tags with accurate tag numbers, VR, VM, descriptions
- Common SOP Classes (CT, MR, CR, DX, US, NM, PT, XA, RF, MG, SC, SR, KO, PR, RT, Encapsulated PDF)
- Transfer Syntaxes (Implicit VR LE, Explicit VR LE, JPEG Baseline/Lossless, JPEG 2000, MPEG, RLE)
- Private tag ranges for 7 major vendors (GE, Siemens, Philips, Fuji, Agfa, Canon/Toshiba, Hologic)
- Structured Report tags for DICOM SR objects

### HL7 v2.x Segments
MSH, EVN, PID, PV1, PV2, ORC, OBR, OBX, DG1, AL1, NK1, IN1, GT1, TXA, FT1 — with all field positions, data types, optionality, table references, and practical notes.

### HL7 Tables
20+ commonly referenced tables including Administrative Sex (0001), Patient Class (0004), Event Type (0003), Order Control (0119), Result Status (0123), Observation Result Status (0085), Identifier Type (0203), Value Type (0125), and more.

### HL7 Message Types
ADT (A01, A02, A03, A04, A08, A11, A13, A18, A28, A31, A34, A40), ORM^O01, ORU^R01, MDM (T01, T02, T11), SIU (S12, S14, S15), DFT^P03, BAR^P01, ACK.

### FHIR R4 Mappings
PID -> Patient, PV1 -> Encounter, ORC/OBR -> ServiceRequest/DiagnosticReport, OBX -> Observation, AL1 -> AllergyIntolerance, DG1 -> Condition, NK1 -> RelatedPerson, IN1 -> Coverage, MSH -> MessageHeader/Bundle.

### Integration Patterns
ADT Feed, Order to Result, Radiology Workflow (IHE SWF), Lab Interface, Report Distribution, Patient Merge, Charge Posting — each with message flow diagrams, trigger events, common pitfalls, and best practices.

## Premium License

Free tier gives you DICOM tag lookup, HL7 parsing, and segment explanation — the tools you use every day.

Premium ($19-39/mo) unlocks cross-standard mapping, Mirth generation, validation, and the deep integration knowledge that takes years to build.

**Get your license:** [https://nyxtools.lemonsqueezy.com](https://nyxtools.lemonsqueezy.com)

Set your license key:
```bash
export DICOM_HL7_LICENSE_KEY=your-key-here
```

## FAQ

**Q: Do I need a license key to use the free tier?**
A: No. Install and use the 5 free tools immediately. No account, no sign-up.

**Q: What HL7 versions are supported?**
A: The knowledge base covers v2.3 through v2.9, with primary focus on v2.5.1 (the most widely deployed version in US healthcare). Version differences are noted where applicable.

**Q: Is the DICOM dictionary complete?**
A: It includes ~200 of the most commonly used tags. The full DICOM dictionary has 4000+ tags — our selection covers what you encounter 95% of the time in PACS/RIS integration work.

**Q: Does this work with Claude Code (CLI)?**
A: Yes. Add to your `.claude/settings.json` or use the `--mcp` flag.

**Q: Can I extend the dictionary?**
A: Yes. Set `DICOM_HL7_CUSTOM_DICTIONARY` environment variable to a JSON file path. Format documentation coming in v0.2.

**Q: Is this HIPAA compliant?**
A: This tool processes standards metadata, not patient data. No PHI is stored or transmitted. The sample messages use fictional test data.

**Q: How accurate is the knowledge base?**
A: The DICOM tags, HL7 segments, and FHIR mappings are sourced from the published standards (DICOM PS3.6, HL7 v2.5.1, FHIR R4, HL7 v2-to-FHIR IG). The practical notes, vendor quirks, and integration tips come from 19 years of hands-on PACS/RIS/HIS integration experience.

## Development

```bash
git clone https://github.com/nyxtools/dicom-hl7-mcp.git
cd dicom-hl7-mcp
pip install -e ".[dev]"
pytest
```

## License

MIT License. See [LICENSE](LICENSE).

## Author

Built by NyxTools · LEW Enterprises LLC — 19 years of PACS, RIS, and healthcare integration experience.

Contact: hello@nyxtools.dev
