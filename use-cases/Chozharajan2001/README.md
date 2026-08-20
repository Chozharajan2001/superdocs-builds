# SuperDocs Community Builds — Chozharajan (`Chozharajan2001`)

This repository folder contains the submissions by **Chozharajan** for SuperDocs Round 2:

---

## 🏆 1. Primary Assigned Build (Band S2)

### 🏥 [Nursing Handoff & Transfer Packet Assembler](./nursing-handoff-assembler/)
- **Assigned Domain**: Healthcare / Clinical Operations (Charge Nurse / Transfer Coordinator).
- **Core Capabilities**: Ingests multi-format clinical charts (H&P, MAR, Labs, Orders, Progress Notes), synthesizes structured SBAR summaries with 100% citation provenance, executes conservative medication reconciliation (100% duplicate drug recall), and enforces **3 hard export blocking safety gates** (`HTTP 422`) on Allergies, Resuscitation Code Status, and High-Alert Medications before compiling a certified 10-page PDF transfer packet.
- **Verification**: 6 automated offline tests in [`test_clinical_pipeline.py`](./nursing-handoff-assembler/test_clinical_pipeline.py).
- **Specification & DoD**: Documented in [`nursing-handoff-assembler/PRD.md`](./nursing-handoff-assembler/PRD.md) and [`LIMITATIONS.md`](./nursing-handoff-assembler/LIMITATIONS.md).

---

## 🌟 2. Voluntary Stretch Explorations (Section 2.2)

Per Section 2.2 of the task specification (*"Beyond Your Assignment — voluntary stretch builds that earn extra credit"*), two additional builds are included as domain demonstrations:

### 🩺 [Clinical Transcript to SMART Care Plan MCP (Band S3)](./clinical-transcript-careplan-mcp/)
- **Domain**: Bedside Dialogue & Outpatient Transition Planning.
- **Capabilities**: Dynamic regex NLP dialogue parser, NANDA-I aligned SMART nursing care goals, 6th-grade health literacy discharge instructions, and outpatient e-prescription compiler.
- **Verification**: 6 automated offline tests in [`test_transcript_careplan_pipeline.py`](./clinical-transcript-careplan-mcp/test_transcript_careplan_pipeline.py).

### 📊 [Finance Board Report & Warehouse Automation MCP (Band S3)](./mcp-finance-board-report/)
- **Domain**: B2B SaaS Corporate Finance & Board Governance.
- **Capabilities**: Modular warehouse connector with mathematical parity auditing, automated ARR bridge waterfall generator, and board packet PDF compilation.
- **Verification**: 6 automated offline tests in [`test_board_report_pipeline.py`](./mcp-finance-board-report/test_board_report_pipeline.py).
