"""
CAMS Consolidated Account Statement PDF parser.

CAMS statements have a consistent structure:
  - Fund name on its own line
  - "Folio No: XXXXXXX / ISIN: INXXXXXXXX" on the next line
  - Transaction rows: Date | Description | Amount | Units | NAV | Balance
"""

import io
import re
from datetime import date, datetime
from typing import Optional

import pdfplumber

from backend.exceptions import ParseError
from backend.models import FundHolding, Transaction, TransactionType

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches the folio/ISIN header line that starts each fund section
FOLIO_PATTERN = re.compile(
    r"Folio\s+No\s*[:\-]\s*(?P<folio>[^\s/]+)"
    r"(?:.*?ISIN\s*[:\-]\s*(?P<isin>[A-Z]{2}[A-Z0-9]{10}))?",
    re.IGNORECASE,
)

# Transaction row: DD-Mon-YYYY  Description  Amount  Units  NAV  Balance
TXN_PATTERN = re.compile(
    r"(?P<date>\d{2}-[A-Za-z]{3}-\d{4})"          # 01-Jan-2023
    r"\s+(?P<desc>[^\d\-]+?)\s+"                   # description (non-greedy)
    r"(?P<amount>[\-\d,]+\.\d{2,4})\s+"            # amount (may be negative)
    r"(?P<units>[\-\d,]+\.\d{2,4})\s+"             # units
    r"(?P<nav>[\d,]+\.\d{2,4})\s+"                 # NAV
    r"(?P<balance>[\-\d,]+\.\d{2,4})",             # balance units
)

# Closing balance line — gives us current units
CLOSING_BALANCE_PATTERN = re.compile(
    r"Closing\s+Unit\s+Balance\s*[:\-]?\s*(?P<units>[\d,]+\.\d{2,4})",
    re.IGNORECASE,
)

# Current NAV line
CURRENT_NAV_PATTERN = re.compile(
    r"NAV\s+on\s+\d{2}-[A-Za-z]{3}-\d{4}\s*[:\-]?\s*(?:INR\s*)?(?P<nav>[\d,]+\.\d{2,4})",
    re.IGNORECASE,
)

# Description → TransactionType mapping
DESC_TYPE_MAP: list[tuple[re.Pattern, TransactionType]] = [
    (re.compile(r"redemption|redeem", re.I), TransactionType.REDEMPTION),
    (re.compile(r"switch\s*out", re.I), TransactionType.SWITCH_OUT),
    (re.compile(r"switch\s*in", re.I), TransactionType.SWITCH_IN),
    (re.compile(r"dividend", re.I), TransactionType.DIVIDEND),
    (re.compile(r"sip|systematic", re.I), TransactionType.SIP),
    (re.compile(r"purchase|invest|subscription|allot", re.I), TransactionType.PURCHASE),
]


def _parse_float(s: str) -> float:
    return float(s.replace(",", ""))


def _parse_date(s: str) -> date:
    return datetime.strptime(s.strip(), "%d-%b-%Y").date()


def _classify_transaction(description: str) -> TransactionType:
    for pattern, txn_type in DESC_TYPE_MAP:
        if pattern.search(description):
            return txn_type
    return TransactionType.PURCHASE  # default fallback


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def detect_fund_sections(full_text: str) -> list[tuple[str, str]]:
    """
    Split full PDF text into (fund_name, section_text) pairs.

    PRECONDITIONS:
      - full_text is non-empty
      - CAMS format uses "Folio No:" as section delimiter

    POSTCONDITIONS:
      - Returns list of (fund_name, section_text) tuples
      - Each section_text contains all transaction lines for that fund
    """
    lines = full_text.splitlines()
    sections: list[tuple[str, str]] = []
    section_start_indices: list[tuple[int, str, str]] = []  # (line_idx, fund_name, folio)

    for i, line in enumerate(lines):
        m = FOLIO_PATTERN.search(line)
        if m:
            # Fund name is typically the non-empty line immediately before the folio line
            fund_name = ""
            for j in range(i - 1, max(i - 4, -1), -1):
                candidate = lines[j].strip()
                if candidate and not FOLIO_PATTERN.search(candidate):
                    fund_name = candidate
                    break
            folio = m.group("folio").strip()
            section_start_indices.append((i, fund_name, folio))

    for idx, (line_idx, fund_name, _folio) in enumerate(section_start_indices):
        end_line = (
            section_start_indices[idx + 1][0]
            if idx + 1 < len(section_start_indices)
            else len(lines)
        )
        section_text = "\n".join(lines[line_idx:end_line])
        sections.append((fund_name, section_text))

    return sections


def extract_transactions(section_text: str) -> list[Transaction]:
    """
    Extract individual transactions from a fund section's text.

    POSTCONDITIONS:
      - Returns list of Transaction objects sorted by date ascending
    """
    transactions: list[Transaction] = []

    for m in TXN_PATTERN.finditer(section_text):
        try:
            txn_date = _parse_date(m.group("date"))
            desc = m.group("desc").strip()
            amount = _parse_float(m.group("amount"))
            units = _parse_float(m.group("units"))
            nav = _parse_float(m.group("nav"))
            balance = _parse_float(m.group("balance"))
            txn_type = _classify_transaction(desc)

            transactions.append(Transaction(
                date=txn_date,
                type=txn_type,
                amount=amount,
                units=units,
                nav=nav,
                balance_units=balance,
            ))
        except (ValueError, AttributeError):
            continue  # skip malformed rows

    return sorted(transactions, key=lambda t: t.date)


def _extract_current_units(section_text: str) -> float:
    m = CLOSING_BALANCE_PATTERN.search(section_text)
    if m:
        return _parse_float(m.group("units"))
    # Fallback: last balance_units from transactions
    txn_matches = list(TXN_PATTERN.finditer(section_text))
    if txn_matches:
        return _parse_float(txn_matches[-1].group("balance"))
    return 0.0


def _extract_current_nav(section_text: str) -> float:
    m = CURRENT_NAV_PATTERN.search(section_text)
    if m:
        return _parse_float(m.group("nav"))
    # Fallback: last NAV from transactions
    txn_matches = list(TXN_PATTERN.finditer(section_text))
    if txn_matches:
        return _parse_float(txn_matches[-1].group("nav"))
    return 0.0


def _extract_isin(section_text: str) -> str:
    m = FOLIO_PATTERN.search(section_text)
    if m and m.group("isin"):
        return m.group("isin")
    return ""


def _extract_folio(section_text: str) -> str:
    m = FOLIO_PATTERN.search(section_text)
    if m:
        return m.group("folio")
    return ""


def parse_statement(pdf_bytes: bytes) -> list[FundHolding]:
    """
    Parse a CAMS PDF statement and return structured holdings.

    PRECONDITIONS:
      - pdf_bytes is non-empty
      - Bytes represent a valid PDF (starts with %PDF)
      - PDF is a CAMS consolidated account statement

    POSTCONDITIONS:
      - Returns list of FundHolding with at least one entry
      - Each FundHolding.transactions is non-empty
      - Raises ParseError if PDF is unreadable or not a CAMS statement
    """
    if not pdf_bytes:
        raise ParseError("Empty file provided")

    if not pdf_bytes[:4] == b"%PDF":
        raise ParseError("File does not appear to be a PDF")

    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            full_text = "\n".join(
                page.extract_text() or "" for page in pdf.pages
            )
    except Exception as exc:
        raise ParseError(f"Could not extract text from PDF: {exc}") from exc

    if not full_text.strip():
        raise ParseError("PDF contains no extractable text")

    sections = detect_fund_sections(full_text)
    if not sections:
        raise ParseError("PDF does not appear to be a CAMS statement — no fund sections found")

    holdings: list[FundHolding] = []
    for fund_name, section_text in sections:
        transactions = extract_transactions(section_text)
        if not transactions:
            continue  # skip sections with no parseable transactions

        holding = FundHolding(
            fund_name=fund_name or "Unknown Fund",
            folio_number=_extract_folio(section_text),
            isin=_extract_isin(section_text),
            transactions=transactions,
            current_nav=_extract_current_nav(section_text),
            current_units=_extract_current_units(section_text),
        )
        holdings.append(holding)

    if not holdings:
        raise ParseError("No fund holdings with transactions found in statement")

    return holdings
