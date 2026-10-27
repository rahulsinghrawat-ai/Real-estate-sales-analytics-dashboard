"""
Clean, validate and transform raw lead records for analysis.

Input : data/raw_leads.csv, data/agents.csv
Output: data/cleaned_leads.csv, data/cleaned_agents.csv,
        data/validation_report.txt

Usage:
    python python/clean_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

RAW_LEADS = DATA / "raw_leads.csv"
RAW_AGENTS = DATA / "agents.csv"
OUT_LEADS = DATA / "cleaned_leads.csv"
OUT_AGENTS = DATA / "cleaned_agents.csv"
REPORT = DATA / "validation_report.txt"

FOLLOW_UP_STALE_DAYS = 14
MIN_AREA, MAX_AREA = 100, 20000

CITY_ALIASES = {
    "bangalore": "Bengaluru",
    "bengaluru": "Bengaluru",
    "new delhi": "Delhi",
    "gurgaon": "Gurugram",
    "gurugram": "Gurugram",
}

CITY_REGION = {
    "Mumbai": "West", "Pune": "West", "Ahmedabad": "West",
    "Delhi": "North", "Gurugram": "North", "Noida": "North",
    "Bengaluru": "South", "Chennai": "South", "Hyderabad": "South",
    "Kolkata": "East",
}

STATUS_CANONICAL = {
    "new": "New",
    "contacted": "Contacted",
    "qualified": "Qualified",
    "negotiation": "Negotiation",
    "closed won": "Closed Won",
    "won": "Closed Won",
    "closed lost": "Closed Lost",
    "lost": "Closed Lost",
}

OPEN_STATUSES = {"New", "Contacted", "Qualified", "Negotiation"}


def standardise_city(series: pd.Series) -> pd.Series:
    cleaned = series.str.strip().str.lower()
    cleaned = cleaned.map(lambda c: CITY_ALIASES.get(c, c) if isinstance(c, str) else c)
    return cleaned.str.title()


def standardise_status(series: pd.Series) -> pd.Series:
    return series.str.strip().str.lower().map(STATUS_CANONICAL)


def clean_leads(raw: pd.DataFrame, log: dict) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]
    log["raw_rows"] = len(df)

    # 1. Exact and key duplicates
    before = len(df)
    df = df.drop_duplicates().drop_duplicates(subset="Lead_ID", keep="first")
    log["duplicates_removed"] = before - len(df)

    # 2. Dates
    df["Lead_Date"] = pd.to_datetime(df["Lead_Date"], errors="coerce")
    df["Closed_Date"] = pd.to_datetime(df["Closed_Date"], errors="coerce")
    df["Last_Follow_Up_Date"] = pd.to_datetime(df["Last_Follow_Up_Date"], errors="coerce")
    before = len(df)
    df = df[df["Lead_Date"].notna()]
    log["missing_lead_date_removed"] = before - len(df)

    # 3. Categorical standardisation
    df["City"] = standardise_city(df["City"].astype("string"))
    df["Lead_Status"] = standardise_status(df["Lead_Status"].astype("string"))
    before = len(df)
    df = df[df["City"].notna() & df["Lead_Status"].notna()]
    log["unmapped_city_or_status_removed"] = before - len(df)

    df["Lead_Source"] = df["Lead_Source"].fillna("Unknown").str.strip()
    # pandas reads the text "NA" as missing; label plots explicitly instead
    df["BHK"] = df["BHK"].fillna("Not Applicable")
    df["Region"] = df["City"].map(CITY_REGION).fillna("Other")

    # 4. Numeric validation
    for col in ["Area_SqFt", "Quoted_Price", "Deal_Value", "Follow_Ups"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    invalid_area = ~df["Area_SqFt"].between(MIN_AREA, MAX_AREA)
    log["invalid_area_flagged"] = int(invalid_area.sum())
    df = df[~invalid_area]

    before = len(df)
    df = df[df["Quoted_Price"].notna() & (df["Quoted_Price"] > 0)]
    log["missing_quoted_price_removed"] = before - len(df)

    df["Follow_Ups"] = df["Follow_Ups"].fillna(0).astype(int)

    # 5. Status flags
    df["Is_Won"] = (df["Lead_Status"] == "Closed Won").astype(int)
    df["Is_Lost"] = (df["Lead_Status"] == "Closed Lost").astype(int)
    df["Is_Open"] = df["Lead_Status"].isin(OPEN_STATUSES).astype(int)

    # 6. Deal value: won deals missing a value are imputed from quoted price, and flagged
    won_missing = (df["Is_Won"] == 1) & df["Deal_Value"].isna()
    log["won_deals_missing_value_imputed"] = int(won_missing.sum())
    df["Deal_Value_Imputed"] = won_missing.astype(int)
    df.loc[won_missing, "Deal_Value"] = df.loc[won_missing, "Quoted_Price"]
    df["Revenue_Won"] = np.where(df["Is_Won"] == 1, df["Deal_Value"], 0.0)

    # 7. Derived metrics
    df["Price_per_SqFt"] = (df["Quoted_Price"] / df["Area_SqFt"]).round(2)
    df["Days_to_Close"] = (df["Closed_Date"] - df["Lead_Date"]).dt.days
    df.loc[df["Is_Open"] == 1, "Days_to_Close"] = np.nan
    df["Days_to_Close"] = df["Days_to_Close"].astype("Int64")  # whole numbers, blank when open

    # Reporting "as of" date: latest activity in the dataset
    as_of = pd.concat([df["Lead_Date"], df["Closed_Date"], df["Last_Follow_Up_Date"]]).max()
    log["as_of_date"] = as_of.date().isoformat()

    df["Days_Since_Follow_Up"] = (as_of - df["Last_Follow_Up_Date"]).dt.days.astype("Int64")

    def follow_up_status(row) -> str:
        if row["Is_Open"] == 0:
            return "Closed"
        if row["Follow_Ups"] == 0 or pd.isna(row["Last_Follow_Up_Date"]):
            return "Never Followed Up"
        if row["Days_Since_Follow_Up"] > FOLLOW_UP_STALE_DAYS:
            return f"Stale (>{FOLLOW_UP_STALE_DAYS} days)"
        return "Active"

    df["Follow_Up_Status"] = df.apply(follow_up_status, axis=1)

    df["Lead_Month"] = df["Lead_Date"].dt.to_period("M").dt.to_timestamp()
    df["Lead_Year"] = df["Lead_Date"].dt.year
    df["Lead_Quarter"] = "Q" + df["Lead_Date"].dt.quarter.astype(str) + "-" + df["Lead_Year"].astype(str)

    log["clean_rows"] = len(df)
    return df


def clean_agents(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [c.strip() for c in df.columns]
    df["Agent_Name"] = df["Agent_Name"].str.strip().str.title()
    df["Hire_Date"] = pd.to_datetime(df["Hire_Date"], errors="coerce")
    return df.drop_duplicates(subset="Agent_ID")


LEAD_COLUMN_ORDER = [
    "Lead_ID", "Lead_Date", "Agent_ID", "City", "Region", "Property_Type", "BHK",
    "Area_SqFt", "Quoted_Price", "Lead_Source", "Lead_Status", "Follow_Ups",
    "Last_Follow_Up_Date", "Closed_Date", "Deal_Value", "Deal_Value_Imputed",
    "Revenue_Won", "Is_Won", "Is_Lost", "Is_Open", "Price_per_SqFt", "Days_to_Close",
    "Days_Since_Follow_Up", "Follow_Up_Status", "Lead_Month", "Lead_Year", "Lead_Quarter",
]

AGENT_COLUMN_ORDER = ["Agent_ID", "Agent_Name", "Team", "Hire_Date"]


def snake_case(df: pd.DataFrame, order: list) -> pd.DataFrame:
    df = df[order].copy()
    df.columns = [c.lower() for c in df.columns]
    return df


def write_report(log: dict, leads: pd.DataFrame, agents: pd.DataFrame, raw_agent_count: int) -> None:
    lines = [
        "VALIDATION REPORT - Real Estate Lead Funnel",
        "=" * 46,
        f"Raw lead rows              : {log['raw_rows']}",
        f"Duplicates removed         : {log['duplicates_removed']}",
        f"Missing lead date removed  : {log['missing_lead_date_removed']}",
        f"Unmapped city/status removed: {log['unmapped_city_or_status_removed']}",
        f"Invalid area removed       : {log['invalid_area_flagged']}",
        f"Missing quoted price removed: {log['missing_quoted_price_removed']}",
        f"Won deals with value imputed: {log['won_deals_missing_value_imputed']}",
        f"Clean lead rows            : {log['clean_rows']}",
        f"Rows dropped in total      : {log['raw_rows'] - log['clean_rows']}",
        "",
        f"As-of date (for follow-up ageing): {log['as_of_date']}",
        f"Agents raw / clean         : {raw_agent_count} / {len(agents)}",
        "",
        "Integrity checks",
        "-" * 16,
        f"Unique Lead_IDs            : {leads['Lead_ID'].is_unique}",
        f"All Agent_IDs exist        : {leads['Agent_ID'].isin(agents['Agent_ID']).all()}",
        f"Won deals have a value     : {(leads.loc[leads['Is_Won'] == 1, 'Deal_Value'].notna()).all()}",
        f"Closed leads have close date: {leads.loc[leads['Is_Open'] == 0, 'Closed_Date'].notna().all()}",
        f"Open leads have no close date: {leads.loc[leads['Is_Open'] == 1, 'Closed_Date'].isna().all()}",
        "",
        "Cities after standardisation:",
        ", ".join(sorted(leads["City"].unique())),
        "",
        "Lead status distribution:",
        leads["Lead_Status"].value_counts().to_string(),
        "",
        "Follow-up status (open leads only):",
        leads.loc[leads["Is_Open"] == 1, "Follow_Up_Status"].value_counts().to_string(),
    ]
    REPORT.write_text("\n".join(lines) + "\n")


def main() -> None:
    raw_leads = pd.read_csv(RAW_LEADS)
    raw_agents = pd.read_csv(RAW_AGENTS)

    log: dict = {}
    leads = clean_leads(raw_leads, log)
    agents = clean_agents(raw_agents)

    # Keep only leads whose agent exists in the agent table
    before = len(leads)
    leads = leads[leads["Agent_ID"].isin(agents["Agent_ID"])]
    log["orphan_agent_removed"] = before - len(leads)
    log["clean_rows"] = len(leads)

    write_report(log, leads, agents, len(raw_agents))

    snake_case(leads, LEAD_COLUMN_ORDER).to_csv(OUT_LEADS, index=False)
    snake_case(agents, AGENT_COLUMN_ORDER).to_csv(OUT_AGENTS, index=False)

    print(f"Clean leads : {len(leads)} rows -> {OUT_LEADS.relative_to(ROOT)}")
    print(f"Clean agents: {len(agents)} rows -> {OUT_AGENTS.relative_to(ROOT)}")
    print(f"Report      : {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
