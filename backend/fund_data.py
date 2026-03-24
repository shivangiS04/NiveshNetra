"""
Static fund metadata database.
Contains expense ratios, benchmark, category, and top holdings for common Indian MFs.
Used for overlap analysis, expense ratio drag, and benchmark comparison.
"""

from dataclasses import dataclass, field


@dataclass
class FundMeta:
    isin: str
    name_keywords: list[str]          # substrings to match fund name (lowercase)
    category: str                      # Large Cap, Flexi Cap, Small Cap, etc.
    benchmark: str                     # Index name
    benchmark_xirr_5y: float           # 5-year annualised benchmark return (decimal)
    expense_ratio: float               # Annual expense ratio (decimal, e.g. 0.0165)
    top_holdings: list[str]            # Top 10 stock names


FUND_DB: list[FundMeta] = [
    FundMeta(
        isin="INF769K01010",
        name_keywords=["mirae asset large cap", "mirae asset emerging bluechip"],
        category="Large Cap",
        benchmark="Nifty 100 TRI",
        benchmark_xirr_5y=0.148,
        expense_ratio=0.0154,
        top_holdings=[
            "HDFC Bank", "Reliance Industries", "ICICI Bank", "Infosys",
            "TCS", "Axis Bank", "Larsen & Toubro", "Kotak Mahindra Bank",
            "Bajaj Finance", "HUL",
        ],
    ),
    FundMeta(
        isin="INF846K01131",
        name_keywords=["axis bluechip", "axis blue chip"],
        category="Large Cap",
        benchmark="Nifty 50 TRI",
        benchmark_xirr_5y=0.142,
        expense_ratio=0.0165,
        top_holdings=[
            "HDFC Bank", "Infosys", "TCS", "ICICI Bank", "Reliance Industries",
            "Bajaj Finance", "Kotak Mahindra Bank", "Avenue Supermarts",
            "Titan Company", "HUL",
        ],
    ),
    FundMeta(
        isin="INF879O01019",
        name_keywords=["parag parikh flexi cap", "ppfas flexi cap", "parag parikh long term"],
        category="Flexi Cap",
        benchmark="Nifty 500 TRI",
        benchmark_xirr_5y=0.162,
        expense_ratio=0.0158,
        top_holdings=[
            "HDFC Bank", "Bajaj Holdings", "ITC", "Coal India",
            "Alphabet (Google)", "Microsoft", "Meta Platforms",
            "Amazon", "Power Grid", "ICICI Bank",
        ],
    ),
    FundMeta(
        isin="INF200K01RD0",
        name_keywords=["sbi small cap"],
        category="Small Cap",
        benchmark="Nifty Smallcap 250 TRI",
        benchmark_xirr_5y=0.198,
        expense_ratio=0.0168,
        top_holdings=[
            "Blue Star", "Chalet Hotels", "Finolex Cables", "Garware Technical Fibres",
            "Hawkins Cookers", "Kalpataru Projects", "Lemon Tree Hotels",
            "Mold-Tek Packaging", "Safari Industries", "Sharda Cropchem",
        ],
    ),
    FundMeta(
        isin="INF179K01BB8",
        name_keywords=["hdfc mid cap opportunities", "hdfc midcap"],
        category="Mid Cap",
        benchmark="Nifty Midcap 150 TRI",
        benchmark_xirr_5y=0.212,
        expense_ratio=0.0172,
        top_holdings=[
            "Cholamandalam Investment", "Persistent Systems", "Tube Investments",
            "Coforge", "Max Financial Services", "Bharat Forge",
            "Sundaram Finance", "Voltas", "Mphasis", "Indian Hotels",
        ],
    ),
    FundMeta(
        isin="INF174K01LS2",
        name_keywords=["kotak flexi cap", "kotak standard multicap"],
        category="Flexi Cap",
        benchmark="Nifty 500 TRI",
        benchmark_xirr_5y=0.155,
        expense_ratio=0.0162,
        top_holdings=[
            "HDFC Bank", "Reliance Industries", "ICICI Bank", "Infosys",
            "TCS", "Axis Bank", "Larsen & Toubro", "Bajaj Finance",
            "Maruti Suzuki", "Sun Pharma",
        ],
    ),
    FundMeta(
        isin="INF204K01B64",
        name_keywords=["nippon india small cap", "reliance small cap"],
        category="Small Cap",
        benchmark="Nifty Smallcap 250 TRI",
        benchmark_xirr_5y=0.198,
        expense_ratio=0.0175,
        top_holdings=[
            "KPIT Technologies", "Tube Investments", "Karur Vysya Bank",
            "Apar Industries", "Bharat Electronics", "Dixon Technologies",
            "Kaynes Technology", "Techno Electric", "Ratnamani Metals", "Epigral",
        ],
    ),
    FundMeta(
        isin="INF090I01239",
        name_keywords=["franklin india prima", "franklin india smaller companies"],
        category="Small Cap",
        benchmark="Nifty Smallcap 250 TRI",
        benchmark_xirr_5y=0.198,
        expense_ratio=0.0182,
        top_holdings=[
            "Cholamandalam Investment", "Persistent Systems", "Coforge",
            "Mphasis", "Birlasoft", "KPIT Technologies", "Cyient",
            "Mastek", "Zensar Technologies", "Hexaware",
        ],
    ),
]


def find_fund_meta(fund_name: str, isin: str = "") -> FundMeta | None:
    """Match a fund by ISIN first, then by name keywords."""
    name_lower = fund_name.lower()

    # Try ISIN match first
    if isin:
        for meta in FUND_DB:
            if meta.isin == isin:
                return meta

    # Fallback: keyword match
    for meta in FUND_DB:
        if any(kw in name_lower for kw in meta.name_keywords):
            return meta

    return None


def compute_overlap(holdings_meta: list[tuple[str, FundMeta]]) -> list[dict]:
    """
    Compute pairwise fund overlap based on shared top holdings.
    Returns list of {fund_a, fund_b, shared_stocks, overlap_pct}.
    """
    results = []
    for i in range(len(holdings_meta)):
        for j in range(i + 1, len(holdings_meta)):
            name_a, meta_a = holdings_meta[i]
            name_b, meta_b = holdings_meta[j]
            set_a = set(meta_a.top_holdings)
            set_b = set(meta_b.top_holdings)
            shared = sorted(set_a & set_b)
            if shared:
                overlap_pct = len(shared) / min(len(set_a), len(set_b))
                results.append({
                    "fundA": name_a,
                    "fundB": name_b,
                    "sharedStocks": shared,
                    "overlapPct": round(overlap_pct, 3),
                })
    return sorted(results, key=lambda x: -x["overlapPct"])
