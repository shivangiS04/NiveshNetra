"""
Unit tests for KFintech CAS parser using synthetic transaction strings.
"""

import pytest
from backend.parser.kfintech_parser import (
    detect_kfin_fund_sections,
    extract_kfin_transactions,
    parse_kfintech_statement,
)
from backend.models import TransactionType
from backend.exceptions import ParseError


SAMPLE_KFIN_TEXT = """
KFin Technologies Private Limited
Consolidated Account Statement
Period: 01-Jan-2022 To 15-Mar-2026
Investor: Test User | PAN: ABCPT1234Z

Folio No: 12345678
Mirae Asset Large Cap Fund - Direct Plan - Growth
ISIN: INF769K01010

01-Jan-2022 SIP Purchase 5000.00 142.857 35.0000 142.857
01-Feb-2022 SIP Purchase 5000.00 138.504 36.1000 281.361
01-Mar-2022 SIP Purchase 5000.00 131.926 37.9000 413.287

Closing Balance: 413.287
NAV as on 15-Mar-2026: INR 68.5000

Folio No: 98765432
Axis Bluechip Fund - Direct Plan - Growth
ISIN: INF846K01131

15-Mar-2021 Purchase 50000.00 1315.789 38.0000 1315.789
15-Jun-2021 SIP Purchase 10000.00 243.309 41.1000 1559.098
20-Aug-2023 Redemption -30000.00 -500.000 60.0000 1059.098

Closing Balance: 1059.098
NAV as on 15-Mar-2026: INR 82.3000
"""


def test_detect_two_fund_sections():
    """Should detect exactly 2 fund sections from sample text."""
    sections = detect_kfin_fund_sections(SAMPLE_KFIN_TEXT)
    assert len(sections) == 2


def test_fund_names_extracted():
    """Fund names should be extracted from the line after Folio No."""
    sections = detect_kfin_fund_sections(SAMPLE_KFIN_TEXT)
    names = [s[0] for s in sections]
    assert any("Mirae" in n for n in names)
    assert any("Axis" in n for n in names)


def test_sip_transactions_classified():
    """SIP Purchase lines should be classified as SIP type."""
    section_text = """
Folio No: 12345678
Mirae Asset Large Cap Fund
01-Jan-2022 SIP Purchase 5000.00 142.857 35.0000 142.857
01-Feb-2022 SIP Purchase 5000.00 138.504 36.1000 281.361
"""
    txns = extract_kfin_transactions(section_text)
    assert len(txns) == 2
    assert all(t.type == TransactionType.SIP for t in txns)


def test_redemption_classified():
    """Redemption lines should be classified as REDEMPTION type."""
    section_text = """
Folio No: 98765432
Axis Bluechip Fund
20-Aug-2023 Redemption -30000.00 -500.000 60.0000 1059.098
"""
    txns = extract_kfin_transactions(section_text)
    assert len(txns) == 1
    assert txns[0].type == TransactionType.REDEMPTION
    assert txns[0].amount == -30000.0


def test_parse_raises_on_unrecognised_format():
    """parse_kfintech_statement should raise ParseError on non-KFintech text."""
    with pytest.raises(ParseError, match="KFintech format not recognised"):
        parse_kfintech_statement("This is some random text with no fund sections.")


def test_full_parse_returns_holdings():
    """Full parse of sample text should return 2 FundHolding objects."""
    holdings = parse_kfintech_statement(SAMPLE_KFIN_TEXT)
    assert len(holdings) == 2
    # Each holding should have transactions
    for h in holdings:
        assert len(h.transactions) > 0
    # NAV and units should be populated
    assert holdings[0].current_nav == pytest.approx(68.5, rel=0.01)
    assert holdings[1].current_nav == pytest.approx(82.3, rel=0.01)
