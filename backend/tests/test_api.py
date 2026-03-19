"""Integration tests for the FastAPI backend."""

import io
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.exceptions import ParseError
from backend.models import FundHolding, FundResult, PortfolioResult, Transaction, TransactionType
from datetime import date, timedelta

client = TestClient(app)


def _make_mock_result() -> PortfolioResult:
    return PortfolioResult(
        funds=[
            FundResult(
                fund_name="Axis Bluechip Fund",
                folio_number="12345",
                total_invested=10000.0,
                current_value=12000.0,
                xirr=0.142,
                absolute_return=0.20,
            )
        ],
        total_invested=10000.0,
        total_current_value=12000.0,
        portfolio_xirr=0.142,
        absolute_return=0.20,
    )


def _make_mock_holdings() -> list[FundHolding]:
    return [
        FundHolding(
            fund_name="Axis Bluechip Fund",
            folio_number="12345",
            isin="INF846K01DP8",
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
            current_nav=120.0,
            current_units=100.0,
        )
    ]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# /api/analyse — success path (mocked parser + XIRR)
# ---------------------------------------------------------------------------

def test_analyse_valid_pdf_returns_200():
    mock_holdings = _make_mock_holdings()
    mock_result = _make_mock_result()

    with patch("backend.api.main.parse_statement", return_value=mock_holdings), \
         patch("backend.api.main.compute_portfolio_xirr", return_value=mock_result):

        fake_pdf = b"%PDF-1.4 fake content"
        response = client.post(
            "/api/analyse",
            files={"file": ("statement.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert "funds" in data
    assert "totalInvested" in data
    assert "totalCurrentValue" in data
    assert "portfolioXirr" in data
    assert "absoluteReturn" in data
    assert "warnings" in data
    assert len(data["funds"]) == 1
    assert data["funds"][0]["fundName"] == "Axis Bluechip Fund"


# ---------------------------------------------------------------------------
# /api/analyse — error paths
# ---------------------------------------------------------------------------

def test_analyse_non_pdf_returns_422():
    response = client.post(
        "/api/analyse",
        files={"file": ("notapdf.txt", io.BytesIO(b"This is plain text"), "text/plain")},
    )
    assert response.status_code == 422


def test_analyse_oversized_file_returns_413():
    big_pdf = b"%PDF-1.4 " + b"x" * (21 * 1024 * 1024)
    response = client.post(
        "/api/analyse",
        files={"file": ("big.pdf", io.BytesIO(big_pdf), "application/pdf")},
    )
    assert response.status_code == 413


def test_analyse_parse_error_returns_422():
    with patch("backend.api.main.parse_statement", side_effect=ParseError("Not a CAMS statement")):
        fake_pdf = b"%PDF-1.4 fake"
        response = client.post(
            "/api/analyse",
            files={"file": ("statement.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        )
    assert response.status_code == 422
    assert "Not a CAMS statement" in response.json()["detail"]


def test_analyse_warnings_for_null_xirr():
    mock_holdings = _make_mock_holdings()
    mock_result = PortfolioResult(
        funds=[
            FundResult(
                fund_name="Axis Bluechip Fund",
                folio_number="12345",
                total_invested=10000.0,
                current_value=0.0,
                xirr=None,  # no XIRR
                absolute_return=-1.0,
            )
        ],
        total_invested=10000.0,
        total_current_value=0.0,
        portfolio_xirr=None,
        absolute_return=-1.0,
    )

    with patch("backend.api.main.parse_statement", return_value=mock_holdings), \
         patch("backend.api.main.compute_portfolio_xirr", return_value=mock_result):

        fake_pdf = b"%PDF-1.4 fake"
        response = client.post(
            "/api/analyse",
            files={"file": ("statement.pdf", io.BytesIO(fake_pdf), "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert len(data["warnings"]) == 1
    assert "Axis Bluechip Fund" in data["warnings"][0]
