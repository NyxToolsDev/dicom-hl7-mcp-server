# DICOM/HL7 Developer AI Assistant — Premium License

## Stop Googling Tag Numbers. Stop Guessing at Field Mappings.

You know the drill. You're building an HL7 interface, and you need to know which DICOM tag maps to which HL7 field. You Google it. You find a 2012 forum post that might be right. You check three different PDFs. You still aren't sure.

**What if your AI assistant just... knew?**

The DICOM/HL7 Developer AI Assistant is an MCP server that gives Claude (or any MCP-compatible AI) deep, accurate knowledge of healthcare interoperability standards. Not generic knowledge scraped from the web — knowledge built from 19 years of real-world PACS, RIS, and integration experience.

---

## Free Forever: 5 Essential Tools

Install today. No account. No credit card. No license key.

- **Look up any DICOM tag** by number or keyword — instantly
- **Get detailed tag explanations** with vendor quirks (GE vs Siemens vs Philips)
- **Parse HL7 messages** into human-readable format with field names and table lookups
- **Explain any HL7 segment** with all fields, data types, and usage notes
- **Look up HL7 table values** — never Google "HL7 Table 0004" again

```bash
pip install dicom-hl7-mcp
```

That's it. Five tools that save you time every single day.

---

## Premium: The Integration Knowledge That Takes Years to Build

$19/mo Individual | $39/mo Team

### Cross-Standard Mapping
- **DICOM to HL7 mapping** — Know exactly which HL7 field corresponds to each DICOM tag, with data type conversion notes
- **HL7 to FHIR mapping** — Map v2 fields to FHIR R4 resources per the official v2-to-FHIR Implementation Guide
- **Private tag decoding** — Identify vendor-specific tags from GE, Siemens, Philips, Fuji, Agfa, Canon/Toshiba, and Hologic

### Integration Engineering
- **Mirth Connect channel generation** — Get a complete channel XML skeleton with source/destination connectors, transformers, filters, and implementation notes. Supports HL7v2, DICOM, FHIR, Database, and File connectors.
- **HL7 message validation** — Validate messages against the standard: required fields, table values, cross-segment consistency
- **Sample message generation** — Generate realistic ADT, ORM, ORU, MDM, SIU, and DFT messages for testing

### Integration Patterns
- **ADT Feed** — Patient demographics flow, merge handling, A08 flood management
- **Order to Result** — Complete order lifecycle from CPOE to final report
- **Radiology Workflow** — IHE Scheduled Workflow profile: MWL, MPPS, C-STORE, report distribution
- **Lab Interface** — Order/result flow, test code mapping, specimen tracking
- **Report Distribution** — MDM/ORU report delivery, preliminary vs final handling
- **Patient Merge** — MPI management, A34/A40 processing, PACS merge considerations
- **Charge Posting** — DFT/BAR charge flow, CPT codes, medical necessity

Each pattern includes message flow diagrams, trigger events, expected segments, common pitfalls, and best practices drawn from real-world implementation experience.

---

## Who This Is For

- **Healthcare integration engineers** building HL7/DICOM interfaces
- **PACS administrators** troubleshooting image routing and worklist issues
- **Health IT developers** working on FHIR migrations and API integrations
- **Mirth Connect developers** building interface channels
- **Clinical informatics professionals** mapping data between systems
- **Consultants** supporting healthcare IT implementations

## The Knowledge Gap Is Real

The healthcare interoperability space has a massive knowledge gap. The standards documents are thousands of pages. The vendor implementations are inconsistent. The tribal knowledge lives in the heads of engineers who've been doing this for decades.

This tool bridges that gap. Not with generic AI training data — with curated, accurate, experience-tested knowledge from someone who's been in the PACS room, at the modality, debugging the HL7 feed at 2 AM.

## What Makes This Different

**Domain expertise is the product.** Anyone can wrap a DICOM tag dictionary in an API. The value here is in the notes:

- "GE scanners often use Implicit VR Little Endian; Philips commonly uses Explicit VR Little Endian or JPEG compressed."
- "Accession Number is THE key field for matching RIS orders to PACS studies. If this doesn't match, the study won't link to the order."
- "Philips Scale Slope/Intercept are REQUIRED for correct quantitative analysis — different from standard Rescale Slope/Intercept."
- "A08 (Update) flood — some ADT systems send A08 for every minor change, overwhelming downstream systems."

This is the knowledge that takes years to accumulate. Now it's available in every conversation.

---

## Get Started

### 1. Install
```bash
pip install dicom-hl7-mcp
```

### 2. Get your premium license
Visit [https://nyxtools.lemonsqueezy.com](https://nyxtools.lemonsqueezy.com)

### 3. Configure
```bash
export DICOM_HL7_LICENSE_KEY=your-key-here
```

### 4. Use with Claude Desktop
```json
{
  "mcpServers": {
    "dicom-hl7-assistant": {
      "command": "dicom-hl7-mcp",
      "env": {
        "DICOM_HL7_LICENSE_KEY": "your-key-here"
      }
    }
  }
}
```

---

## Pricing

| Plan | Price | Includes |
|------|-------|----------|
| Free | $0 | 5 core tools: tag lookup, tag explain, HL7 parse, segment explain, table lookup |
| Individual | $19/mo | All 12 tools + all future tools. Single-user license. |
| Team | $39/mo | All 12 tools + all future tools. Up to 5 users. Priority support. |

**30-day money-back guarantee.** If it doesn't save you time, we'll refund you. No questions.

---

*Built by NyxTools · LEW Enterprises LLC — 19 years of PACS, RIS, and healthcare integration experience.*

*Questions? hello@nyxtools.dev*
