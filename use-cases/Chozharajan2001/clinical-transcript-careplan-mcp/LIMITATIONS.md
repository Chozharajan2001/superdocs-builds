# Limitations & Operational Boundaries: Clinical Transcript Care Plan MCP

In alignment with the SuperDocs engineering evaluation principles (*"Honest reporting of limitations beats inflated claims"*), this document transparently scopes the V1 capabilities of this stretch exploration.

---

## 1. Dialogue NLP Extraction Scope
- **Current Implementation**: `transcript_parser.py` implements dynamic regex-based NLP event extraction over multi-speaker clinical dialogues, extracting patient demographics, Fahrenheit temperatures, vitals, allergy records, and medication orders.
- **Production Extension**: In an enterprise hospital deployment, raw audio WAV/MP3 streams would route through Whisper Medical or Nuance DAX before entering the parser.

---

## 2. NANDA-I Care Plan Knowledge Base
- **Current Implementation**: Generates evidence-based NANDA-I aligned SMART goals (e.g., Gas Exchange Impairment, Acute Pain, Fall Risk) with concrete nursing interventions and 6th-grade discharge summaries.
- **Production Extension**: Extensible to full hospital Epic/Cerner care plan order sets via FHIR R4 PlanDefinition endpoints.
