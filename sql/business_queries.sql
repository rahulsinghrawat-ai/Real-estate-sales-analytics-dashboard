-- =====================================================================
-- Business queries: lead funnel, sales performance, follow-up status,
-- regional KPIs. Each query answers one question a sales leader would ask.
-- Results of these queries are reproduced in README.md.
-- =====================================================================


-- Q1. Lead funnel: how many leads sit at each stage, and what share of all leads?
SELECT
    lead_status,
    COUNT(*)                                             AS leads,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)   AS share_pct
FROM leads
GROUP BY lead_status
ORDER BY CASE lead_status
            WHEN 'New' THEN 1 WHEN 'Contacted' THEN 2 WHEN 'Qualified' THEN 3
            WHEN 'Negotiation' THEN 4 WHEN 'Closed Won' THEN 5 WHEN 'Closed Lost' THEN 6
         END;


-- Q2. Regional KPIs: volume, win rate, revenue and pricing by region
SELECT
    region,
    COUNT(*)                                              AS total_leads,
    SUM(is_won)                                           AS won_leads,
    ROUND(100.0 * SUM(is_won) / NULLIF(SUM(is_won) + SUM(is_lost), 0), 1) AS closed_win_rate_pct,
    ROUND(SUM(revenue_won) / 1e7, 2)                      AS revenue_crore_inr,
    ROUND(AVG(CASE WHEN is_won = 1 THEN revenue_won END) / 1e5, 1) AS avg_deal_lakh_inr,
    ROUND(AVG(price_per_sqft), 0)                         AS avg_price_per_sqft
FROM leads
GROUP BY region
ORDER BY revenue_crore_inr DESC;


-- Q3. City ranking by revenue, with win rate and a rank for the sales team
SELECT
    city,
    region,
    SUM(revenue_won)                                      AS revenue_won,
    SUM(is_won)                                           AS won_leads,
    ROUND(100.0 * SUM(is_won) / NULLIF(SUM(is_won) + SUM(is_lost), 0), 1) AS closed_win_rate_pct,
    RANK() OVER (ORDER BY SUM(revenue_won) DESC)          AS revenue_rank
FROM leads
GROUP BY city, region
ORDER BY revenue_rank;


-- Q4. Monthly trend with month-over-month revenue growth (uses window LAG)
WITH monthly AS (
    SELECT
        lead_month,
        COUNT(*)              AS total_leads,
        SUM(is_won)           AS won_leads,
        SUM(revenue_won)      AS revenue_won
    FROM leads
    GROUP BY lead_month
)
SELECT
    lead_month,
    total_leads,
    won_leads,
    ROUND(100.0 * won_leads / total_leads, 1)                              AS win_rate_pct,
    ROUND(revenue_won / 1e7, 2)                                             AS revenue_crore_inr,
    ROUND(100.0 * (revenue_won - LAG(revenue_won) OVER (ORDER BY lead_month))
          / NULLIF(LAG(revenue_won) OVER (ORDER BY lead_month), 0), 1)     AS mom_revenue_growth_pct
FROM monthly
ORDER BY lead_month;


-- Q5. Agent leaderboard: closed win rate and revenue, ranked.
-- Filter to agents with at least 20 closed deals so small samples don't dominate.
SELECT
    a.agent_name,
    a.team,
    COUNT(*)                                                               AS total_leads,
    SUM(l.is_won)                                                          AS won_leads,
    ROUND(100.0 * SUM(l.is_won) / NULLIF(SUM(l.is_won) + SUM(l.is_lost), 0), 1) AS closed_win_rate_pct,
    ROUND(SUM(l.revenue_won) / 1e7, 2)                                     AS revenue_crore_inr,
    RANK() OVER (ORDER BY SUM(l.revenue_won) DESC)                         AS revenue_rank
FROM leads l
JOIN agents a ON a.agent_id = l.agent_id
GROUP BY a.agent_name, a.team
HAVING SUM(l.is_won) + SUM(l.is_lost) >= 20
ORDER BY revenue_rank;


-- Q6. Does follow-up discipline change the outcome?
-- Win rate on closed leads, grouped by how many times the lead was followed up.
SELECT
    CASE
        WHEN follow_ups = 0 THEN '0'
        WHEN follow_ups BETWEEN 1 AND 2 THEN '1-2'
        WHEN follow_ups BETWEEN 3 AND 5 THEN '3-5'
        ELSE '6+'
    END                                                                    AS follow_up_band,
    COUNT(*)                                                               AS closed_leads,
    ROUND(100.0 * SUM(is_won) / COUNT(*), 1)                               AS win_rate_pct
FROM leads
WHERE is_open = 0
GROUP BY 1
ORDER BY MIN(follow_ups);


-- Q7. Follow-up health of open pipeline (the action list for managers)
SELECT
    follow_up_status,
    COUNT(*)                                                               AS open_leads,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1)                     AS share_pct,
    ROUND(SUM(quoted_price) / 1e7, 2)                                      AS pipeline_value_crore_inr
FROM leads
WHERE is_open = 1
GROUP BY follow_up_status
ORDER BY open_leads DESC;


-- Q8. Priority call list: open, high-value leads with stale or no follow-up
SELECT
    l.lead_id,
    a.agent_name,
    l.city,
    l.property_type,
    l.lead_status,
    l.quoted_price,
    l.follow_up_status,
    l.days_since_follow_up
FROM leads l
JOIN agents a ON a.agent_id = l.agent_id
WHERE l.is_open = 1
  AND l.follow_up_status IN ('Never Followed Up', 'Stale (>14 days)')
  AND l.lead_status IN ('Qualified', 'Negotiation')
ORDER BY l.quoted_price DESC
LIMIT 25;


-- Q9. Lead source performance: which channels produce wins, not just leads?
SELECT
    lead_source,
    COUNT(*)                                                               AS total_leads,
    SUM(is_won)                                                            AS won_leads,
    ROUND(100.0 * SUM(is_won) / NULLIF(SUM(is_won) + SUM(is_lost), 0), 1) AS closed_win_rate_pct,
    ROUND(SUM(revenue_won) / 1e7, 2)                                       AS revenue_crore_inr
FROM leads
GROUP BY lead_source
ORDER BY closed_win_rate_pct DESC;


-- Q10. Product mix: property type and BHK configuration performance
SELECT
    property_type,
    bhk,
    COUNT(*)                                                               AS total_leads,
    ROUND(100.0 * SUM(is_won) / NULLIF(SUM(is_won) + SUM(is_lost), 0), 1) AS closed_win_rate_pct,
    ROUND(AVG(days_to_close), 0)                                           AS avg_days_to_close,
    ROUND(AVG(CASE WHEN is_won = 1 THEN revenue_won END) / 1e5, 1)        AS avg_deal_lakh_inr
FROM leads
GROUP BY property_type, bhk
HAVING COUNT(*) >= 30
ORDER BY closed_win_rate_pct DESC;


-- Q11. Sales cycle length: average days from lead to close, by property type
SELECT
    property_type,
    COUNT(*)                                AS closed_leads,
    ROUND(AVG(days_to_close), 1)            AS avg_days_to_close,
    MIN(days_to_close)                      AS fastest_close,
    MAX(days_to_close)                      AS slowest_close
FROM leads
WHERE is_open = 0
GROUP BY property_type
ORDER BY avg_days_to_close;
