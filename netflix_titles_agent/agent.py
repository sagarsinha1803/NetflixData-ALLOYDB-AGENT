import os
import datetime
import decimal
import psycopg2
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from dotenv import load_dotenv

load_dotenv()

# ── Schema ────────────────────────────────────────────────────────────────────
SCHEMA = """
Table: netflix_titles
Columns:
  - show_id      TEXT        (primary key, e.g. 's1')
  - type         TEXT        ('Movie' or 'TV Show')
  - title        TEXT
  - director     TEXT        (may be NULL)
  - "cast"       TEXT        (comma-separated cast members, may be NULL)
  - country      TEXT        (may be NULL)
  - date_added   DATE        (date added to Netflix, may be NULL)
  - release_year SMALLINT
  - rating       TEXT        (e.g. PG-13, TV-MA, R, TV-14, PG — may be NULL)
  - duration     TEXT        ('90 min' for movies, '2 Seasons' for TV shows)
  - listed_in    TEXT        (comma-separated genres/categories)
  - description  TEXT

IMPORTANT NOTES:
  - "cast" must always be double-quoted in SQL because it is a reserved keyword in PostgreSQL.
  - Use ILIKE for all case-insensitive text searches.
  - date_added is a DATE column — use standard date comparisons (e.g. date_added >= '2020-01-01').
  - listed_in contains genres — use ILIKE '%Horror%' style to filter by genre.
  - duration contains the unit in the string — '90 min' for movies, '3 Seasons' for TV shows.
"""

# ── Tool: Execute SQL ─────────────────────────────────────────────────────────
def execute_sql_query(sql: str) -> dict:
    """
    Execute a SELECT SQL query against AlloyDB and return results.
    Args:
        sql: A valid PostgreSQL SELECT query
    Returns:
        dict with columns, rows, and row_count
    """
    clean_sql = sql.strip().rstrip(";")

    # ⛔ Block all write operations
    blocked_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", "ALTER", "CREATE"]
    for keyword in blocked_keywords:
        if keyword in clean_sql.upper():
            return {
                "error": f"❌ '{keyword}' operations are not allowed. This is a read-only database.",
                "columns": [],
                "rows": [],
                "row_count": 0
            }

    # ⛔ Only allow SELECT
    if not clean_sql.upper().startswith("SELECT"):
        return {
            "error": "❌ Only SELECT queries are allowed.",
            "columns": [],
            "rows": [],
            "row_count": 0
        }

    try:
        conn = psycopg2.connect(
            host=os.getenv("ALLOYDB_HOST"),
            port=int(os.getenv("ALLOYDB_PORT", "5432")),
            dbname=os.getenv("ALLOYDB_DATABASE"),
            user=os.getenv("ALLOYDB_USER"),
            password=os.getenv("ALLOYDB_PASSWORD"),
            sslmode="require"
        )
        cursor = conn.cursor()
        cursor.execute(clean_sql)
        columns = [desc[0] for desc in cursor.description]

        # Serialize every cell to a JSON-safe Python primitive.
        # psycopg2 returns non-standard types (datetime.date, decimal.Decimal,
        # numpy int subtypes for SMALLINT, memoryview for bytea, etc.) that
        # cause ADK's trace UI to throw "error parsing request".
        # Casting everything through str→native ensures clean JSON output.
        def _serialize(val):
            if val is None:
                return None
            if isinstance(val, bool):
                return val
            if isinstance(val, (datetime.date, datetime.datetime)):
                return val.isoformat()
            if isinstance(val, decimal.Decimal):
                return float(val)
            if isinstance(val, int):
                return int(val)       # coerce SMALLINT/BIGINT subtypes
            if isinstance(val, float):
                return float(val)
            return str(val)           # TEXT, UUID, enums, anything else

        rows = [[_serialize(cell) for cell in row] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return {
            "columns": columns,
            "rows": rows,
            "row_count": len(rows)
        }
    except Exception as e:
        return {
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0
        }


# ── Root Agent ────────────────────────────────────────────────────────────────
root_agent = Agent(
    name="netflix_query_agent",
    model="gemini-2.5-flash",
    description="Answers natural language questions about Netflix titles stored in AlloyDB.",
    instruction=f"""
You are a friendly Netflix data assistant powered by AlloyDB (PostgreSQL 15).

IMPORTANT RULES FOR TOOL USAGE:
- To query the database, you MUST call execute_sql_query directly
- NEVER wrap tool calls in print() or any other function
- NEVER use default_api prefix
- Just call: execute_sql_query(sql="YOUR SQL HERE")

You have access to this database schema:
{SCHEMA}

Your workflow for every user question:
1. Understand what the user is asking
2. Generate a valid PostgreSQL SELECT query based on the schema
3. Validate and apply these SQL rules:
   - Table name must always be: netflix_titles
   - Always double-quote the cast column: "cast"
   - Use ILIKE for case-insensitive text searches
   - For genre/category filtering use: listed_in ILIKE '%Drama%'
   - For date filtering use DATE comparisons: date_added >= '2020-01-01'
   - Add LIMIT 10 if no limit is specified
   - Only SELECT queries are allowed
4. Call execute_sql_query with the validated SQL
5. Present the results in a clear, friendly format with a brief summary

⛔ STRICT RULES:
- SELECT only — reject INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, CREATE
- Table name must be: netflix_titles
- "cast" must always be double-quoted
- Use ILIKE for text searches
- Add LIMIT 10 if not specified

Example queries you can handle:
- "Show me all horror movies"
  → SELECT show_id, title, listed_in FROM netflix_titles WHERE type = 'Movie' AND listed_in ILIKE '%Horror%' LIMIT 10
- "Which TV shows have more than 3 seasons?"
  → SELECT title, duration FROM netflix_titles WHERE type = 'TV Show' AND duration ILIKE '%Season%' AND CAST(split_part(duration, ' ', 1) AS INT) > 3 LIMIT 10
- "List all movies from South Korea"
  → SELECT title, release_year FROM netflix_titles WHERE type = 'Movie' AND country ILIKE '%South Korea%' LIMIT 10
- "Find content directed by Christopher Nolan"
  → SELECT title, type, release_year FROM netflix_titles WHERE director ILIKE '%Christopher Nolan%' LIMIT 10
- "What are the 5 most recently added titles?"
  → SELECT title, type, date_added FROM netflix_titles WHERE date_added IS NOT NULL ORDER BY date_added DESC LIMIT 5
- "Which country has the most Netflix titles?"
  → SELECT country, COUNT(*) AS total FROM netflix_titles WHERE country IS NOT NULL GROUP BY country ORDER BY total DESC LIMIT 10
- "Show me all TV-MA rated content"
  → SELECT title, type FROM netflix_titles WHERE rating = 'TV-MA' LIMIT 10
- "Who are the cast members in Inception?"
  → SELECT title, "cast" FROM netflix_titles WHERE title ILIKE '%Inception%' LIMIT 10
- "Delete all movies" → REJECT this

If no results are found, say so helpfully and suggest a related query.
Keep responses concise and easy to read.
""",
    tools=[FunctionTool(func=execute_sql_query)],
)