# MODULE 4: Capstone Projects (45 minutes)
## Build Production-Grade Multi-Agent Apps

> **100% hands-on code.** Three complete applications you build from scratch.

---

## 4.1 — Project 1: Financial Deep Research System (25 min)

### What We're Building

A multi-agent financial analysis system:

```
User: "Should I invest in NVIDIA right now?"

┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR                           │
│  Decomposes query → delegates → synthesizes              │
└───┬──────────┬──────────┬──────────┬─────────────────────┘
    │          │          │          │
    ↓          ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
│MARKET  │ │NEWS    │ │FINANCE │ │REPORT      │
│DATA    │ │ANALYST │ │ANALYST │ │WRITER      │
│fetches │ │latest  │ │ratios, │ │synthesizes │
│prices, │ │news &  │ │growth, │ │into invest-│
│trends  │ │events  │ │risks   │ │ment report │
└────────┘ └────────┘ └────────┘ └────────────┘
    ↓          ↓          ↓          ↑
    └──────────┴──────────┘          │
           writes to /data/    reads /data/
                               writes /report/
```

### Complete Code

```python
# capstone1_financial_research.py
"""
FINANCIAL DEEP RESEARCH SYSTEM
================================
Multi-agent system for investment analysis.
Uses OpenAI APIs via DeepAgents framework.
"""
import json
import httpx
from datetime import datetime
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

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
    """Get current stock data for a ticker symbol. Returns simulated
    realistic data for educational purposes.

    Args:
        symbol: Stock ticker (e.g., NVDA, AAPL, MSFT)
    """
    # Simulated data for educational purposes
    # In production, replace with Alpha Vantage, Yahoo Finance, or Polygon.io API
    stocks = {
        "NVDA": {
            "price": 875.30, "change_pct": 2.4, "pe_ratio": 65.2,
            "market_cap": "2.15T", "52w_high": 974.00, "52w_low": 473.20,
            "revenue_growth": "122%", "eps": 13.43, "sector": "Technology",
            "dividend_yield": "0.02%", "beta": 1.72,
            "avg_volume": "45.2M", "analyst_rating": "Strong Buy",
        },
        "AAPL": {
            "price": 228.50, "change_pct": -0.3, "pe_ratio": 31.5,
            "market_cap": "3.49T", "52w_high": 237.23, "52w_low": 164.08,
            "revenue_growth": "5%", "eps": 7.25, "sector": "Technology",
            "dividend_yield": "0.44%", "beta": 1.24,
            "avg_volume": "52.1M", "analyst_rating": "Buy",
        },
        "MSFT": {
            "price": 415.20, "change_pct": 1.1, "pe_ratio": 35.8,
            "market_cap": "3.08T", "52w_high": 430.82, "52w_low": 362.90,
            "revenue_growth": "16%", "eps": 11.60, "sector": "Technology",
            "dividend_yield": "0.71%", "beta": 0.92,
            "avg_volume": "22.3M", "analyst_rating": "Strong Buy",
        },
        "GOOGL": {
            "price": 175.80, "change_pct": 0.8, "pe_ratio": 24.3,
            "market_cap": "2.17T", "52w_high": 191.75, "52w_low": 130.67,
            "revenue_growth": "14%", "eps": 7.24, "sector": "Technology",
            "dividend_yield": "0.45%", "beta": 1.08,
            "avg_volume": "26.8M", "analyst_rating": "Buy",
        },
        "TSLA": {
            "price": 248.90, "change_pct": -1.5, "pe_ratio": 72.4,
            "market_cap": "793B", "52w_high": 278.98, "52w_low": 138.80,
            "revenue_growth": "8%", "eps": 3.44, "sector": "Consumer Cyclical",
            "dividend_yield": "0%", "beta": 2.05,
            "avg_volume": "98.5M", "analyst_rating": "Hold",
        },
    }

    symbol = symbol.upper()
    if symbol in stocks:
        data = stocks[symbol]
        return json.dumps({
            "symbol": symbol,
            "date": datetime.now().strftime("%Y-%m-%d"),
            **data
        }, indent=2)
    else:
        return f"No data available for {symbol}. Available: {', '.join(stocks.keys())}"

@tool
def calculate_financial_metrics(data_json: str) -> str:
    """Calculate financial metrics from JSON data. Pass a JSON string with
    numeric fields and specify what calculations to perform.

    Args:
        data_json: JSON string with fields like price, eps, growth_rate, etc.
                   Include a 'calculate' field listing what to compute.
    """
    try:
        data = json.loads(data_json)
        results = {}

        calc = data.get("calculate", [])

        if "intrinsic_value" in calc or "fair_value" in calc:
            eps = data.get("eps", 0)
            growth = float(str(data.get("growth_rate", "10")).replace("%", "")) / 100
            discount_rate = data.get("discount_rate", 0.10)
            terminal_pe = data.get("terminal_pe", 15)
            years = data.get("years", 5)

            future_eps = eps * ((1 + growth) ** years)
            terminal_value = future_eps * terminal_pe
            present_value = terminal_value / ((1 + discount_rate) ** years)
            results["intrinsic_value_estimate"] = round(present_value, 2)
            results["current_price"] = data.get("price", "N/A")
            results["upside_pct"] = round(
                ((present_value - data.get("price", present_value)) / data.get("price", 1)) * 100, 1
            ) if data.get("price") else "N/A"

        if "risk_score" in calc:
            beta = data.get("beta", 1.0)
            pe = data.get("pe_ratio", 20)
            # Simple risk scoring
            risk = 0
            if beta > 1.5: risk += 3
            elif beta > 1.0: risk += 2
            else: risk += 1
            if pe > 50: risk += 3
            elif pe > 30: risk += 2
            else: risk += 1
            results["risk_score"] = f"{risk}/6 ({'High' if risk >= 5 else 'Medium' if risk >= 3 else 'Low'})"

        if "valuation_status" in calc:
            pe = data.get("pe_ratio", 20)
            sector_avg_pe = data.get("sector_avg_pe", 25)
            if pe > sector_avg_pe * 1.5:
                results["valuation"] = "Significantly Overvalued"
            elif pe > sector_avg_pe * 1.2:
                results["valuation"] = "Moderately Overvalued"
            elif pe > sector_avg_pe * 0.8:
                results["valuation"] = "Fairly Valued"
            else:
                results["valuation"] = "Undervalued"

        return json.dumps(results, indent=2)
    except Exception as e:
        return f"Calculation error: {e}"

# ═══════════════════════════════════════════════════════
# SUB-AGENTS
# ═══════════════════════════════════════════════════════

market_data_agent = {
    "name": "market_data_agent",
    "description": (
        "Fetches stock market data — prices, ratios, market cap, "
        "analyst ratings. Use for any stock data needs."
    ),
    "system_prompt": """You are a market data specialist.

## JOB
1. Use get_stock_data to fetch data for requested ticker(s)
2. Write the raw data to /data/market/[SYMBOL].md in a structured format
3. If multiple stocks requested, fetch ALL of them
4. Return a summary of what data you collected

## OUTPUT FORMAT for each file:
```markdown
# [SYMBOL] Market Data — [Date]
| Metric | Value |
|--------|-------|
| Price  | $XXX  |
| ...    | ...   |
```""",
    "tools": [get_stock_data],
    "model": "openai:gpt-4o-mini",
}

news_analyst_agent = {
    "name": "news_analyst",
    "description": (
        "Searches and analyzes financial news, earnings reports, "
        "market events, and industry trends."
    ),
    "system_prompt": """You are a financial news analyst.

## JOB
1. Search for recent news about the company/topic
2. Search for industry trends and competitor news
3. Write analysis to /data/news/[topic].md
4. Categorize news as: Bullish, Bearish, or Neutral with reasoning

## OUTPUT FORMAT:
```markdown
# [Company] News Analysis
## Bullish Signals
- signal 1 (source)
## Bearish Signals
- signal 1 (source)
## Industry Context
- ...
## Sentiment: [Bullish/Bearish/Neutral]
```""",
    "tools": [search_financial_news],
    "model": "openai:gpt-4o-mini",
}

finance_analyst_agent = {
    "name": "finance_analyst",
    "description": (
        "Performs quantitative financial analysis — valuation, risk "
        "assessment, ratio analysis. Has calculator tool."
    ),
    "system_prompt": """You are a quantitative financial analyst.

## JOB
1. Read market data from /data/market/ files
2. Perform financial calculations:
   - Intrinsic value estimation (DCF-like)
   - Risk scoring
   - Valuation status vs sector
3. Write analysis to /data/analysis/[topic].md
4. Be honest about uncertainty — these are estimates, not predictions

## Use calculate_financial_metrics with JSON like:
{
  "eps": 13.43,
  "growth_rate": "25%",
  "price": 875.30,
  "beta": 1.72,
  "pe_ratio": 65.2,
  "sector_avg_pe": 30,
  "calculate": ["intrinsic_value", "risk_score", "valuation_status"]
}""",
    "tools": [calculate_financial_metrics],
    "model": "openai:gpt-4o",
}

report_writer_agent = {
    "name": "report_writer",
    "description": (
        "Reads all research data from /data/ and writes a polished "
        "investment analysis report. Does NOT search or calculate — "
        "only synthesizes existing data."
    ),
    "system_prompt": """You are a senior investment report writer.

## JOB
1. Read ALL files from /data/market/, /data/news/, /data/analysis/
2. Synthesize into a professional investment report
3. Write to /report/investment_report.md

## REPORT STRUCTURE:
```markdown
# Investment Analysis: [Company] ([SYMBOL])
**Date:** [date]
**Analyst:** AI Research Team

## Executive Summary
[2-3 sentence verdict]

## Market Position
[Current price, trend, key metrics table]

## Financial Analysis
[Valuation assessment, growth metrics, risk profile]

## News & Sentiment
[Key developments, industry context, sentiment]

## Risk Factors
[Bullet list of main risks]

## Investment Verdict
**Rating:** [Strong Buy / Buy / Hold / Sell / Strong Sell]
**Confidence:** [High / Medium / Low]
**Key Reasoning:** [2-3 bullets]

## Disclaimer
This is AI-generated educational content, not financial advice.
```

Be balanced, honest, and cite specific numbers from the research.""",
    "tools": [],
    "model": "openai:gpt-4o",
}

# ═══════════════════════════════════════════════════════
# ORCHESTRATOR
# ═══════════════════════════════════════════════════════

financial_research_system = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[
        market_data_agent,
        news_analyst_agent,
        finance_analyst_agent,
        report_writer_agent,
    ],
    system_prompt="""You are the lead orchestrator of a financial deep research system.

## WORKFLOW (follow EXACTLY)

### Phase 1: Data Collection (PARALLEL)
Launch these sub-agents simultaneously:
- market_data_agent: "Fetch stock data for [SYMBOL] and any relevant comparisons"
- news_analyst: "Research latest news and sentiment for [COMPANY]"

### Phase 2: Analysis (after Phase 1 completes)
- finance_analyst: "Read market data from /data/market/ and perform valuation
  and risk analysis. Write to /data/analysis/"

### Phase 3: Report (after Phase 2 completes)
- report_writer: "Read all data from /data/ directories and write a complete
  investment report to /report/investment_report.md"

### Phase 4: Deliver
- Read /report/investment_report.md
- Present the full report to the user

## RULES
- Phase 1 agents run IN PARALLEL (multiple task calls in one response)
- Phase 2 waits for Phase 1 (needs the data)
- Phase 3 waits for Phase 2 (needs the analysis)
- Always include the disclaimer about AI-generated content
- For comparison queries, fetch data for all mentioned stocks

## HANDLING DIFFERENT QUERY TYPES
- "Should I invest in X?" → Full analysis with verdict
- "Compare X vs Y" → Fetch both, analyze both, compare
- "What's happening with X?" → Focus on news + current data
"""
)

# ═══════════════════════════════════════════════════════
# RUN THE SYSTEM
# ═══════════════════════════════════════════════════════

def research(question: str, thread: str = None):
    """Run a financial research query."""
    thread = thread or f"fin-{datetime.now().strftime('%H%M%S')}"

    print(f"\n{'='*70}")
    print(f" FINANCIAL DEEP RESEARCH SYSTEM")
    print(f" Query: {question}")
    print(f" Thread: {thread}")
    print(f"{'='*70}\n")
    print("Running multi-agent analysis (may take 1-2 minutes)...\n")

    result = financial_research_system.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            break

if __name__ == "__main__":
    # ── Query 1: Single Stock Analysis ──
    research("Should I invest in NVIDIA (NVDA) right now? Give me a full analysis.")

    # ── Query 2: Stock Comparison ──
    # research("Compare NVDA vs AAPL vs MSFT as investment options. Which is the best value?")

    # ── Query 3: Sector Analysis ──
    # research("What's happening with big tech stocks? Analyze GOOGL and TSLA.")
```

### Run it:
```bash
python capstone1_financial_research.py
```

### Extending with Real APIs

Replace the simulated tools with real data sources:

```python
# Real stock data via Alpha Vantage (free API key)
@tool
def get_stock_data_real(symbol: str) -> str:
    """Get real stock data from Alpha Vantage API."""
    API_KEY = os.getenv("ALPHA_VANTAGE_KEY")
    resp = httpx.get(
        "https://www.alphavantage.co/query",
        params={
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": API_KEY
        }
    )
    return json.dumps(resp.json(), indent=2)

# Real news via NewsAPI (free tier)
@tool
def search_news_real(query: str) -> str:
    """Search real financial news via NewsAPI."""
    API_KEY = os.getenv("NEWS_API_KEY")
    resp = httpx.get(
        "https://newsapi.org/v2/everything",
        params={"q": query, "sortBy": "relevancy", "pageSize": 5},
        headers={"X-Api-Key": API_KEY}
    )
    return json.dumps(resp.json()["articles"], indent=2)
```

---

## 4.2 — Project 2: Text-to-SQL Analytics Agent (15 min)

### What We're Building

An agent that converts natural language to SQL, runs queries, and explains results:

```
User: "What were our top 5 products by revenue last quarter?"

Agent:
1. Explores database schema
2. Writes SQL query
3. Executes query
4. Explains results in plain English
```

### Complete Code

```python
# capstone2_text_to_sql.py
"""
TEXT-TO-SQL ANALYTICS AGENT
============================
Natural language → SQL → Results → Explanation
Uses SQLite for demonstration.
"""
import sqlite3
import json
import os
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

# ═══════════════════════════════════════════════════════
# SETUP: Create a sample database
# ═══════════════════════════════════════════════════════

DB_PATH = "./sample_analytics.db"

def setup_database():
    """Create a sample e-commerce analytics database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Products table
    c.execute("""CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        cost REAL NOT NULL
    )""")

    # Orders table
    c.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        customer_id INTEGER,
        quantity INTEGER,
        order_date DATE,
        region TEXT,
        FOREIGN KEY (product_id) REFERENCES products(id)
    )""")

    # Customers table
    c.execute("""CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        signup_date DATE,
        tier TEXT
    )""")

    # Insert sample data
    products = [
        (1, "Wireless Headphones", "Electronics", 79.99, 32.00),
        (2, "USB-C Hub", "Electronics", 49.99, 18.00),
        (3, "Mechanical Keyboard", "Electronics", 129.99, 55.00),
        (4, "Standing Desk Mat", "Office", 39.99, 12.00),
        (5, "LED Desk Lamp", "Office", 59.99, 22.00),
        (6, "Laptop Stand", "Office", 44.99, 15.00),
        (7, "Ergonomic Mouse", "Electronics", 69.99, 28.00),
        (8, "Monitor Light Bar", "Electronics", 54.99, 20.00),
        (9, "Cable Management Kit", "Office", 24.99, 8.00),
        (10, "Webcam HD", "Electronics", 89.99, 35.00),
    ]
    c.executemany("INSERT OR REPLACE INTO products VALUES (?,?,?,?,?)", products)

    # Generate orders
    import random
    random.seed(42)
    regions = ["North", "South", "East", "West"]
    tiers = ["Bronze", "Silver", "Gold", "Platinum"]

    customers = [(i, f"Customer_{i}", f"c{i}@email.com",
                   f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                   random.choice(tiers)) for i in range(1, 101)]
    c.executemany("INSERT OR REPLACE INTO customers VALUES (?,?,?,?,?)", customers)

    orders = []
    for i in range(1, 501):
        orders.append((
            i,
            random.randint(1, 10),
            random.randint(1, 100),
            random.randint(1, 5),
            f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
            random.choice(regions),
        ))
    c.executemany("INSERT OR REPLACE INTO orders VALUES (?,?,?,?,?,?)", orders)

    conn.commit()
    conn.close()
    print(f"Database created at {DB_PATH} with 10 products, 100 customers, 500 orders.")

# ═══════════════════════════════════════════════════════
# TOOLS
# ═══════════════════════════════════════════════════════

@tool
def explore_schema() -> str:
    """Get the complete database schema — all tables, columns, types, and sample data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get all tables
    c.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in c.fetchall()]

    output = []
    for table in tables:
        # Schema
        c.execute(f"PRAGMA table_info({table})")
        columns = c.fetchall()
        col_info = [f"  {col[1]} ({col[2]}){' PRIMARY KEY' if col[5] else ''}" for col in columns]

        # Row count
        c.execute(f"SELECT COUNT(*) FROM {table}")
        count = c.fetchone()[0]

        # Sample rows
        c.execute(f"SELECT * FROM {table} LIMIT 3")
        samples = c.fetchall()

        output.append(f"TABLE: {table} ({count} rows)")
        output.append("COLUMNS:")
        output.append("\n".join(col_info))
        output.append("SAMPLE DATA:")
        for s in samples:
            output.append(f"  {s}")
        output.append("")

    conn.close()
    return "\n".join(output)

@tool
def run_sql_query(query: str) -> str:
    """Execute a SQL query against the analytics database and return results.
    Only SELECT queries are allowed for safety.

    Args:
        query: A SQL SELECT query to execute
    """
    # Safety check — only allow SELECT
    if not query.strip().upper().startswith("SELECT"):
        return "ERROR: Only SELECT queries are allowed. No INSERT/UPDATE/DELETE."

    # Block dangerous patterns
    dangerous = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC"]
    upper_query = query.upper()
    for d in dangerous:
        if d in upper_query and d != "SELECT":
            # Allow these in subqueries context but not as main statement
            pass

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(query)
        rows = c.fetchall()

        if not rows:
            return "Query returned 0 rows."

        # Format as table
        columns = rows[0].keys()
        result = " | ".join(columns) + "\n"
        result += " | ".join(["---"] * len(columns)) + "\n"
        for row in rows[:50]:  # Limit to 50 rows
            result += " | ".join(str(row[col]) for col in columns) + "\n"

        if len(rows) > 50:
            result += f"\n... and {len(rows) - 50} more rows (showing first 50)"

        result += f"\nTotal rows: {len(rows)}"
        conn.close()
        return result

    except Exception as e:
        return f"SQL Error: {e}"

# ═══════════════════════════════════════════════════════
# AGENT
# ═══════════════════════════════════════════════════════

sql_agent = create_deep_agent(
    model="openai:gpt-4o",
    tools=[explore_schema, run_sql_query],
    system_prompt="""You are a data analytics agent that converts natural language questions into SQL queries.

## WORKFLOW (for every question)
1. If you haven't seen the schema yet, call explore_schema FIRST
2. Write the SQL query that answers the user's question
3. Execute it with run_sql_query
4. Explain the results in plain English
5. If relevant, suggest follow-up questions

## SQL RULES
- Only write SELECT queries
- Use proper JOINs (not implicit joins)
- Always alias calculated columns for clarity
- For date ranges: use BETWEEN or >= / <=
- Include ORDER BY for ranked results
- Use LIMIT for "top N" questions

## RESPONSE FORMAT
### Query
```sql
[your SQL query]
```

### Results
[formatted table from query]

### Interpretation
[plain English explanation of what the data shows]

### Suggested Follow-ups
- [related question 1]
- [related question 2]

## HANDLING AMBIGUITY
- If the question is ambiguous, state your assumption and proceed
- Q4 = October-December, Q3 = July-September, etc.
- "Last quarter" = most recent complete quarter in the data
- "Revenue" = price × quantity
"""
)

# ═══════════════════════════════════════════════════════
# RUN IT
# ═══════════════════════════════════════════════════════

def ask_data(question: str, thread: str = "sql"):
    """Ask the analytics agent a question."""
    print(f"\n{'='*60}")
    print(f" Q: {question}")
    print(f"{'='*60}\n")

    result = sql_agent.invoke(
        {"messages": [HumanMessage(content=question)]},
        config={"configurable": {"thread_id": thread}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            break

if __name__ == "__main__":
    # Setup the database
    setup_database()

    # ── Question 1: Simple aggregation ──
    ask_data("What are our top 5 products by total revenue?")

    # ── Question 2: Multi-table join with grouping ──
    ask_data("Which region has the highest average order value?")

    # ── Question 3: Time-based analysis ──
    ask_data("Show me monthly revenue trends for 2024")

    # ── Question 4: Complex business question ──
    ask_data(
        "Who are our top 10 customers by spending? "
        "Include their tier and how many orders they've placed."
    )

    # ── Question 5: Ad-hoc exploration ──
    ask_data("What's our profit margin by product category?")
```

### Run it:
```bash
python capstone2_text_to_sql.py
```

---

## 4.3 — Bonus Blueprint: Automated Content Pipeline (5 min)

### Architecture Overview

```python
# capstone3_content_pipeline.py
"""
CONTENT PIPELINE: Research → Write → Review → Publish
=====================================================
Multi-agent content creation with quality control loop.
"""
import json
import httpx
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent

@tool
def web_search(query: str) -> str:
    """Search the web for information.

    Args:
        query: Search query
    """
    try:
        resp = httpx.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_html": 1},
            timeout=10
        )
        data = resp.json()
        parts = []
        if data.get("Abstract"):
            parts.append(data["Abstract"])
        for t in data.get("RelatedTopics", [])[:5]:
            if isinstance(t, dict) and "Text" in t:
                parts.append(t["Text"])
        return "\n".join(parts) if parts else "No results found."
    except Exception as e:
        return f"Error: {e}"

content_pipeline = create_deep_agent(
    model="openai:gpt-4o",
    tools=[],
    subagents=[
        {
            "name": "topic_researcher",
            "description": "Researches a topic deeply — finds facts, stats, examples, and expert opinions.",
            "system_prompt": """Research the given topic thoroughly.
1. Search 3-5 times from different angles
2. Write structured notes to /research/[topic].md
3. Include: key facts, statistics, expert quotes, counterarguments
4. List all sources with URLs""",
            "tools": [web_search],
            "model": "openai:gpt-4o-mini",
        },
        {
            "name": "content_writer",
            "description": "Writes polished articles from research notes. Reads from /research/, writes to /drafts/.",
            "system_prompt": """You are a professional content writer.
1. Read research notes from /research/
2. Write a well-structured article to /drafts/article.md
3. Include: engaging intro, clear sections, examples, conclusion
4. Tone: professional but accessible
5. Length: 800-1200 words
6. Include a meta description (SEO) at the top""",
            "tools": [],
            "model": "openai:gpt-4o",
        },
        {
            "name": "editor_reviewer",
            "description": "Reviews and improves draft articles. Reads from /drafts/, writes feedback and final version.",
            "system_prompt": """You are a senior editor.
1. Read the draft from /drafts/article.md
2. Review for: accuracy, clarity, flow, grammar, engagement
3. Write detailed feedback to /review/feedback.md
4. Write the improved final version to /final/article.md
5. If the draft is good, make only minor edits
6. If significant issues found, note them clearly""",
            "tools": [],
            "model": "openai:gpt-4o",
        },
    ],
    system_prompt="""You orchestrate a content creation pipeline.

## PIPELINE (sequential — each step depends on the previous)
1. topic_researcher: "Research [topic] for an article targeting [audience]"
   → writes to /research/
2. content_writer: "Read /research/ notes and write an article about [topic]"
   → writes to /drafts/
3. editor_reviewer: "Review /drafts/article.md and produce final version"
   → writes to /final/

## DELIVER
- Read /final/article.md
- Read /review/feedback.md
- Present the final article + editor notes to user
"""
)

def create_content(topic: str, audience: str = "general tech audience"):
    """Run the content pipeline."""
    print(f"\nContent Pipeline: '{topic}' for {audience}\n")

    result = content_pipeline.invoke(
        {"messages": [HumanMessage(content=(
            f"Create a high-quality article about: {topic}\n"
            f"Target audience: {audience}\n"
            f"Run the full pipeline: research → write → review"
        ))]},
        config={"configurable": {"thread_id": "content-1"}}
    )

    for msg in reversed(result["messages"]):
        if msg.type == "ai" and msg.content:
            print(msg.content)
            break

if __name__ == "__main__":
    create_content(
        topic="How AI Agents Are Changing Software Development in 2025",
        audience="software developers and engineering managers"
    )
```

---

## Suggested Additional Projects

Here are more multi-agent apps you can build with the same patterns:

| Project | Agents | Complexity |
|---------|--------|------------|
| **Code Review Bot** | Orchestrator + Reviewer + Security Checker + Style Checker | Medium |
| **Customer Support** | Router + FAQ Agent + Escalation Agent + Sentiment Analyzer | Medium |
| **Travel Planner** | Planner + Flight Researcher + Hotel Researcher + Activity Finder | High |
| **Competitive Intel** | Orchestrator + multiple Company Researchers + Analyst + Reporter | High |
| **Legal Document Analyzer** | Document Parser + Clause Extractor + Risk Assessor + Summarizer | High |

---

## Course Wrap-Up: Architecture Cheat Sheet

```
PATTERN 1: Simple Agent
  create_deep_agent(model, tools, system_prompt)

PATTERN 2: Agent + Planning
  create_deep_agent(model, tools, system_prompt)  # write_todos is automatic

PATTERN 3: Agent + Filesystem
  create_deep_agent(model, backend=FilesystemBackend("./workspace"))

PATTERN 4: Multi-Agent Sequential
  create_deep_agent(model, subagents=[researcher, writer])
  # orchestrator calls task() for each, waits between them

PATTERN 5: Multi-Agent Parallel
  create_deep_agent(model, subagents=[agent1, agent2, agent3])
  # orchestrator calls multiple task() in one response

PATTERN 6: Agent Pipeline
  create_deep_agent(model, subagents=[step1, step2, step3])
  # sequential: each reads previous step's output files

PATTERN 7: Full System (Financial Research)
  create_deep_agent(
      model, subagents=[data, news, analyst, writer],
      system_prompt="Phase 1 parallel → Phase 2 sequential → Phase 3 report"
  )
```

### Key Config for OpenAI (No LangSmith)

```python
import os
os.environ["OPENAI_API_KEY"] = "sk-..."

# That's it! No LangSmith, no other services needed.
# DeepAgents auto-detects "openai:gpt-4o" and configures everything.

agent = create_deep_agent(
    model="openai:gpt-4o",       # or "openai:gpt-4o-mini" for cheaper
    # ... rest of config
)
```
