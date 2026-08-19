"""
Model Context Protocol (MCP) Server for Clinical Transcript to Care Plan & Prescription Automation.
Enables AI coding agents (Claude Code, Cursor, Windsurf) to process bedside transcripts and compile care dossiers.
"""
from typing import Dict, Any, List
import json

from transcript_parser import ClinicalTranscriptParser, ClinicalTranscriptData
from careplan_engine import NursingCarePlanEngine
from prescription_compiler import PrescriptionCompiler


class MCPClinicalToolsServer:
    """MCP Server exposing clinical care plan and transcript automation tools."""

    def __init__(self):
        self.parser = ClinicalTranscriptParser()
        self.careplan_engine = NursingCarePlanEngine()
        self.compiler = PrescriptionCompiler()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns standard MCP tool schemas."""
        return [
            {
                "name": "parse_clinical_transcript",
                "description": "Ingests bedside multi-speaker clinical audio transcripts and extracts structured diagnoses, vitals, and medication orders.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "transcript_text": {
                            "type": "string",
                            "description": "Raw dialogue transcript with timestamps and speakers."
                        }
                    }
                }
            },
            {
                "name": "generate_nursing_careplan",
                "description": "Synthesizes evidence-based NANDA-I nursing diagnoses, SMART outcome goals, and actionable interventions.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_mrn": {"type": "string", "default": "883921"}
                    }
                }
            },
            {
                "name": "generate_discharge_instructions",
                "description": "Compiles plain-language patient discharge instructions (6th-grade reading level) with warning signs and follow-up milestones.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_mrn": {"type": "string", "default": "883921"}
                    }
                }
            },
            {
                "name": "check_prescription_contraindications",
                "description": "Audits extracted medication orders against documented allergy profiles and cross-reactivity flags.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_mrn": {"type": "string", "default": "883921"}
                    }
                }
            },
            {
                "name": "compile_clinical_care_dossier",
                "description": "Generates and exports the standardized multi-page PDF Care Plan & Prescription Dossier with certified sign-off block.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "patient_mrn": {"type": "string", "default": "883921"},
                        "format": {"type": "string", "enum": ["pdf", "json"], "default": "pdf"}
                    }
                }
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution."""
        transcript_text = arguments.get("transcript_text")
        data = self.parser.parse_transcript(transcript_text)

        if tool_name == "parse_clinical_transcript":
            return {
                "status": "success",
                "patient": data.patient_name,
                "mrn": data.mrn,
                "primary_diagnosis": data.primary_diagnosis,
                "vitals": data.vital_signs,
                "medications_extracted": len(data.prescribed_medications),
            }
        elif tool_name == "generate_nursing_careplan":
            goals = self.careplan_engine.formulate_smart_care_plan(data)
            return {
                "status": "success",
                "patient": data.patient_name,
                "goals_count": len(goals),
                "goals": [
                    {
                        "diagnosis": g.nursing_diagnosis,
                        "smart_outcome": g.smart_outcome_goal,
                        "timeframe": g.target_timeframe,
                        "interventions": g.nursing_interventions,
                    }
                    for g in goals
                ]
            }
        elif tool_name == "generate_discharge_instructions":
            packet = self.careplan_engine.build_discharge_packet(data)
            return {
                "status": "success",
                "patient": packet.patient_name,
                "condition": packet.primary_condition_explanation,
                "red_flags": packet.red_flag_warning_signs,
                "appointments": packet.follow_up_appointments,
            }
        elif tool_name == "check_prescription_contraindications":
            audit = self.compiler.check_contraindications(data)
            return {"status": "success", "audit": audit}
        elif tool_name == "compile_clinical_care_dossier":
            pdf_path = self.compiler.compile_clinical_care_pdf(data)
            return {
                "status": "success",
                "patient": data.patient_name,
                "exported_pdf": str(pdf_path),
                "bytes": pdf_path.stat().st_size,
            }
        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
