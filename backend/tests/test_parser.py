"""Unit tests for the CAMS PDF parser."""

import pytest

from backend.exceptions import ParseError
from backend.models import TransactionType
from backend.parser.parser import (
    detect_fund_sections,
    extract_transactions,
    parse_statement,
)

# ---------------------------------------------------------------------------
# Fixture text helpers
# ---------------------------------------------------------------------------

SINGLE_FUND_TEXT = """
CAMS Consolidated Account Statement

Axis Bluechip Fund - Growth
Folio No: 1234567890 / ISIN: INF846K01DP8

Date        Description                     Amount      Units       NAV         Balance
01-Jan-2022 Purchase                        10000.00    100.000     100.0000    100.000
01-Feb-2022 SIP                             5000.00     48.000      104.1667    148.000
01-Mar-2023 Redemption                      5000.00     -45.000     111.1111    103.000

Closing Unit Balance: 103.000
NAV on 01-Jan-2024: 130.5000
"""

MULTI_FUND_TEXT = """
CAMS Consolidated Account Statement

Axis Bluechip Fund - Growth
Folio No: 1234567890 / ISIN: INF846K01DP8

Date        Description                     Amount      Units       NAV         Balance
01-Jan-2022 Purchase                        10000.00    100.000     100.0000    100.000
01-Feb-2022 SIP                             5000.00     48.000      104.1667    148.000

Closing Unit Balance: 148.000
NAV on 01-Jan-2024: 130.5000

HDFC Mid-Cap Opportunities Fund - Growth
Folio No: 9876543210 / ISIN: INF179K01VQ8

Date        Description                     Amount      Units       NAV         Balance
15-Mar-2022 Purchase                        20000.00    200.000     100.0000    200.000
15-Apr-2022 SIP                             5000.00     47.000      106.3830    247.000

Closing Unit Balance: 247.000
NAV on 01-Jan-2024: 155.2000
"""


# ---------------------------------------------------------------------------
# detect_fund_sections
# ---------------------------------------------------------------------------

class TestDetectFundSections:
    def test_single_fund(self):
        sections = detect_fund_sections(SINGLE_FUND_TEXT)
        assert len(sections) == 1
        fund_name, section_text = sections[0]
        assert "Axis Bluechip" in fund_name
        assert "Folio No" in section_text

    def test_multi_fund(self):
        sections = detect_fund_sections(MULTI_FUND_TEXT)
        assert len(sections) == 2
        names = [s[0] for s in sections]
        assert any("Axis" in n for n in names)
        assert any("HDFC" in n for n in names)

    def test_empty_text_returns_empty(self):
        assert detect_fund_sections("") == []

    def test_no_folio_returns_empty(self):
        assert detect_fund_sections("Some random text without folio numbers") == []


# ---------------------------------------------------------------------------
# extract_transactions
# ---------------------------------------------------------------------------

class TestExtractTransactions:
    def test_extracts_purchase(self):
        txns = extract_transactions(SINGLE_FUND_TEXT)
        purchases = [t for t in txns if t.type == TransactionType.PURCHASE]
        assert len(purchases) >= 1
        assert purchases[0].amount == 10000.00
        assert purchases[0].units == 100.0

    def test_extracts_sip(self):
        txns = extract_transactions(SINGLE_FUND_TEXT)
        sips = [t for t in txns if t.type == TransactionType.SIP]
        assert len(sips) >= 1

    def test_extracts_redemption(self):
        txns = extract_transactions(SINGLE_FUND_TEXT)
        redemptions = [t for t in txns if t.type == TransactionType.REDEMPTION]
        assert len(redemptions) >= 1

    def test_sorted_by_date(self):
        txns = extract_transactions(SINGLE_FUND_TEXT)
        dates = [t.date for t in txns]
        assert dates == sorted(dates)

    def test_empty_section_returns_empty(self):
        assert extract_transactions("No transactions here") == []


# ---------------------------------------------------------------------------
# parse_statement — error cases (no real PDF needed)
# ---------------------------------------------------------------------------

class TestParseStatementErrors:
    def test_empty_bytes_raises(self):
        with pytest.raises(ParseError, match="Empty file"):
            parse_statement(b"")

    def test_non_pdf_bytes_raises(self):
        with pytest.raises(ParseError, match="does not appear to be a PDF"):
            parse_statement(b"This is not a PDF at all")

    def test_invalid_pdf_bytes_raises(self):
        # Starts with %PDF but is not a valid PDF
        with pytest.raises(ParseError):
            parse_statement(b"%PDF-1.4 garbage data that cannot be parsed")
