"""
Automated Test Suite for Clinical Transcript to Care Plan & Prescription Pipeline (Band S3).
Executes 100% offline with zero third-party API spend.
"""
from pathlib import Path
import pytest

from transcript_parser import ClinicalTranscriptParser, ClinicalTranscriptData
from careplan_engine import NursingCarePlanEngine, SMARTNursingGoal, DischargeInstructionPacket
from prescription_compiler import PrescriptionCompiler
from mcp_clinical_tools import MCPClinicalToolsServer


@pytest.fixture
def parser():
    return ClinicalTranscriptParser()


@pytest.fixture
def engine():
    return NursingCarePlanEngine()


@pytest.fixture
def compiler(tmp_path):
    return PrescriptionCompiler(output_dir=tmp_path)


@pytest.fixture
def mcp_server():
    return MCPClinicalToolsServer()


def test_transcript_entity_extraction(parser):
    """Test extracting clinical entities from raw bedside dialogue."""
    data = parser.parse_transcript()
    assert data.patient_name == "Eleanor Vance"
    assert data.mrn == "883921"
    assert "pneumonia" in data.primary_diagnosis.lower()
    assert data.vital_signs["spo2_pct"] == 96
    assert len(data.prescribed_medications) == 3


def test_smart_careplan_generation(parser, engine):
    """Test formulating NANDA-I aligned SMART nursing goals."""
    data = parser.parse_transcript()
    goals = engine.formulate_smart_care_plan(data)
    assert len(goals) == 3
    assert any("Gas Exchange" in g.nursing_diagnosis for g in goals)
    assert any("Falls" in g.nursing_diagnosis for g in goals)
    assert any("Deficient Knowledge" in g.nursing_diagnosis for g in goals)
    for g in goals:
        assert len(g.nursing_interventions) >= 3
        assert g.smart_outcome_goal != ""


def test_discharge_packet_generation(parser, engine):
    """Test generating plain-language patient discharge instructions."""
    data = parser.parse_transcript()
    packet = engine.build_discharge_packet(data)
    assert packet.patient_name == "Eleanor Vance"
    assert len(packet.red_flag_warning_signs) >= 4
    assert len(packet.follow_up_appointments) == 2
    assert len(packet.medication_schedule) == 3


def test_contraindication_safety_check(parser, compiler):
    """Test clinical contraindication and allergy safety audit."""
    data = parser.parse_transcript()
    audit = compiler.check_contraindications(data)
    assert audit["safe_to_dispense"] is True
    assert audit["warnings_count"] >= 1


def test_clinical_care_pdf_compilation(parser, compiler):
    """Test generating standardized ReportLab clinical care PDF dossier."""
    data = parser.parse_transcript()
    pdf_path = compiler.compile_clinical_care_pdf(data, "test_care_dossier.pdf")
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000


def test_mcp_clinical_tools_dispatch(mcp_server):
    """Test MCP tool definitions and JSON-RPC dispatch."""
    defs = mcp_server.get_tool_definitions()
    assert len(defs) == 5
    tool_names = [t["name"] for t in defs]
    assert "parse_clinical_transcript" in tool_names
    assert "generate_nursing_careplan" in tool_names
    assert "generate_discharge_instructions" in tool_names
    assert "compile_clinical_care_dossier" in tool_names

    # Execute tool
    res = mcp_server.call_tool("generate_nursing_careplan", {"patient_mrn": "883921"})
    assert res["status"] == "success"
    assert res["goals_count"] == 3
