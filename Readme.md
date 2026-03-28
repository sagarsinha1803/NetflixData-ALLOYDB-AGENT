Netflix AlloyDB Agent
A conversational AI agent built with Google Agent Development Kit (ADK) and Gemini 2.5 Flash that answers natural language questions about Netflix titles stored in AlloyDB for PostgreSQL.

Overview
This agent translates plain English questions into SQL queries, executes them against an AlloyDB database, and returns results in a friendly, readable format. It is read-only — all write operations are blocked at the tool level.

Project Structure
NETFLIXDATA-ALLOYDB-AGENT/
├── netflix_titles_agent/
│   ├── __init__.py
│   ├── .env                        # Environment variables (not committed)
│   └── agent.py                    # Agent definition and SQL tool
├── .adk/                           # ADK config (not committed)
├── .venv/                          # Virtual environment (not committed)
├── .gitignore
├── netflix_titles_create_table.sql # AlloyDB schema
├── netflix_titles_dataset.sql      # INSERT statements for dataset
├── requirements.txt
└── README.md

Prerequisites

Python 3.11+
A running AlloyDB for PostgreSQL instance
A Google Cloud project with the Gemini API enabled
google-adk installed


Setup
1. Clone the repository
bashgit clone <your-repo-url>
cd NETFLIXDATA-ALLOYDB-AGENT
2. Create and activate a virtual environment
bashpython -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows
3. Install dependencies
bashpip install -r requirements.txt
4. Configure environment variables
Create a .env file inside the netflix_titles_agent/ folder:
envALLOYDB_HOST=<your-alloydb-host-ip>
ALLOYDB_PORT=5432
ALLOYDB_DATABASE=<your-database-name>
ALLOYDB_USER=<your-db-user>
ALLOYDB_PASSWORD=<your-db-password>
GOOGLE_API_KEY=<your-gemini-api-key>
5. Set up the database
Run the SQL files against your AlloyDB instance in order:
bashpsql -h $ALLOYDB_HOST -U $ALLOYDB_USER -d $ALLOYDB_DATABASE -f netflix_titles_create_table.sql
psql -h $ALLOYDB_HOST -U $ALLOYDB_USER -d $ALLOYDB_DATABASE -f netflix_titles_dataset.sql

Running the Agent
bashadk web
Then open http://localhost:8000 in your browser and select netflix_titles_agent from the dropdown.

Database Schema
ColumnTypeNotesshow_idTEXTPrimary key (e.g. s1)typeTEXTMovie or TV ShowtitleTEXTdirectorTEXTNullable"cast"TEXTComma-separated, nullable. Double-quoted — reserved keyword in PostgreSQLcountryTEXTNullabledate_addedDATEISO 8601, nullablerelease_yearSMALLINTratingTEXTe.g. TV-MA, PG-13, nullabledurationTEXT90 min for movies, 2 Seasons for TV showslisted_inTEXTComma-separated genresdescriptionTEXT

Example Questions
QuestionWhat it does"Show me all horror movies"Filters by listed_in ILIKE '%Horror%' and type = 'Movie'"Which TV shows have more than 3 seasons?"Parses duration string and filters"List all movies from South Korea"Filters by country ILIKE '%South Korea%'"Find content directed by Christopher Nolan"Searches director column"What are the 5 most recently added titles?"Orders by date_added DESC LIMIT 5"Which country has the most Netflix titles?"Groups by country, counts, orders"Who are the cast members in Inception?"Selects "cast" column by title

Security
The execute_sql_query tool enforces strict read-only access:

Only SELECT statements are permitted
Any query containing INSERT, UPDATE, DELETE, DROP, TRUNCATE, ALTER, or CREATE is blocked before execution
AlloyDB connection uses sslmode=require


Tech Stack

Google ADK — Agent Development Kit
Gemini 2.5 Flash — LLM
AlloyDB for PostgreSQL — Database
psycopg2 — PostgreSQL adapter
python-dotenv — Environment config