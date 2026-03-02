"""
LAB 4 — CAPSTONE: Financial Deep Research System (Module 4)
=============================================================
Production-grade multi-agent financial analysis.

Architecture:
  Orchestrator
    ├─→ market_data_agent   (fetches stock data)     ─┐ PARALLEL
    ├─→ news_analyst        (searches financial news) ─┘
    ├─→ finance_analyst     (quantitative analysis)   ← after data
    └─→ report_writer       (synthesizes report)      ← after analysis

Data flow: agents write to /data/, report reads from /data/ → /report/

Run: python lab4_financial_research.py
"""
import json
import httpx
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ═════════════════════════════════════════════════════════
# TOOLS
# ═════════════════════════════════════════════════════════

@tool
def search_financial_news(query: str) -> str:
    """Search for financial news and market information.

    Args:
        query: Financial search query (e.g., "NVIDIA earnings 2025")
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": f"{query} finance stock market", "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        results = []
        if data.get("Abstract"):
            results.append(f"**{data['Heading']}**: {data['Abstract']}")
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                results.append(f"- {t['Text']}")
        return "\n".join(results) if results else "No financial news found."
    except Exception as e:
        return f"Search error: {e}"


@tool
def get_stock_data(symbol: str) -> str:
    """Get stock market data for a ticker symbol.
    Returns price, ratios, and key financial metrics.

    Args:
        symbol: Stock ticker (e.g., NVDA, AAPL, MSFT, GOOGL, TSLA, AMZN, META)
    """
    # Simulated data for educational purposes
    # In production: use Alpha Vantage, Yahoo Finance, or Polygon.io
    stocks = {
        "NVDA": {
            "price": 875.30, "change_pct": 2.4, "pe_ratio": 65.2,
            "market_cap": "2.15T", "52w_high": 974.00, "52w_low": 473.20,
            "revenue_growth_yoy": "122%", "eps": 13.43, "forward_eps": 18.50,
            "sector": "Technology / Semiconductors",
            "dividend_yield": "0.02%", "beta": 1.72,
            "avg_volume": "45.2M", "analyst_rating": "Strong Buy",
            "price_to_sales": 38.5, "debt_to_equity": 0.41,
            "free_cash_flow": "29.5B", "gross_margin": "74.5%",
        },
        "AAPL": {
            "price": 228.50, "change_pct": -0.3, "pe_ratio": 31.5,
            "market_cap": "3.49T", "52w_high": 237.23, "52w_low": 164.08,
            "revenue_growth_yoy": "5%", "eps": 7.25, "forward_eps": 7.80,
            "sector": "Technology / Consumer Electronics",
            "dividend_yield": "0.44%", "beta": 1.24,
            "avg_volume": "52.1M", "analyst_rating": "Buy",
            "price_to_sales": 8.9, "debt_to_equity": 1.87,
            "free_cash_flow": "110.5B", "gross_margin": "46.2%",
        },
        "MSFT": {
            "price": 415.20, "change_pct": 1.1, "pe_ratio": 35.8,
            "market_cap": "3.08T", "52w_high": 430.82, "52w_low": 362.90,
            "revenue_growth_yoy": "16%", "eps": 11.60, "forward_eps": 13.20,
            "sector": "Technology / Software",
            "dividend_yield": "0.71%", "beta": 0.92,
            "avg_volume": "22.3M", "analyst_rating": "Strong Buy",
            "price_to_sales": 13.2, "debt_to_equity": 0.39,
            "free_cash_flow": "74.1B", "gross_margin": "69.8%",
        },
        "GOOGL": {
            "price": 175.80, "change_pct": 0.8, "pe_ratio": 24.3,
            "market_cap": "2.17T", "52w_high": 191.75, "52w_low": 130.67,
            "revenue_growth_yoy": "14%", "eps": 7.24, "forward_eps": 8.50,
            "sector": "Technology / Internet Services",
            "dividend_yield": "0.45%", "beta": 1.08,
            "avg_volume": "26.8M", "analyst_rating": "Buy",
            "price_to_sales": 6.8, "debt_to_equity": 0.05,
            "free_cash_flow": "69.5B", "gross_margin": "57.4%",
        },
        "TSLA": {
            "price": 248.90, "change_pct": -1.5, "pe_ratio": 72.4,
            "market_cap": "793B", "52w_high": 278.98, "52w_low": 138.80,
            "revenue_growth_yoy": "8%", "eps": 3.44, "forward_eps": 4.10,
            "sector": "Consumer Cyclical / Auto Manufacturers",
            "dividend_yield": "0%", "beta": 2.05,
            "avg_volume": "98.5M", "analyst_rating": "Hold",
            "price_to_sales": 8.2, "debt_to_equity": 0.11,
            "free_cash_flow": "4.4B", "gross_margin": "18.2%",
        },
        "AMZN": {
            "price": 198.40, "change_pct": 0.5, "pe_ratio": 42.1,
            "market_cap": "2.07T", "52w_high": 201.20, "52w_low": 151.61,
            "revenue_growth_yoy": "12%", "eps": 4.71, "forward_eps": 5.80,
            "sector": "Consumer Cyclical / E-Commerce",
            "dividend_yield": "0%", "beta": 1.16,
            "avg_volume": "43.2M", "analyst_rating": "Strong Buy",
            "price_to_sales": 3.4, "debt_to_equity": 0.59,
            "free_cash_flow": "54.3B", "gross_margin": "48.4%",
        },
        "META": {
            "price": 582.70, "change_pct": 1.8, "pe_ratio": 27.3,
            "market_cap": "1.47T", "52w_high": 602.95, "52w_low": 390.42,
            "revenue_growth_yoy": "22%", "eps": 21.34, "forward_eps": 25.00,
            "sector": "Technology / Social Media",
            "dividend_yield": "0.34%", "beta": 1.21,
            "avg_volume": "18.7M", "analyst_rating": "Strong Buy",
            "price_to_sales": 10.1, "debt_to_equity": 0.28,
            "free_cash_flow": "52.1B", "gross_margin": "81.5%",
        },
    }

    symbol = symbol.upper().strip()
    if symbol in stocks:
        return json.dumps({"symbol": symbol, "date": datetime.now().strftime("%Y-%m-%d"), **stocks[symbol]}, indent=2)
    return f"No data for {symbol}. Available: {', '.join(stocks.keys())}"


@tool
def calculate_financial_metrics(data_json: str) -> str:
    """Calculate financial metrics from JSON data.

    Args:
        data_json: JSON with fields: eps, growth_rate, price, beta, pe_ratio,
                   sector_avg_pe, discount_rate, terminal_pe, years.
                   Include 'calculate' array with: 'intrinsic_value',
                   'risk_score', 'valuation_status'
    """
    try:
        data = json.loads(data_json)
        results = {}
        calc = data.get("calculate", [])

        if "intrinsic_value" in calc:
            eps = data.get("eps", 0)
            growth = float(str(data.get("growth_rate", "10")).replace("%", "")) / 100
            discount = data.get("discount_rate", 0.10)
            terminal_pe = data.get("terminal_pe", 15)
            years = data.get("years", 5)
            future_eps = eps * ((1 + growth) ** years)
            terminal_value = future_eps * terminal_pe
            present_value = terminal_value / ((1 + discount) ** years)
            results["intrinsic_value_estimate"] = round(present_value, 2)
            results["current_price"] = data.get("price", "N/A")
            if data.get("price"):
                upside = ((present_value - data["price"]) / data["price"]) * 100
                results["upside_downside_pct"] = f"{round(upside, 1)}%"

        if "risk_score" in calc:
            beta = data.get("beta", 1.0)
            pe = data.get("pe_ratio", 20)
            risk = 0
            risk += 3 if beta > 1.5 else (2 if beta > 1.0 else 1)
            risk += 3 if pe > 50 else (2 if pe > 30 else 1)
            level = "High" if risk >= 5 else ("Medium" if risk >= 3 else "Low")
            results["risk_score"] = f"{risk}/6 ({level})"

        if "valuation_status" in calc:
            pe = data.get("pe_ratio", 20)
            sector_avg = data.get("sector_avg_pe", 25)
            if pe > sector_avg * 1.5:
                results["valuation"] = "Significantly Overvalued"
            elif pe > sector_avg * 1.2:
                results["valuation"] = "Moderately Overvalued"
            elif pe > sector_avg * 0.8:
                results["valuation"] = "Fairly Valued"
            else:
                results["valuation"] = "Undervalued"

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Calculation error: {e}"


# ═════════════════════════════════════════════════════════
# SUB-AGENTS
# ═════════════════════════════════════════════════════════

market_data_agent = {
    "name": "market_data_agent",
    "description": "Fetches stock data — prices, ratios, metrics. Use for any ticker data needs.",
    "system_prompt": """You fetch market data for stocks.

JOB:
1. Use get_stock_data for each requested ticker
2. Write structured data to /data/market/[SYMBOL].md as a markdown table
3. If comparing multiple stocks, fetch ALL of them
4. Return a summary of what you collected

FILE FORMAT:
# [SYMBOL] Market Data — [Date]
| Metric | Value |
|--------|-------|
| Price  | $XXX  |
| P/E    | XX.X  |
(include all available metrics)
""",
    "tools": [get_stock_data],
    "model": "openai:gpt-4o-mini",
}

news_analyst_agent = {
    "name": "news_analyst",
    "description": "Searches financial news, earnings, events, industry trends.",
    "system_prompt": """You are a financial news analyst.

JOB:
1. Search for recent news about the company/sector (2-3 searches)
2. Search for competitor news and industry trends
3. Write to /data/news/[topic].md
4. Categorize each item as Bullish / Bearish / Neutral

FILE FORMAT:
# [Company] News Analysis
## Bullish Signals
- signal (source)
## Bearish Signals
- signal (source)
## Industry Context
- trend
## Overall Sentiment: [Bullish/Bearish/Neutral]
""",
    "tools": [search_financial_news],
    "model": "openai:gpt-4o-mini",
}

finance_analyst_agent = {
    "name": "finance_analyst",
    "description": "Quantitative analysis — valuation, risk scoring, ratio analysis. Has calculator.",
    "system_prompt": """You are a quantitative financial analyst.

JOB:
1. Read market data from /data/market/ files
2. Calculate metrics using calculate_financial_metrics:
   Pass JSON with: eps, growth_rate, price, beta, pe_ratio, sector_avg_pe
   And calculate: ["intrinsic_value", "risk_score", "valuation_status"]
3. Write analysis to /data/analysis/[topic].md
4. Be honest about uncertainty — these are estimates

IMPORTANT: Read the data files FIRST, then calculate.""",
    "tools": [calculate_financial_metrics],
    "model": "openai:gpt-4o",
}

report_writer_agent = {
    "name": "report_writer",
    "description": "Reads all /data/ research and writes polished investment report to /report/.",
    "system_prompt": """You are a senior investment report writer.

JOB:
1. Read ALL files: /data/market/, /data/news/, /data/analysis/
2. Synthesize into a professional report at /report/investment_report.md

REPORT STRUCTURE:
# Investment Analysis: [Company] ([SYMBOL])
**Date:** [date] | **Analyst:** AI Research Team

## Executive Summary
[2-3 sentence verdict with rating]

## Market Data Snapshot
| Metric | Value |
|--------|-------|
[key metrics table]

## Financial Analysis
[Valuation, growth, risk assessment with numbers]

## News & Sentiment
[Key developments, sentiment, catalysts]

## Risk Factors
- [risk 1]
- [risk 2]

## Investment Verdict
**Rating:** Strong Buy / Buy / Hold / Sell / Strong Sell
**Confidence:** High / Medium / Low
**Key Reasons:**
1. [reason]
2. [reason]
3. [reason]

---
*Disclaimer: AI-generated educational content. Not financial advice.*
""",
    "tools": [],
    "model": "openai:gpt-4o",
}


# ═════════════════════════════════════════════════════════
# ORCHESTRATOR
# ═════════════════════════════════════════════════════════

financial_system = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[market_data_agent, news_analyst_agent, finance_analyst_agent, report_writer_agent],
    system_prompt="""You are the lead orchestrator of a financial deep research system.

## WORKFLOW (follow this phased approach)

### Phase 1: Data Collection (PARALLEL)
Launch SIMULTANEOUSLY:
- market_data_agent: "Fetch stock data for [SYMBOL(s)]"
- news_analyst: "Research latest news and sentiment for [COMPANY]"

### Phase 2: Quantitative Analysis (after Phase 1)
- finance_analyst: "Read /data/market/ files, perform valuation & risk analysis, write to /data/analysis/"

### Phase 3: Report Generation (after Phase 2)
- report_writer: "Read all /data/ directories, write investment report to /report/"

### Phase 4: Deliver
- Read /report/investment_report.md
- Present the full report to the user

## RULES
- Phase 1 runs IN PARALLEL (multiple task() calls in one response)
- Phase 2 waits for Phase 1 to complete
- Phase 3 waits for Phase 2 to complete
- For "compare X vs Y" queries: fetch data for ALL stocks
- Always include the disclaimer
"""
)


# ═════════════════════════════════════════════════════════
# RUN THE SYSTEM
# ═════════════════════════════════════════════════════════

def research(question: str):
    """Run a financial research query."""
    thread = f"fin-{datetime.now().strftime('%H%M%S')}"
    print(f"\n{'='*70}")
    print(f" FINANCIAL DEEP RESEARCH SYSTEM")
    print(f"{'='*70}")
    print(f" Query: {question}")
    print(f" Thread: {thread}")
    print(f" Agents: market_data → news → finance_analyst → report_writer")
    print(f"{'='*70}\n")
    print("Running multi-agent analysis (1-2 minutes)...\n")

    result = financial_system.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*70}")
            print(msg.content)
            break


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  CAPSTONE 1: Financial Deep Research System              ║
║  4 Agents · Parallel + Sequential · File Communication   ║
╚══════════════════════════════════════════════════════════╝
    """)

    # ── Query 1: Single Stock Deep Dive ──
    research("Should I invest in NVIDIA (NVDA) right now? Give me a full analysis.")

    # Uncomment for more queries:
    # ── Query 2: Head-to-Head Comparison ──
    # research("Compare NVDA vs MSFT vs GOOGL as investment options for 2025. Which is best value?")

    # ── Query 3: Sector Overview ──
    # research("Analyze the Magnificent 7 tech stocks. Which are overvalued and which are undervalued?")

    print(f"\n{'='*70}")
    print(" CAPSTONE 1 COMPLETE!")
    print("=" * 70)
    print("""
    ARCHITECTURE RECAP:
    ┌──────────────────────────────────────────┐
    │           ORCHESTRATOR (gpt-4o)          │
    └──┬──────────┬──────────┬──────────┬──────┘
       │ PARALLEL │          │          │
       ↓          ↓          ↓          ↓
    [market]   [news]    [analyst]  [writer]
    gpt-4o-mini gpt-4o-mini gpt-4o   gpt-4o
       ↓          ↓          ↑          ↑
       └──→ /data/ ──→──────┘          │
                    └──→ /data/analysis/┘
                              └──→ /report/

    PATTERNS USED:
    ✓ Parallel sub-agent execution (Phase 1)
    ✓ Sequential dependency (Phase 2→3)
    ✓ File-based inter-agent communication
    ✓ Specialist agents with different models
    ✓ Structured output (investment report format)

    NEXT: python lab5_text_to_sql.py
    """)
