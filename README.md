# DICOM/HL7/FHIR Interoperability MCP Server

<!-- mcp-name: io.github.NyxToolsDev/dicom-hl7-mcp-server -->

[![NyxToolsDev/dicom-hl7-mcp-server MCP server](https://glama.ai/mcp/servers/NyxToolsDev/dicom-hl7-mcp-server/badges/score.svg)](https://glama.ai/mcp/servers/NyxToolsDev/dicom-hl7-mcp-server)

**The only MCP server that bridges DICOM, HL7v2, and FHIR in one package — with optional PACS connectivity.**

Built by a healthcare IT engineer with 19 years of PACS, RIS, and integration experience. This isn't a wrapper around a FHIR API or a DICOM tag dictionary — it's the interoperability knowledge that takes years on the job to build, plus the ability to connect to real PACS systems.

## What Makes This Different

| Capability | This Server | DICOM-only servers | FHIR-only servers |
|-----------|:-----------:|:------------------:|:-----------------:|
| DICOM tag lookup + vendor quirks | Yes | Yes | No |
| HL7v2 message parsing | Yes | No | No |
| FHIR R4 resource mapping | Yes | No | Yes |
| **DICOM ↔ HL7v2 mapping** | **Yes** | No | No |
| **HL7v2 → FHIR conversion** | **Yes** | No | No |
| **Mirth Connect channel generation** | **Yes** | No | No |
| **PACS connectivity (C-FIND/C-MOVE)** | **Yes** | Some | No |
| **DICOMweb (QIDO-RS/WADO-RS)** | **Yes** | No | No |
| **Query PACS + auto-map to HL7/FHIR** | **Yes** | No | No |
| Vendor private tag decoding (GE, Siemens, Philips) | Yes | Some | No |
| Integration pattern knowledge (IHE SWF, ADT flows) | Yes | No | No |

## Tools

### Reference Tools (Free)

| Tool | What It Does |
|------|-------------|
| `lookup_dicom_tag` | Look up any DICOM tag by number or keyword |
| `explain_dicom_tag` | Detailed tag explanation with vendor quirks and gotchas |
| `parse_hl7_message` | Parse HL7 v2.x messages into human-readable format |
| `explain_hl7_segment` | Explain segment fields, data types, and usage |
| `lookup_hl7_table` | Look up HL7 table values (Administrative Sex, Patient Class, etc.) |

### Mapping & Generation Tools (Premium)

| Tool | What It Does |
|------|-------------|
| `map_dicom_to_hl7` | Map DICOM tags to HL7 v2 fields with conversion notes |
| `map_hl7_to_fhir` | Map HL7 v2 fields to FHIR R4 resources |
| `generate_mirth_channel` | Generate Mirth Connect channel configurations |
| `validate_hl7_message` | Validate HL7 messages against the standard |
| `explain_integration_pattern` | Explain healthcare integration patterns with flow diagrams |
| `decode_private_tags` | Decode vendor private DICOM tags (GE, Siemens, Philips, etc.) |
| `generate_sample_message` | Generate realistic sample HL7 messages for testing |

### PACS Connectivity Tools (Premium)

| Tool | What It Does |
|------|-------------|
| `pacs_echo` | Verify PACS connectivity (C-ECHO or DICOMweb ping) |
| `pacs_query` | Search for studies/series by patient, date, modality, accession |
| `pacs_get_metadata` | Retrieve detailed study/series metadata from PACS |
| `pacs_retrieve` | C-MOVE images to a destination AE title |
| `pacs_study_summary` | **Query a study + auto-map through DICOM→HL7→FHIR with generated ORM** |

## Installation

**Reference tools only** (no PACS connectivity):

```bash
pip install dicom-hl7-mcp
```

**With PACS connectivity** (adds pynetdicom + httpx):

```bash
pip install dicom-hl7-mcp[pacs]
```

## Configuration

### Basic (Reference Tools Only)

Add to your Claude Desktop config:

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

### With Premium License

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

### With PACS Connectivity (Traditional DICOM)

Connect to a PACS using C-FIND/C-MOVE/C-ECHO:

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "uvx",
      "args": ["--with", "dicom-hl7-mcp[pacs]", "dicom-hl7-mcp"],
      "env": {
        "DICOM_HL7_LICENSE_KEY": "your-license-key-here",
        "DICOM_HL7_PACS_AE_TITLE": "YOUR_PACS",
        "DICOM_HL7_PACS_HOST": "pacs.hospital.org",
        "DICOM_HL7_PACS_PORT": "4242",
        "DICOM_HL7_LOCAL_AE_TITLE": "CLAUDE_MCP"
      }
    }
  }
}
```

### With PACS Connectivity (DICOMweb)

Connect to a DICOMweb-capable PACS (QIDO-RS/WADO-RS):

```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "uvx",
      "args": ["--with", "dicom-hl7-mcp[pacs]", "dicom-hl7-mcp"],
      "env": {
        "DICOM_HL7_LICENSE_KEY": "your-license-key-here",
        "DICOM_HL7_DICOMWEB_URL": "https://pacs.hospital.org/dicom-web",
        "DICOM_HL7_DICOMWEB_AUTH": "bearer",
        "DICOM_HL7_DICOMWEB_TOKEN": "your-auth-token"
      }
    }
  }
}
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DICOM_HL7_LICENSE_KEY` | For premium | — | Premium license key |
| `DICOM_HL7_LOG_LEVEL` | No | `INFO` | Logging level |
| **Traditional DICOM** | | | |
| `DICOM_HL7_PACS_AE_TITLE` | For DIMSE | — | Remote PACS AE title |
| `DICOM_HL7_PACS_HOST` | For DIMSE | — | Remote PACS hostname/IP |
| `DICOM_HL7_PACS_PORT` | For DIMSE | — | Remote PACS port |
| `DICOM_HL7_LOCAL_AE_TITLE` | No | `DICOM_HL7_MCP` | This server's AE title |
| **DICOMweb** | | | |
| `DICOM_HL7_DICOMWEB_URL` | For DICOMweb | — | DICOMweb base URL |
| `DICOM_HL7_DICOMWEB_AUTH` | No | `none` | Auth type: `none`, `bearer`, `basic` |
| `DICOM_HL7_DICOMWEB_TOKEN` | For bearer | — | Bearer token |
| `DICOM_HL7_DICOMWEB_USERNAME` | For basic | — | Basic auth username |
| `DICOM_HL7_DICOMWEB_PASSWORD` | For basic | — | Basic auth password |
| **Safety** | | | |
| `DICOM_HL7_PACS_PROTOCOL` | No | `auto` | Protocol: `auto`, `dimse`, `dicomweb` |
| `DICOM_HL7_PACS_ALLOW_RETRIEVE` | No | `false` | Enable C-MOVE (`true` to enable) |
| `DICOM_HL7_PHI_REDACT` | No | `false` | Redact patient name/ID in output |

## PHI Safety

When connected to a real PACS, query results contain Protected Health Information (PHI).

- **Log redaction**: PHI fields are automatically stripped from all log output
- **Result warnings**: Every PACS query result includes a PHI warning banner
- **Optional redaction**: Set `DICOM_HL7_PHI_REDACT=true` to replace patient name/ID with `[REDACTED]` in tool output
- **No disk caching**: PACS query results are never written to disk
- **C-MOVE is disabled by default**: Must explicitly set `DICOM_HL7_PACS_ALLOW_RETRIEVE=true`

**Important:** Do not use PACS connectivity with cloud-hosted LLMs unless your organization's policies permit sending PHI to that LLM provider. For on-premises deployments or local LLM setups, this is not a concern.

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

### Query PACS + Auto-Map to HL7/FHIR (Premium)

> "Look up accession number ACC12345 in PACS and show me the HL7/FHIR mapping"

Returns a complete interoperability summary:
1. Study metadata from PACS (patient, date, modality, description)
2. DICOM→HL7 field mapping for every key field
3. HL7→FHIR R4 resource mapping
4. A pre-filled HL7 ORM^O01 message skeleton
5. Integration pattern context (IHE SWF workflow)

### Map DICOM → HL7 (Premium)

> "What HL7 field does DICOM Accession Number map to?"

Returns: OBR-3 / ORC-3 (Filler Order Number) with data type conversion notes (SH → EI) and mapping pitfalls.

### Generate a Mirth Channel (Premium)

> "Generate a Mirth channel for receiving ADT messages and writing to a FHIR server"

Returns: Complete channel config with MLLP source, FHIR HTTP destination, transformer steps, event filtering, and implementation notes.

## Knowledge Base

### Standards Coverage
- **DICOM:** ~200 most common tags, SOP Classes, Transfer Syntaxes, private tag ranges for 7 vendors
- **HL7 v2.x:** 15 segments, 20+ tables, message types (ADT, ORM, ORU, MDM, SIU, DFT, BAR), versions 2.3-2.9
- **FHIR R4:** Mappings for Patient, Encounter, ServiceRequest, DiagnosticReport, Observation, AllergyIntolerance, Condition, RelatedPerson, Coverage
- **Integration Patterns:** ADT Feed, Order-to-Result, Radiology Workflow (IHE SWF), Lab Interface, Report Distribution, Patient Merge, Charge Posting

### Where the Knowledge Comes From
The tags, segments, and mappings are from published standards (DICOM PS3.6, HL7 v2.5.1, FHIR R4, HL7 v2-to-FHIR IG). The vendor quirks, integration tips, and "watch out for this" notes come from 19 years of building PACS/RIS/HIS interfaces in production healthcare environments.

## Premium License

Free tier gives you DICOM tag lookup, HL7 parsing, and segment explanation — the tools you use every day.

Premium unlocks cross-standard mapping, Mirth generation, validation, PACS connectivity, and the deep integration knowledge that takes years to build.

**Get your license:** [nyxtools.gumroad.com](https://nyxtools.gumroad.com)

## FAQ

**Do I need a license for the free tools?**
No. Install and use the 5 free tools immediately. No account, no sign-up.

**Do I need PACS connectivity?**
No. The reference and mapping tools work without any PACS connection. PACS connectivity is optional — install with `pip install dicom-hl7-mcp[pacs]` only if you want to query real PACS systems.

**What HL7 versions are supported?**
v2.3 through v2.9, with focus on v2.5.1 (the most widely deployed in US healthcare).

**Is this HIPAA compliant?**
The reference tools process standards metadata, not patient data. PACS connectivity tools access real patient data — PHI safety measures are built in (log redaction, optional output redaction, C-MOVE disabled by default), but you are responsible for ensuring use complies with your organization's policies.

**What PACS systems are supported?**
Any PACS that supports DICOM C-FIND/C-ECHO (virtually all of them) or DICOMweb (QIDO-RS/WADO-RS). Tested with Orthanc, RamSoft, and DCM4CHEE.

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

Built by [NyxTools](https://github.com/NyxToolsDev)
