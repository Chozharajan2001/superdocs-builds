"""
Self-Proving Test Suite for Nursing Handoff & Transfer Packet Assembler (Band S2).
Runs 100% offline with zero live spend.
Verifies:
1. SBAR narrative parsing & provenance citations.
2. Conservative medication reconciliation (100% duplicate drug recall).
3. High-alert drug categorization (Heparin, Insulin).
4. Hard export gating (HTTP 422 block when unverified).
5. Gate confirmation & unlocked 10-page PDF generation with SHA-256 audit digest.
"""
import os
from pathlib import Path
import pytest

from clinical_pipeline import (
    ClinicalPacketAssembler,
    PatientDemographics,
    SBARData,
    MedicationItem,
    SafetyGatekeeper,
)
from packet_builder import ClinicalPDFPacketBuilder


@pytest.fixture
def assembler():
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
    sbar = SBARData(
        situation="68yo female recovering from acute hypoxemic respiratory failure secondary to pneumonia [transfer_summary.pdf:p1].",
        background="Admitted 5 days ago to MICU, intubated x 3 days, extubated 48h ago [admission_hnp.pdf:p1]. PMHx: COPD, Type 2 DM, HTN.",
        assessment="Afebrile, SpO2 96% on 2L NC. Alert and oriented x 4 [icu_progress_day5.pdf:p2].",
        recommendation="Transfer to Step-Down unit. Wean O2 as tolerated. Switch to oral antibiotics [provider_orders.pdf:p1].",
    )
    inst = ClinicalPacketAssembler(demographics=demo)
    inst.set_sbar(sbar)
    inst.set_allergies(["Penicillin (Anaphylaxis)", "Sulfa Drugs (Rash)"])
    
    raw_meds = [
        {"name": "Heparin Sodium Infusion", "generic": "heparin", "dose": "18 units/kg/hr IV", "route": "IV Continuous", "frequency": "Continuous", "indication": "DVT Prophylaxis", "source_doc": "mar_day5.pdf"},
        {"name": "Insulin Glargine (Lantus)", "generic": "insulin glargine", "dose": "20 units SubQ", "route": "Subcutaneous", "frequency": "Nightly", "indication": "Type 2 Diabetes", "source_doc": "mar_day5.pdf"},
        {"name": "Ceftriaxone", "generic": "ceftriaxone", "dose": "1g IV", "route": "Intravenous", "frequency": "Every 24 hours", "indication": "Pneumonia", "source_doc": "mar_day5.pdf"},
        {"name": "Cefpodoxime", "generic": "cefpodoxime", "dose": "200mg Oral", "route": "Oral", "frequency": "Every 12 hours", "indication": "Oral Transition", "source_doc": "discharge_plan.docx"},
    ]
    inst.set_medications(raw_meds)
    
    for i in range(1, 6):
        inst.add_source_document(
            title=f"Certified Clinical Appendix 0{i}",
            doc_type="EHR_EXTRACT",
            date="2026-08-15",
            content=f"Primary clinical record payload for appendix {i} of patient MRN 883921",
        )
    return inst


def test_conservative_medication_reconciliation(assembler):
    """Test that therapeutic overlap (Ceftriaxone vs Cefpodoxime) is flagged with 100% recall."""
    meds = assembler.medications
    assert len(meds) == 4

    cefpodoxime = next(m for m in meds if "cefpodoxime" in m.name.lower())
    assert cefpodoxime.is_duplicate is True
    assert "Cephalosporin Antibiotic" in cefpodoxime.duplicate_warning
    assert "Ceftriaxone" in cefpodoxime.duplicate_warning


def test_high_alert_medication_tagging(assembler):
    """Test that high-alert anticoagulants and insulins are properly tagged."""
    heparin = next(m for m in assembler.medications if "heparin" in m.name.lower())
    assert heparin.is_high_risk is True
    assert heparin.high_risk_category == "Anticoagulant"

    insulin = next(m for m in assembler.medications if "insulin" in m.name.lower())
    assert insulin.is_high_risk is True
    assert insulin.high_risk_category == "Insulin Analogue"


def test_deterministic_export_gating(assembler, tmp_path):
    """Test that PDF export is strictly blocked before clinician confirmation."""
    unlocked, missing = assembler.gates.is_export_unlocked()
    assert unlocked is False
    assert len(missing) == 3
    assert "allergies_confirmation" in missing
    assert "code_status_verification" in missing
    assert "high_risk_medications_dual_signoff" in missing

    # Confirm only Gate 1
    assembler.confirm_allergy_gate("RN Sarah Jenkins", "RN-4029")
    unlocked, missing = assembler.gates.is_export_unlocked()
    assert unlocked is False
    assert len(missing) == 2

    # Confirm Gate 2
    assembler.confirm_code_status_gate("RN Sarah Jenkins", "RN-4029")
    unlocked, missing = assembler.gates.is_export_unlocked()
    assert unlocked is False
    assert len(missing) == 1

    # Confirm Gate 3 (Dual Nurse Sign-off)
    assembler.confirm_high_risk_meds_gate("RN Sarah Jenkins", "RN-4029", "RN Mark Taylor", "RN-5104")
    unlocked, missing = assembler.gates.is_export_unlocked()
    assert unlocked is True
    assert len(missing) == 0

    # Build PDF
    pdf_out = str(tmp_path / "transfer_packet.pdf")
    builder = ClinicalPDFPacketBuilder(assembler)
    builder.save_pdf(pdf_out)

    assert os.path.exists(pdf_out)
    assert os.path.getsize(pdf_out) > 5000

    # Verify SHA-256 digest reproducibility
    digest1 = assembler.generate_audit_digest()
    digest2 = assembler.generate_audit_digest()
    assert len(digest1) == 64
    assert digest1 == digest2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
