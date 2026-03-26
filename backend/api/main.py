"""NiveshNetra FastAPI backend."""

import os
from datetime import date
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load .env from project root regardless of where uvicorn is invoked from
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from backend.ai_advisor import generate_rebalancing_plan, build_structured_actions, compute_health_score, generate_fire_summary, generate_tax_summary
from backend.exceptions import ParseError
from backend.parser.parser import parse_statement
from backend.xirr.engine import compute_portfolio_xirr
from backend.fire_planner import compute_fire_plan
from backend.tax_wizard import compute_tax_plan
from backend.report_generator import generate_report

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI(title="NiveshNetra API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------

class FundResultResponse(BaseModel):
    fundName: str
    folioNumber: str
    totalInvested: float
    currentValue: float
    xirr: Optional[float]
    absoluteReturn: float
    category: str
    benchmark: str
    benchmarkXirr: Optional[float]
    expenseRatio: Optional[float]
    expenseDragAnnual: float


class OverlapResponse(BaseModel):
    fundA: str
    fundB: str
    sharedStocks: list[str]
    overlapPct: float


class RebalancingAction(BaseModel):
    type: str          # "exit" | "reduce" | "switch" | "enter" | "action"
    fund: str
    detail: str
    impact: str        # e.g. "saves ₹1,867/yr"


class HealthScoreDimension(BaseModel):
    label: str
    score: int
    insight: str


class AnalysisResponse(BaseModel):
    funds: list[FundResultResponse]
    totalInvested: float
    totalCurrentValue: float
    portfolioXirr: Optional[float]
    absoluteReturn: float
    warnings: list[str]
    overlaps: list[OverlapResponse]
    totalExpenseDragAnnual: float
    rebalancingPlan: str
    rebalancingActions: list[RebalancingAction]
    moneyHealthScore: int
    moneyHealthDimensions: list[HealthScoreDimension]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class ManualInputRequest(BaseModel):
    age: int
    monthlyIncome: float
    monthlySip: float
    riskAppetite: str  # "conservative" | "moderate" | "aggressive"
    goal: str


class FirePlanRequest(BaseModel):
    age: int
    monthlyIncome: float
    monthlyExpenses: float
    existingCorpus: float = 0.0
    monthlySip: float = 0.0
    riskAppetite: str = "moderate"  # "conservative" | "moderate" | "aggressive"
    retirementAge: int = 60


class TaxPlanRequest(BaseModel):
    basicSalary: float
    hra: float = 0.0
    specialAllowance: float = 0.0
    otherAllowance: float = 0.0
    rentPaid: float = 0.0
    cityType: str = "metro"  # "metro" | "non-metro"
    section80C: float = 0.0
    section80D: float = 0.0
    homeLoanInterest: float = 0.0
    npsEmployer: float = 0.0
    otherDeductions: float = 0.0
    existingInvestments: list[str] = []


@app.post("/api/quick-plan")
async def quick_plan(req: ManualInputRequest) -> dict:
    """Generate a mini financial plan without a PDF upload."""
    from backend.ai_advisor import generate_quick_plan
    plan = generate_quick_plan(req.model_dump())
    return {"plan": plan}


@app.post("/api/fire-plan")
async def fire_plan(req: FirePlanRequest) -> dict:
    """Compute FIRE path plan and return structured JSON with AI summary."""
    plan = compute_fire_plan(
        age=req.age,
        monthly_income=req.monthlyIncome,
        monthly_expenses=req.monthlyExpenses,
        existing_corpus=req.existingCorpus,
        monthly_sip=req.monthlySip,
        risk_appetite=req.riskAppetite,
        retirement_age=req.retirementAge,
    )
    plan["aiSummary"] = generate_fire_summary(plan)
    return plan


@app.post("/api/tax-plan")
async def tax_plan(req: TaxPlanRequest) -> dict:
    """Compute old vs new tax regime comparison and return structured JSON."""
    plan = compute_tax_plan(
        basic_salary=req.basicSalary,
        hra=req.hra,
        special_allowance=req.specialAllowance,
        other_allowance=req.otherAllowance,
        rent_paid=req.rentPaid,
        city_type=req.cityType,
        section80c=req.section80C,
        section80d=req.section80D,
        home_loan_interest=req.homeLoanInterest,
        nps_employer=req.npsEmployer,
        other_deductions=req.otherDeductions,
        existing_investments=req.existingInvestments,
    )
    plan["aiSummary"] = generate_tax_summary(plan)
    return plan


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/report")
async def download_report(data: AnalysisResponse) -> Response:
    """Generate a 2-page PDF report from the analysis result."""
    from fastapi.responses import Response
    pdf_bytes = generate_report(data.model_dump())
    today = date.today().strftime("%Y-%m-%d")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="NiveshNetra_Report_{today}.pdf"'},
    )


@app.post("/api/analyse", response_model=AnalysisResponse)
async def analyse(file: UploadFile = File(...)) -> AnalysisResponse:
    pdf_bytes = await file.read()

    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    if not pdf_bytes[:4] == b"%PDF":
        raise HTTPException(status_code=422, detail="File does not appear to be a PDF")

    try:
        holdings = parse_statement(pdf_bytes)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result = compute_portfolio_xirr(holdings)

    warnings = [
        f"Could not compute XIRR for {f.fund_name} — insufficient data"
        for f in result.funds
        if f.xirr is None
    ]

    fund_responses = [
        FundResultResponse(
            fundName=f.fund_name,
            folioNumber=f.folio_number,
            totalInvested=f.total_invested,
            currentValue=f.current_value,
            xirr=f.xirr,
            absoluteReturn=f.absolute_return,
            category=f.category,
            benchmark=f.benchmark,
            benchmarkXirr=f.benchmark_xirr,
            expenseRatio=f.expense_ratio,
            expenseDragAnnual=f.expense_drag_annual,
        )
        for f in result.funds
    ]

    overlap_responses = [
        OverlapResponse(
            fundA=o.fund_a,
            fundB=o.fund_b,
            sharedStocks=o.shared_stocks,
            overlapPct=o.overlap_pct,
        )
        for o in result.overlaps
    ]

    # Build portfolio data dict for AI advisor
    portfolio_data = {
        "funds": [r.model_dump() for r in fund_responses],
        "totalInvested": result.total_invested,
        "totalCurrentValue": result.total_current_value,
        "portfolioXirr": result.portfolio_xirr,
        "overlaps": [o.model_dump() for o in overlap_responses],
        "totalExpenseDragAnnual": result.total_expense_drag_annual,
    }
    rebalancing_plan = generate_rebalancing_plan(portfolio_data)
    actions = build_structured_actions(portfolio_data)
    health = compute_health_score(portfolio_data)

    return AnalysisResponse(
        funds=fund_responses,
        totalInvested=result.total_invested,
        totalCurrentValue=result.total_current_value,
        portfolioXirr=result.portfolio_xirr,
        absoluteReturn=result.absolute_return,
        warnings=warnings,
        overlaps=overlap_responses,
        totalExpenseDragAnnual=result.total_expense_drag_annual,
        rebalancingPlan=rebalancing_plan,
        rebalancingActions=actions,
        moneyHealthScore=health["overall"],
        moneyHealthDimensions=[HealthScoreDimension(**d) for d in health["dimensions"]],
    )
