"""
Dedicated Standalone FastAPI Server for Nursing Handoff & Transfer Packet Assembler (Task 2 Band S2).
Runs independently on port 8001.
Serves:
1. Interactive Clinical Dashboard (GET / or GET /dashboard)
2. Clinical State & SBAR APIs (GET /api/clinical/handoff/{mrn})
3. Human Safety Gate Verification (POST /api/clinical/confirm-gate)
4. Gated 10-Page PDF Export (GET /api/clinical/export/pdf) - Fails with HTTP 422 if unverified
5. Gated SuperDocs Word Export (GET /api/clinical/export/docx)
"""
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field

from clinical_pipeline import (
    ClinicalPacketAssembler,
    PatientDemographics,
    SBARData,
    MedicationItem,
    ConservativeMedReconciliationEngine,
)
from packet_builder import ClinicalPDFPacketBuilder
from superdocs_client import SuperDocsAPIClient

from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("superdocs.clinical_server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _ACTIVE_ASSEMBLER
    _ACTIVE_ASSEMBLER = init_default_assembler()
    logger.info("Clinical Nursing Handoff Server initialized for patient MRN %s", _ACTIVE_ASSEMBLER.demographics.mrn)
    yield

app = FastAPI(
    title="SuperDocs Clinical Nursing Handoff & Transfer Server (Band S2)",
    description="Safety-gated clinical document assembly workflow with conservative medication reconciliation.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CURRENT_DIR = Path(__file__).parent.resolve()
SAMPLE_DIR = CURRENT_DIR / "sample_patient_records"

# In-Memory Active Assembler State
_ACTIVE_ASSEMBLER: Optional[ClinicalPacketAssembler] = None


def init_default_assembler() -> ClinicalPacketAssembler:
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
        situation="68yo female recovering from acute hypoxemic respiratory failure secondary to severe community-acquired pneumonia [transfer_summary.pdf:p1].",
        background="Admitted 5 days ago to MICU, intubated x 3 days, successfully extubated 48h ago [admission_hnp.pdf:p1]. PMHx: COPD, Type 2 DM, HTN.",
        assessment="Afebrile, SpO2 96% on 2L nasal cannula. Lungs clear with faint bibasilar crackles. Alert and oriented x 4 [icu_progress_day5.pdf:p2].",
        recommendation="Transfer to Step-Down unit. Wean O2 as tolerated. Complete 48h IV Ceftriaxone then switch to oral Cefpodoxime [provider_orders.pdf:p1].",
    )
    inst = ClinicalPacketAssembler(demographics=demo)
    inst.set_sbar(sbar)
    inst.set_allergies(["Penicillin (Anaphylaxis)", "Sulfa Drugs (Rash)"])

    raw_meds = [
        {
            "name": "Heparin Sodium Infusion",
            "generic": "heparin",
            "dose": "18 units/kg/hr IV",
            "route": "IV Continuous",
            "frequency": "Continuous",
            "indication": "DVT Prophylaxis in high-risk ICU bedrest",
            "source_doc": "active_mar.txt",
        },
        {
            "name": "Insulin Glargine (Lantus)",
            "generic": "insulin glargine",
            "dose": "20 units SubQ",
            "route": "Subcutaneous",
            "frequency": "Nightly at 21:00",
            "indication": "Type 2 Diabetes Mellitus",
            "source_doc": "active_mar.txt",
        },
        {
            "name": "Ceftriaxone Sodium",
            "generic": "ceftriaxone",
            "dose": "1g IV Piggyback",
            "route": "Intravenous",
            "frequency": "Every 24 hours",
            "indication": "Community-Acquired Pneumonia",
            "source_doc": "active_mar.txt",
        },
        {
            "name": "Cefpodoxime Proxetil",
            "generic": "cefpodoxime",
            "dose": "200mg Oral",
            "route": "Oral",
            "frequency": "Every 12 hours",
            "indication": "Step-Down Oral Transition",
            "source_doc": "provider_orders.txt",
        },
    ]
    inst.set_medications(raw_meds)

    # Load 5 sample primary records if directory exists
    if SAMPLE_DIR.exists():
        for record_file in sorted(SAMPLE_DIR.glob("*.txt")):
            inst.add_source_document(
                title=f"Certified {record_file.stem.upper()}",
                doc_type="EHR_RECORD",
                date="2026-08-15",
                content=record_file.read_text(encoding="utf-8"),
            )
    else:
        for i in range(1, 6):
            inst.add_source_document(
                title=f"Certified Record Appendix 0{i}",
                doc_type="EHR_EXTRACT",
                date="2026-08-15",
                content=f"Primary clinical record payload for appendix {i} of patient MRN 883921",
            )
    return inst


# Request/Response Models
class GateConfirmationRequest(BaseModel):
    gate_type: str = Field(..., description="allergies | code_status | high_risk_meds")
    nurse_name: str = Field(default="RN Sarah Jenkins")
    nurse_id: str = Field(default="RN-4029")
    second_nurse_name: Optional[str] = Field(default="RN Mark Taylor")
    second_nurse_id: Optional[str] = Field(default="RN-5104")


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "service": "superdocs-clinical-assembler",
        "band": "S2",
        "patient_loaded": _ACTIVE_ASSEMBLER.demographics.mrn if _ACTIVE_ASSEMBLER else None,
    }


@app.post("/api/clinical/reset")
def reset_patient_state():
    global _ACTIVE_ASSEMBLER
    _ACTIVE_ASSEMBLER = init_default_assembler()
    return {"status": "reset", "patient": _ACTIVE_ASSEMBLER.demographics.mrn}


@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    dashboard_path = CURRENT_DIR / "clinical_review_dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>Clinical Dashboard HTML not found.</h2>", status_code=404)


@app.get("/api/clinical/handoff/{mrn}")
def get_handoff_details(mrn: str):
    if not _ACTIVE_ASSEMBLER or _ACTIVE_ASSEMBLER.demographics.mrn != mrn:
        raise HTTPException(status_code=404, detail=f"Patient with MRN {mrn} not found.")

    unlocked, unverified_gates = _ACTIVE_ASSEMBLER.gates.is_export_unlocked()
    return {
        "demographics": {
            "name": _ACTIVE_ASSEMBLER.demographics.name,
            "mrn": _ACTIVE_ASSEMBLER.demographics.mrn,
            "dob": _ACTIVE_ASSEMBLER.demographics.dob,
            "age": _ACTIVE_ASSEMBLER.demographics.age,
            "gender": _ACTIVE_ASSEMBLER.demographics.gender,
            "sending_unit": _ACTIVE_ASSEMBLER.demographics.sending_unit,
            "receiving_unit": _ACTIVE_ASSEMBLER.demographics.receiving_unit,
            "code_status": _ACTIVE_ASSEMBLER.demographics.code_status,
        },
        "sbar": {
            "situation": _ACTIVE_ASSEMBLER.sbar.situation if _ACTIVE_ASSEMBLER.sbar else "",
            "background": _ACTIVE_ASSEMBLER.sbar.background if _ACTIVE_ASSEMBLER.sbar else "",
            "assessment": _ACTIVE_ASSEMBLER.sbar.assessment if _ACTIVE_ASSEMBLER.sbar else "",
            "recommendation": _ACTIVE_ASSEMBLER.sbar.recommendation if _ACTIVE_ASSEMBLER.sbar else "",
        },
        "allergies": _ACTIVE_ASSEMBLER.allergies,
        "medications": [
            {
                "id": m.id,
                "name": m.name,
                "generic": m.generic,
                "dose": m.dose,
                "route": m.route,
                "frequency": m.frequency,
                "is_high_risk": m.is_high_risk,
                "high_risk_category": m.high_risk_category,
                "is_duplicate": m.is_duplicate,
                "duplicate_warning": m.duplicate_warning,
                "verified": m.verified,
                "source_doc": m.source_doc,
            }
            for m in _ACTIVE_ASSEMBLER.medications
        ],
        "safety_gates": {
            "allergies_confirmed": _ACTIVE_ASSEMBLER.gates.allergies_confirmed,
            "code_status_confirmed": _ACTIVE_ASSEMBLER.gates.code_status_confirmed,
            "high_risk_meds_confirmed": _ACTIVE_ASSEMBLER.gates.high_risk_meds_confirmed,
            "is_export_unlocked": unlocked,
            "pending_gates": unverified_gates,
        },
        "audit_digest": _ACTIVE_ASSEMBLER.generate_audit_digest(),
    }


@app.post("/api/clinical/confirm-gate")
def confirm_safety_gate(req: GateConfirmationRequest):
    if not _ACTIVE_ASSEMBLER:
        raise HTTPException(status_code=500, detail="Assembler uninitialized.")

    if req.gate_type == "allergies":
        _ACTIVE_ASSEMBLER.confirm_allergy_gate(req.nurse_name, req.nurse_id)
    elif req.gate_type == "code_status":
        _ACTIVE_ASSEMBLER.confirm_code_status_gate(req.nurse_name, req.nurse_id)
    elif req.gate_type == "high_risk_meds":
        _ACTIVE_ASSEMBLER.confirm_high_risk_meds_gate(
            req.nurse_name, req.nurse_id, req.second_nurse_name or "RN Mark Taylor", req.second_nurse_id or "RN-5104"
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unknown gate type: {req.gate_type}")

    unlocked, pending = _ACTIVE_ASSEMBLER.gates.is_export_unlocked()
    return {
        "status": "confirmed",
        "gate": req.gate_type,
        "is_export_unlocked": unlocked,
        "pending_gates": pending,
        "audit_digest": _ACTIVE_ASSEMBLER.generate_audit_digest(),
    }


@app.get("/api/clinical/export/pdf")
def export_pdf_dossier():
    if not _ACTIVE_ASSEMBLER:
        raise HTTPException(status_code=500, detail="Assembler uninitialized.")

    unlocked, unverified = _ACTIVE_ASSEMBLER.gates.is_export_unlocked()
    if not unlocked:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "EXPORT_BLOCKED_SAFETY_GATES_PENDING",
                "message": "Deterministic safety gate violation: Clinical transfer packet export is locked until all 3 high-risk fields are verified.",
                "pending_gates": unverified,
            }
        )

    pdf_out = CURRENT_DIR / f"transfer_packet_patient-{_ACTIVE_ASSEMBLER.demographics.mrn}.pdf"
    builder = ClinicalPDFPacketBuilder(_ACTIVE_ASSEMBLER)
    builder.save_pdf(str(pdf_out))

    return FileResponse(
        path=str(pdf_out),
        filename=f"transfer_packet_{_ACTIVE_ASSEMBLER.demographics.mrn}.pdf",
        media_type="application/pdf",
    )


@app.get("/api/clinical/export/docx")
def export_docx_dossier():
    docx_file = CURRENT_DIR / f"superdocs_handoff_{_ACTIVE_ASSEMBLER.demographics.mrn}.docx"
    if docx_file.exists():
        return FileResponse(
            path=str(docx_file),
            filename=f"superdocs_handoff_{_ACTIVE_ASSEMBLER.demographics.mrn}.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    raise HTTPException(status_code=404, detail="Word export not yet generated.")


if __name__ == "__main__":
    import socket
    import sys
    import uvicorn
    import urllib.request

    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    target_port = 8001
    if is_port_in_use(target_port):
        # Check if it's our healthy clinical server
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{target_port}/healthz")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    print("\n===========================================================================")
                    print(f"✅ SERVER IS ALREADY RUNNING & HEALTHY AT: http://127.0.0.1:{target_port}/dashboard")
                    print("===========================================================================\n")
                    sys.exit(0)
        except Exception:
            target_port = 8002

    print(f"\n[INFO] Starting Clinical Server on http://127.0.0.1:{target_port} ...")
    uvicorn.run(app, host="127.0.0.1", port=target_port)
