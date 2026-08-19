"""
FastAPI Server for MCP Finance Board Report Automation.
Exposes REST endpoints, telemetry metrics, and the executive review dashboard.
"""
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from warehouse_connector import WarehouseConnector, FinancialMetrics
from board_packet_compiler import BoardPacketCompiler

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("superdocs.finance_server")

CURRENT_DIR = Path(__file__).parent.resolve()
DASHBOARD_FILE = CURRENT_DIR / "board_report_dashboard.html"

connector = WarehouseConnector()
compiler = BoardPacketCompiler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Financial Board Report Automation Server initialized.")
    yield


app = FastAPI(
    title="SuperDocs Finance Board Report Automation (Band S3)",
    description="Data Warehouse to Executive Board Packet Pipeline with Chart Rendering and Exact Grounding.",
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
        "service": "superdocs-finance-board-server",
        "band": "S3",
        "warehouse_status": "connected",
    }


@app.get("/dashboard", response_class=HTMLResponse)
def get_dashboard():
    if DASHBOARD_FILE.exists():
        return HTMLResponse(content=DASHBOARD_FILE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Board Report Dashboard not found.</h1>", status_code=404)


@app.get("/api/finance/metrics")
def get_metrics(quarter: str = "Q2 2026"):
    metrics = connector.fetch_quarterly_financials(quarter)
    return metrics.to_dict()


@app.get("/api/finance/narrative")
def get_narrative(quarter: str = "Q2 2026"):
    metrics = connector.fetch_quarterly_financials(quarter)
    narrative = compiler.synthesize_narrative(metrics)
    audit = connector.verify_exact_numerical_grounding(narrative, metrics)
    return {
        "fiscal_quarter": quarter,
        "narrative": narrative,
        "grounding_audit": audit,
    }


@app.get("/api/finance/export/pdf")
def export_board_pdf(quarter: str = "Q2 2026"):
    metrics = connector.fetch_quarterly_financials(quarter)
    pdf_path = compiler.compile_board_pdf(metrics)
    if pdf_path.exists():
        return FileResponse(
            path=str(pdf_path),
            filename=f"board_packet_{quarter.replace(' ', '_').lower()}.pdf",
            media_type="application/pdf",
        )
    raise HTTPException(status_code=500, detail="PDF generation failed.")


if __name__ == "__main__":
    import socket
    import sys
    import uvicorn
    import urllib.request

    def is_port_in_use(port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("127.0.0.1", port)) == 0

    target_port = 8003
    if is_port_in_use(target_port):
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{target_port}/healthz")
            with urllib.request.urlopen(req, timeout=1) as resp:
                if resp.status == 200:
                    print(f"✅ Finance Board Server already active on http://127.0.0.1:{target_port}/dashboard")
                    sys.exit(0)
        except Exception:
            target_port = 8004

    print(f"\n[INFO] Starting Finance Board Server on http://127.0.0.1:{target_port} ...")
    uvicorn.run(app, host="127.0.0.1", port=target_port)
