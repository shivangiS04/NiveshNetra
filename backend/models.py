from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    PURCHASE = "purchase"
    REDEMPTION = "redemption"
    DIVIDEND = "dividend"
    SWITCH_IN = "switch_in"
    SWITCH_OUT = "switch_out"
    SIP = "sip"


@dataclass
class Transaction:
    date: date
    type: TransactionType
    amount: float          # INR; negative = outflow
    units: float
    nav: float
    balance_units: float


@dataclass
class FundHolding:
    fund_name: str
    folio_number: str
    isin: str
    transactions: list[Transaction] = field(default_factory=list)
    current_nav: float = 0.0
    current_units: float = 0.0

    @property
    def current_value(self) -> float:
        return self.current_units * self.current_nav

    @property
    def total_invested(self) -> float:
        return sum(
            abs(t.amount) for t in self.transactions
            if t.type in (TransactionType.PURCHASE, TransactionType.SIP)
        )


@dataclass
class CashFlow:
    date: date
    amount: float   # negative = outflow, positive = inflow


@dataclass
class FundResult:
    fund_name: str
    folio_number: str
    total_invested: float
    current_value: float
    xirr: Optional[float]       # annualised decimal; None if unconverged
    absolute_return: float      # (current_value - invested) / invested


@dataclass
class PortfolioResult:
    funds: list[FundResult]
    total_invested: float
    total_current_value: float
    portfolio_xirr: Optional[float]
    absolute_return: float
