# Power BI Build Guide

This guide walks through building `RealEstate_Dashboard.pbix` from the cleaned data.
Save the finished file as `powerbi/RealEstate_Dashboard.pbix`.

---

## 1. Connect to data

**Option A (quickest):** Get Data → Text/CSV → select `data/cleaned_leads.csv`, then repeat for `data/cleaned_agents.csv`.

**Option B (SQL, recommended for the portfolio):** Get Data → PostgreSQL database → server `localhost`, database `real_estate`. Select `leads` and `agents`. Use `vw_monthly_kpi` if you want a pre-aggregated monthly view.

Load both tables. In Power Query, confirm these types:

| Column | Type |
|---|---|
| lead_date, closed_date, last_follow_up_date, lead_month | Date |
| quoted_price, deal_value, revenue_won | Decimal / Fixed decimal |
| is_won, is_lost, is_open, deal_value_imputed | Whole number |

---

## 2. Data model

1. **Create the Calendar table** from `powerbi/DAX_measures.dax` (section 1, a calculated table).
2. **Mark it as the date table:** Table tools → Mark as date table → column `Date`.
3. **Relationships** (Model view):
   - `agents[agent_id]` (1) → `leads[agent_id]` (*) : single direction
   - `Calendar[Date]` (1) → `leads[lead_date]` (*) : single direction
4. Hide the foreign-key columns and the raw flag columns (`is_won`, `is_lost`, `is_open`); the measures use them.
5. Create a `_Measures` table (Enter Data → name it `_Measures` → Load) and move every measure from `DAX_measures.dax` into it. Keeping them in one place makes the model easier to navigate.

---

## 3. Dashboard pages

### Page 1: Executive Overview
Purpose: one-screen health check for the sales head.

- **KPI cards (top row):** Revenue Won (Crore), Closed Win Rate %, Total Leads, Open Pipeline Value, Avg Deal Size, Avg Days to Close.
  - Conditional formatting on Closed Win Rate % using `Win Rate Status`.
- **Line + column combo:** `lead_month` on the axis. Columns = Total Leads, line = Closed Win Rate 3M.
- **Line chart:** Revenue Won by month with Revenue Won PY as a comparison line.
- **Insight card:** `Pipeline Action Insight` measure.
- **Slicers:** Year, Region, Team.

### Page 2: Lead Funnel
Purpose: where leads are getting stuck.

- **Funnel chart:** Lead Status (New → Contacted → Qualified → Negotiation → Closed Won). Values = Total Leads.
- **Stacked bar:** Lead Source by Won Leads and Lost Leads.
- **Bar chart:** Closed Win Rate % by Lead Source, sorted descending.
- **Insight card:** `Lead Source Insight` measure.

### Page 3: Regional KPIs
Purpose: which regions and cities make money.

- **Map:** Bubble map of City with Revenue Won as size and Closed Win Rate % as colour. (Power BI maps need location permission; if unavailable, use a bar chart.)
- **Matrix:** Rows = Region → City. Values = Total Leads, Won Leads, Closed Win Rate %, Revenue Won (Crore), Avg Price per SqFt. Turn on conditional formatting (data bars on revenue, colour scale on win rate).
- **KPI card:** `Top Region` measure.

### Page 4: Agent Performance
Purpose: coaching and recognition.

- **Table:** Agent Name, Team, Total Leads, Closed Win Rate %, Revenue Won, Agent Win Rate Rank. Sort by Revenue Won.
- **Scatter chart:** X = Total Leads, Y = Closed Win Rate %, Legend = Team. Agents in the top-right are high-volume and high-conversion.
- **Filter visual:** `Agent Win Rate Rank` is not blank (this limits the ranking to agents with 20+ closed deals).

### Page 5: Follow-up and Pipeline Health
Purpose: the action list for managers.

- **KPI cards:** Open Leads, Stale Open Leads, Never Followed Up Leads, Pipeline At Risk %.
- **Donut chart:** Open leads by Follow Up Status.
- **Column chart:** Closed Win Rate % by follow-up band (create a band column in Power Query or use `follow_ups` as a bin).
- **Detail table (drill-through target):** Lead ID, Agent, City, Lead Status, Quoted Price, Follow Up Status, Days Since Follow Up, sorted by Quoted Price descending.

### Page 6: Recommendations
Purpose: turn the numbers into decisions. Use text boxes with the findings from the README, and keep the figures in sync with your data.

---

## 4. Design standards

- **Theme:** a single navy accent (#1F3864) with one green for "on track" and one red for "action needed".
- **Titles:** state the question, for example "Which regions convert best?", not just "Regional KPIs".
- **Number formats:** Crore/Lakh for Indian audiences. Use the `Revenue Won (Crore)` measure, which is already divided by 10 million.
- **Tooltips:** add a tooltip page showing monthly detail on the trend charts.
- **Bookmarks:** create a "Management view" (Page 1 only, no filters) and a "Manager view" (Page 5 with agent filter).

---

## 5. Publish and capture

1. Save as `powerbi/RealEstate_Dashboard.pbix`.
2. Take a screenshot of each page and save to `images/` as `dashboard_page_1.png` and so on.
3. Optional: File → Publish to Power BI Service for a live link on your GitHub README.
