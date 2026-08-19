# 🩺 Clinical Audio Transcript to SMART Care Plan & E-Prescription Suite

> **Category**: Agent-Loop Demos & Living Documents / Original Invention  
> **Candidate**: Chozharajan (`Chozharajan2001`)  
> **Difficulty Band**: **Band S3 (Stretch) + Original Healthcare Invention**  
> **Who It Serves**: Inpatient Charge Nurses, Hospital Case Managers, and Attending Physicians.  
> **Credit Line**: Built by Chozharajan for the SuperDocs Round 2 Engineering Evaluation.

---

## 🎯 Executive Summary

Bedside clinical discussions contain critical therapeutic orders and nursing priorities that are currently transcribed and rewritten into care plans by hand.

This build implements an **autonomous Model Context Protocol (MCP) and REST pipeline** that:
1. **Parses Bedside Audio Dialogue**: Ingests multi-speaker physician/nurse dialogue and extracts structured diagnoses, vital signs, and medication orders.
2. **Formulates Evidence-Based Nursing Care Plans (NANDA-I Aligned)**: Synthesizes SMART outcome goals (Specific, Measurable, Achievable, Relevant, Time-bound) with concrete nursing interventions.
3. **Builds Plain-Language Discharge Packets**: Translates complex clinical regimens into patient-friendly discharge packets (6th-grade health literacy reading level) with red-flag warning signs.
4. **Validates Prescriptions & Contraindications**: Audits medication orders against allergy records (e.g., penicillin anaphylaxis) and compiles official outpatient e-prescriptions.
5. **Exports Standardized Clinical Care Dossiers**: Generates multi-page PDF care packs and OpenXML Word dossiers with clinician sign-off blocks.

---

## 🏗️ Architecture & Component Flow

```
┌──────────────────────────┐      ┌──────────────────────────┐
│  Bedside Audio Dialogue  │ ───► │ ClinicalTranscriptParser │
│  (Multi-Speaker Text)    │      │ (Entity Extraction)      │
└──────────────────────────┘      └────────────┬─────────────┘
                                               │
                                               ▼
┌──────────────────────────┐      ┌──────────────────────────┐
│   PrescriptionCompiler   │ ◄─── │   NursingCarePlanEngine  │
│ (Allergy & Drug Audit)   │      │ (NANDA SMART Care Goals) │
└────────────┬─────────────┘      └────────────┬─────────────┘
             │                                 │
             ▼                                 ▼
┌────────────────────────────────────────────────────────────┐
│                    TRIPLE SURFACE INTERFACE                │
│  1. FastAPI Application Server (Port 8005)                 │
│  2. Interactive Bedside Review Dashboard (Space Grotesk)   │
│  3. Model Context Protocol (MCP) Server (5 Tools)          │
└────────────────────────────────────────────────────────────┘
```

---

## 🧪 Verification & Automated Tests

All tests execute completely offline without live API spend:

```bash
cd use-cases/Chozharajan2001/clinical-transcript-careplan-mcp
pytest test_transcript_careplan_pipeline.py -v
```

### Test Coverage (6/6 Passed):
- `test_transcript_entity_extraction`: Validates parsing dialogue into structured clinical entities.
- `test_smart_careplan_generation`: Asserts 3 NANDA diagnoses, SMART goals, and interventions.
- `test_discharge_packet_generation`: Verifies plain-language discharge packet with red flags.
- `test_contraindication_safety_check`: Tests antibiotic cross-reactivity and contraindications.
- `test_clinical_care_pdf_compilation`: Validates multi-page ReportLab PDF care dossier generation.
- `test_mcp_clinical_tools_dispatch`: Validates MCP tool definitions and JSON-RPC dispatch.

---

## ⚡ Quickstart Commands

```bash
# Start standalone server
python server.py

# Open dashboard in browser
# http://127.0.0.1:8005/dashboard
```

---

## 📜 License
MIT Licensed. Zero secrets or API keys exposed.
