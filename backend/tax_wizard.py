"""
Indian Income Tax Wizard — FY 2024-25
Old regime vs New regime comparison for salaried employees.
"""


def _hra_exemption(basic: float, hra: float, rent_paid: float, city_type: str) -> float:
    """Compute HRA exemption under old regime."""
    if rent_paid <= 0 or hra <= 0:
        return 0.0
    city_pct = 0.50 if city_type == "metro" else 0.40
    actual_hra = hra
    rent_minus_10pct = max(0, rent_paid - 0.10 * basic)
    pct_of_basic = city_pct * basic
    return min(actual_hra, rent_minus_10pct, pct_of_basic)


def _old_regime_tax(taxable_income: float) -> float:
    """Compute tax under old regime slabs (FY 2024-25)."""
    slabs = [
        (250000, 0.0),
        (250000, 0.05),
        (500000, 0.20),
        (float("inf"), 0.30),
    ]
    tax = 0.0
    remaining = max(0, taxable_income)
    for slab_size, rate in slabs:
        if remaining <= 0:
            break
        taxable = min(remaining, slab_size)
        tax += taxable * rate
        remaining -= taxable
    # Rebate u/s 87A: if income ≤ 5L, tax = 0
    if taxable_income <= 500000:
        tax = 0.0
    return tax


def _new_regime_tax(taxable_income: float) -> float:
    """Compute tax under new regime slabs (FY 2024-25)."""
    slabs = [
        (300000, 0.0),
        (400000, 0.05),
        (300000, 0.10),
        (200000, 0.15),
        (300000, 0.20),
        (float("inf"), 0.30),
    ]
    tax = 0.0
    remaining = max(0, taxable_income)
    for slab_size, rate in slabs:
        if remaining <= 0:
            break
        taxable = min(remaining, slab_size)
        tax += taxable * rate
        remaining -= taxable
    # Rebate u/s 87A: if income ≤ 7L, tax = 0
    if taxable_income <= 700000:
        tax = 0.0
    return tax


def _tax_saving_recommendations(
    section80c_used: float,
    existing_investments: list[str],
) -> list[dict]:
    """Rank tax-saving instruments by impact and liquidity."""
    recs = []
    gap_80c = max(0, 150000 - section80c_used)

    instruments = [
        {
            "name": "ELSS (Equity Linked Savings Scheme)",
            "maxBenefit": min(gap_80c, 150000),
            "section": "80C",
            "lockIn": "3 years",
            "risk": "High",
            "taxSaving": round(min(gap_80c, 150000) * 0.30),
            "alreadyCovered": any("elss" in inv.lower() or "equity" in inv.lower() for inv in existing_investments),
        },
        {
            "name": "PPF (Public Provident Fund)",
            "maxBenefit": min(gap_80c, 150000),
            "section": "80C",
            "lockIn": "15 years",
            "risk": "Low",
            "taxSaving": round(min(gap_80c, 150000) * 0.30),
            "alreadyCovered": False,
        },
        {
            "name": "NPS (National Pension System) — Tier I",
            "maxBenefit": 50000,
            "section": "80CCD(1B)",
            "lockIn": "Till retirement",
            "risk": "Medium",
            "taxSaving": round(50000 * 0.30),
            "alreadyCovered": False,
        },
        {
            "name": "Health Insurance Premium",
            "maxBenefit": 25000,
            "section": "80D",
            "lockIn": "1 year",
            "risk": "None",
            "taxSaving": round(25000 * 0.30),
            "alreadyCovered": False,
        },
    ]
    # Only show instruments with actual benefit
    return [i for i in instruments if i["maxBenefit"] > 0]


def compute_tax_plan(
    basic_salary: float,
    hra: float,
    special_allowance: float,
    other_allowance: float,
    rent_paid: float,
    city_type: str,
    section80c: float,
    section80d: float,
    home_loan_interest: float,
    nps_employer: float,
    other_deductions: float,
    existing_investments: list[str],
) -> dict:
    gross_income = basic_salary + hra + special_allowance + other_allowance

    # --- Old Regime ---
    hra_exempt = _hra_exemption(basic_salary, hra, rent_paid, city_type)
    std_deduction_old = 50000
    deduction_80c = min(section80c, 150000)
    deduction_80d = min(section80d, 25000)
    deduction_24b = min(home_loan_interest, 200000)
    deduction_80ccd2 = nps_employer  # no cap for employer NPS

    total_deductions_old = (
        hra_exempt + std_deduction_old + deduction_80c +
        deduction_80d + deduction_24b + deduction_80ccd2 + other_deductions
    )
    taxable_old = max(0, gross_income - total_deductions_old)
    tax_old_base = _old_regime_tax(taxable_old)
    cess_old = tax_old_base * 0.04
    tax_old_total = round(tax_old_base + cess_old, 2)

    # --- New Regime ---
    std_deduction_new = 75000
    taxable_new = max(0, gross_income - std_deduction_new - deduction_80ccd2)
    tax_new_base = _new_regime_tax(taxable_new)
    cess_new = tax_new_base * 0.04
    tax_new_total = round(tax_new_base + cess_new, 2)

    # Winner
    if tax_old_total < tax_new_total:
        winner = "old"
        savings = round(tax_new_total - tax_old_total, 2)
    elif tax_new_total < tax_old_total:
        winner = "new"
        savings = round(tax_old_total - tax_new_total, 2)
    else:
        winner = "tie"
        savings = 0.0

    # Missing deductions
    missing = []
    gap_80c = max(0, 150000 - section80c)
    if gap_80c > 0:
        missing.append({
            "section": "80C",
            "gap": round(gap_80c),
            "potentialSaving": round(gap_80c * 0.30),
            "message": f"You're leaving ₹{gap_80c:,.0f} of 80C unused — invest more in ELSS/PPF to save ₹{round(gap_80c*0.30):,} in tax",
        })
    gap_80d = max(0, 25000 - section80d)
    if gap_80d > 0:
        missing.append({
            "section": "80D",
            "gap": round(gap_80d),
            "potentialSaving": round(gap_80d * 0.30),
            "message": f"₹{gap_80d:,.0f} of 80D health insurance deduction unused",
        })

    recommendations = _tax_saving_recommendations(section80c, existing_investments)

    return {
        "grossIncome": round(gross_income, 2),
        "oldRegime": {
            "hraExemption": round(hra_exempt, 2),
            "standardDeduction": std_deduction_old,
            "deduction80C": round(deduction_80c, 2),
            "deduction80D": round(deduction_80d, 2),
            "deduction24B": round(deduction_24b, 2),
            "deduction80CCD2": round(deduction_80ccd2, 2),
            "totalDeductions": round(total_deductions_old, 2),
            "taxableIncome": round(taxable_old, 2),
            "taxBeforeCess": round(tax_old_base, 2),
            "cess": round(cess_old, 2),
            "totalTax": tax_old_total,
        },
        "newRegime": {
            "standardDeduction": std_deduction_new,
            "taxableIncome": round(taxable_new, 2),
            "taxBeforeCess": round(tax_new_base, 2),
            "cess": round(cess_new, 2),
            "totalTax": tax_new_total,
        },
        "winner": winner,
        "savings": savings,
        "missingDeductions": missing,
        "recommendations": recommendations,
        "aiSummary": "",  # filled by caller
    }
