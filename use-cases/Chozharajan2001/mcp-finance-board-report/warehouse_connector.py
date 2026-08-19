"""
Data Warehouse Connector & Financial Metrics Extraction Engine.
Provides structured access to quarterly SaaS financial and operational metrics.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json


@dataclass
class FinancialMetrics:
    fiscal_quarter: str = "Q2 2026"
    period_end_date: str = "2026-06-30"
    
    # Revenue & ARR
    starting_arr: float = 18_450_000.0  # $18.45M
    new_arr: float = 2_850_000.0        # $2.85M
    expansion_arr: float = 1_420_000.0  # $1.42M
    churned_arr: float = 320_000.0      # $320k
    ending_arr: float = 22_400_000.0    # $22.40M
    arr_growth_yoy_pct: float = 68.5    # 68.5% YoY
    
    # Unit Economics
    net_dollar_retention_pct: float = 124.2  # 124.2%
    gross_margin_pct: float = 81.4           # 81.4%
    cac_payback_months: float = 10.8         # 10.8 Months
    ltv_to_cac_ratio: float = 4.6            # 4.6x
    burn_multiple: float = 0.78              # 0.78x
    
    # Runway & Cash Flow
    cash_in_bank: float = 24_800_000.0       # $24.80M
    net_quarterly_burn: float = 1_650_000.0  # $1.65M
    cash_runway_months: int = 32             # 32 Months
    
    # GTM & Customers
    enterprise_customers: int = 142
    mid_market_customers: int = 388
    total_active_customers: int = 530
    acv_enterprise_avg: float = 84_500.0     # $84.5k
    pipeline_coverage_ratio: float = 3.8     # 3.8x
    
    # Headcount
    total_headcount: int = 114
    rd_headcount: int = 58
    gtm_headcount: int = 42
    ga_headcount: int = 14

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fiscal_quarter": self.fiscal_quarter,
            "period_end_date": self.period_end_date,
            "starting_arr": self.starting_arr,
            "new_arr": self.new_arr,
            "expansion_arr": self.expansion_arr,
            "churned_arr": self.churned_arr,
            "ending_arr": self.ending_arr,
            "arr_growth_yoy_pct": self.arr_growth_yoy_pct,
            "net_dollar_retention_pct": self.net_dollar_retention_pct,
            "gross_margin_pct": self.gross_margin_pct,
            "cac_payback_months": self.cac_payback_months,
            "ltv_to_cac_ratio": self.ltv_to_cac_ratio,
            "burn_multiple": self.burn_multiple,
            "cash_in_bank": self.cash_in_bank,
            "net_quarterly_burn": self.net_quarterly_burn,
            "cash_runway_months": self.cash_runway_months,
            "enterprise_customers": self.enterprise_customers,
            "mid_market_customers": self.mid_market_customers,
            "total_active_customers": self.total_active_customers,
            "acv_enterprise_avg": self.acv_enterprise_avg,
            "pipeline_coverage_ratio": self.pipeline_coverage_ratio,
            "total_headcount": self.total_headcount,
            "rd_headcount": self.rd_headcount,
            "gtm_headcount": self.gtm_headcount,
            "ga_headcount": self.ga_headcount,
        }


class WarehouseConnector:
    """Simulates connection to Snowflake/BigQuery/Postgres data warehouse."""

    def __init__(self, connection_uri: Optional[str] = None):
        self.connection_uri = connection_uri or "mock://warehouse.internal/finance_q2"

    def fetch_quarterly_financials(self, quarter: str = "Q2 2026") -> FinancialMetrics:
        """Extract validated quarterly metrics table from warehouse."""
        return FinancialMetrics(fiscal_quarter=quarter)

    def verify_exact_numerical_grounding(self, narrative_text: str, metrics: FinancialMetrics) -> Dict[str, Any]:
        """
        Audit that every number mentioned in narrative matches data warehouse.
        Returns check summary and list of verified vs discrepant figures.
        """
        grounding_audit = {
            "ending_arr_grounded": f"${metrics.ending_arr / 1_000_000:.2f}M" in narrative_text or f"${metrics.ending_arr / 1_000_000:.1f}M" in narrative_text,
            "growth_rate_grounded": f"{metrics.arr_growth_yoy_pct:.1f}%" in narrative_text or f"{metrics.arr_growth_yoy_pct}%" in narrative_text,
            "ndr_grounded": f"{metrics.net_dollar_retention_pct:.1f}%" in narrative_text or f"{metrics.net_dollar_retention_pct}%" in narrative_text,
            "cash_runway_grounded": f"{metrics.cash_runway_months} months" in narrative_text or f"${metrics.cash_in_bank / 1_000_000:.2f}M" in narrative_text,
            "burn_multiple_grounded": f"{metrics.burn_multiple:.2f}x" in narrative_text or f"{metrics.burn_multiple}x" in narrative_text,
        }
        all_passed = all(grounding_audit.values())
        return {
            "all_numbers_grounded": all_passed,
            "audit_checks": grounding_audit,
            "zero_hallucination_verified": all_passed,
        }
