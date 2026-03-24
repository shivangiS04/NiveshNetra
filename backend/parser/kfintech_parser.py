"""
KFintech (formerly Karvy) CAS PDF parser.

KFintech format differences from CAMS:
  - Header contains "KFin Technologies" or "Karvy"
  - "Folio No: XXXXXXXX" appears on its own line before the fund name
  - Transaction lines: DD-MMM-YYYY  [type]  Amount  Units  NAV  Balance
"""

import re
from datetime import date, datetime

from backend.exceptions import ParseError
from backend.models import FundHolding, Transaction, TransactionType

# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# KFintech folio line: "Folio No: 12345678"  (no ISIN on same line)
KFIN_FOLIO_PATTERN = re.compile(
    r"Folio\s+No\s*[:\-]\s*(?P<folio>\S+)",
    re.IGNORECASE,
)

# ISIN may appear separately
KFIN_ISIN_PATTERN = re.compile(
    r"ISIN\s*[:\-]\s*(?P<isin>[A-Z]{2}[A-Z0-9]{10})",
    re.IGNORECASE,
)

# Transaction row (KFintech includes Units and NAV columns)
KFIN_TXN_PATTERN = re.compile(
    r"(?P<date>\d{2}-[A-Za-z]{3}-\d{4})"
    r"\s+(?P<desc>[^\d\-]+?)\s+"
    r"(?P<amount>[\-\d,]+\.\d{2,4})\s+"
    r"(?P<units>[\-\d,]+\.\d{2,4})\s+"
    r"(?P<nav>[\d,]+\.\d{2,4})\s+"
    r"(?P<balance>[\-\d,]+\.\d{2,4})",
)

KFIN_CLOSING_PATTERN = re.compile(
    r"Closing\s+(?:Unit\s+)?Balance\s*[:\-]?\s*(?P<units>[\d,]+\.\d{2,4})",
    re.IGNORECASE,
)

KFIN_NAV_PATTERN = re.compile(
    r"NAV\s+(?:as\s+on|on)\s+\d{2}-[A-Za-z]{3}-\d{4}\s*[:\-]?\s*(?:INR\s*)?(?P<nav>[\d,]+\.\d{2,4})",
    re.IGNORECASE,
)

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


def _classify(desc: str) -> TransactionType:
    for pattern, txn_type in DESC_TYPE_MAP:
        if pattern.search(desc):
            return txn_type
    return TransactionType.PURCHASE


# ---------------------------------------------------------------------------
# Section detection
# ---------------------------------------------------------------------------

def detect_kfin_fund_sections(full_text: str) -> list[tuple[str, str]]:
    """
    Split KFintech PDF text into (fund_name, section_text) pairs.

    In KFintech format, "Folio No: XXXX" appears BEFORE the fund name line.
    """
    lines = full_text.splitlines()
    sections: list[tuple[str, str]] = []
    section_starts: list[tuple[int, str, str]] = []  # (line_idx, fund_name, folio)

    for i, line in enumerate(lines):
        m = KFIN_FOLIO_PATTERN.search(line)
        if m:
            folio = m.group("folio").strip()
            # Fund name is the non-empty line AFTER the folio line
            fund_name = ""
            for j in range(i + 1, min(i + 4, len(lines))):
                candidate = lines[j].strip()
                if candidate and not KFIN_FOLIO_PATTERN.search(candidate):
                    fund_name = candidate
                    break
            section_starts.append((i, fund_name, folio))

    for idx, (line_idx, fund_name, _folio) in enumerate(section_starts):
        end_line = (
            section_starts[idx + 1][0]
            if idx + 1 < len(section_starts)
            else len(lines)
        )
        section_text = "\n".join(lines[line_idx:end_line])
        sections.append((fund_name, section_text))

    return sections


def extract_kfin_transactions(section_text: str) -> list[Transaction]:
    transactions: list[Transaction] = []
    for m in KFIN_TXN_PATTERN.finditer(section_text):
        try:
            transactions.append(Transaction(
                date=_parse_date(m.group("date")),
                type=_classify(m.group("desc").strip()),
                amount=_parse_float(m.group("amount")),
                units=_parse_float(m.group("units")),
                nav=_parse_float(m.group("nav")),
                balance_units=_parse_float(m.group("balance")),
            ))
        except (ValueError, AttributeError):
            continue
    return sorted(transactions, key=lambda t: t.date)


def _extract_closing_units(section_text: str) -> float:
    m = KFIN_CLOSING_PATTERN.search(section_text)
    if m:
        return _parse_float(m.group("units"))
    txn_matches = list(KFIN_TXN_PATTERN.finditer(section_text))
    if txn_matches:
        return _parse_float(txn_matches[-1].group("balance"))
    return 0.0


def _extract_current_nav(section_text: str) -> float:
    m = KFIN_NAV_PATTERN.search(section_text)
    if m:
        return _parse_float(m.group("nav"))
    txn_matches = list(KFIN_TXN_PATTERN.finditer(section_text))
    if txn_matches:
        return _parse_float(txn_matches[-1].group("nav"))
    return 0.0


def _extract_folio(section_text: str) -> str:
    m = KFIN_FOLIO_PATTERN.search(section_text)
    return m.group("folio") if m else ""


def _extract_isin(section_text: str) -> str:
    m = KFIN_ISIN_PATTERN.search(section_text)
    return m.group("isin") if m else ""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_kfintech_statement(full_text: str) -> list[FundHolding]:
    """
    Parse KFintech CAS text and return structured holdings.

    PRECONDITIONS:
      - full_text is non-empty
      - Text is from a KFintech CAS PDF

    POSTCONDITIONS:
      - Returns list of FundHolding with at least one entry
      - Raises ParseError if format not recognised
    """
    sections = detect_kfin_fund_sections(full_text)
    if not sections:
        raise ParseError("KFintech format not recognised")

    holdings: list[FundHolding] = []
    for fund_name, section_text in sections:
        transactions = extract_kfin_transactions(section_text)
        if not transactions:
            continue
        holdings.append(FundHolding(
            fund_name=fund_name or "Unknown Fund",
            folio_number=_extract_folio(section_text),
            isin=_extract_isin(section_text),
            transactions=transactions,
            current_nav=_extract_current_nav(section_text),
            current_units=_extract_closing_units(section_text),
        ))

    if not holdings:
        raise ParseError("KFintech format not recognised")

    return holdings
