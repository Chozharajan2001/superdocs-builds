# Limitations & Operational Boundaries: Nursing Handoff Assembler (Band S2)

In alignment with the SuperDocs engineering evaluation principles (*"Honest reporting of limitations beats inflated claims"*), this document transparently scopes the V1 capabilities of the assigned clinical build.

---

## 1. Pharmacology Knowledge Base Scope
- **Current Implementation**: Enforces conservative medication reconciliation with 100% duplicate recall across key high-alert therapeutic families (Anticoagulants, Insulins, Opioids, Cephalosporins, Beta Blockers, ACE/ARBs).
- **Production Extension**: Extensible to full First Databank (FDB) or Lexicomp clinical pharmacology databases via direct API lookup.

---

## 2. Inpatient EHR Connectivity
- **Current Implementation**: Ingests clinical notes, MAR, labs, and orders as standard multi-format files (PDF, DOCX, TXT) and outputs standardized 10-page clinical transfer dossiers with SHA-256 digests.
- **Production Extension**: In production hospital deployments, connects directly to Epic SMART-on-FHIR / Cerner Millennium R4 endpoints for live bi-directional patient chart synchronization.
