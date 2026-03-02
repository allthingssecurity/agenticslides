# Module 4: Capstone Projects — Production-Grade Multi-Agent Apps

## Student: Copy-Paste This Prompt Into a New Agent Session

> Open a **new session** in your AI coding agent and paste this:

```
Read the file course/agent-docs/04-capstones.md and follow it step by step.

First complete the Environment Setup section (skip if already done), then build
Labs 4, 5, and 6 from scratch in the my-agents/ directory. Run and verify each
lab before moving to the next.

This module builds three production-grade apps: a financial deep research system
(4 sub-agents), a text-to-SQL analytics agent, and an automated content pipeline.

If you get stuck, consult the references at course/labs/lab4_financial_research.py,
course/labs/lab5_text_to_sql.py, and course/labs/lab6_content_pipeline.py.
```

---

## Environment Setup

This is a new agent session, so the environment must be ready. Follow every step — the checks will skip anything already done.

### Step 1: Ensure Python 3.11+ is available

**Action:** `shell`
**OS[mac/linux]:**
```bash
python3 --version
```
**OS[windows]:**
```cmd
python --version
```
**Expected:** `Python 3.11.x` or higher. If not installed, follow the Python installation steps in `course/agent-docs/01-foundations.md` → Environment Setup → Step 1.

### Step 2: Create working directory, venv, install deps, set API key

**Action:** `shell`
**OS[mac/linux]:**
```bash
mkdir -p my-agents
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
export OPENAI_API_KEY="sk-your-key-here"
```
**OS[windows]:**
```cmd
mkdir my-agents 2>nul
if not exist .venv python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install "deepagents>=0.4.3" "langchain-openai>=1.1.8" "openai>=1.66.0"
set OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Verify

**Action:** `shell`
```bash
python -c "import sys; assert sys.version_info >= (3,11); print(f'Python {sys.version} OK')"
python -c "from deepagents import create_deep_agent; print('deepagents OK')"
python -c "import openai; print('openai OK')"
python -c "import os; assert os.getenv('OPENAI_API_KEY','').startswith('sk-'); print('API key OK')"
```
**Expected:** Four lines of "OK".

### Prerequisites
- Modules 1-3 completed (Labs 0 through 3c built and ran successfully)
- Understanding of: sub-agents, parallel execution, file-based communication, planning

---

## Lab 4: Build a Financial Deep Research System

### Goal
Build a production-grade multi-agent financial analysis system:

```
Orchestrator (gpt-4o)
  ├─→ market_data_agent (gpt-4o-mini)   ─┐ PHASE 1: PARALLEL
  ├─→ news_analyst (gpt-4o-mini)         ─┘
  ├─→ finance_analyst (gpt-4o)           ← PHASE 2: after Phase 1
  └─→ report_writer (gpt-4o)            ← PHASE 3: after Phase 2
```

### Step 1: Create the file with imports

**Action:** `create-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python
"""
LAB 4 — CAPSTONE: Financial Deep Research System
==================================================
4 sub-agents + orchestrator with phased execution.
"""
import json
from openai import OpenAI
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
```

### Step 2: Build the financial news search tool

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════

@tool
def search_financial_news(query: str) -> str:
    """Search for financial news and market information.

    Args:
        query: Financial search query (e.g., "NVIDIA earnings 2025")
    """
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=f"{query} finance stock market"
        )
        return response.output_text
    except Exception as e:
        return f"Search error: {e}"
```

### Step 3: Build the stock data tool (simulated)

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


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
```

**Why simulated data?** This is a teaching lab. In production, replace with Alpha Vantage (`alphavantage.co`), Yahoo Finance, or Polygon.io APIs. The agent code stays the same — only the tool internals change.

### Step 4: Build the financial metrics calculator tool

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


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
```

### Step 5: Define the 4 sub-agents

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# SUB-AGENTS
# ═══════════════════════════════════════════════════════

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
```

### Step 6: Build the orchestrator with phased workflow

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════

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
```

### Step 7: Add the runner and main block

**Action:** `append-to-file`
**File:** `my-agents/lab4_financial_research.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# RUN THE SYSTEM
# ═══════════════════════════════════════════════════════

def research(question: str):
    """Run a financial research query."""
    thread = f"fin-{datetime.now().strftime('%H%M%S')}"
    print(f"\n{'='*70}")
    print(f" FINANCIAL DEEP RESEARCH SYSTEM")
    print(f"{'='*70}")
    print(f" Query: {question}")
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
    print("=" * 70)
    print(" CAPSTONE 1: Financial Deep Research System")
    print(" 4 Agents · Parallel + Sequential · File Communication")
    print("=" * 70)

    research("Should I invest in NVIDIA (NVDA) right now? Give me a full analysis.")

    print(f"\n{'='*70}")
    print(" CAPSTONE 1 COMPLETE!")
    print("=" * 70)
```

### Step 8: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab4_financial_research.py
```

**Note:** Takes 1-2 minutes — 4 agents across 3 phases.

### Step 9: Verify

**Success criteria:**
- A structured investment report is produced (no errors)
- Contains NVDA stock data (price ~$875, P/E ~65)
- Includes financial analysis (intrinsic value, risk score)
- News sentiment is categorized (bullish/bearish/neutral)
- Report includes a disclaimer

### What You Built
- **3 specialized tools** — news search, stock data, financial calculator
- **4 sub-agents** — each with a specific role, model, and file output path
- **Multi-phase orchestration** — Phase 1 parallel, Phases 2-3 sequential
- **Production report format** — professional investment report template

---

## Lab 5: Build a Text-to-SQL Analytics Agent

### Goal
Build a single agent that converts natural language to SQL, executes queries against a sample database, and explains results.

### Step 1: Create the file with imports and database setup

**Action:** `create-file`
**File:** `my-agents/lab5_text_to_sql.py`
**Content:**
```python
"""
LAB 5 — CAPSTONE: Text-to-SQL Analytics Agent
================================================
Natural language → SQL → Results → Explanation
"""
import sqlite3
import json
import os
import random
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ═══════════════════════════════════════════════════════
# DATABASE SETUP
# ═══════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_analytics.db")


def setup_database():
    """Create a realistic e-commerce analytics database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop existing tables for clean setup
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS customers")
    c.execute("DROP TABLE IF EXISTS products")

    # Products table
    c.execute("""CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        cost REAL NOT NULL,
        supplier TEXT NOT NULL
    )""")

    products = [
        (1, "Wireless Headphones", "Electronics", 79.99, 32.00, "SoundTech"),
        (2, "USB-C Hub 7-Port", "Electronics", 49.99, 18.00, "ConnectPro"),
        (3, "Mechanical Keyboard", "Electronics", 129.99, 55.00, "KeyMaster"),
        (4, "Standing Desk Mat", "Office", 39.99, 12.00, "ErgoLife"),
        (5, "LED Desk Lamp", "Office", 59.99, 22.00, "BrightWork"),
        (6, "Laptop Stand Aluminum", "Office", 44.99, 15.00, "ErgoLife"),
        (7, "Ergonomic Mouse", "Electronics", 69.99, 28.00, "KeyMaster"),
        (8, "Monitor Light Bar", "Electronics", 54.99, 20.00, "BrightWork"),
        (9, "Cable Management Kit", "Office", 24.99, 8.00, "ConnectPro"),
        (10, "Webcam 1080p", "Electronics", 89.99, 35.00, "SoundTech"),
        (11, "Desk Organizer Set", "Office", 34.99, 11.00, "ErgoLife"),
        (12, "Blue Light Glasses", "Accessories", 29.99, 9.00, "OptikPro"),
        (13, "Wrist Rest Gel", "Accessories", 19.99, 6.00, "ErgoLife"),
        (14, "Screen Cleaner Kit", "Accessories", 14.99, 4.00, "CleanTech"),
        (15, "USB Microphone", "Electronics", 119.99, 48.00, "SoundTech"),
    ]
    c.executemany("INSERT INTO products VALUES (?,?,?,?,?,?)", products)

    # Customers table
    c.execute("""CREATE TABLE customers (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        city TEXT NOT NULL,
        state TEXT NOT NULL,
        signup_date DATE NOT NULL,
        tier TEXT NOT NULL
    )""")

    cities = [
        ("New York", "NY"), ("Los Angeles", "CA"), ("Chicago", "IL"),
        ("Houston", "TX"), ("Phoenix", "AZ"), ("Philadelphia", "PA"),
        ("San Antonio", "TX"), ("San Diego", "CA"), ("Dallas", "TX"),
        ("Austin", "TX"), ("Seattle", "WA"), ("Denver", "CO"),
        ("Boston", "MA"), ("Portland", "OR"), ("Miami", "FL"),
    ]
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]
    tier_weights = [40, 30, 20, 10]

    random.seed(42)  # Reproducible data
    customers = []
    for i in range(1, 201):
        city, state = random.choice(cities)
        tier = random.choices(tiers, weights=tier_weights, k=1)[0]
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        customers.append((
            i, f"Customer_{i:03d}", f"customer{i}@email.com",
            city, state, f"2024-{month:02d}-{day:02d}", tier
        ))
    c.executemany("INSERT INTO customers VALUES (?,?,?,?,?,?,?)", customers)

    # Orders table
    c.execute("""CREATE TABLE orders (
        id INTEGER PRIMARY KEY,
        product_id INTEGER NOT NULL,
        customer_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        order_date DATE NOT NULL,
        region TEXT NOT NULL,
        status TEXT NOT NULL,
        FOREIGN KEY (product_id) REFERENCES products(id),
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )""")

    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    statuses = ["completed", "completed", "completed", "completed",
                "shipped", "processing", "returned"]

    orders = []
    for i in range(1, 1001):
        orders.append((
            i,
            random.randint(1, 15),
            random.randint(1, 200),
            random.randint(1, 5),
            f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            random.choice(regions),
            random.choice(statuses),
        ))
    c.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f" Database created: {DB_PATH}")
    print(f" Tables: products (15), customers (200), orders (1000)\n")
```

### Step 2: Build the schema exploration and SQL execution tools

**Action:** `append-to-file`
**File:** `my-agents/lab5_text_to_sql.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════

@tool
def explore_schema() -> str:
    """Get the complete database schema — all tables, columns, types,
    relationships, and sample data. Call this FIRST before writing SQL."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in c.fetchall()]

    output = ["DATABASE SCHEMA", "=" * 50]

    for table in tables:
        c.execute(f"PRAGMA table_info({table})")
        columns = c.fetchall()

        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]

        c.execute(f"SELECT * FROM {table} LIMIT 3")
        samples = c.fetchall()

        col_names = [col[1] for col in columns]

        output.append(f"\nTABLE: {table} ({count} rows)")
        output.append("COLUMNS:")
        for col in columns:
            pk = " [PRIMARY KEY]" if col[5] else ""
            nullable = "" if col[3] else " [NOT NULL]"
            output.append(f"  {col[1]:20s} {col[2]:10s}{pk}{nullable}")

        c.execute(f"PRAGMA foreign_key_list({table})")
        fks = c.fetchall()
        if fks:
            output.append("FOREIGN KEYS:")
            for fk in fks:
                output.append(f"  {fk[3]} → {fk[2]}.{fk[4]}")

        output.append(f"SAMPLE DATA ({', '.join(col_names)}):")
        for s in samples:
            output.append(f"  {s}")

    conn.close()
    return "\n".join(output)


@tool
def run_sql_query(query: str) -> str:
    """Execute a READ-ONLY SQL query and return results as a formatted table.
    Only SELECT statements are allowed.

    Args:
        query: A SQL SELECT query
    """
    stripped = query.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        return "ERROR: Only SELECT queries are allowed for safety."

    # Block write operations even in subqueries
    dangerous = ["DROP ", "DELETE ", "INSERT ", "UPDATE ", "ALTER ", "CREATE ", "TRUNCATE "]
    upper_q = stripped.upper()
    for d in dangerous:
        if d in upper_q:
            return f"ERROR: {d.strip()} operations are not allowed."

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(stripped)
        rows = c.fetchall()

        if not rows:
            return "Query returned 0 rows."

        columns = rows[0].keys()

        # Calculate column widths
        widths = {col: len(col) for col in columns}
        display_rows = rows[:100]
        for row in display_rows:
            for col in columns:
                widths[col] = max(widths[col], len(str(row[col])))

        # Format as table
        header = " | ".join(f"{col:<{widths[col]}}" for col in columns)
        separator = " | ".join("-" * widths[col] for col in columns)

        result_lines = [header, separator]
        for row in display_rows:
            line = " | ".join(f"{str(row[col]):<{widths[col]}}" for col in columns)
            result_lines.append(line)

        result = "\n".join(result_lines)

        if len(rows) > 100:
            result += f"\n\n... showing 100 of {len(rows)} total rows"
        else:
            result += f"\n\nTotal: {len(rows)} rows"

        conn.close()
        return result

    except Exception as e:
        return f"SQL Error: {e}\n\nQuery attempted:\n{stripped}"
```

**Safety note:** `run_sql_query` blocks all write operations (DROP, DELETE, INSERT, UPDATE, ALTER, CREATE, TRUNCATE). Only SELECT queries are allowed.

### Step 3: Build the SQL agent and runner

**Action:** `append-to-file`
**File:** `my-agents/lab5_text_to_sql.py`
**Content:**
```python


# ═══════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════

sql_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[explore_schema, run_sql_query],
    system_prompt="""You are a data analytics agent that converts natural language to SQL.

## WORKFLOW (for every question)
1. If you haven't explored the schema yet, call explore_schema FIRST
2. Analyze the question and identify which tables/columns are needed
3. Write the SQL query
4. Execute it with run_sql_query
5. Explain the results in plain English
6. Suggest 2-3 follow-up questions

## SQL BEST PRACTICES
- Use proper JOINs with ON clauses (never implicit joins)
- Always alias calculated columns: SUM(price * quantity) AS total_revenue
- Use GROUP BY for aggregations
- Use ORDER BY for rankings (DESC for "top", ASC for "bottom")
- Use LIMIT for "top N" / "bottom N" questions
- Use HAVING for filtered aggregations

## RESPONSE FORMAT
**Query:**
```sql
SELECT ...
```

**Results:**
[table output]

**Interpretation:**
[plain English — what does this data mean for the business?]

**Follow-up Questions:**
- [related question 1]
- [related question 2]

## HANDLING AMBIGUITY
- "Revenue" = products.price × orders.quantity
- "Profit" = (products.price - products.cost) × orders.quantity
- "This year" / "2024" = WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
- "Top customers" = by total spending unless specified otherwise
"""
)


# ═══════════════════════════════════════════════════════
# RUN IT
# ═══════════════════════════════════════════════════════

def ask_data(question: str, thread: str = "sql-lab"):
    """Ask the analytics agent a question about the data."""
    print(f"\n{'─'*60}")
    print(f" Q: {question}")
    print(f"{'─'*60}\n")

    result = sql_agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            return


if __name__ == "__main__":
    print("=" * 60)
    print(" CAPSTONE 2: Text-to-SQL Analytics Agent")
    print(" Ask questions in English → Get SQL + results + insights")
    print("=" * 60)

    # Setup the database
    setup_database()

    # Run test queries
    ask_data("What are our top 5 products by total revenue?")
    ask_data("Which region generates the most revenue? Break it down by region.")
    ask_data(
        "Who are our top 10 customers by total spending? "
        "Show their tier, city, and number of orders."
    )
    ask_data("Show me monthly revenue and order count trends for 2024.")
    ask_data(
        "What's our profit margin by product category? "
        "Which category is most profitable?"
    )

    print(f"\n{'='*60}")
    print(" CAPSTONE 2 COMPLETE!")
    print("=" * 60)
```

### Step 4: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab5_text_to_sql.py
```

### Step 5: Verify

**Success criteria:**
- Database created (15 products, 200 customers, 1000 orders)
- All 5 queries produce SQL + results + explanations
- SQL uses proper JOINs (not implicit joins)
- Results explained in business terms
- `sample_analytics.db` file created in `my-agents/`

### What You Built
- **A database setup function** — creates an e-commerce database with realistic data
- **Schema exploration tool** — lets the agent discover the database structure
- **Safe SQL execution** — read-only with write operation blocking
- **A conversational analytics agent** — natural language in, SQL + explanation out

---

## Lab 6: Build an Automated Content Pipeline

### Goal
Build a 3-stage sequential pipeline: Researcher → Writer → Editor, communicating through files.

### Step 1: Create the full file

**Action:** `create-file`
**File:** `my-agents/lab6_content_pipeline.py`
**Content:**
```python
"""
LAB 6 — BONUS: Automated Content Pipeline
============================================
Researcher → Writer → Editor/Reviewer → Final Output
"""
from openai import OpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent


# ─── TOOL ──────────────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    try:
        client = OpenAI()
        response = client.responses.create(
            model="gpt-4o-mini",
            tools=[{"type": "web_search_preview"}],
            input=query
        )
        return response.output_text
    except Exception as e:
        return f"Error: {e}"


# ─── PIPELINE AGENTS ──────────────────────────────────

content_pipeline = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[
        # Stage 1: Research
        {
            "name": "topic_researcher",
            "description": (
                "Deep topic researcher. Searches web, gathers facts, stats, "
                "and expert opinions. Writes notes to /research/."
            ),
            "system_prompt": """You are an expert topic researcher.

JOB:
1. Search 3-5 times with different query angles
2. Write structured research notes to /research/notes.md
3. Include: key facts, statistics, expert quotes, trends
4. List ALL source URLs
5. Note any conflicting information

NOTE FORMAT:
# Research: [Topic]
## Key Facts & Stats
- fact (source URL)
## Expert Opinions
- quote/opinion (source)
## Current Trends
- trend
## Counterarguments / Controversies
- point
## Sources
- [Source](URL)
""",
            "tools": [web_search],
            "model": "openai:gpt-4o-mini",
        },

        # Stage 2: Write
        {
            "name": "content_writer",
            "description": (
                "Professional writer. Reads /research/ notes and writes "
                "polished articles to /drafts/. Does NOT search."
            ),
            "system_prompt": """You are a professional content writer.

JOB:
1. Read research notes from /research/notes.md
2. Write a polished article to /drafts/article.md
3. Structure: engaging intro → clear sections → examples → conclusion

ARTICLE FORMAT:
---
title: [SEO-friendly title]
meta_description: [155 chars for SEO]
word_count_target: 1000
---

# [Title]

[Engaging opening hook — a surprising stat or question]

## [Section 1 — the core concept]
[Explain with examples]

## [Section 2 — deeper dive]
[Data, comparisons, expert insights]

## [Section 3 — practical implications]
[What this means for the reader]

## Key Takeaways
- [takeaway 1]
- [takeaway 2]
- [takeaway 3]

## Sources
- [Source](URL)

RULES:
- Write 800-1200 words
- Use short paragraphs (2-3 sentences)
- Include at least one data point per section
- Conversational but authoritative tone
- NO fluff or filler — every sentence adds value
""",
            "tools": [],
            "model": "openai:gpt-4o",
        },

        # Stage 3: Review & Polish
        {
            "name": "editor_reviewer",
            "description": (
                "Senior editor. Reviews /drafts/ for quality, accuracy, "
                "and engagement. Writes feedback + final version."
            ),
            "system_prompt": """You are a senior content editor.

JOB:
1. Read the draft from /drafts/article.md
2. Read original research from /research/notes.md (to fact-check)
3. Write detailed feedback to /review/feedback.md
4. Write the IMPROVED final version to /final/article.md

REVIEW CHECKLIST:
- Accuracy — claims match research notes?
- Structure — logical flow, clear headings?
- Engagement — strong hook, interesting examples?
- Clarity — jargon explained, sentences concise?
- Completeness — all key points from research covered?
- SEO — title, meta description, headers good?
- Grammar — clean, professional writing?

FEEDBACK FORMAT (/review/feedback.md):
# Editorial Review
## Overall Rating: [A/B/C/D]
## Strengths
- ...
## Issues Found
- [issue]: [fix applied]
## Changes Made
- [change 1]
- [change 2]

THEN write the polished final version to /final/article.md
""",
            "tools": [],
            "model": "openai:gpt-4o",
        },
    ],

    system_prompt="""You orchestrate a content creation pipeline.

## PIPELINE (SEQUENTIAL — each step depends on the previous)

### Step 1: Research
- task to topic_researcher: "Research [topic] for an article targeting [audience]"
- Researcher writes to /research/notes.md

### Step 2: Write Draft
- task to content_writer: "Read /research/notes.md and write an article about [topic] for [audience]"
- Writer reads /research/ → writes to /drafts/article.md

### Step 3: Edit & Finalize
- task to editor_reviewer: "Review /drafts/article.md against /research/notes.md. Write feedback to /review/ and final version to /final/"
- Editor reads /drafts/ + /research/ → writes /review/feedback.md + /final/article.md

### Step 4: Deliver
- Read /final/article.md
- Read /review/feedback.md
- Present BOTH to the user: the final article + editor's notes

## IMPORTANT
- Steps MUST run sequentially (each needs previous step's files)
- Be specific in task descriptions about file paths
- Include target audience in writer's task
"""
)


# ─── RUN IT ─────────────────────────────────────────────

def create_content(topic: str, audience: str = "tech professionals"):
    """Run the full content pipeline."""
    print(f"\n{'='*60}")
    print(f" CONTENT PIPELINE")
    print(f" Topic: {topic}")
    print(f" Audience: {audience}")
    print(f" Pipeline: Research → Write → Edit → Deliver")
    print(f"{'='*60}\n")
    print("Running 3-stage pipeline (1-2 minutes)...\n")

    result = content_pipeline.invoke(
        {"messages": [HumanMessage(content=(
            f"Create a high-quality article.\n"
            f"Topic: {topic}\n"
            f"Target audience: {audience}\n"
            f"Run the full pipeline: research → write → review & edit"
        ))]},
        config={"configurable": {"thread_id": "content-pipeline"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(f"\n{'─'*60}")
            print(msg.content)
            break


if __name__ == "__main__":
    print("=" * 60)
    print(" BONUS: Automated Content Pipeline")
    print(" Researcher → Writer → Editor → Final Article")
    print("=" * 60)

    create_content(
        topic="How AI Agents Are Changing Software Development in 2025",
        audience="software developers and engineering managers"
    )

    print(f"\n{'='*60}")
    print(" CONTENT PIPELINE COMPLETE!")
    print("=" * 60)
```

### Step 2: Run it

**Action:** `shell`
**OS[mac/linux/windows]:**
```bash
python my-agents/lab6_content_pipeline.py
```

**Note:** Takes 1-2 minutes — three agents run sequentially.

### Step 3: Verify

**Success criteria:**
- Content about AI agents in software development is produced
- Output is structured (headings, sections, takeaways)
- Editor feedback is present (rating, strengths, changes)
- No errors

### What You Built
- **A 3-stage sequential pipeline** — each stage depends on the previous stage's files
- **Quality control** — the editor reviews the draft against original research
- **File-based handoff**: `/research/` → `/drafts/` → `/review/` + `/final/`

---

## Course Complete

You built 9 applications from scratch:

| Lab | What You Built | Core Pattern |
|-----|---------------|-------------|
| Lab 0 | Environment verifier | Diagnostic script + smoke test |
| Lab 1 | Calculator + clock agent | Single agent with custom tools |
| Lab 2 | Research agent | Filesystem + planning + web search |
| Lab 3a | Orchestrator + researcher | Sub-agent delegation |
| Lab 3b | Three parallel specialists | Parallel sub-agent execution |
| Lab 3c | Data pipeline | Filesystem as communication bus |
| Lab 4 | Financial research system | Multi-phase (parallel + sequential) |
| Lab 5 | Text-to-SQL analytics | Single agent with DB tools |
| Lab 6 | Content pipeline | Sequential pipeline + quality control |

**Five principles you now know:**
1. Deep agents = Planning + Sub-agents + Filesystem + System Prompts
2. Context isolation prevents sub-agents from polluting each other
3. The filesystem is your async message bus between agents
4. System prompts define workflows, not just personality
5. Different models for different roles optimizes cost
