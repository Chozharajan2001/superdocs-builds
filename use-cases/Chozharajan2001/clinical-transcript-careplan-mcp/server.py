"""
FastAPI Server for Clinical Transcript to Care Plan & Prescription Automation.
Exposes REST endpoints, clinical safety checks, and the interactive bedside dashboard.
"""
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from transcript_parser import ClinicalTranscriptParser, ClinicalTranscriptData
from careplan_engine import NursingCarePlanEngine
from prescription_compiler import PrescriptionCompiler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("superdocs.transcript_careplan_server")

CURRENT_DIR = Path(__file__).parent.resolve()
DASHBOARD_FILE = CURRENT_DIR / "transcript_careplan_dashboard.html"

parser = ClinicalTranscriptParser()
careplan_engine = NursingCarePlanEngine()
compiler = PrescriptionCompiler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Clinical Transcript Care Plan Server initialized.")
    yield


app = FastAPI(
    title="SuperDocs Clinical Transcript to Care Plan & Prescription Suite (Band S3)",
    description="Automated Bedside Transcript Parsing, NANDA Care Plan Synthesis, and Gated Prescription Compilation.",
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


@app.get("/healthz")
def health_check():
    return {
        "status": "healthy",
        "service": "superdocs-transcript-careplan-server",
        "band": "S3",
        "mode": "bedside_audio_nlp",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    if DASHBOARD_FILE.exists():
        return HTMLResponse(content=DASHBOARD_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Clinical Dashboard not found.</h1>", status_code=404)


@app.get("/api/transcript/data")
def get_transcript_data():
    data = parser.parse_transcript()
    return {
        "patient_name": data.patient_name,
        "mrn": data.mrn,
        "primary_diagnosis": data.primary_diagnosis,
        "allergies": data.allergies,
        "vitals": data.vital_signs,
        "medications": [
            {
                "drug": m.drug_name,
                "dose": m.dosage,
                "route": m.route,
                "freq": m.frequency,
                "indication": m.indication,
                "high_risk": m.is_high_risk,
            }
            for m in data.prescribed_medications
        ],
    }


@app.get("/api/transcript/careplan")
def get_careplan():
    data = parser.parse_transcript()
    goals = careplan_engine.formulate_smart_care_plan(data)
    return [
        {
            "diagnosis": g.nursing_diagnosis,
            "smart_goal": g.smart_outcome_goal,
            "timeframe": g.target_timeframe,
            "interventions": g.nursing_interventions,
            "evaluation": g.evaluation_criteria,
        }
        for g in goals
    ]


@app.get("/api/transcript/discharge")
def get_discharge():
    data = parser.parse_transcript()
    packet = careplan_engine.build_discharge_packet(data)
    return {
        "patient": packet.patient_name,
        "explanation": packet.primary_condition_explanation,
        "schedule": packet.medication_schedule,
        "rules": packet.activity_and_diet_rules,
        "red_flags": packet.red_flag_warning_signs,
        "appointments": packet.follow_up_appointments,
    }


@app.get("/api/transcript/export/pdf")
def export_careplan_pdf():
    data = parser.parse_transcript()
    pdf_path = compiler.compile_clinical_care_pdf(data)
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            filename=f"clinical_care_dossier_{data.mrn}.pdf",
            media_type="application/pdf",
        )
    raise HTTPException(status_code=500, detail="Care Plan PDF compilation failed.")


if __name__ == "__main__":
    import socket
    import sys
    import uvicorn
    import urllib.request

    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    target_port = 8005
    if is_port_in_use(target_port):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{target_port}/healthz")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    print(f"✅ Transcript Care Plan Server already active on http://127.0.0.1:{target_port}/dashboard")
                    sys.exit(0)
        except Exception:
            target_port = 8006

    print(f"\n[INFO] Starting Clinical Transcript Care Plan Server on http://127.0.0.1:{target_port} ...")
    uvicorn.run(app, host="127.0.0.1", port=target_port)
