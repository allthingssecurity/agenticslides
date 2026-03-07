"""
LAB 5 — CAPSTONE: Text-to-SQL Analytics Agent (Module 4)
==========================================================
Natural language → SQL → Results → Explanation

The agent:
1. Explores the database schema automatically
2. Converts your question to SQL
3. Executes the query (read-only for safety)
4. Explains results in plain English
5. Suggests follow-up questions

Includes: sample e-commerce database with products, orders, customers.

Run: python lab5_text_to_sql.py
"""
import sqlite3
import json
import os
import random
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from deepagents import create_deep_agent
from trace_utils import run_with_trace, interactive_mode


# ═════════════════════════════════════════════════════════
# DATABASE SETUP
# ═════════════════════════════════════════════════════════

DB_PATH = os.path.join(os.path.dirname(__file__), "sample_analytics.db")


def setup_database():
    """Create a realistic e-commerce analytics database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Drop existing tables for clean setup
    c.execute("DROP TABLE IF EXISTS orders")
    c.execute("DROP TABLE IF EXISTS customers")
    c.execute("DROP TABLE IF EXISTS products")

    # Products
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

    # Customers
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

    random.seed(42)
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

    # Orders
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
                "shipped", "processing", "returned"]  # 4:1:1:1 ratio

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


# ═════════════════════════════════════════════════════════
# TOOLS
# ═════════════════════════════════════════════════════════

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

        # Foreign keys
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

        # Format header
        header = " | ".join(f"{col:<{widths[col]}}" for col in columns)
        separator = " | ".join("-" * widths[col] for col in columns)

        # Format rows
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


# ═════════════════════════════════════════════════════════
# AGENT
# ═════════════════════════════════════════════════════════

sql_agent = create_deep_agent(
    model="openai:gpt-4o-mini",
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
- Format dates consistently

## RESPONSE FORMAT
**Query:**
```sql
SELECT ...
```

**Results:**
[table output]

**Interpretation:**
[plain English explanation — what does this data mean for the business?]

**Follow-up Questions:**
- [related question 1]
- [related question 2]

## HANDLING AMBIGUITY
- "Revenue" = products.price × orders.quantity
- "Profit" = (products.price - products.cost) × orders.quantity
- "This year" / "2024" = use WHERE order_date BETWEEN '2024-01-01' AND '2024-12-31'
- "Q1" = Jan-Mar, "Q2" = Apr-Jun, "Q3" = Jul-Sep, "Q4" = Oct-Dec
- "Top customers" = by total spending unless specified otherwise
- State your assumptions when the question is ambiguous
"""
)


# ═════════════════════════════════════════════════════════
# RUN IT
# ═════════════════════════════════════════════════════════

def ask_data(question: str, thread: str = "sql-lab"):
    """Ask the analytics agent a question about the data."""
    run_with_trace(sql_agent, question, thread_id=thread)


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║  CAPSTONE 2: Text-to-SQL Analytics Agent                 ║
║  Ask questions in English → Get SQL + results + insights ║
╚══════════════════════════════════════════════════════════╝
    """)

    # Setup the database
    setup_database()

    # ── Q1: Revenue analysis ──
    ask_data("What are our top 5 products by total revenue?")

    # ── Q2: Regional performance ──
    ask_data("Which region generates the most revenue? Break it down by region.")

    # ── Q3: Customer segmentation ──
    ask_data(
        "Who are our top 10 customers by total spending? "
        "Show their tier, city, and number of orders."
    )

    # ── Q4: Time trends ──
    ask_data("Show me monthly revenue and order count trends for 2024.")

    # ── Q5: Profitability ──
    ask_data(
        "What's our profit margin by product category? "
        "Which category is most profitable?"
    )

    # ── Q6: Complex business question ──
    ask_data(
        "Compare Platinum vs Bronze tier customers: "
        "average order value, total orders, total revenue. "
        "Are Platinum customers actually more valuable?"
    )

    print(f"\n{'='*60}")
    print(" CAPSTONE 2 COMPLETE!")
    print("=" * 60)
    print("""
    WHAT THE AGENT DID:
    ✓ Auto-explored database schema (tables, columns, relationships)
    ✓ Converted natural language → SQL queries
    ✓ Executed queries safely (read-only)
    ✓ Explained results in business terms
    ✓ Suggested follow-up questions

    THE AGENT HANDLED:
    • Simple aggregations (top products)
    • Multi-table JOINs (customers + orders + products)
    • Time-series analysis (monthly trends)
    • Calculated metrics (profit margins)
    • Customer segmentation comparisons

    EXTENSION IDEAS:
    - Add a visualization tool (matplotlib/plotly)
    - Add a "save report" tool that writes analysis to files
    - Make it a multi-agent: SQL Writer + Data Interpreter + Recommender

    NEXT: python lab6_content_pipeline.py (Bonus!)
    """)

    interactive_mode(sql_agent, "Lab 5: Text-to-SQL", thread_id="sql-lab")
