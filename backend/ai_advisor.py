"""
AI-generated rebalancing plan.
Primary: Groq (free) — llama-3.3-70b-versatile
Fallback: rule-based advice

Get a free Groq key at: https://console.groq.com
Set it as GROQ_API_KEY in your .env file.
"""

import os


def _build_prompt(funds, overlaps, total_invested, total_current, portfolio_xirr, expense_drag):
    xirr_display = f"{portfolio_xirr*100:.2f}%" if portfolio_xirr else "N/A"
    fund_lines = []
    for f in funds:
        xirr_str = f"{f['xirr']*100:.1f}%" if f.get("xirr") is not None else "N/A"
        bench_str = f"{f['benchmarkXirr']*100:.1f}%" if f.get("benchmarkXirr") else "N/A"
        er_str = f"{f['expenseRatio']*100:.2f}%" if f.get("expenseRatio") else "N/A"
        alloc = f["currentValue"] / total_current * 100 if total_current > 0 else 0
        fund_lines.append(
            f"- {f['fundName']} | {f.get('category','')} | "
            f"Alloc: {alloc:.1f}% | XIRR: {xirr_str} | Benchmark: {bench_str} | ER: {er_str}"
        )

    overlap_lines = [
        f"- {o['fundA'].split()[0]} ↔ {o['fundB'].split()[0]}: "
        f"{round(o['overlapPct']*100)}% overlap ({', '.join(o['sharedStocks'][:3])})"
        for o in overlaps[:3]
    ]

    return f"""You are a SEBI-registered financial advisor for Indian retail investors.

Portfolio:
- Invested: ₹{total_invested:,.0f} | Current: ₹{total_current:,.0f}
- Portfolio XIRR: {xirr_display}
- Annual fee drag: ₹{expense_drag:,.0f}

Funds:
{chr(10).join(fund_lines)}

Overlaps:
{chr(10).join(overlap_lines) if overlap_lines else "None significant"}

Give a specific, actionable rebalancing plan in exactly 4-5 bullet points. Rules:
- Name specific funds to exit or reduce, with exact rupee amounts or SIP changes
- Suggest specific Direct plan alternatives where relevant (e.g. "switch from Mirae Regular to Mirae Direct — saves ₹X/yr")
- Quantify the benefit (fees saved, expected XIRR improvement)
- End with ONE concrete action to take THIS month (specific fund, specific amount)
- Use Indian number formatting (₹ symbol, lakhs)
- Under 200 words total"""


def _rule_based_plan(funds: list, overlaps: list, total_expense_drag: float) -> str:
    lines = []

    underperformers = [
        f for f in funds
        if f.get("xirr") is not None and f.get("benchmarkXirr") is not None
        and f["xirr"] < f["benchmarkXirr"] - 0.02
    ]
    if underperformers:
        names = ", ".join(" ".join(f["fundName"].split()[:3]) for f in underperformers[:2])
        lines.append(
            f"- **Underperformers detected:** {names} are lagging their benchmark by >2%. "
            "Consider switching to index funds for these categories."
        )

    high_overlap = [o for o in overlaps if o.get("overlapPct", 0) >= 0.4]
    if high_overlap:
        o = high_overlap[0]
        lines.append(
            f"- **High overlap:** {o['fundA'].split()[0]} and {o['fundB'].split()[0]} share "
            f"{round(o['overlapPct']*100)}% of top holdings ({', '.join(o['sharedStocks'][:3])}). "
            "You're paying double fees for the same stocks — consider consolidating."
        )

    if total_expense_drag > 5000:
        savings = round(total_expense_drag * 0.4)
        lines.append(
            f"- **Expense drag:** You're losing ₹{round(total_expense_drag):,}/year in fees. "
            f"Switching to Direct plans could save ~₹{savings:,}/year."
        )

    categories = {f.get("category", "") for f in funds}
    if "Small Cap" in categories and "Large Cap" not in categories:
        lines.append(
            "- **Risk concentration:** You have Small Cap exposure but no Large Cap anchor. "
            "Add a Large Cap or index fund for stability."
        )

    if not lines:
        lines.append(
            "- **Portfolio looks healthy.** Continue your SIPs consistently and review annually."
        )

    lines.append(
        "- **This month's action:** Review your oldest fund's performance vs its benchmark. "
        "If it has underperformed for 3+ consecutive years, consider switching to a Direct index fund."
    )

    return "\n".join(lines)


def _try_groq(prompt: str, api_key: str) -> str | None:
    try:
        from groq import Groq  # type: ignore
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.7,
        )
        text = response.choices[0].message.content
        print("[AI] used Groq llama-3.3-70b-versatile")
        return text
    except Exception as e:
        print(f"[Groq error] {e}")
        return None


def generate_rebalancing_plan(portfolio_data: dict) -> str:
    funds = portfolio_data.get("funds", [])
    total_invested = portfolio_data.get("totalInvested", 0)
    total_current = portfolio_data.get("totalCurrentValue", 0)
    portfolio_xirr = portfolio_data.get("portfolioXirr")
    overlaps = portfolio_data.get("overlaps", [])
    expense_drag = portfolio_data.get("totalExpenseDragAnnual", 0)

    groq_key = os.environ.get("GROQ_API_KEY", "")

    if groq_key:
        prompt = _build_prompt(funds, overlaps, total_invested, total_current, portfolio_xirr, expense_drag)
        result = _try_groq(prompt, groq_key)
        if result:
            return result

    return _rule_based_plan(funds, overlaps, expense_drag)


def generate_quick_plan(inputs: dict) -> str:
    """Generate a mini financial plan from manual inputs (no PDF needed)."""
    age = inputs.get("age", 30)
    income = inputs.get("monthlyIncome", 50000)
    sip = inputs.get("monthlySip", 5000)
    risk = inputs.get("riskAppetite", "moderate")
    goal = inputs.get("goal", "retirement")

    groq_key = os.environ.get("GROQ_API_KEY", "")

    prompt = f"""You are a SEBI-registered financial advisor for Indian retail investors.

User profile:
- Age: {age} years
- Monthly income: ₹{income:,.0f}
- Current monthly SIP: ₹{sip:,.0f} ({sip/income*100:.1f}% of income)
- Risk appetite: {risk}
- Primary goal: {goal}

Give a personalised 4-5 bullet financial plan. Include:
- Recommended monthly SIP amount and fund categories (e.g. 60% large cap index, 30% flexi cap, 10% small cap)
- Whether current SIP rate is sufficient for the goal
- One specific Direct plan fund recommendation per category
- Emergency fund check (should be 6x monthly expenses)
- One action to take this week
Under 200 words. Use ₹ and Indian number formatting."""

    if groq_key:
        result = _try_groq(prompt, groq_key)
        if result:
            return result

    # Rule-based fallback
    sip_pct = sip / income * 100
    years_to_retire = max(1, 60 - age)
    recommended_sip = round(income * 0.20 / 500) * 500
    lines = [
        f"- **SIP rate:** You're investing {sip_pct:.0f}% of income. "
        f"Target 20% (₹{recommended_sip:,}/mo) for long-term wealth creation.",
        f"- **Allocation for {risk} risk:** "
        + ("60% large-cap index + 30% flexi cap + 10% debt" if risk == "conservative"
           else "50% flexi cap + 30% large-cap index + 20% small cap" if risk == "aggressive"
           else "60% large-cap index + 25% flexi cap + 15% small cap"),
        f"- **Goal — {goal}:** With ₹{sip:,}/mo SIP over {years_to_retire} years at 12% XIRR, "
        f"you could build ₹{round(sip * ((1.01**( years_to_retire*12)-1)/0.01) / 100000):.0f}L corpus.",
        "- **Emergency fund:** Keep 6 months of expenses in a liquid fund before increasing equity SIPs.",
        "- **This week's action:** Open a Direct plan account on MF Central (mfcentral.com) — zero commission, same funds, lower fees.",
    ]
    return "\n".join(lines)


def build_structured_actions(portfolio_data: dict) -> list[dict]:
    """
    Build a deterministic list of structured rebalancing action cards from portfolio data.
    These are always present regardless of AI availability.
    """
    funds = portfolio_data.get("funds", [])
    overlaps = portfolio_data.get("overlaps", [])
    total_current = portfolio_data.get("totalCurrentValue", 0)
    expense_drag = portfolio_data.get("totalExpenseDragAnnual", 0)
    actions = []

    # 1. Switch Regular → Direct for each fund
    switch_actions = []
    for f in funds:
        er = f.get("expenseRatio") or 0
        drag = f.get("expenseDragAnnual") or 0
        if er > 0.01 and drag > 500:
            raw = " ".join(f["fundName"].split()[:4]).rstrip(" -,.")
            savings = round(drag * 0.4)  # matches ExpenseRadar 0.4 multiplier
            switch_actions.append({
                "type": "switch",
                "fund": raw,
                "detail": "Switch from Regular to Direct plan",
                "impact": f"saves ~₹{savings:,}/yr in fees",
                "_savings": savings,
            })
    # Sort by savings descending so highest-impact switch is first
    switch_actions.sort(key=lambda x: x["_savings"], reverse=True)
    for a in switch_actions:
        del a["_savings"]
    actions.extend(switch_actions)

    # 2. Reduce high-overlap pairs
    high_overlap = [o for o in overlaps if o.get("overlapPct", 0) >= 0.6]
    for o in high_overlap[:1]:
        a_short = " ".join(o["fundA"].split()[:3]).rstrip(" -,.")
        b_short = " ".join(o["fundB"].split()[:3]).rstrip(" -,.")
        actions.append({
            "type": "reduce",
            "fund": a_short,
            "detail": f"{round(o['overlapPct']*100)}% overlap with {b_short} — consolidate into one fund",
            "impact": "eliminates duplicate fee payment",
        })

    # 3. Exit underperformers
    underperformers = [
        f for f in funds
        if f.get("xirr") is not None and f.get("benchmarkXirr") is not None
        and f["xirr"] < f["benchmarkXirr"] - 0.02
    ]
    for f in underperformers[:2]:
        short = " ".join(f["fundName"].split()[:4]).rstrip(" -,.")
        gap = round((f["benchmarkXirr"] - f["xirr"]) * 100, 1)
        actions.append({
            "type": "exit",
            "fund": short,
            "detail": f"Underperforming benchmark by {gap}% — consider switching to index fund",
            "impact": f"potential +{gap}% XIRR improvement",
        })

    # 4. Top 2 action cards — highest-savings switches first
    switch_cards = [a for a in actions if a["type"] == "switch"]
    if switch_cards:
        for sw in switch_cards[:2]:
            actions.append({
                "type": "action",
                "fund": "This month",
                "detail": f"Log in to MF Central (mfcentral.com) and switch {sw['fund']} to Direct plan",
                "impact": sw["impact"],
            })
    else:
        actions.append({
            "type": "action",
            "fund": "This month",
            "detail": "Review each fund's 3-year performance vs benchmark — exit any with consistent underperformance",
            "impact": "keeps portfolio on track",
        })

    return actions


def generate_fire_summary(plan: dict) -> str:
    """Generate a 3-sentence personalised FIRE plan summary using Groq."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    age = plan.get("age", 30)
    risk = plan.get("riskAppetite", "moderate")
    fire_date = plan.get("fireDate", "")
    target = plan.get("targetCorpus", 0)
    projected = plan.get("projectedCorpusAtRetirement", 0)
    gap_sip = plan.get("additionalSipNeeded", 0)
    on_track = plan.get("onTrack", False)

    prompt = f"""You are a SEBI-registered financial advisor. Write exactly 3 sentences summarising this FIRE plan for an Indian investor.

Profile: Age {age}, {risk} risk appetite
Target corpus: ₹{target:,.0f} (= ₹{target/1e7:.2f} crore)
Projected corpus at 60: ₹{projected:,.0f} (= ₹{projected/1e7:.2f} crore)
FIRE date: {fire_date}
On track: {on_track}
Additional SIP needed: ₹{gap_sip:,.0f}/month

Be specific, encouraging, and use Indian number formatting (₹, lakhs, crores). Under 80 words."""

    if groq_key:
        result = _try_groq(prompt, groq_key)
        if result:
            return result

    # Fallback
    if on_track:
        return (
            f"Great news — at your current {risk} investment pace, you're on track to reach your ₹{target/1e7:.1f}Cr FIRE target by {fire_date}. "
            f"Your projected corpus of ₹{projected/1e7:.1f}Cr at age 60 comfortably covers 25x your inflation-adjusted expenses. "
            "Keep your SIPs consistent and review your asset allocation each decade as suggested."
        )
    else:
        return (
            f"Your current trajectory projects ₹{projected/1e7:.1f}Cr at age 60, which falls short of the ₹{target/1e7:.1f}Cr target. "
            f"Increasing your monthly SIP by ₹{gap_sip:,.0f} will close this gap and help you retire on time. "
            "Consider shifting to more equity-heavy funds in your 30s to maximise compounding over the long horizon."
        )


def generate_tax_summary(plan: dict) -> str:
    """Generate a tax recommendations paragraph using Groq."""
    groq_key = os.environ.get("GROQ_API_KEY", "")
    winner = plan.get("winner", "new")
    savings = plan.get("savings", 0)
    missing = plan.get("missingDeductions", [])
    gross = plan.get("grossIncome", 0)

    missing_text = "; ".join(m["message"] for m in missing[:2]) if missing else "all major deductions are claimed"

    prompt = f"""You are a SEBI-registered tax advisor for Indian salaried employees. Write a 3-sentence tax recommendation paragraph.

Gross income: ₹{gross:,.0f}
Better regime: {winner} regime saves ₹{savings:,.0f}
Missing deductions: {missing_text}

Be specific and actionable. Use Indian number formatting. Under 80 words."""

    if groq_key:
        result = _try_groq(prompt, groq_key)
        if result:
            return result

    regime_name = "Old" if winner == "old" else "New"
    return (
        f"Based on your income profile, the {regime_name} Tax Regime saves you ₹{savings:,.0f} this financial year. "
        f"{missing[0]['message'] + '.' if missing else 'You have claimed all major deductions.'} "
        "Review your investments before March 31 to maximise deductions and file your ITR under the optimal regime."
    )


def compute_health_score(portfolio_data: dict) -> dict:
    """
    Compute Money Health Score from portfolio data.
    Returns overall score (0-100) and per-dimension breakdown.
    Mirrors the frontend MoneyHealthScore component logic.
    """
    funds = portfolio_data.get("funds", [])
    overlaps = portfolio_data.get("overlaps", [])
    total_current = portfolio_data.get("totalCurrentValue", 0)
    expense_drag = portfolio_data.get("totalExpenseDragAnnual", 0)
    portfolio_xirr = portfolio_data.get("portfolioXirr") or 0

    categories = {f.get("category", "") for f in funds if f.get("category")}
    high_overlap = sum(1 for o in overlaps if o.get("overlapPct", 0) >= 0.5)
    diversification = max(20, min(100, int(
        (len(categories) / 4) * 60 + (40 if high_overlap == 0 else 20 if high_overlap == 1 else 0)
    )))

    expense_ratio = expense_drag / total_current if total_current > 0 else 0
    expense_efficiency = max(10, min(100, int(
        100 - ((expense_ratio - 0.005) / (0.02 - 0.005)) * 80
    )))

    return_quality = max(10, min(100, int((portfolio_xirr / 0.15) * 100)))

    funds_with_bench = [f for f in funds if f.get("xirr") is not None and f.get("benchmarkXirr") is not None]
    beaters = [f for f in funds_with_bench if (f.get("xirr") or 0) >= (f.get("benchmarkXirr") or 0)]
    benchmark_alignment = int((len(beaters) / len(funds_with_bench)) * 100) if funds_with_bench else 50

    corpus_growth = min(100, int((total_current / 500000) * 60 + 20))
    consistency = min(100, len(funds) * 20 + 20)

    dimensions = [
        {"label": "Diversification", "score": diversification,
         "insight": f"{high_overlap} overlap pair(s) >50%" if high_overlap else f"{len(categories)} categories"},
        {"label": "Expense Efficiency", "score": expense_efficiency,
         "insight": f"{expense_ratio*100:.2f}% avg expense ratio"},
        {"label": "Return Quality", "score": return_quality,
         "insight": f"XIRR {portfolio_xirr*100:.1f}% vs 12% target"},
        {"label": "Benchmark Alignment", "score": benchmark_alignment,
         "insight": f"{len(beaters)}/{len(funds_with_bench)} funds beating benchmark"},
        {"label": "Corpus Growth", "score": corpus_growth,
         "insight": f"₹{total_current/100000:.1f}L portfolio value"},
        {"label": "Consistency", "score": consistency,
         "insight": f"{len(funds)} fund(s) tracked"},
    ]
    overall = round(sum(d["score"] for d in dimensions) / len(dimensions))
    return {"overall": overall, "dimensions": dimensions}
