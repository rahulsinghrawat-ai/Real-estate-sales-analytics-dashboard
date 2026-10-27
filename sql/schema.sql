-- =====================================================================
-- Real Estate Sales & Portfolio Analytics Dashboard
-- Schema for PostgreSQL (also loads cleanly into MySQL 8 with minor changes)
-- Run once, then load data/cleaned_agents.csv and data/cleaned_leads.csv
-- =====================================================================

DROP VIEW  IF EXISTS vw_monthly_kpi;
DROP TABLE IF EXISTS leads;
DROP TABLE IF EXISTS agents;

CREATE TABLE agents (
    agent_id    VARCHAR(10) PRIMARY KEY,
    agent_name  VARCHAR(100) NOT NULL,
    team        VARCHAR(30)  NOT NULL,
    hire_date   DATE
);

CREATE TABLE leads (
    lead_id              VARCHAR(10)  PRIMARY KEY,
    lead_date            DATE         NOT NULL,
    agent_id             VARCHAR(10)  NOT NULL REFERENCES agents(agent_id),
    city                 VARCHAR(50)  NOT NULL,
    region               VARCHAR(20)  NOT NULL,
    property_type        VARCHAR(20)  NOT NULL,
    bhk                  VARCHAR(10),
    area_sqft            NUMERIC(10,2) NOT NULL,
    quoted_price         NUMERIC(14,2) NOT NULL,
    lead_source          VARCHAR(40)  NOT NULL,
    lead_status          VARCHAR(20)  NOT NULL,
    follow_ups           INTEGER      NOT NULL DEFAULT 0,
    last_follow_up_date  DATE,
    closed_date          DATE,
    deal_value           NUMERIC(14,2),
    deal_value_imputed   SMALLINT     NOT NULL DEFAULT 0,
    revenue_won          NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_won               SMALLINT     NOT NULL,
    is_lost              SMALLINT     NOT NULL,
    is_open              SMALLINT     NOT NULL,
    price_per_sqft       NUMERIC(12,2),
    days_to_close        INTEGER,
    days_since_follow_up INTEGER,
    follow_up_status     VARCHAR(30)  NOT NULL,
    lead_month           DATE         NOT NULL,
    lead_year            SMALLINT     NOT NULL,
    lead_quarter         VARCHAR(10)  NOT NULL
);

CREATE INDEX idx_leads_agent  ON leads(agent_id);
CREATE INDEX idx_leads_city   ON leads(city);
CREATE INDEX idx_leads_month  ON leads(lead_month);

-- Reusable monthly KPI view: Power BI can connect to this directly
CREATE VIEW vw_monthly_kpi AS
SELECT
    lead_month,
    COUNT(*)                                        AS total_leads,
    SUM(is_won)                                     AS won_leads,
    SUM(is_lost)                                    AS lost_leads,
    SUM(is_open)                                    AS open_leads,
    SUM(revenue_won)                                AS revenue_won,
    ROUND(100.0 * SUM(is_won) / COUNT(*), 2)        AS win_rate_pct
FROM leads
GROUP BY lead_month;

-- Load instructions (PostgreSQL, run from psql in project root):
--   \copy agents FROM 'data/cleaned_agents.csv' WITH (FORMAT csv, HEADER true)
--   \copy leads  FROM 'data/cleaned_leads.csv'  WITH (FORMAT csv, HEADER true)
