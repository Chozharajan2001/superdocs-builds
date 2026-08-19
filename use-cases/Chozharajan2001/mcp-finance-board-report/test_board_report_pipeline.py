"""
Automated Test Suite for Finance Board Report Automation (Band S3).
Executes 100% offline with zero third-party API spend.
"""
from pathlib import Path
import pytest

from warehouse_connector import WarehouseConnector, FinancialMetrics
from chart_generator import FinancialChartGenerator
from board_packet_compiler import BoardPacketCompiler
from mcp_board_tools import MCPBoardToolsServer


@pytest.fixture
def connector():
    return WarehouseConnector()


@pytest.fixture
def compiler(tmp_path):
    return BoardPacketCompiler(output_dir=tmp_path)


@pytest.fixture
def mcp_server():
    return MCPBoardToolsServer()


def test_warehouse_metrics_extraction(connector):
    """Test extracting quarterly SaaS metrics from warehouse."""
    metrics = connector.fetch_quarterly_financials("Q2 2026")
    assert metrics.fiscal_quarter == "Q2 2026"
    assert metrics.ending_arr == 22_400_000.0
    assert metrics.net_dollar_retention_pct == 124.2
    assert metrics.cash_runway_months == 32
    assert metrics.gross_margin_pct == 81.4


def test_exact_numerical_grounding(connector, compiler):
    """Test that generated narrative achieves 100% zero-hallucination numerical parity."""
    metrics = connector.fetch_quarterly_financials("Q2 2026")
    narrative = compiler.synthesize_narrative(metrics)
    audit = connector.verify_exact_numerical_grounding(narrative, metrics)
    
    assert audit["all_numbers_grounded"] is True
    assert audit["zero_hallucination_verified"] is True
    assert audit["audit_checks"]["ending_arr_grounded"] is True
    assert audit["audit_checks"]["growth_rate_grounded"] is True
    assert audit["audit_checks"]["ndr_grounded"] is True


def test_discrepancy_detection_on_hallucination(connector):
    """Test that corrupted narrative text fails numerical grounding audit."""
    metrics = connector.fetch_quarterly_financials("Q2 2026")
    hallucinated_narrative = "Our ending ARR reached $99.9M with 300% growth."
    audit = connector.verify_exact_numerical_grounding(hallucinated_narrative, metrics)
    
    assert audit["all_numbers_grounded"] is False
    assert audit["zero_hallucination_verified"] is False
    assert audit["audit_checks"]["ending_arr_grounded"] is False


def test_chart_generation(tmp_path):
    """Test rendering financial ARR bridge and unit economics charts."""
    chart_gen = FinancialChartGenerator(output_dir=tmp_path)
    arr_chart = chart_gen.render_arr_growth_chart("test_arr.png")
    unit_chart = chart_gen.render_unit_economics_chart("test_unit.png")
    
    assert arr_chart.exists()
    assert arr_chart.stat().st_size > 1000
    assert unit_chart.exists()
    assert unit_chart.stat().st_size > 1000


def test_board_pdf_compilation(connector, compiler):
    """Test compiling multi-page executive board PDF dossier."""
    metrics = connector.fetch_quarterly_financials("Q2 2026")
    pdf_path = compiler.compile_board_pdf(metrics, "test_board_packet.pdf")
    
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 5000


def test_mcp_tools_dispatch(mcp_server):
    """Test MCP tool definitions and JSON-RPC execution."""
    defs = mcp_server.get_tool_definitions()
    assert len(defs) == 4
    tool_names = [t["name"] for t in defs]
    assert "query_financial_warehouse" in tool_names
    assert "generate_board_narrative" in tool_names
    assert "audit_numerical_grounding" in tool_names
    assert "export_board_dossier" in tool_names

    # Test tool execution
    res = mcp_server.call_tool("query_financial_warehouse", {"fiscal_quarter": "Q2 2026"})
    assert res["status"] == "success"
    assert res["metrics"]["ending_arr"] == 22_400_000.0
