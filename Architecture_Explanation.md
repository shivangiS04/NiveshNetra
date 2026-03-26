# NiveshNetra — System Architecture

ET AI Hackathon 2026 · Track 9: AI Money Mentor

---

## Agent Architecture Overview

```
User (Browser)
     |
     | Upload PDF / Form Input
     v
+------------------+
|   React Frontend  |  Vite 5 · TypeScript · Tailwind · Recharts
|  (localhost:5173) |
+------------------+
     |
     | HTTP (REST)
     v
+------------------------------------------------------------+
|                  FastAPI Orchestrator                       |
|                  backend/api/main.py                        |
|                                                            |
|  POST /api/analyse   POST /api/fire-plan                   |
|  POST /api/tax-plan  POST /api/report                      |
|  POST /api/quick-plan  GET /api/health                     |
+------------------------------------------------------------+
     |              |              |              |
     v              v              v              v
+----------+  +----------+  +----------+  +----------+
| Parser   |  |  XIRR    |  |   Tax    |  |  FIRE    |
| Agent    |  |  Agent   |  |  Agent   |  |  Agent   |
+----------+  +----------+  +----------+  +----------+
|CAMS/KFin |  |scipy     |  |Old/New   |  |Corpus    |
|pdfplumber|  |Brent's   |  |regime    |  |projection|
|auto-     |  |method    |  |HRA/80C   |  |SIP gap   |
|detect    |  |Newton-   |  |87A rebate|  |4% rule   |
|          |  |Raphson   |  |          |  |          |
+----------+  +----------+  +----------+  +----------+
     |              |
     v              v
+------------------------------------------------------------+
|              Fund Metadata Agent                            |
|              backend/fund_data.py                           |
|                                                            |
|  - Benchmark lookup (Nifty 50/100/500/Smallcap 250)        |
|  - Expense ratio database (8 fund families)                |
|  - Top-10 holdings per fund (overlap computation)          |
+------------------------------------------------------------+
     |
     v
+------------------------------------------------------------+
|              AI Advisor Agent                               |
|              backend/ai_advisor.py                          |
|                                                            |
|  Primary:  Groq API — llama-3.3-70b-versatile              |
|  Fallback: Rule-based engine (always available)            |
|                                                            |
|  Outputs:                                                  |
|  - Rebalancing plan (with STCG/LTCG tax context)           |
|  - Structured action cards (switch/exit/reduce/action)     |
|  - Money Health Score (6 dimensions)                       |
|  - FIRE summary (3 sentences)                              |
|  - Tax recommendations paragraph                           |
+------------------------------------------------------------+
     |
     v
+------------------------------------------------------------+
|              Report Agent                                   |
|              backend/report_generator.py                    |
|                                                            |
|  - reportlab 2-page PDF                                    |
|  - Hero metrics, Health Score bars, Fund table             |
|  - Overlap matrix, AI plan, Action items                   |
|  - Footer disclaimer on every page                         |
+------------------------------------------------------------+
```

---

## Data Flow — MF Portfolio X-Ray

```
PDF Upload
    |
    v
[Parser Agent] ──────────────────────────────────────────────
    |  pdfplumber extracts raw text                          |
    |  Auto-detects CAMS vs KFintech (first 3 pages)        |
    |  Regex: fund sections, folio numbers, transactions     |
    |  Output: list[FundHolding]                             |
    v
[XIRR Agent]
    |  build_cash_flows(): purchases → negative, redemptions → positive
    |  Terminal cash flow: current_nav × current_units (today)
    |  scipy.optimize.brentq: solves NPV(r) = 0
    |  Output: per-fund XIRR + portfolio XIRR
    v
[Fund Metadata Agent]
    |  ISIN lookup → benchmark, expense ratio, top holdings
    |  Pairwise overlap: shared stocks / min(holdings_A, holdings_B)
    |  Expense drag: expense_ratio × current_value
    v
[AI Advisor Agent]
    |  Groq prompt: portfolio summary + fund details + overlaps
    |  Includes STCG/LTCG tax context in rebalancing advice
    |  Rule-based fallback if Groq unavailable
    |  compute_health_score(): 6-dimension weighted average
    v
[FastAPI Response] → JSON → React Dashboard
    |
    v
[Report Agent] (on-demand) → 2-page PDF download
```

---

## Data Flow — Tax Wizard

```
Salary Inputs (basic, HRA, allowances, deductions)
    |
    v
[Tax Agent — Old Regime]
    Step 1: Gross Income = basic + HRA + special + other
    Step 2: HRA Exemption = min(actual HRA, rent−10%×basic, 50%/40%×basic)
    Step 3: Total Deductions = std(50K) + HRA + 80C(≤1.5L) + 80D(≤25K) + 24b(≤2L) + 80CCD(2)
    Step 4: Taxable Income = Gross − Total Deductions
    Step 5: Tax = slabs (0/5/20/30%)
    Step 6: Rebate 87A if taxable ≤ 5L
    Step 7: Cess = tax × 4%
    |
    v
[Tax Agent — New Regime]
    Step 1: Gross Income (same)
    Step 2: Deductions = std(75K) + 80CCD(2) only
    Step 3: Taxable Income = Gross − Deductions
    Step 4: Tax = slabs (0/5/10/15/20/30%)
    Step 5: Rebate 87A if taxable ≤ 7L
    Step 6: Cess = tax × 4%
    |
    v
[AI Advisor Agent] → ranked instrument recommendations
    |
    v
Step-by-step UI (every deduction shown line by line, verifiable)
```

---

## Data Flow — FIRE Planner

```
User Inputs (age, income, expenses, corpus, SIP, risk, retirement age)
    |
    v
[FIRE Agent]
    Step 1: Inflation-adjusted annual expenses at retirement
            = monthly_expenses × 12 × (1.06)^years_to_retirement
    Step 2: Target corpus = inflated_expenses / 0.04  (4% rule, 25x)
    Step 3: Month-by-month projection until corpus ≥ target
            corpus(t+1) = corpus(t) × (1 + r/12) + monthly_SIP
    Step 4: SIP gap = solve FV equation for required SIP at retirement age
    Step 5: Year-by-year chart data (projected vs required path)
    |
    v
[AI Advisor Agent] → 3-sentence personalised summary
    |
    v
React Frontend — What-if sliders (SIP + retirement age)
    Pure client-side math — no API call on slider change
    Updates: FIRE date, corpus projection, SIP gap, chart — all live
```

---

## Autonomy & Resilience

| Failure Mode | Recovery |
|---|---|
| Groq API unavailable | Rule-based rebalancing plan + health score (always works) |
| PDF parse failure | ParseError → 422 with human-readable message |
| XIRR non-convergence | XIRRError caught per-fund → xirr=null, warning in response |
| Unknown fund (not in DB) | Graceful degradation: category="", benchmark="", no overlap |
| File too large (>20MB) | 413 before parsing begins |
| Non-PDF upload | 422 before parsing begins |

---

## Compliance Guardrails

- Disclaimer banner on every Dashboard page view
- AI prompt explicitly states "SEBI-registered advisor" framing
- Every AI response ends with disclaimer text
- Report PDF footer: "Not financial advice"
- No user data stored — PDF processed in memory, discarded after response

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI 0.111, uvicorn |
| PDF Parsing | pdfplumber 0.11 |
| XIRR | scipy 1.13 (brentq), numpy 1.26 |
| AI | Groq API (llama-3.3-70b-versatile), rule-based fallback |
| PDF Generation | reportlab 4.2 |
| Frontend | React 18, TypeScript, Vite 5, Tailwind CSS, Recharts |
| Testing | pytest 8.2, Hypothesis 6.100 (property-based) |
| Environment | python-dotenv, GROQ_API_KEY in .env |
