# DICOM/HL7/FHIR Interoperability MCP Server

<!-- mcp-name: io.github.NyxToolsDev/dicom-hl7-mcp-server -->

**The only MCP server that bridges DICOM, HL7v2, and FHIR in one package.**

Built by a healthcare IT engineer with 19 years of PACS, RIS, and integration experience. This isn't a wrapper around a FHIR API or a DICOM tag dictionary — it's the interoperability knowledge that takes years on the job to build.

> Looking for PACS query/retrieve? Check out [dicom-mcp](https://github.com/aiblocksdev/dicom-mcp) — it's excellent for DICOM network operations. Need to **bridge standards** — map DICOM to HL7, convert HL7v2 to FHIR, generate Mirth channels, decode vendor private tags? You're in the right place.

## What Makes This Different

| Capability | This Server | DICOM-only servers | FHIR-only servers |
|-----------|:-----------:|:------------------:|:-----------------:|
| DICOM tag lookup + vendor quirks | Yes | Yes | No |
| HL7v2 message parsing | Yes | No | No |
| FHIR R4 resource mapping | Yes | No | Yes |
| **DICOM ↔ HL7v2 mapping** | **Yes** | No | No |
| **HL7v2 → FHIR conversion** | **Yes** | No | No |
| **Mirth Connect channel generation** | **Yes** | No | No |
| Vendor private tag decoding (GE, Siemens, Philips) | Yes | Some | No |
| Integration pattern knowledge (IHE SWF, ADT flows) | Yes | No | No |

**The gap in the MCP ecosystem is interoperability** — the hard work of mapping between standards, understanding vendor differences, and building integration engine configs. That's what this server does.

## Tools

| Tool | Tier | What It Does |
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

## Configure with Claude

**Claude Desktop** — add to your config:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

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

For premium features, add your license key:

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "uvx",
      "args": ["dicom-hl7-mcp"],
      "env": {
        "DICOM_HL7_LICENSE_KEY": "your-license-key-here"
      }
    }
  }
}
```

## Real-World Examples

### "What is DICOM tag (0008,0050)?"

> AccessionNumber — SH — RIS-generated number that identifies the order. THE key field for matching RIS orders to PACS studies.

### Parse an HL7 message

> "Parse this HL7 message:"
> ```
> MSH|^~\&|RIS|RAD|EMR|HOSP|20240315140000||ORU^R01|MSG003|P|2.5.1
> PID|1||MRN12345^^^HOSP^MR||DOE^JOHN||19650315|M
> OBR|1|ORD001|ACC001|CTABD^CT Abdomen^L|||20240315130000
> OBX|1|FT|&GDT^Report||FINDINGS: Normal CT.||||||F
> ```

Returns each segment parsed with field names, values, table lookups, and contextual explanations.

### Map DICOM → HL7 (Premium)

> "What HL7 field does DICOM Accession Number map to?"

Returns: OBR-3 / ORC-3 (Filler Order Number) with data type conversion notes (SH → EI) and mapping pitfalls.

### Map HL7v2 → FHIR R4 (Premium)

> "How does PID-3 (Patient Identifier List) map to FHIR?"

Returns: Patient.identifier with field-by-field conversion — CX.1→Identifier.value, CX.4→Identifier.system, CX.5→Identifier.type.

### Generate a Mirth Channel (Premium)

> "Generate a Mirth channel for receiving ADT messages and writing to a FHIR server"

Returns: Complete channel config with MLLP source, FHIR HTTP destination, transformer steps, event filtering, and implementation notes.

### Decode Vendor Private Tags (Premium)

> "What is Siemens private tag (0019,100C)?"

Returns: B Value (Siemens) — Diffusion b-value, critical for DWI/ADC maps. Covers GE, Siemens, Philips, Fuji, Agfa, Canon/Toshiba, and Hologic.

## Knowledge Base

### Standards Coverage
- **DICOM:** ~200 most common tags, SOP Classes, Transfer Syntaxes, private tag ranges for 7 vendors
- **HL7 v2.x:** 15 segments, 20+ tables, message types (ADT, ORM, ORU, MDM, SIU, DFT, BAR), versions 2.3–2.9
- **FHIR R4:** Mappings for Patient, Encounter, ServiceRequest, DiagnosticReport, Observation, AllergyIntolerance, Condition, RelatedPerson, Coverage
- **Integration Patterns:** ADT Feed, Order-to-Result, Radiology Workflow (IHE SWF), Lab Interface, Report Distribution, Patient Merge, Charge Posting

### Where the Knowledge Comes From
The tags, segments, and mappings are from published standards (DICOM PS3.6, HL7 v2.5.1, FHIR R4, HL7 v2-to-FHIR IG). The vendor quirks, integration tips, and "watch out for this" notes come from 19 years of building PACS/RIS/HIS interfaces in production healthcare environments.

## Premium License

Free tier gives you DICOM tag lookup, HL7 parsing, and segment explanation — the tools you use every day.

Premium unlocks cross-standard mapping, Mirth generation, validation, and the deep integration knowledge that takes years to build.

**Get your license:** [nyxtools.gumroad.com](https://nyxtools.gumroad.com)

## FAQ

**Do I need a license for the free tools?**
No. Install and use the 5 free tools immediately. No account, no sign-up.

**What HL7 versions are supported?**
v2.3 through v2.9, with focus on v2.5.1 (the most widely deployed in US healthcare).

**Is this HIPAA compliant?**
This tool processes standards metadata, not patient data. No PHI is stored or transmitted. Sample messages use fictional test data.

**How does this compare to other healthcare MCP servers?**
Other servers are excellent at specific things — PACS queries, FHIR CRUD, PubMed search. This server fills the gap between them: the interoperability layer that maps DICOM↔HL7↔FHIR and generates integration engine configs. They complement each other.

## Development

```bash
git clone https://github.com/NyxToolsDev/dicom-hl7-mcp-server.git
cd dicom-hl7-mcp-server
pip install -e ".[dev]"
pytest
```

## License

MIT License. See [LICENSE](LICENSE).

---

Built by [NyxTools](https://github.com/NyxToolsDev) · NyxTools
