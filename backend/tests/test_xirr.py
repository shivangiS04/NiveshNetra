"""Unit tests for the XIRR engine."""

from datetime import date, timedelta

import pytest

from backend.exceptions import XIRRError
from backend.models import CashFlow, FundHolding, Transaction, TransactionType
from backend.xirr.engine import (
    _npv,
    build_cash_flows,
    compute_portfolio_xirr,
    compute_xirr,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_holding(
    transactions: list[Transaction],
    current_nav: float = 100.0,
    current_units: float = 100.0,
) -> FundHolding:
    return FundHolding(
        fund_name="Test Fund",
        folio_number="12345",
        isin="INF000000000",
        transactions=transactions,
        current_nav=current_nav,
        current_units=current_units,
    )


def make_txn(
    days_ago: int,
    amount: float,
    txn_type: TransactionType = TransactionType.PURCHASE,
    units: float = 100.0,
    nav: float = 100.0,
) -> Transaction:
    return Transaction(
        date=date.today() - timedelta(days=days_ago),
        type=txn_type,
        amount=amount,
        units=units,
        nav=nav,
        balance_units=units,
    )


# ---------------------------------------------------------------------------
# compute_xirr — known values
# ---------------------------------------------------------------------------

class TestComputeXirr:
    def test_exact_10_percent_annual(self):
        """Invest 1000 today, get back 1100 in exactly 1 year → XIRR ≈ 10%."""
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today, amount=1100.0),
        ]
        rate = compute_xirr(flows)
        assert abs(rate - 0.10) < 0.001

    def test_zero_return(self):
        """Invest 1000, get back exactly 1000 → XIRR ≈ 0%."""
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today, amount=1000.0),
        ]
        rate = compute_xirr(flows)
        assert abs(rate) < 0.001

    def test_negative_return(self):
        """Invest 1000, get back 900 → XIRR < 0."""
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today, amount=900.0),
        ]
        rate = compute_xirr(flows)
        assert rate < 0

    def test_high_return(self):
        """Invest 1000, get back 2000 in 1 year → XIRR ≈ 100%."""
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today, amount=2000.0),
        ]
        rate = compute_xirr(flows)
        assert abs(rate - 1.0) < 0.01

    def test_npv_near_zero_at_solution(self):
        """NPV at the computed XIRR should be approximately zero."""
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today - timedelta(days=180), amount=-500.0),
            CashFlow(date=today, amount=1800.0),
        ]
        rate = compute_xirr(flows)
        assert abs(_npv(rate, flows)) < 1e-4

    def test_raises_with_single_flow(self):
        flows = [CashFlow(date=date.today(), amount=-1000.0)]
        with pytest.raises(XIRRError):
            compute_xirr(flows)

    def test_raises_with_all_outflows(self):
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=-1000.0),
            CashFlow(date=today, amount=-500.0),
        ]
        with pytest.raises(XIRRError):
            compute_xirr(flows)

    def test_raises_with_all_inflows(self):
        today = date.today()
        flows = [
            CashFlow(date=today - timedelta(days=365), amount=1000.0),
            CashFlow(date=today, amount=500.0),
        ]
        with pytest.raises(XIRRError):
            compute_xirr(flows)


# ---------------------------------------------------------------------------
# build_cash_flows
# ---------------------------------------------------------------------------

class TestBuildCashFlows:
    def test_purchase_is_negative(self):
        holding = make_holding([make_txn(365, 10000.0, TransactionType.PURCHASE)])
        flows = build_cash_flows(holding)
        outflows = [f for f in flows if f.amount < 0]
        assert len(outflows) >= 1
        assert outflows[0].amount == -10000.0

    def test_sip_is_negative(self):
        holding = make_holding([make_txn(180, 5000.0, TransactionType.SIP)])
        flows = build_cash_flows(holding)
        outflows = [f for f in flows if f.amount < 0]
        assert any(abs(f.amount) == 5000.0 for f in outflows)

    def test_redemption_is_positive(self):
        holding = make_holding([
            make_txn(365, 10000.0, TransactionType.PURCHASE),
            make_txn(180, 5000.0, TransactionType.REDEMPTION),
        ])
        flows = build_cash_flows(holding)
        inflows = [f for f in flows if f.amount > 0]
        assert any(f.amount == 5000.0 for f in inflows)

    def test_terminal_cash_flow_appended(self):
        holding = make_holding(
            [make_txn(365, 10000.0, TransactionType.PURCHASE)],
            current_nav=120.0,
            current_units=100.0,
        )
        flows = build_cash_flows(holding)
        # Last flow should be today's current value
        assert flows[-1].date == date.today()
        assert flows[-1].amount == 12000.0  # 120 * 100

    def test_zero_current_value_no_terminal_flow(self):
        holding = make_holding(
            [make_txn(365, 10000.0, TransactionType.PURCHASE)],
            current_nav=0.0,
            current_units=0.0,
        )
        flows = build_cash_flows(holding)
        # No terminal inflow when current value is 0
        assert all(f.amount <= 0 for f in flows)

    def test_dividend_skipped(self):
        holding = make_holding([
            make_txn(365, 10000.0, TransactionType.PURCHASE),
            make_txn(180, 500.0, TransactionType.DIVIDEND),
        ])
        flows = build_cash_flows(holding)
        # Dividend should not appear as a separate cash flow
        non_terminal_flows = [f for f in flows if f.date != date.today()]
        assert len(non_terminal_flows) == 1  # only the purchase


# ---------------------------------------------------------------------------
# compute_portfolio_xirr
# ---------------------------------------------------------------------------

class TestComputePortfolioXirr:
    def _make_simple_holding(self, invested: float, current_value: float) -> FundHolding:
        nav = current_value / 100.0
        return FundHolding(
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

    def test_total_invested_is_sum(self):
        h1 = self._make_simple_holding(10000, 12000)
        h2 = self._make_simple_holding(20000, 25000)
        result = compute_portfolio_xirr([h1, h2])
        assert abs(result.total_invested - 30000) < 0.01

    def test_total_current_value_is_sum(self):
        h1 = self._make_simple_holding(10000, 12000)
        h2 = self._make_simple_holding(20000, 25000)
        result = compute_portfolio_xirr([h1, h2])
        assert abs(result.total_current_value - 37000) < 0.01

    def test_fund_xirr_none_on_error(self):
        """A holding with no current value should get xirr=None, not crash."""
        holding = FundHolding(
            fund_name="Broken Fund",
            folio_number="999",
            isin="INF000000001",
            transactions=[
                Transaction(
                    date=date.today() - timedelta(days=365),
                    type=TransactionType.PURCHASE,
                    amount=10000.0,
                    units=100.0,
                    nav=100.0,
                    balance_units=100.0,
                )
            ],
            current_nav=0.0,
            current_units=0.0,
        )
        result = compute_portfolio_xirr([holding])
        assert result.funds[0].xirr is None

    def test_portfolio_xirr_is_finite(self):
        h1 = self._make_simple_holding(10000, 12000)
        result = compute_portfolio_xirr([h1])
        assert result.portfolio_xirr is not None
        assert -1.0 < result.portfolio_xirr < 100.0
