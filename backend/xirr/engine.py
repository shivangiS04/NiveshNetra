"""
XIRR computation engine.

Uses scipy.optimize.brentq to solve the XIRR equation:
  sum( amount_i / (1 + r)^(days_i / 365) ) = 0
"""

from datetime import date
from typing import Optional

import scipy.optimize

from backend.exceptions import XIRRError
from backend.fund_data import compute_overlap, find_fund_meta
from backend.models import (
    CashFlow,
    FundHolding,
    FundResult,
    OverlapResult,
    PortfolioResult,
    TransactionType,
)

# Sign convention
OUTFLOW_TYPES = {TransactionType.PURCHASE, TransactionType.SIP, TransactionType.SWITCH_IN}
INFLOW_TYPES = {TransactionType.REDEMPTION, TransactionType.SWITCH_OUT}


# ---------------------------------------------------------------------------
# Cash flow builder
# ---------------------------------------------------------------------------

def build_cash_flows(holding: FundHolding) -> list[CashFlow]:
    """
    Convert a FundHolding's transactions into a signed cash flow series,
    appending the current market value as the terminal inflow.

    PRECONDITIONS:
      - holding.transactions is non-empty
      - holding.current_nav >= 0
      - holding.current_units >= 0

    POSTCONDITIONS:
      - Purchases/SIPs → negative amounts (outflows)
      - Redemptions/switch-outs → positive amounts (inflows)
      - Final entry is (today, current_value) as terminal inflow
      - List is sorted by date ascending
    """
    flows: list[CashFlow] = []

    for txn in sorted(holding.transactions, key=lambda t: t.date):
        if txn.type in OUTFLOW_TYPES:
            flows.append(CashFlow(date=txn.date, amount=-abs(txn.amount)))
        elif txn.type in INFLOW_TYPES:
            flows.append(CashFlow(date=txn.date, amount=+abs(txn.amount)))
        # DIVIDEND: skip — reinvestment already captured as a purchase transaction

    # Terminal cash flow: current market value as of today
    current_value = holding.current_value
    if current_value > 0:
        flows.append(CashFlow(date=date.today(), amount=current_value))

    return flows


# ---------------------------------------------------------------------------
# XIRR core
# ---------------------------------------------------------------------------

def _npv(rate: float, cash_flows: list[CashFlow]) -> float:
    """Net present value at the given rate."""
    t0 = cash_flows[0].date
    return sum(
        cf.amount / (1.0 + rate) ** ((cf.date - t0).days / 365.0)
        for cf in cash_flows
    )


def compute_xirr(cash_flows: list[CashFlow]) -> float:
    """
    Compute XIRR for a series of dated cash flows using Brent's method.

    PRECONDITIONS:
      - len(cash_flows) >= 2
      - At least one cash_flow.amount < 0 (investment)
      - At least one cash_flow.amount > 0 (return / current value)
      - cash_flows are sorted by date ascending

    POSTCONDITIONS:
      - Returns r such that NPV(r) ≈ 0
      - -1.0 < r < 100.0
      - Raises XIRRError if no solution converges
    """
    if len(cash_flows) < 2:
        raise XIRRError("Need at least 2 cash flows to compute XIRR")

    has_outflow = any(cf.amount < 0 for cf in cash_flows)
    has_inflow = any(cf.amount > 0 for cf in cash_flows)
    if not has_outflow or not has_inflow:
        raise XIRRError("Cash flows must contain both outflows and inflows")

    try:
        rate = scipy.optimize.brentq(
            _npv,
            -0.999,
            100.0,
            args=(cash_flows,),
            xtol=1e-6,
            maxiter=1000,
        )
        return float(rate)
    except ValueError as exc:
        raise XIRRError(
            f"No XIRR solution found — check cash flows have a sign change: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Portfolio-level computation
# ---------------------------------------------------------------------------

def compute_portfolio_xirr(holdings: list[FundHolding]) -> PortfolioResult:
    """
    Compute per-fund XIRR and aggregate portfolio XIRR.
    Also enriches results with fund metadata (category, benchmark, expense ratio, overlap).
    """
    fund_results: list[FundResult] = []
    all_cash_flows: list[CashFlow] = []
    holdings_meta = []

    for holding in holdings:
        flows = build_cash_flows(holding)
        all_cash_flows.extend(flows)

        xirr: Optional[float] = None
        try:
            xirr = compute_xirr(flows)
        except XIRRError:
            pass

        invested = holding.total_invested
        current = holding.current_value
        abs_return = (current - invested) / invested if invested > 0 else 0.0

        # Enrich with fund metadata
        meta = find_fund_meta(holding.fund_name, holding.isin)
        expense_drag = (meta.expense_ratio * current) if meta else 0.0
        if meta:
            holdings_meta.append((holding.fund_name, meta))

        fund_results.append(FundResult(
            fund_name=holding.fund_name,
            folio_number=holding.folio_number,
            total_invested=invested,
            current_value=current,
            xirr=xirr,
            absolute_return=abs_return,
            category=meta.category if meta else "",
            benchmark=meta.benchmark if meta else "",
            benchmark_xirr=meta.benchmark_xirr_5y if meta else None,
            expense_ratio=meta.expense_ratio if meta else None,
            expense_drag_annual=expense_drag,
        ))

    total_invested = sum(h.total_invested for h in holdings)
    total_current = sum(h.current_value for h in holdings)
    abs_return = (total_current - total_invested) / total_invested if total_invested > 0 else 0.0
    total_expense_drag = sum(f.expense_drag_annual for f in fund_results)

    portfolio_xirr: Optional[float] = None
    if all_cash_flows:
        all_cash_flows_sorted = sorted(all_cash_flows, key=lambda cf: cf.date)
        try:
            portfolio_xirr = compute_xirr(all_cash_flows_sorted)
        except XIRRError:
            pass

    # Compute overlaps
    raw_overlaps = compute_overlap(holdings_meta)
    overlaps = [
        OverlapResult(
            fund_a=o["fundA"],
            fund_b=o["fundB"],
            shared_stocks=o["sharedStocks"],
            overlap_pct=o["overlapPct"],
        )
        for o in raw_overlaps
    ]

    return PortfolioResult(
        funds=fund_results,
        total_invested=total_invested,
        total_current_value=total_current,
        portfolio_xirr=portfolio_xirr,
        absolute_return=abs_return,
        overlaps=overlaps,
        total_expense_drag_annual=total_expense_drag,
    )
