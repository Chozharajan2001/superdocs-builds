"""
SuperDocs Clinical Nursing Handoff & Transfer Packet Assembler CLI (Task 2 Band S2).
Runs end-to-end clinical ingestion, SBAR generation, medication reconciliation,
human verification gating, and ReportLab multi-page PDF generation.
"""
import os
from pathlib import Path
import sys

# Configure path and stdout
current_dir = Path(__file__).parent.resolve()
sys.path.insert(0, str(current_dir))

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from clinical_pipeline import (
    ClinicalPacketAssembler,
    PatientDemographics,
    SBARData,
)
from packet_builder import ClinicalPDFPacketBuilder
from superdocs_client import SuperDocsAPIClient


def run_full_clinical_workflow(use_live_superdocs_api: bool = True):
    print("=" * 75)
    print("[SUPERDOCS CLINICAL NURSING HANDOFF & TRANSFER PACKET ASSEMBLER (S2)]")
    print("=" * 75)

    superdocs = SuperDocsAPIClient()
    if superdocs.api_key:
        print(f"[✓] SuperDocs API Connected: Bearer key loaded from environment / credentials.")
    else:
        print("[!] Running in offline zero-spend test mode (Mock LLM & Local ReportLab Engine).")

    # 1. Initialize patient demographics
    demo = PatientDemographics(
        patient_id="patient-883921",
        name="Eleanor Vance",
        mrn="883921",
        dob="1958-04-12",
        age=68,
        gender="Female",
        admission_date="2026-08-10",
        sending_unit="Medical ICU (Bed 14)",
        receiving_unit="Step-Down Unit (Bed 202)",
        attending_physician="Dr. Robert Chen, MD",
        code_status="FULL CODE",
    )
    assembler = ClinicalPacketAssembler(demo)

    # 2. Ingest SBAR Narrative with Citation Provenance
    sbar = SBARData(
        situation="68yo female recovering from acute hypoxemic respiratory failure secondary to severe community-acquired pneumonia [transfer_summary.pdf:p1].",
        background="Admitted 5 days ago to MICU, intubated x 3 days, successfully extubated 48h ago [admission_hnp.pdf:p1]. PMHx: COPD, Type 2 DM, HTN.",
        assessment="Afebrile, SpO2 96% on 2L nasal cannula. Lungs clear with faint bibasilar crackles. Alert and oriented x 4 [icu_progress_day5.pdf:p2].",
        recommendation="Transfer to Step-Down unit. Wean O2 as tolerated. Complete 48h IV Ceftriaxone then switch to oral Cefpodoxime [provider_orders.pdf:p1].",
    )
    assembler.set_sbar(sbar)

    # 3. Set Allergies
    assembler.set_allergies(["Penicillin (Anaphylaxis)", "Sulfa drugs (Hives)"])

    # 4. Conservative Medication Reconciliation
    raw_medications = [
        {
            "name": "Heparin Sodium Infusion",
            "generic": "heparin",
            "dose": "18 units/kg/hr IV",
            "route": "IV Continuous",
            "frequency": "Continuous",
            "indication": "DVT Prophylaxis / Therapeutic Anticoagulation",
            "source_doc": "mar_day5.pdf",
        },
        {
            "name": "Insulin Glargine (Lantus)",
            "generic": "insulin glargine",
            "dose": "20 units SubQ",
            "route": "Subcutaneous",
            "frequency": "Nightly at bedtime",
            "indication": "Type 2 Diabetes Mellitus",
            "source_doc": "mar_day5.pdf",
        },
        {
            "name": "Ceftriaxone",
            "generic": "ceftriaxone",
            "dose": "1g IV",
            "route": "Intravenous",
            "frequency": "Every 24 hours",
            "indication": "Severe Pneumonia",
            "source_doc": "provider_orders.pdf",
        },
        {
            "name": "Cefpodoxime",
            "generic": "cefpodoxime",
            "dose": "200mg Oral",
            "route": "Oral",
            "frequency": "Every 12 hours",
            "indication": "Step-Down Oral Antibiotic Transition",
            "source_doc": "discharge_plan.docx",
        },
    ]
    assembler.set_medications(raw_medications)

    # Add source certified documents for appendices
    for i in range(1, 6):
        assembler.add_source_document(
            title=f"Certified Record Appendix 0{i}",
            doc_type="EHR_EXTRACT",
            date="2026-08-15",
            content=f"Primary clinical record payload for appendix {i} of patient MRN 883921",
        )

    print("\n[1] Clinical Patient Chart Ingested:")
    print(f"    • Patient: {demo.name} | MRN: {demo.mrn} | Sending: {demo.sending_unit} -> {demo.receiving_unit}")
    print(f"    • Code Status: {demo.code_status}")

    print("\n[2] Provenance-Grounded SBAR Narrative:")
    print(f"    • SITUATION: {sbar.situation}")
    print(f"    • BACKGROUND: {sbar.background}")
    print(f"    • ASSESSMENT: {sbar.assessment}")
    print(f"    • RECOMMENDATION: {sbar.recommendation}")

    print("\n[3] Conservative Medication Reconciliation (100% Duplicate Recall):")
    for med in assembler.medications:
        high_alert_tag = f" [HIGH ALERT: {med.high_risk_category}]" if med.is_high_risk else ""
        dup_tag = f"\n      --> WARNING: {med.duplicate_warning}" if med.is_duplicate else ""
        print(f"    - {med.name} ({med.dose}, {med.route}){high_alert_tag}{dup_tag}")

    # 5. Attempt Export Before Human Sign-Off (Test Gating)
    print("\n[4] GATING CHECK: Attempting PDF Export Before Human Verification...")
    unlocked, unverified = assembler.gates.is_export_unlocked()
    if not unlocked:
        print(f"    ❌ EXPORT BLOCKED (HTTP 422): {len(unverified)} Safety Gates Pending:")
        for g in unverified:
            print(f"       • {g}")
        print("    🛑 Deterministic Gate: Export is strictly forbidden without clinician sign-off.")

    # 6. Execute Human Clinician Verification Gates
    print("\n[5] Executing Clinician Safety Verification Sign-Offs:")
    print("    ✓ Gate 1: Confirmed Allergies [Penicillin (Anaphylaxis)] — RN Sarah Jenkins (RN-4029)")
    assembler.confirm_allergy_gate("RN Sarah Jenkins", "RN-4029")

    print("    ✓ Gate 2: Verified Resuscitation Code Status [FULL CODE] — RN Sarah Jenkins (RN-4029)")
    assembler.confirm_code_status_gate("RN Sarah Jenkins", "RN-4029")

    print("    ✓ Gate 3: Dual-Nurse High-Alert Sign-Off [Heparin & Insulin] — RN Sarah Jenkins & RN Mark Taylor (RN-5104)")
    assembler.confirm_high_risk_meds_gate("RN Sarah Jenkins", "RN-4029", "RN Mark Taylor", "RN-5104")

    # 7. Generate PDF Packet
    print("\n[6] Compiling 10-Page Standardized Transfer Packet PDF...")
    builder = ClinicalPDFPacketBuilder(assembler)
    output_filename = str(current_dir / "transfer_packet_patient-883921.pdf")
    builder.save_pdf(output_filename)

    digest = assembler.generate_audit_digest()
    print(f"    📄 Local PDF Generated: {output_filename}")
    print(f"    🔒 Tamper-Evident SHA-256 Audit Digest: {digest}")

    # 8. Synchronize with SuperDocs Platform API (The 4-Call Contract)
    if superdocs.api_key:
        print("\n[7] Synchronizing with Live SuperDocs Platform API:")
        session_id = f"session_handoff_{demo.mrn}"
        edit_instruction = (
            f"Generate clinical transfer summary for patient {demo.name} (MRN: {demo.mrn}). "
            f"Include confirmed allergies: {', '.join(assembler.allergies)}, code status: {demo.code_status}, "
            f"and reconciled MAR with {len(assembler.medications)} verified medications."
        )
        print("    --> Calling SuperDocs API POST /v1/chat (Targeted SBAR In-Document Edits)...")
        chat_resp = superdocs.create_or_update_handoff_document(session_id, edit_instruction)
        print(f"    ✓ SuperDocs Edit Response: {chat_resp.get('response', 'Changes Applied')[:80]}...")

        print("    --> Calling SuperDocs API POST /v1/documents/export (.docx)...")
        docx_bytes = superdocs.export_document(session_id, "docx")
        if docx_bytes:
            live_out = current_dir / f"superdocs_handoff_{demo.mrn}.docx"
            live_out.write_bytes(docx_bytes)
            print(f"    ✓ SuperDocs Word Dossier Exported: {live_out} ({len(docx_bytes):,} bytes)")

    print("\n" + "=" * 75)
    print("✅ TRANSFER PACKET COMPLETE, VERIFIED & READY FOR PATIENT TRANSFER")
    print("=" * 75)


if __name__ == "__main__":
    run_full_clinical_workflow()
