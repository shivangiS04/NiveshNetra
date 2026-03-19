"""Property-based tests for the PDF parser."""

from hypothesis import given, settings, strategies as st

from backend.parser.parser import detect_fund_sections, extract_transactions


@given(st.text())
@settings(max_examples=200)
def test_detect_fund_sections_idempotent(text: str):
    """detect_fund_sections is pure — same input always gives same output."""
    assert detect_fund_sections(text) == detect_fund_sections(text)


@given(st.text())
@settings(max_examples=200)
def test_extract_transactions_idempotent(text: str):
    """extract_transactions is pure — same input always gives same output."""
    assert extract_transactions(text) == extract_transactions(text)


@given(st.text())
@settings(max_examples=200)
def test_detect_fund_sections_returns_list(text: str):
    """detect_fund_sections always returns a list (never raises on arbitrary text)."""
    result = detect_fund_sections(text)
    assert isinstance(result, list)


@given(st.text())
@settings(max_examples=200)
def test_extract_transactions_sorted(text: str):
    """extract_transactions always returns transactions sorted by date."""
    txns = extract_transactions(text)
    dates = [t.date for t in txns]
    assert dates == sorted(dates)
