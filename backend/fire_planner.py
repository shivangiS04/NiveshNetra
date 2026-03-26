"""
FIRE (Financial Independence Retire Early) Path Planner computations.
"""

import math
from datetime import date


INFLATION_RATE = 0.06
WITHDRAWAL_RATE = 0.04  # 4% rule → 25x corpus
RETURN_RATES = {
    "conservative": 0.10,
    "moderate": 0.12,
    "aggressive": 0.14,
}
DEFAULT_RETIREMENT_AGE = 60


def _months_to_fire(
    existing_corpus: float,
    monthly_sip: float,
    annual_return: float,
    target_corpus: float,
) -> int | None:
    """Return number of months until corpus hits target, or None if never in 600 months."""
    monthly_rate = annual_return / 12
    corpus = existing_corpus
    for month in range(1, 601):
        corpus = corpus * (1 + monthly_rate) + monthly_sip
        if corpus >= target_corpus:
            return month
    return None


def _project_corpus_yearly(
    existing_corpus: float,
    monthly_sip: float,
    annual_return: float,
    years: int,
) -> list[float]:
    """Return corpus value at end of each year for `years` years."""
    monthly_rate = annual_return / 12
    corpus = existing_corpus
    result = []
    for year in range(1, years + 1):
        for _ in range(12):
            corpus = corpus * (1 + monthly_rate) + monthly_sip
        result.append(round(corpus, 2))
    return result


def _required_corpus_yearly(
    target_corpus: float,
    years_to_retirement: int,
) -> list[float]:
    """Linear ramp from 0 to target_corpus over years_to_retirement years."""
    if years_to_retirement <= 0:
        return []
    return [
        round(target_corpus * (y / years_to_retirement), 2)
        for y in range(1, years_to_retirement + 1)
    ]


def _sip_gap(
    existing_corpus: float,
    annual_return: float,
    target_corpus: float,
    months_to_retirement: int,
) -> float:
    """
    Additional monthly SIP needed so corpus hits target exactly at retirement.
    Uses FV formula: FV = P*(1+r)^n + SIP*[((1+r)^n - 1)/r]
    Solve for SIP.
    """
    if months_to_retirement <= 0:
        return 0.0
    r = annual_return / 12
    fv_existing = existing_corpus * ((1 + r) ** months_to_retirement)
    sip_fv_factor = ((1 + r) ** months_to_retirement - 1) / r if r > 0 else months_to_retirement
    required_sip = (target_corpus - fv_existing) / sip_fv_factor
    return max(0.0, required_sip)


def compute_fire_plan(
    age: int,
    monthly_income: float,
    monthly_expenses: float,
    existing_corpus: float,
    monthly_sip: float,
    risk_appetite: str,
    retirement_age: int = DEFAULT_RETIREMENT_AGE,
) -> dict:
    annual_return = RETURN_RATES.get(risk_appetite, 0.12)
    years_to_retirement = max(0, retirement_age - age)
    months_to_retirement = years_to_retirement * 12

    # Inflation-adjusted annual expenses at retirement
    annual_expenses_now = monthly_expenses * 12
    annual_expenses_at_retirement = annual_expenses_now * ((1 + INFLATION_RATE) ** years_to_retirement)

    # Target corpus (25x rule)
    target_corpus = annual_expenses_at_retirement / WITHDRAWAL_RATE

    # Project current trajectory
    fire_month = _months_to_fire(existing_corpus, monthly_sip, annual_return, target_corpus)

    today = date.today()
    if fire_month is not None:
        fire_year = today.year + (today.month - 1 + fire_month) // 12
        fire_month_num = (today.month - 1 + fire_month) % 12 + 1
        fire_date_str = date(fire_year, fire_month_num, 1).strftime("%B %Y")
        fire_age = age + fire_month // 12
        years_early = max(0, retirement_age - fire_age)
        on_track = fire_month <= months_to_retirement
    else:
        fire_date_str = "Beyond age 110"
        fire_age = None
        years_early = 0
        on_track = False

    # Projected corpus at retirement
    projected_at_retirement = _project_corpus_yearly(
        existing_corpus, monthly_sip, annual_return, years_to_retirement
    )
    projected_corpus_at_retirement = projected_at_retirement[-1] if projected_at_retirement else existing_corpus

    # SIP gap to retire exactly at 60
    gap_sip = _sip_gap(existing_corpus, annual_return, target_corpus, months_to_retirement)
    additional_sip_needed = max(0.0, gap_sip - monthly_sip)

    # Year-by-year chart data
    current_trajectory = _project_corpus_yearly(
        existing_corpus, monthly_sip, annual_return, years_to_retirement
    )
    required_trajectory = _required_corpus_yearly(target_corpus, years_to_retirement)

    chart_data = [
        {
            "year": age + i + 1,
            "projected": current_trajectory[i] if i < len(current_trajectory) else None,
            "required": required_trajectory[i] if i < len(required_trajectory) else None,
        }
        for i in range(years_to_retirement)
    ]

    # Asset allocation by decade
    asset_allocation = [
        {"decade": "30s", "equity": 80, "debt": 20},
        {"decade": "40s", "equity": 60, "debt": 40},
        {"decade": "50s", "equity": 40, "debt": 60},
    ]

    return {
        "age": age,
        "retirementAge": retirement_age,
        "riskAppetite": risk_appetite,
        "annualReturn": annual_return,
        "yearsToRetirement": years_to_retirement,
        "annualExpensesNow": round(annual_expenses_now, 2),
        "annualExpensesAtRetirement": round(annual_expenses_at_retirement, 2),
        "targetCorpus": round(target_corpus, 2),
        "projectedCorpusAtRetirement": round(projected_corpus_at_retirement, 2),
        "fireDate": fire_date_str,
        "fireAge": fire_age,
        "onTrack": on_track,
        "yearsEarly": years_early,
        "additionalSipNeeded": round(additional_sip_needed, 2),
        "chartData": chart_data,
        "assetAllocation": asset_allocation,
        "aiSummary": "",  # filled by caller
    }
