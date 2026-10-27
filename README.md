# Real Estate Sales Analytics Dashboard

I built this project to answer a simple question a sales head would ask: where is our effort turning into revenue, and where is it leaking? It takes raw lead records from a CRM-style export, cleans them in Python, models them in SQL, and presents the results in a Power BI dashboard with DAX measures.

**Tools:** Python (Pandas) · PostgreSQL · Power BI · DAX · Excel

---

## The Problem

A brokerage wants to know four things:

1. **Funnel:** Where do leads get stuck, and which sources actually produce deals?
2. **Regions:** Which regions and cities bring in revenue, and where does conversion fall behind?
3. **Pipeline:** How much open business has gone cold because nobody followed up?
4. **People:** Which agents and property types convert best?

---

## Dashboard

![Yearly overview](images/DASHBOARD%20YEARLY.png)

![East region view](images/EAST%20REGION.png)

---

## About the Data

The data is a **sample dataset I generated** to behave like a real CRM export: 6,120 lead records across 10 Indian cities, 4 property types, and 25 agents, covering January 2025 to September 2026. I deliberately left in the kind of mess real exports have, such as duplicate rows, inconsistent city spellings, impossible areas, missing prices, and mixed-case status labels. Cleaning those is most of the work, and the cleaning script logs every change.

Because the data is synthetic, the numbers show the method and how to read it. They are not market findings.

---

## Project Structure

```text
real-estate-sales-analytics-dashboard/
├── data/
│   ├── raw_leads.csv              raw export, including messy records
│   ├── agents.csv                 agent roster
│   ├── cleaned_leads.csv          output of clean_data.py
│   ├── cleaned_agents.csv         output of clean_data.py
│   └── validation_report.txt      log of every cleaning step
├── python/
│   ├── clean_data.py              cleaning, validation, derived columns
│   ├── validate_sql.py            runs the schema and all queries to check them
│   └── generate_sample_data.py    recreates the sample dataset
├── sql/
│   ├── schema.sql                 tables, indexes and a monthly KPI view
│   └── business_queries.sql       11 business questions
├── powerbi/
│   ├── RealEstate_Dashboard.pbix  the dashboard
│   ├── DAX_measures.dax           all measures
│   └── BUILD_GUIDE.md             how the dashboard is laid out
├── excel/
│   ├── Real_Estate_Analysis.xlsx  summary workbook with live formulas
│   └── build_excel_summary.py     rebuilds the workbook
├── docs/
│   └── BEGINNER_GUIDE.md          step-by-step setup guide
├── images/                        dashboard screenshots
├── requirements.txt
└── README.md
```

---

## Running It

You need Python 3.10 or newer. Then, from the project folder:

```bash
pip install -r requirements.txt
python python/clean_data.py
python python/validate_sql.py
python excel/build_excel_summary.py
```

The first command produces the cleaned data. The second runs every SQL query against a small test database, so you can see they work without installing PostgreSQL. The third rebuilds the Excel workbook.

To load the data into PostgreSQL:

```bash
psql -d real_estate -f sql/schema.sql
psql -d real_estate -c "\copy agents FROM 'data/cleaned_agents.csv' WITH (FORMAT csv, HEADER true)"
psql -d real_estate -c "\copy leads FROM 'data/cleaned_leads.csv' WITH (FORMAT csv, HEADER true)"
```

Open `powerbi/RealEstate_Dashboard.pbix` in Power BI Desktop, or follow `powerbi/BUILD_GUIDE.md` to build it yourself. `docs/BEGINNER_GUIDE.md` covers setup from scratch.

---

## What the Cleaning Did

| Step | Rule | Rows affected |
|---|---|---|
| Remove duplicates | Same Lead_ID appears more than once | 120 removed |
| Standardise cities | "Bangalore" becomes Bengaluru, "gurgaon" becomes Gurugram | Mapped |
| Standardise status | "won" becomes Closed Won, "lost" becomes Closed Lost | Mapped |
| Check areas | Keep only 100 to 20,000 sq ft | 91 removed |
| Check prices | Quoted price must be present and positive | 116 removed |
| Fill deal values | Won deals with no value use the quoted price, flagged in `deal_value_imputed` | 57 filled |

Result: 6,120 raw rows became 5,793 clean rows. The validation report confirms every Lead_ID is unique and every lead links to a real agent.

---

## How I Measure It

- **Closed win rate:** won deals divided by all closed deals (won plus lost). I use this for comparisons because it ignores deals still in progress.
- **Lead conversion rate:** won deals divided by all leads. This is the funnel view, and it looks lower while many leads are still open.
- **Revenue won:** the deal value of every won lead.
- **Pipeline at risk:** open leads with no follow-up in the last 14 days, or never followed up, as a share of open leads.
- **Days to close:** time from lead date to closed date, for closed leads only.

---

## What the Data Says

**The pipeline is going cold.** There are 1,422 open leads worth ₹2,946 crore. Of those, 1,160 leads (81.6%, about ₹2,401 crore) have either gone 14+ days without a follow-up or never had one. This is the most urgent problem in the data, and it's where I would start.

**Referrals and walk-ins win the most.** Referral leads close at 32.8% and walk-ins at 30.8%. Cold calls close at 16.1%, about half the referral rate. If the goal is more deals per rupee of effort, referrals are the place to spend it.

**North makes the money, East converts best.** North brings in ₹810 crore, the most of any region. East has the highest win rate at 28.7%, but also the fewest leads, so it is under-used. Adding lead volume in East is worth testing.

**Big homes carry the deals, and small flats struggle.** A 5BHK villa averages about ₹7.4 crore per won deal, and a 4BHK about ₹4.4 crore. The weakest segment is 3BHK apartments: they make up a large share of leads but close at only 22.1%.

**Follow-up count alone doesn't predict a win.** Closed-deal win rate is roughly flat across follow-up bands (24.7% to 25.8%). The problem is not how often closed deals were chased, but how many open leads have been left alone. Sales cycles are steady at about 64 days across property types, so speed is not the lever.

---

## What I'd Do Next

1. Reassign or re-engage the 1,160 stale or untouched open leads, starting with the high-value Qualified and Negotiation ones.
2. Move spend toward referral programmes and walk-in capture.
3. Test extra lead generation in East.
4. Set a follow-up rule, for example no open lead goes more than 14 days without contact, and track it weekly.
5. Study how the top agents pitch 3BHK apartments, since that segment converts worst.

---

## Skills Shown

- Cleaning messy data in Pandas, with a log of every change
- SQL for joins, window functions (`RANK`, `LAG`), conditional aggregation, and views
- Power BI data modelling with a star schema and a date table
- DAX for measures, year-on-year and rolling calculations, and dynamic text
- Excel tables and formulas
- Turning numbers into specific recommendations
