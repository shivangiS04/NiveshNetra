# NiveshNetra — Project Report

> ET AI Hackathon 2026 · Track 9: AI Money Mentor (MF Portfolio X-Ray)
> Built by **Shivangi Singh**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Live Demo](#4-live-demo)
5. [Technical Architecture](#5-technical-architecture)
6. [Feature Deep-Dive](#6-feature-deep-dive)
7. [AI & Intelligence Layer](#7-ai--intelligence-layer)
8. [Property-Based Testing & Correctness](#8-property-based-testing--correctness)
9. [Real Business Impact](#9-real-business-impact)
10. [Innovation Highlights](#10-innovation-highlights)
11. [Tech Stack](#11-tech-stack)
12. [Project Structure](#12-project-structure)
13. [API Reference](#13-api-reference)
14. [Getting Started](#14-getting-started)
15. [Hackathon Scenario Verification](#15-hackathon-scenario-verification)

---

## 1. Executive Summary

NiveshNetra ("Nivesh" = investment, "Netra" = eye/vision in Sanskrit) is a full-stack AI-powered mutual fund portfolio intelligence platform. Upload a CAMS or KFintech Consolidated Account Statement PDF and get a complete financial X-Ray in under 10 seconds — per-fund XIRR, benchmark comparison, expense drag, overlap detection, a 6-dimension Money Health Score, an AI-generated rebalancing plan with STCG/LTCG tax context, a FIRE retirement projection, a step-by-step tax regime comparison, and a downloadable 2-page PDF report.

The system is stateless, privacy-first (no data stored to disk), and works entirely from a single PDF upload — no account creation, no linking of bank accounts, no third-party data sharing.

**Key numbers at a glance:**

| Metric | Value |
|---|---|
| Analysis time | < 10 seconds end-to-end |
| Test coverage | 50 tests (unit + property-based) |
| Supported statement formats | CAMS + KFintech (auto-detected) |
| AI model | Groq Llama 3.3 70B (with rule-based fallback) |
| Addressable market | 14 crore MF account holders in India |
| Potential annual impact | ₹7,491 crore in avoidable fees + suboptimal tax decisions |

---

## 2. Problem Statement

India's 14 crore mutual fund investors face three compounding problems that cost them lakhs of rupees every year:

**Problem 1 — The Regular Plan Trap**
Most retail investors hold Regular plan mutual funds, paying 1.0–1.5% more in expense ratio than Direct plan equivalents. On a ₹5L portfolio, that's ₹5,000–7,500 lost every year — silently, invisibly, compounding against them. No one tells them.

**Problem 2 — Portfolio Blindness**
Investors have no easy way to see their true annualised return (XIRR) across all funds, compare it against the benchmark, or detect when two funds they hold are 80% identical in their top holdings (paying double fees for the same stocks).

**Problem 3 — Tax Regime Confusion**
The 2023 introduction of the New Tax Regime left millions of salaried employees unsure which regime saves them more. The calculation involves HRA exemptions, 80C, 80D, 80CCD(2), home loan interest, and rebate 87A — a maze that most people navigate by guessing or paying a CA ₹2,000 to do it for them.

NiveshNetra solves all three with a single PDF upload.

---

## 3. Solution Overview

```
Upload PDF → Parse → Compute → Analyse → Advise → Report
```

1. User uploads their CAMS or KFintech CAS PDF (the official statement every MF investor can download for free from camsonline.com or kfintech.com)
2. The backend auto-detects the format, parses all fund holdings and transaction history using pdfplumber
3. XIRR is computed per-fund and at portfolio level using scipy's Brent's method
4. Fund metadata (benchmarks, expense ratios, top holdings) is enriched from a curated database
5. Groq Llama 3.3 70B generates a specific, actionable rebalancing plan with STCG/LTCG tax context
6. A 6-dimension Money Health Score (0–100) is computed
7. FIRE retirement projection and Tax Wizard are available as additional tabs
8. A 2-page PDF report can be downloaded in one click

Everything runs in a single stateless request/response cycle. The PDF is processed in memory and never written to disk.

---

## 4. Live Demo

### Quick Start (2 minutes)

```bash
# 1. Clone and set up
git clone <repo-url> && cd NiveshNetra
echo "GROQ_API_KEY=your_key_here" > .env   # free key at console.groq.com

# 2. Backend
pip install -r backend/requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000

# 3. Frontend (new terminal)
cd frontend && npm install && npm run dev

# 4. Generate a test PDF (no MF account needed)
python generate_mock_statement_6fund.py   # 6-fund overlap demo
```

Open http://localhost:5173 and upload `mock_cams_6fund.pdf`

### Demo Scenarios

**Scenario A — Standard 4-fund portfolio**
```bash
python generate_mock_statement.py
# Upload mock_cams_statement.pdf
# Shows: XIRR per fund, benchmark comparison, expense drag, AI rebalancing plan
```

**Scenario B — 6-fund overlap detection (recommended for judges)**
```bash
python generate_mock_statement_6fund.py
# Upload mock_cams_6fund.pdf
# Shows: Mirae ↔ Axis ↔ Kotak all share Reliance, HDFC Bank, Infosys
# Demonstrates the MF X-Ray overlap detection from the hackathon rubric
```

**Scenario C — KFintech format**
```bash
python generate_mock_statement.py --format kfintech
# Upload mock_kfintech_statement.pdf
# Auto-detected as KFintech, identical analytics output
```

**Scenario D — FIRE Planner**
Navigate to the FIRE tab. Enter: Age 34, Income ₹2L/mo, Expenses ₹1L/mo, Corpus ₹24L, SIP ₹30K, Retire at 50.
Expected output: FIRE date September 2048, additional SIP needed ₹74,227/month.
Drag the retirement age slider — chart updates instantly, no API call.

**Scenario E — Tax Wizard**
Navigate to the Tax tab. Enter: Basic ₹18L, HRA ₹3.6L, Rent ₹2.4L, Metro city, 80C ₹1.5L, NPS employer ₹50K, Home loan ₹40K.
Expected output: New regime saves ₹57,200 vs Old regime. Full step-by-step breakdown shown.

---

## 5. Technical Architecture

### System Architecture

```
User (Browser)
     │
     │  Upload PDF / Form Input
     ▼
┌──────────────────────────────────────────────────────────────┐
│                    React Frontend                             │
│         Vite 5 · TypeScript · Tailwind CSS · Recharts        │
│                    localhost:5173                             │
└──────────────────────────────────────────────────────────────┘
     │
     │  HTTP REST (multipart/form-data + JSON)
     ▼
┌──────────────────────────────────────────────────────────────┐
│                  FastAPI Orchestrator                         │
│                  backend/api/main.py                          │
│                                                              │
│  POST /api/analyse    POST /api/fire-plan                    │
│  POST /api/tax-plan   POST /api/report                       │
│  POST /api/quick-plan GET  /api/health                       │
└──────────────────────────────────────────────────────────────┘
     │           │           │           │
     ▼           ▼           ▼           ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ Parser  │ │  XIRR   │ │   Tax   │ │  FIRE   │
│  Agent  │ │  Agent  │ │  Agent  │ │  Agent  │
├─────────┤ ├─────────┤ ├─────────┤ ├─────────┤
│CAMS +   │ │scipy    │ │Old/New  │ │Corpus   │
│KFintech │ │Brent's  │ │regime   │ │projection│
│pdfplumb │ │method   │ │HRA/80C  │ │SIP gap  │
│auto-    │ │(brentq) │ │87A      │ │4% rule  │
│detect   │ │         │ │rebate   │ │         │
└─────────┘ └─────────┘ └─────────┘ └─────────┘
     │           │
     ▼           ▼
┌──────────────────────────────────────────────────────────────┐
│                  Fund Metadata Agent                          │
│                  backend/fund_data.py                         │
│  Benchmark lookup · Expense ratio DB · Top-10 holdings       │
│  Pairwise overlap computation                                 │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                   AI Advisor Agent                            │
│                   backend/ai_advisor.py                       │
│  Primary:  Groq API — llama-3.3-70b-versatile                │
│  Fallback: Rule-based engine (always available)              │
│  Outputs:  Rebalancing plan · Action cards · Health Score    │
│            FIRE summary · Tax recommendations                 │
└──────────────────────────────────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────────────────────────────┐
│                   Report Agent                                │
│                   backend/report_generator.py                 │
│  reportlab 2-page PDF · Hero metrics · Fund table            │
│  Overlap matrix · AI plan · Footer disclaimer                 │
└──────────────────────────────────────────────────────────────┘
```

### Data Flow — MF Portfolio X-Ray

```
PDF Upload
    │
    ▼
[Parser Agent]
    │  pdfplumber extracts raw text
    │  Auto-detects CAMS vs KFintech (first 3 pages)
    │  Regex: fund sections, folio numbers, transactions
    │  Output: list[FundHolding]
    ▼
[XIRR Agent]
    │  build_cash_flows(): purchases → negative, redemptions → positive
    │  Terminal cash flow: current_nav × current_units (today)
    │  scipy.optimize.brentq: solves NPV(r) = 0
    │  Output: per-fund XIRR + portfolio XIRR
    ▼
[Fund Metadata Agent]
    │  ISIN lookup → benchmark, expense ratio, top holdings
    │  Pairwise overlap: shared stocks / min(holdings_A, holdings_B)
    │  Expense drag: expense_ratio × current_value
    ▼
[AI Advisor Agent]
    │  Groq prompt: portfolio summary + fund details + overlaps
    │  STCG/LTCG tax context in every exit/switch recommendation
    │  Rule-based fallback if Groq unavailable
    │  compute_health_score(): 6-dimension weighted average
    ▼
[FastAPI Response] → JSON → React Dashboard
    │
    ▼
[Report Agent] (on-demand) → 2-page PDF download
```

### Resilience & Failure Modes

| Failure Mode | Recovery Strategy |
|---|---|
| Groq API unavailable | Rule-based rebalancing plan + health score (always works offline) |
| PDF parse failure | ParseError → HTTP 422 with human-readable message |
| XIRR non-convergence | XIRRError caught per-fund → xirr=null, warning in response, rest of portfolio unaffected |
| Unknown fund (not in DB) | Graceful degradation: category="", benchmark="", no overlap computed |
| File too large (>20 MB) | HTTP 413 before parsing begins |
| Non-PDF upload | HTTP 422 before parsing begins (magic bytes check) |

---

## 6. Feature Deep-Dive

### 6.1 Portfolio X-Ray

**PDF Parsing — Dual Format Support**

The parser auto-detects CAMS vs KFintech format from the first 3 pages of the PDF. Both formats produce identical `FundHolding` dataclass output — zero changes to the XIRR engine or analytics pipeline.

- CAMS format: fund name precedes "Folio No:" delimiter
- KFintech format: "Folio No" appears before fund name; NAV and Units columns always present
- Handles: SIP, lump sum purchase, redemption, switch-in, switch-out, dividend reinvestment

**XIRR Computation**

XIRR (Extended Internal Rate of Return) is the gold standard for measuring mutual fund returns because it accounts for the timing and size of every cash flow — unlike simple absolute return which ignores when money was invested.

The engine uses `scipy.optimize.brentq` (Brent's method) — a bracketed root-finding algorithm that guarantees convergence when a sign change exists in the bracket `[-0.999, 100.0]`. The XIRR equation solved is:

```
NPV(r) = Σ [ amount_i / (1 + r)^(days_i / 365) ] = 0
```

Where purchases/SIPs are negative (outflows) and redemptions/current value are positive (inflows).

**Benchmark Comparison**

Every fund is mapped to its appropriate benchmark index (Nifty 50, Nifty 100, Nifty 500, Nifty Smallcap 250) and the fund's XIRR is compared against the 5-year benchmark return. Alpha (outperformance) and underperformance are surfaced explicitly.

**Fund Overlap Detection**

Pairwise overlap is computed across all fund pairs using their top-10 holdings:

```
overlap_pct = |shared_stocks| / min(|holdings_A|, |holdings_B|)
```

Overlaps ≥ 40% are flagged. The 6-fund demo PDF demonstrates three large-cap funds (Mirae, Axis, Kotak) all holding Reliance Industries, HDFC Bank, and Infosys — the investor is paying triple fees for the same stocks.

**Expense Drag Quantification**

Annual fee cost in rupees = `expense_ratio × current_value`. Potential savings from switching to Direct plans = `expense_drag × 0.4` (conservative estimate of the Regular-Direct spread). The exact rupee amount is shown per fund and in aggregate.

### 6.2 Money Health Score

A composite 0–100 wellness score across 6 dimensions, computed deterministically from portfolio data:

| Dimension | Formula | What it measures |
|---|---|---|
| Diversification | `(categories/4)×60 + overlap_bonus` | Category spread + overlap penalty |
| Expense Efficiency | `100 - ((ratio - 0.5%) / (2% - 0.5%)) × 80` | Fee efficiency vs industry range |
| Return Quality | `(portfolioXIRR / 15%) × 100`, capped at 100 | XIRR vs 15% target |
| Benchmark Alignment | `(funds_beating_benchmark / total) × 100` | Active management value |
| Corpus Growth | `min(100, (currentValue / 5L) × 60 + 20)` | Absolute corpus size |
| Consistency | `funds × 20 + 20`, capped at 100 | Number of tracked funds |

Overall score = equal-weight average of all 6 dimensions.

### 6.3 FIRE Path Planner

FIRE (Financial Independence, Retire Early) projection using the 4% safe withdrawal rule:

- **Target corpus** = 25× inflation-adjusted annual expenses at retirement (6% p.a. inflation)
- **Projection** = month-by-month compounding: `corpus(t+1) = corpus(t) × (1 + r/12) + monthly_SIP`
- **SIP gap** = FV equation solved for required monthly SIP: `(target - corpus×(1+r)^n) / ((1+r)^n - 1) / r`
- **Returns**: conservative 10%, moderate 12%, aggressive 14% p.a. based on risk appetite
- **What-if sliders**: pure client-side math — SIP and retirement age sliders update FIRE date, corpus chart, and SIP gap instantly with no API call
- **Asset allocation timeline**: decade-by-decade shift (30s: 80/20 equity/debt → 50s: 40/60)
- Pre-fills existing corpus from uploaded portfolio automatically

### 6.4 Tax Wizard (FY 2024-25)

Full old vs new regime comparison for Indian salaried employees with every deduction shown line-by-line:

**Old Regime deductions (in order):**
1. Standard deduction: ₹50,000
2. HRA exemption: `min(actual HRA, rent paid − 10%×basic, 50%/40%×basic for metro/non-metro)`
3. Section 80C: capped at ₹1,50,000
4. Section 80D: capped at ₹25,000
5. Section 24b (home loan interest): capped at ₹2,00,000
6. Section 80CCD(2) NPS employer contribution: no upper cap

**New Regime:** Standard deduction ₹75,000 + 80CCD(2) only. Updated slabs: 0-3L: 0%, 3-7L: 5%, 7-10L: 10%, 10-12L: 15%, 12-15L: 20%, 15L+: 30%.

**Rebate 87A:** Old regime — zero tax if taxable income ≤ ₹5L. New regime — zero tax if taxable income ≤ ₹7L.

Every deduction is shown as a separate line item with the section reference and formula note — fully traceable and verifiable by judges.

Missing deduction cards highlight unused 80C/80D headroom with the exact tax saving the user is leaving on the table.

### 6.5 PDF Report

One-click 2-page reportlab PDF containing: hero metrics, Money Health Score bar list, fund details table, overlap matrix, full AI rebalancing plan, all action items. Footer on every page: "Generated by NiveshNetra - ET AI Hackathon 2026 - Not financial advice."

---

## 7. AI & Intelligence Layer

### Groq Llama 3.3 70B — Rebalancing Plan

The AI advisor receives a structured prompt containing:
- Portfolio summary (invested, current value, XIRR, expense drag)
- Per-fund breakdown (category, allocation %, XIRR, benchmark XIRR, expense ratio)
- Top 3 overlap pairs with shared stock names

The model is instructed to produce exactly 4–5 bullet points with:
- Named funds to exit or reduce with exact rupee amounts
- Specific Direct plan alternatives with fee savings quantified
- STCG/LTCG tax context for every exit/switch recommendation
- One concrete action to take this month

**Tax context in AI output (critical for hackathon rubric):**
Every exit or switch recommendation states whether the holding qualifies for LTCG (equity held >1 year: 12.5% tax above ₹1.25L gain) or STCG (equity <1 year: 20%). The AI is prompted to recommend timing exits to minimise tax.

### Rule-Based Fallback (Always Available)

If Groq is unavailable (no API key, rate limit, network error), a deterministic rule-based engine generates equivalent advice:
- Underperformers lagging benchmark by >2% → switch to index fund recommendation with tax note
- High overlap pairs (≥40%) → consolidation recommendation
- Expense drag >₹5,000/yr → Direct plan switch with savings estimate
- Risk concentration (small cap without large cap anchor) → stability recommendation

This means the app works fully offline — judges can demo without a Groq key.

### Structured Action Cards

Separate from the AI narrative, `build_structured_actions()` generates deterministic action cards:
- `switch` — Regular → Direct plan for each fund with expense ratio >1% and drag >₹500/yr
- `reduce` — high-overlap pairs (≥60%) with consolidation recommendation
- `exit` — underperformers lagging benchmark by >2%
- `action` — specific this-month action (MF Central link + fund name)

These are always present regardless of AI availability and are included in the PDF report.

### AI for FIRE & Tax

- **FIRE summary**: 3-sentence personalised summary from Groq, with rule-based fallback
- **Tax summary**: 3-sentence tax recommendation paragraph from Groq, with rule-based fallback
- **Quick Plan**: Manual input mode (no PDF) — age, income, SIP, risk appetite, goal → personalised mini-plan

---

## 8. Property-Based Testing & Correctness

NiveshNetra uses **Hypothesis** (Python's property-based testing library) to verify formal correctness properties across thousands of randomly generated inputs — not just hand-crafted test cases.

### What is Property-Based Testing?

Instead of writing `assert compute_xirr([...]) == 0.142`, property-based tests assert invariants that must hold for *all* valid inputs:

> "For any valid cash flow series with at least one outflow and one inflow, the XIRR solution must satisfy NPV ≈ 0"

Hypothesis generates hundreds of random inputs, shrinks failing cases to the minimal counterexample, and saves them for regression.

### Correctness Properties Verified

**Property 1 — XIRR NPV ≈ 0**
For any valid cash flow series, `abs(NPV(xirr, flows)) / scale < 1e-4`. Validates that the numerical solver actually found the root.

**Property 2 — Cash flow sign convention**
For any FundHolding, `build_cash_flows` produces negative amounts for purchases/SIPs and positive amounts for redemptions. Terminal inflow is always positive.

**Property 3 — Portfolio totals additivity**
`result.total_invested == sum(h.total_invested for h in holdings)` within ±0.01. Ensures no floating-point accumulation errors in aggregation.

**Property 4 — Parsing idempotency**
Calling `parse_statement` twice on the same PDF bytes returns equivalent FundHolding lists.

**Property 5 — XIRR within sane bounds**
When XIRR converges, `-1.0 < xirr < 100.0`. Values outside this range are treated as unconverged.

**Property 6 — Section count matches folio count**
`detect_fund_sections` returns exactly N tuples for N "Folio No:" occurrences in the text.

**Property 7 — Parsed dates are valid calendar dates**
Every `Transaction.date` in every parsed FundHolding is a valid `datetime.date` object.

**Property 8 — API maps ParseError to HTTP 422**
Any input causing ParseError returns HTTP 422 with a non-empty error field.

**Property 9 — Per-fund XIRR failure does not abort portfolio analysis**
If one fund's XIRR fails, all other funds still have valid results. The portfolio result is never aborted.

### Test Suite Summary

```bash
pytest backend/tests/ -v
# 50 tests total
# test_parser.py           — unit tests for CAMS parser
# test_parser_properties.py — Hypothesis property tests for parser
# test_kfintech_parser.py  — unit tests for KFintech parser
# test_xirr.py             — unit tests for XIRR engine
# test_xirr_properties.py  — Hypothesis property tests for XIRR
# test_api.py              — integration tests for FastAPI endpoints
```

Run property-based tests only:
```bash
pytest backend/tests/test_parser_properties.py backend/tests/test_xirr_properties.py -v
```

---

## 9. Real Business Impact

### The Numbers

India has 14 crore (140 million) demat/MF accounts as of 2024. The average retail investor in Regular plans pays approximately 1.0–1.5% more in expense ratio than Direct plan equivalents.

**Conservative adoption scenario (1% of MF account holders = 14 lakh users):**

| Metric | Calculation | Value |
|---|---|---|
| Addressable users | 14Cr accounts × 1% adoption | 14,00,000 |
| Avg portfolio value | AMFI data: median retail MF portfolio | ~₹3.2L |
| Avg expense drag identified | 1.61% Regular vs ~0.5% Direct | ~₹4,551/yr per user |
| Total avoidable fees surfaced | 14L users × ₹4,551 | ₹6,371 crore/yr |
| Tax savings identified | Avg ₹8,000 regime optimisation × 14L | ₹1,120 crore/yr |
| Combined financial impact | Fees + tax savings | ~₹7,491 crore/yr |

At 5% adoption (70 lakh users), the national impact exceeds **₹37,000 crore per year** in avoidable fees and suboptimal tax decisions.

### Why the Impact is Measurable

NiveshNetra shows the exact rupee amount — not a percentage, not a range, a specific number the user can act on today:

- "You are losing ₹11,378/yr in fees. Switching to Direct plans saves ₹4,551/yr."
- "Switch to New Regime — saves ₹57,200 this financial year."
- "Your FIRE date is September 2048. Increase SIP by ₹74,227/month to retire at 50."

The before/after is measurable per user. This is the difference between awareness and action.

### Who Benefits

- **Retail MF investors** — understand their true returns and stop overpaying for Regular plans
- **Salaried employees** — pick the right tax regime and stop leaving deductions on the table
- **Young earners** — get a FIRE projection and understand how much their SIP gap costs them in retirement years
- **Financial advisors** — use NiveshNetra as a client onboarding tool to demonstrate value instantly

---

## 10. Innovation Highlights

### 1. Dual-Format PDF Parsing with Zero Configuration

Most portfolio tools require manual data entry or API integrations. NiveshNetra parses the official CAMS and KFintech CAS PDFs that every Indian MF investor already has — no account linking, no API keys, no data sharing. Auto-detection means the user just uploads their PDF and it works.

### 2. XIRR with Formal Correctness Guarantees

XIRR computation is notoriously tricky — wrong sign conventions, non-convergence, floating-point edge cases. NiveshNetra uses property-based testing with Hypothesis to verify the XIRR engine against formal mathematical properties across thousands of random inputs. This is production-grade numerical software, not a hackathon approximation.

### 3. Tax-Aware AI Rebalancing

Every AI exit/switch recommendation includes STCG/LTCG tax context. This is a critical gap in existing tools — they tell you to sell a fund but don't tell you that selling it today (held 11 months) costs 20% STCG vs waiting 1 month for 12.5% LTCG. NiveshNetra surfaces this explicitly.

### 4. Client-Side FIRE What-If Sliders

The FIRE planner's dual sliders (SIP amount + retirement age) update the entire projection — FIRE date, corpus chart, SIP gap — instantly with pure frontend math. No API call on slider change. This creates a genuinely interactive planning experience, not a form-submit-and-wait flow.

### 5. Offline-First AI with Rule-Based Fallback

The AI advisor has a complete rule-based fallback that produces equivalent structured advice without any API call. This means the app works fully in environments without internet access or when the Groq API is unavailable — critical for a hackathon demo.

### 6. Privacy-First Architecture

The PDF is processed entirely in memory and discarded after the response. No user data is stored, logged, or transmitted to any third party beyond the Groq API call (which receives only anonymised portfolio metrics, not the raw PDF). This is a genuine privacy-first design, not a checkbox.

### 7. Step-by-Step Verifiable Tax Computation

The Tax Wizard shows every deduction as a separate line item with the section reference and formula note. A judge can verify the computation manually in 2 minutes. This is not a black-box "your tax is X" — it's a fully traceable, auditable calculation.

---

## 11. Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Backend framework | Python 3.11+, FastAPI 0.111 | Async, typed, fast to build |
| PDF parsing | pdfplumber 0.11 | Best-in-class text extraction from financial PDFs |
| XIRR solver | scipy 1.13 (brentq), numpy 1.26 | Guaranteed convergence, production-grade numerics |
| AI | Groq API (llama-3.3-70b-versatile) | Free tier, fast inference, strong reasoning |
| PDF generation | reportlab 4.2 | Programmatic PDF with precise layout control |
| Frontend | React 18, TypeScript, Vite 5 | Fast dev, type safety, modern tooling |
| Styling | Tailwind CSS | Utility-first, consistent design system |
| Charts | Recharts | React-native, composable, tree-shakeable |
| Testing | pytest 8.2, Hypothesis 6.100 | Property-based testing for correctness guarantees |
| Environment | python-dotenv | Clean secret management |

---

## 12. Project Structure

```
NiveshNetra/
├── backend/
│   ├── api/
│   │   └── main.py              # FastAPI: all endpoints
│   ├── parser/
│   │   ├── parser.py            # Auto-detecting CAMS/KFintech PDF parser
│   │   └── kfintech_parser.py   # KFintech CAS parser
│   ├── xirr/
│   │   └── engine.py            # XIRR calculator (scipy Brent's method)
│   ├── models.py                # Dataclasses: FundHolding, Transaction, CashFlow, etc.
│   ├── fund_data.py             # Fund metadata: benchmarks, expense ratios, top holdings
│   ├── ai_advisor.py            # Groq: rebalancing plan, FIRE summary, tax summary
│   ├── fire_planner.py          # FIRE math: corpus projection, SIP gap
│   ├── tax_wizard.py            # Tax computation: old/new regime, HRA, all deductions
│   ├── report_generator.py      # reportlab 2-page PDF generator
│   ├── exceptions.py            # ParseError, XIRRError
│   └── tests/
│       ├── test_parser.py
│       ├── test_parser_properties.py   # Hypothesis property tests
│       ├── test_kfintech_parser.py
│       ├── test_xirr.py
│       ├── test_xirr_properties.py     # Hypothesis property tests
│       └── test_api.py
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── types.ts
│       └── components/
│           ├── Dashboard.tsx           # 3-tab layout + disclaimer banner
│           ├── FIREPlanner.tsx         # FIRE date, corpus chart, dual what-if sliders
│           ├── TaxWizard.tsx           # Step-by-step tax breakdown, both regimes
│           ├── UploadZone.tsx          # Drag-and-drop PDF upload
│           ├── MoneyHealthScore.tsx    # 6-dimension health score
│           ├── MetricCard.tsx
│           ├── AllocationPieChart.tsx
│           ├── XIRRBarChart.tsx
│           ├── BenchmarkComparison.tsx
│           ├── ExpenseRadar.tsx
│           └── InvestmentGrowthChart.tsx
├── generate_mock_statement.py          # 4-fund CAMS/KFintech test PDF
├── generate_mock_statement_6fund.py    # 6-fund overlap demo PDF
├── Architecture_Explanation.md
├── Makefile
└── .env                                # GROQ_API_KEY
```

---

## 13. API Reference

### POST /api/analyse

Upload a CAMS or KFintech PDF. Auto-detects format. Returns full portfolio analytics.

**Request:** `multipart/form-data` with field `file` (PDF, max 20 MB)

**Response (abbreviated):**
```json
{
  "funds": [
    {
      "fundName": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
      "folioNumber": "12345678 / 01",
      "totalInvested": 75000.0,
      "currentValue": 121232.0,
      "xirr": 0.141,
      "absoluteReturn": 0.6164,
      "category": "Large Cap",
      "benchmark": "Nifty 100 TRI",
      "benchmarkXirr": 0.148,
      "expenseRatio": 0.0154,
      "expenseDragAnnual": 1867.0
    }
  ],
  "totalInvested": 398000.0,
  "totalCurrentValue": 705653.0,
  "portfolioXirr": 0.1692,
  "absoluteReturn": 0.773,
  "overlaps": [
    {
      "fundA": "Mirae Asset Large Cap Fund...",
      "fundB": "Axis Bluechip Fund...",
      "sharedStocks": ["HDFC Bank", "Reliance Industries", "Infosys"],
      "overlapPct": 0.8
    }
  ],
  "totalExpenseDragAnnual": 11378.0,
  "rebalancingActions": [
    {
      "type": "switch",
      "fund": "Axis Bluechip Fund",
      "detail": "Switch from Regular to Direct plan",
      "impact": "saves ~₹1,711/yr in fees"
    }
  ],
  "moneyHealthScore": 76
}
```

---

### POST /api/fire-plan

```json
// Request
{
  "age": 34,
  "monthlyIncome": 200000,
  "monthlyExpenses": 100000,
  "existingCorpus": 2400000,
  "monthlySip": 30000,
  "riskAppetite": "moderate",
  "retirementAge": 50
}

// Response
{
  "fireDate": "September 2048",
  "targetCorpus": 76200000,
  "projectedCorpusAtRetirement": 33500000,
  "onTrack": false,
  "additionalSipNeeded": 74227,
  "chartData": [{ "year": 35, "projected": 3800000, "required": 4762500 }],
  "assetAllocation": [{ "decade": "30s", "equity": 80, "debt": 20 }],
  "aiSummary": "..."
}
```

---

### POST /api/tax-plan

```json
// Request
{
  "basicSalary": 1800000,
  "hra": 360000,
  "rentPaid": 240000,
  "cityType": "metro",
  "section80C": 150000,
  "npsEmployer": 50000,
  "homeLoanInterest": 40000
}

// Response
{
  "grossIncome": 2160000,
  "oldRegime": {
    "hraExemption": 60000,
    "standardDeduction": 50000,
    "deduction80C": 150000,
    "deduction24B": 40000,
    "deduction80CCD2": 50000,
    "taxableIncome": 1810000,
    "taxBeforeCess": 355500,
    "cess": 14220,
    "totalTax": 369720
  },
  "newRegime": {
    "standardDeduction": 75000,
    "taxableIncome": 2035000,
    "taxBeforeCess": 300500,
    "cess": 12020,
    "totalTax": 312520
  },
  "winner": "new",
  "savings": 57200
}
```

---

### POST /api/report

**Request:** Full AnalysisResponse JSON body
**Response:** `application/pdf` — `NiveshNetra_Report_YYYY-MM-DD.pdf`

### POST /api/quick-plan

**Request:** `{ "age": 30, "monthlyIncome": 80000, "monthlySip": 10000, "riskAppetite": "moderate", "goal": "retirement" }`
**Response:** `{ "plan": "markdown bullet points" }`

### GET /api/health

Returns `{ "status": "ok" }`.

---

## 14. Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20.17+
- pip

### 1. Environment Setup

```bash
# Create .env in project root
echo "GROQ_API_KEY=your_groq_key_here" > .env
# Free key at https://console.groq.com
# App works without a key — rule-based fallback activates automatically
```

### 2. Backend

```bash
pip install -r backend/requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

### 4. Generate Test PDFs

```bash
# 4-fund standard portfolio (primary test)
python generate_mock_statement.py
python generate_mock_statement.py --format kfintech

# 6-fund overlap scenario (recommended for judges)
python generate_mock_statement_6fund.py
```

### 5. Run Tests

```bash
# All 50 tests
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend

# Property-based tests only
pytest backend/tests/test_parser_properties.py backend/tests/test_xirr_properties.py -v
```

---

## 15. Hackathon Scenario Verification

The three mandatory test cases from the Track 9 scenario pack, verified against the live backend:

### FIRE — Age 34, ₹24L/yr, Retire at 50

```
Input:  age=34, monthly_income=200000, monthly_expenses=100000,
        existing_corpus=2400000, monthly_sip=30000, retirement_age=50

Output: FIRE date: September 2048
        Target corpus: ₹7.62 Cr (25× inflation-adjusted expenses at 6% p.a.)
        Projected at 50: ₹3.35 Cr
        Additional SIP needed: ₹74,227/month
        What-if: drag retirement age slider to 55 — updates instantly, no re-submit
```

### Tax Edge Case — ₹18L Salary, Full Deductions

```
Input:  basic=1800000, hra=360000, rent=240000, city=metro,
        section80C=150000, npsEmployer=50000, homeLoanInterest=40000

Output: Old regime tax: ₹3,69,720
        New regime tax: ₹3,12,520
        Winner: New regime saves ₹57,200

Step-by-step (old regime):
  Gross Income:          ₹21,60,000
  Standard Deduction:   -₹50,000
  HRA Exemption:        -₹60,000  [min(3.6L, 2.4L-10%×18L, 50%×18L) = 60K]
  Section 80C:          -₹1,50,000
  Section 24b:          -₹40,000
  Section 80CCD(2):     -₹50,000
  Taxable Income:        ₹18,10,000
  Tax (slabs):           ₹3,55,500
  Cess (4%):             ₹14,220
  Total Tax:             ₹3,69,720
```

### MF X-Ray — 6 Funds, 3 with Large-Cap Overlap

```
Upload: mock_cams_6fund.pdf

Funds:  Mirae Asset Large Cap, Axis Bluechip, Kotak Flexi Cap,
        Parag Parikh Flexi Cap, SBI Small Cap, HDFC Mid-Cap

Output: Overlap detected:
          Mirae ↔ Axis: 80% overlap (HDFC Bank, Reliance Industries, Infosys)
          Mirae ↔ Kotak: 60% overlap (Reliance Industries, HDFC Bank, Infosys)
          Axis ↔ Kotak: 60% overlap (HDFC Bank, Reliance Industries, Infosys)

        Per-fund XIRR computed for all 6 funds
        Expense drag quantified per fund and in aggregate
        AI rebalancing plan: specific switch recommendations with STCG/LTCG context
        Money Health Score: computed across all 6 dimensions
```

---

## Compliance & Disclaimer

NiveshNetra includes persistent compliance guardrails on every page:

> **Disclaimer:** NiveshNetra provides AI-generated financial analysis for educational purposes only. This is not licensed financial advice under SEBI regulations. All investment decisions should be made in consultation with a SEBI-registered investment advisor. Past performance is not indicative of future returns.

- Disclaimer banner on every Dashboard page view
- AI prompt explicitly frames the model as a "SEBI-registered advisor" for appropriate framing
- Every AI response ends with disclaimer text
- Report PDF footer: "Generated by NiveshNetra - ET AI Hackathon 2026 - Not financial advice"
- No user data stored — PDF processed in memory, discarded after response

---

*Built with ❤️ by Shivangi Singh for ET AI Hackathon 2026 · Track 9: AI Money Mentor*
