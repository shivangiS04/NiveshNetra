"""NiveshNetra FastAPI backend."""

from dataclasses import asdict
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.exceptions import ParseError, XIRRError
from backend.parser.parser import parse_statement
from backend.xirr.engine import compute_portfolio_xirr

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB

app = FastAPI(title="NiveshNetra API", version="1.0.0")

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


class AnalysisResponse(BaseModel):
    funds: list[FundResultResponse]
    totalInvested: float
    totalCurrentValue: float
    portfolioXirr: Optional[float]
    absoluteReturn: float
    warnings: list[str]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/api/analyse", response_model=AnalysisResponse)
async def analyse(file: UploadFile = File(...)) -> AnalysisResponse:
    # File size check
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 20 MB)")

    # Magic bytes check
    if not pdf_bytes[:4] == b"%PDF":
        raise HTTPException(status_code=422, detail="File does not appear to be a PDF")

    # Parse
    try:
        holdings = parse_statement(pdf_bytes)
    except ParseError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    # Compute XIRR
    result = compute_portfolio_xirr(holdings)

    # Build warnings for funds where XIRR could not be computed
    warnings = [
        f"Could not compute XIRR for {f.fund_name} — insufficient data"
        for f in result.funds
        if f.xirr is None
    ]

    return AnalysisResponse(
        funds=[
            FundResultResponse(
                fundName=f.fund_name,
                folioNumber=f.folio_number,
                totalInvested=f.total_invested,
                currentValue=f.current_value,
                xirr=f.xirr,
                absoluteReturn=f.absolute_return,
            )
            for f in result.funds
        ],
        totalInvested=result.total_invested,
        totalCurrentValue=result.total_current_value,
        portfolioXirr=result.portfolio_xirr,
        absoluteReturn=result.absolute_return,
        warnings=warnings,
    )
