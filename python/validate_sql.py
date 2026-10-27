"""
Validate the SQL layer end-to-end without installing a database server.

Loads the cleaned CSVs into an in-memory SQLite database, runs schema.sql,
then executes every query in business_queries.sql and prints a preview.
Use this to confirm the SQL works before loading into PostgreSQL.

Usage:
    python python/validate_sql.py
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "sql" / "schema.sql"
QUERIES = ROOT / "sql" / "business_queries.sql"


def split_queries(sql_text: str) -> list[tuple[str, str]]:
    """Return (title, query) pairs, splitting on the '-- Qn.' headers."""
    chunks = re.split(r"^-- (Q\d+\.)", sql_text, flags=re.MULTILINE)
    pairs = []
    for i in range(1, len(chunks), 2):
        label = chunks[i]
        body = chunks[i + 1]
        lines = body.strip().splitlines()
        title = lines[0].strip()
        query = "\n".join(l for l in lines[1:] if not l.strip().startswith("--")).strip()
        pairs.append((f"{label} {title}", query))
    return pairs


def main() -> None:
    con = sqlite3.connect(":memory:")
    con.executescript(SCHEMA.read_text())

    pd.read_csv(ROOT / "data" / "cleaned_agents.csv").to_sql("agents", con, if_exists="append", index=False)
    pd.read_csv(ROOT / "data" / "cleaned_leads.csv").to_sql("leads", con, if_exists="append", index=False)
    print("Schema created and data loaded.\n")

    failures = 0
    for title, query in split_queries(QUERIES.read_text()):
        try:
            df = pd.read_sql_query(query, con)
            print(f"[OK]   {title}  ({len(df)} rows)")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"[FAIL] {title}: {exc}")

    print(f"\n{'All queries passed.' if failures == 0 else f'{failures} query(ies) failed.'}")


if __name__ == "__main__":
    main()
