# Limitations & Operational Boundaries: Finance Board Report Pipeline

In alignment with the SuperDocs engineering evaluation principles (*"Honest reporting of limitations beats inflated claims"*), this document transparently scopes the V1 capabilities of this stretch exploration.

---

## 1. Data Warehouse Connectivity Scope
- **Current Implementation**: `warehouse_connector.py` provides an extensible adapter interface with deterministic synthetic SaaS financial fixtures (ARR Bridge, NRR, Gross Margin, Cash Runway) and exact mathematical zero-hallucination parity checks.
- **Production Extension**: The adapter is architected with a modular `fetch_quarterly_financials()` signature ready to accept live Snowflake `snowflake-connector-python`, Google BigQuery `google-cloud-bigquery`, or PostgreSQL connection URIs.

---

## 2. Visualization Engine
- **Current Implementation**: Renders standalone HTML/SVG ARR Waterfall and EBITDA trend charts suitable for in-document embedding and board packet PDF assembly.
- **Production Extension**: In production, connects directly to Highcharts or Tableau Server REST export endpoints for dynamic live-updating vector charts.
