"""
Model Context Protocol (MCP) Tool Exposer for Financial Board Report Automation.
Enables AI coding agents (Claude Code, Cursor, Cline) to query warehouse metrics and compile board dossiers.
"""
from typing import Dict, Any, List
import json

from warehouse_connector import WarehouseConnector, FinancialMetrics
from board_packet_compiler import BoardPacketCompiler


class MCPBoardToolsServer:
    """MCP Server exposing financial board report automation tools."""

    def __init__(self):
        self.connector = WarehouseConnector()
        self.compiler = BoardPacketCompiler()

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns standard MCP tool schemas."""
        return [
            {
                "name": "query_financial_warehouse",
                "description": "Extracts validated quarterly SaaS financial and unit economics metrics from the data warehouse.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "fiscal_quarter": {
                            "type": "string",
                            "description": "Fiscal quarter identifier (e.g., 'Q2 2026')",
                            "default": "Q2 2026"
                        }
                    },
                    "required": ["fiscal_quarter"]
                }
            },
            {
                "name": "generate_board_narrative",
                "description": "Synthesizes structured executive commentary strictly grounded against warehouse metrics with zero hallucination.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "fiscal_quarter": {
                            "type": "string",
                            "default": "Q2 2026"
                        }
                    },
                    "required": ["fiscal_quarter"]
                }
            },
            {
                "name": "audit_numerical_grounding",
                "description": "Audits generated board narrative text against primary warehouse figures to guarantee 100% numerical parity.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "narrative_text": {"type": "string"},
                        "fiscal_quarter": {"type": "string", "default": "Q2 2026"}
                    },
                    "required": ["narrative_text"]
                }
            },
            {
                "name": "export_board_dossier",
                "description": "Compiles and exports the complete multi-page PDF board packet with embedded visual charts and audit ledger.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "fiscal_quarter": {"type": "string", "default": "Q2 2026"},
                        "format": {"type": "string", "enum": ["pdf", "json"], "default": "pdf"}
                    }
                }
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches tool execution."""
        quarter = arguments.get("fiscal_quarter", "Q2 2026")
        metrics = self.connector.fetch_quarterly_financials(quarter)

        if tool_name == "query_financial_warehouse":
            return {"status": "success", "metrics": metrics.to_dict()}
        elif tool_name == "generate_board_narrative":
            narrative = self.compiler.synthesize_narrative(metrics)
            return {"status": "success", "fiscal_quarter": quarter, "narrative": narrative}
        elif tool_name == "audit_numerical_grounding":
            text = arguments.get("narrative_text", "")
            audit = self.connector.verify_exact_numerical_grounding(text, metrics)
            return {"status": "success", "audit": audit}
        elif tool_name == "export_board_dossier":
            pdf_path = self.compiler.compile_board_pdf(metrics)
            return {
                "status": "success",
                "fiscal_quarter": quarter,
                "exported_pdf": str(pdf_path),
                "bytes": pdf_path.stat().st_size,
                "charts_embedded": ["arr_growth_bridge.png", "unit_economics.png"]
            }
        else:
            raise ValueError(f"Unknown MCP tool: {tool_name}")
