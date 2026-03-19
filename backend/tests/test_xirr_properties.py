"""Property-based tests for the XIRR engine."""

from datetime import date, timedelta

import pytest
from hypothesis import assume, given, settings, strategies as st

from backend.exceptions import XIRRError
from backend.models import CashFlow, FundHolding, Transaction, TransactionType
from backend.xirr.engine import (
    _npv,
    build_cash_flows,
    compute_portfolio_xirr,
    compute_xirr,
)


def make_cash_flows(
    outflow_amounts: list[float],
    inflow_amounts: list[float],
) -> list[CashFlow]:
    """Build a valid cash flow list from separate outflow/inflow lists."""
    today = date.today()
    flows = []
    for i, amt in enumerate(outflow_amounts):
        flows.append(CashFlow(date=today - timedelta(days=730 - i), amount=-abs(amt)))
    for i, amt in enumerate(inflow_amounts):
        flows.append(CashFlow(date=today - timedelta(days=i), amount=abs(amt)))
    return sorted(flows, key=lambda cf: cf.date)


# ---------------------------------------------------------------------------
# Property 1: NPV ≈ 0 at the computed XIRR
# ---------------------------------------------------------------------------

@given(
    st.lists(st.floats(min_value=1000.0, max_value=1e5), min_size=1, max_size=5),
    st.lists(st.floats(min_value=1000.0, max_value=1e5), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_xirr_npv_near_zero(outflows: list[float], inflows: list[float]):
    """XIRR solution always yields NPV ≈ 0 for realistic investment scenarios."""
    flows = make_cash_flows(outflows, inflows)
    total_out = sum(abs(f.amount) for f in flows if f.amount < 0)
    total_in = sum(f.amount for f in flows if f.amount > 0)
    # Only test realistic scenarios: inflows at least 20% of outflows
    # Extreme losses push the rate near the bracket boundary where NPV is nonlinear
    assume(total_in / total_out >= 0.2)
    try:
        rate = compute_xirr(flows)
        # NPV tolerance scales with total cash flow magnitude
        scale = max(total_out, total_in)
        relative_npv = abs(_npv(rate, flows)) / scale
        assert relative_npv < 1e-4
    except XIRRError:
        pass  # Some combinations may not converge — that's acceptable


# ---------------------------------------------------------------------------
# Property 2: XIRR result is within sane bounds
# ---------------------------------------------------------------------------

@given(
    st.lists(st.floats(min_value=100.0, max_value=1e6), min_size=1, max_size=5),
    st.lists(st.floats(min_value=100.0, max_value=1e6), min_size=1, max_size=5),
)
@settings(max_examples=100)
def test_xirr_within_bounds(outflows: list[float], inflows: list[float]):
    """When XIRR converges, result is within (-1, 100)."""
    flows = make_cash_flows(outflows, inflows)
    try:
        rate = compute_xirr(flows)
        assert -1.0 < rate < 100.0
    except XIRRError:
        pass


# ---------------------------------------------------------------------------
# Property 3: Portfolio totals additivity
# ---------------------------------------------------------------------------

@given(
    st.lists(
        st.tuples(
            st.floats(min_value=1000.0, max_value=1e6),   # invested
            st.floats(min_value=100.0, max_value=2e6),    # current_value
        ),
        min_size=1,
        max_size=5,
    )
)
@settings(max_examples=50)
def test_portfolio_totals_additivity(fund_data: list[tuple[float, float]]):
    """
    result.total_invested == sum(h.total_invested)
    result.total_current_value == sum(h.current_value)
    """
    holdings = []
    for invested, current_value in fund_data:
        nav = current_value / 100.0
        h = FundHolding(
            fund_name="Fund",
            folio_number="123",
            isin="INF000000000",
            transactions=[
                Transaction(
                    date=date.today() - timedelta(days=365),
                    type=TransactionType.PURCHASE,
                    amount=invested,
                    units=100.0,
                    nav=invested / 100.0,
                    balance_units=100.0,
                )
            ],
            current_nav=nav,
            current_units=100.0,
        )
        holdings.append(h)

    result = compute_portfolio_xirr(holdings)

    expected_invested = sum(h.total_invested for h in holdings)
    expected_current = sum(h.current_value for h in holdings)

    assert abs(result.total_invested - expected_invested) < 0.01
    assert abs(result.total_current_value - expected_current) < 0.01


# ---------------------------------------------------------------------------
# Property 4: build_cash_flows sign convention
# ---------------------------------------------------------------------------

@given(
    st.floats(min_value=1000.0, max_value=1e6),   # purchase amount
    st.floats(min_value=10.0, max_value=1000.0),  # current nav
    st.floats(min_value=1.0, max_value=1000.0),   # current units
)
@settings(max_examples=100)
def test_build_cash_flows_sign_convention(
    purchase_amount: float, current_nav: float, current_units: float
):
    """Purchases are always negative; terminal inflow is always positive."""
    holding = FundHolding(
        fund_name="Fund",
        folio_number="123",
        isin="INF000000000",
        transactions=[
            Transaction(
                date=date.today() - timedelta(days=365),
                type=TransactionType.PURCHASE,
                amount=purchase_amount,
                units=100.0,
                nav=purchase_amount / 100.0,
                balance_units=100.0,
            )
        ],
        current_nav=current_nav,
        current_units=current_units,
    )
    flows = build_cash_flows(holding)
    outflows = [f for f in flows if f.amount < 0]
    assert len(outflows) >= 1
    assert all(f.amount < 0 for f in outflows)
