# NiveshNetra

A full-stack mutual fund portfolio analyser. Upload your CAMS Consolidated Account Statement PDF and instantly get XIRR, absolute returns, allocation breakdown, and fund-level analytics — all computed locally, nothing leaves your machine.

---

## Features

- **PDF parsing** — extracts transactions from CAMS statements using pdfplumber
- **XIRR computation** — per-fund and portfolio-level annualised returns via scipy
- **Interactive dashboard** — allocation pie chart, XIRR bar chart, investment growth line chart
- **Fund table** — invested amount, current value, XIRR, and absolute return per fund
- **Privacy-first** — PDF is processed in memory, never stored

---

## Tech Stack

| Layer    | Technology                              |
|----------|-----------------------------------------|
| Backend  | Python 3.11+, FastAPI, pdfplumber, scipy |
| Frontend | React 18, TypeScript, Vite 5, Tailwind CSS, Recharts |
| Testing  | pytest, Hypothesis (property-based tests) |

---

## Project Structure

```
NiveshNetra/
├── backend/
│   ├── api/main.py          # FastAPI app — /api/analyse, /api/health
│   ├── parser/parser.py     # CAMS PDF parser
│   ├── xirr/engine.py       # XIRR calculator (scipy brentq)
│   ├── models.py            # Dataclasses
│   ├── exceptions.py        # ParseError, XIRRError
│   ├── tests/               # 44 tests (unit + property-based)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── UploadZone.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── MetricCard.tsx
│   │   │   ├── AllocationPieChart.tsx
│   │   │   ├── XIRRBarChart.tsx
│   │   │   └── InvestmentGrowthChart.tsx
│   │   └── types.ts
│   └── vite.config.ts
├── generate_mock_statement.py   # Generates a test CAMS PDF
└── Makefile
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20.17+ (but < 20.19 — use Vite 5, not Vite 6+)
- pip

### 1. Backend

```bash
# From the project root
pip install -r backend/requirements.txt
python -m uvicorn backend.api.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

### 3. Generate a test PDF (no mutual fund account needed)

```bash
pip install reportlab
python generate_mock_statement.py
# Creates mock_cams_statement.pdf — upload this to the app
```

---

## Running Tests

```bash
# All 44 tests
pytest

# With coverage
pytest --cov=backend

# Property-based tests only
pytest backend/tests/test_parser_properties.py backend/tests/test_xirr_properties.py -v
```

---

## API

### `POST /api/analyse`

Upload a CAMS PDF and get portfolio analytics.

**Request:** `multipart/form-data` with field `file` (PDF)

**Response:**
```json
{
  "funds": [
    {
      "fundName": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
      "folioNumber": "12345678 / 01",
      "totalInvested": 75000.0,
      "currentValue": 121232.0,
      "xirr": 0.141,
      "absoluteReturn": 0.6164
    }
  ],
  "totalInvested": 398000.0,
  "totalCurrentValue": 705653.0,
  "portfolioXirr": 0.1692,
  "absoluteReturn": 0.773,
  "warnings": []
}
```

### `GET /api/health`

Returns `{"status": "ok"}`.

---

## How XIRR Works

XIRR (Extended Internal Rate of Return) is the annualised return that makes the net present value of all cash flows equal to zero. Each SIP instalment is a negative cash flow (money out), and the current portfolio value is a positive cash flow (money in today). We solve for the rate using scipy's `brentq` root-finding algorithm.

---

## License

MIT
