"""
Generates a realistic mock CAS PDF for testing NiveshNetra.

Usage:
    python generate_mock_statement.py                    # CAMS format
    python generate_mock_statement.py --format kfintech  # KFintech format
    python generate_mock_statement.py --format cams      # CAMS format (explicit)
"""

import argparse
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

FUNDS = [
    {
        "name": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
        "folio": "12345678 / 01",
        "isin": "INF769K01010",
        "transactions": [
            ("01-Jan-2022", "SIP Purchase",        "5000.00",  "142.857",  "35.0000",  "142.857"),
            ("01-Feb-2022", "SIP Purchase",        "5000.00",  "138.504",  "36.1000",  "281.361"),
            ("01-Mar-2022", "SIP Purchase",        "5000.00",  "131.926",  "37.9000",  "413.287"),
            ("01-Apr-2022", "SIP Purchase",        "5000.00",  "128.205",  "39.0000",  "541.492"),
            ("01-May-2022", "SIP Purchase",        "5000.00",  "125.000",  "40.0000",  "666.492"),
            ("01-Jun-2022", "SIP Purchase",        "5000.00",  "121.951",  "41.0000",  "788.443"),
            ("01-Jul-2022", "SIP Purchase",        "5000.00",  "119.048",  "42.0000",  "907.491"),
            ("01-Aug-2022", "SIP Purchase",        "5000.00",  "116.279",  "43.0000", "1023.770"),
            ("01-Sep-2022", "SIP Purchase",        "5000.00",  "113.636",  "44.0000", "1137.406"),
            ("01-Oct-2022", "SIP Purchase",        "5000.00",  "111.111",  "45.0000", "1248.517"),
            ("01-Nov-2022", "SIP Purchase",        "5000.00",  "108.696",  "46.0000", "1357.213"),
            ("01-Dec-2022", "SIP Purchase",        "5000.00",  "106.383",  "47.0000", "1463.596"),
            ("01-Jan-2023", "SIP Purchase",        "5000.00",  "104.167",  "48.0000", "1567.763"),
            ("01-Feb-2023", "SIP Purchase",        "5000.00",  "102.041",  "49.0000", "1669.804"),
            ("01-Mar-2023", "SIP Purchase",        "5000.00",  "100.000",  "50.0000", "1769.804"),
        ],
        "closing_units": "1769.804",
        "nav_date": "15-Mar-2026",
        "current_nav": "68.5000",
    },
    {
        "name": "Axis Bluechip Fund - Regular Plan - Growth",
        "folio": "98765432 / 01",
        "isin": "INF846K01131",
        "transactions": [
            ("15-Mar-2021", "Purchase",           "50000.00",  "1315.789",  "38.0000",  "1315.789"),
            ("15-Jun-2021", "SIP Purchase",       "10000.00",   "243.309",  "41.1000",  "1559.098"),
            ("15-Sep-2021", "SIP Purchase",       "10000.00",   "232.558",  "43.0000",  "1791.656"),
            ("15-Dec-2021", "SIP Purchase",       "10000.00",   "222.222",  "45.0000",  "2013.878"),
            ("15-Mar-2022", "SIP Purchase",       "10000.00",   "212.766",  "47.0000",  "2226.644"),
            ("15-Jun-2022", "SIP Purchase",       "10000.00",   "204.082",  "49.0000",  "2430.726"),
            ("15-Sep-2022", "SIP Purchase",       "10000.00",   "196.078",  "51.0000",  "2626.804"),
            ("15-Dec-2022", "SIP Purchase",       "10000.00",   "188.679",  "53.0000",  "2815.483"),
            ("15-Mar-2023", "SIP Purchase",       "10000.00",   "181.818",  "55.0000",  "2997.301"),
            ("15-Jun-2023", "SIP Purchase",       "10000.00",   "175.439",  "57.0000",  "3172.740"),
            ("20-Aug-2023", "Redemption",        "-30000.00",  "-500.000",  "60.0000",  "2672.740"),
            ("15-Sep-2023", "SIP Purchase",       "10000.00",   "163.934",  "61.0000",  "2836.674"),
            ("15-Dec-2023", "SIP Purchase",       "10000.00",   "158.730",  "63.0000",  "2995.404"),
            ("15-Mar-2024", "SIP Purchase",       "10000.00",   "153.846",  "65.0000",  "3149.250"),
        ],
        "closing_units": "3149.250",
        "nav_date": "15-Mar-2026",
        "current_nav": "82.3000",
    },
    {
        "name": "Parag Parikh Flexi Cap Fund - Regular Plan - Growth",
        "folio": "11223344 / 01",
        "isin": "INF879O01019",
        "transactions": [
            ("01-Apr-2020", "Purchase",           "25000.00",   "892.857",  "28.0000",   "892.857"),
            ("01-Jul-2020", "SIP Purchase",        "5000.00",   "161.290",  "31.0000",  "1054.147"),
            ("01-Oct-2020", "SIP Purchase",        "5000.00",   "147.059",  "34.0000",  "1201.206"),
            ("01-Jan-2021", "SIP Purchase",        "5000.00",   "135.135",  "37.0000",  "1336.341"),
            ("01-Apr-2021", "SIP Purchase",        "5000.00",   "125.000",  "40.0000",  "1461.341"),
            ("01-Jul-2021", "SIP Purchase",        "5000.00",   "115.741",  "43.2000",  "1577.082"),
            ("01-Oct-2021", "SIP Purchase",        "5000.00",   "107.527",  "46.5000",  "1684.609"),
            ("01-Jan-2022", "SIP Purchase",        "5000.00",   "100.000",  "50.0000",  "1784.609"),
            ("01-Apr-2022", "SIP Purchase",        "5000.00",    "93.458",  "53.5000",  "1878.067"),
            ("01-Jul-2022", "SIP Purchase",        "5000.00",    "87.719",  "57.0000",  "1965.786"),
            ("01-Oct-2022", "SIP Purchase",        "5000.00",    "82.645",  "60.5000",  "2048.431"),
            ("01-Jan-2023", "SIP Purchase",        "5000.00",    "78.125",  "64.0000",  "2126.556"),
            ("01-Apr-2023", "SIP Purchase",        "5000.00",    "73.529",  "68.0000",  "2200.085"),
            ("01-Jul-2023", "SIP Purchase",        "5000.00",    "69.444",  "72.0000",  "2269.529"),
            ("01-Oct-2023", "SIP Purchase",        "5000.00",    "65.789",  "76.0000",  "2335.318"),
            ("01-Jan-2024", "SIP Purchase",        "5000.00",    "62.500",  "80.0000",  "2397.818"),
        ],
        "closing_units": "2397.818",
        "nav_date": "15-Mar-2026",
        "current_nav": "95.7500",
    },
    {
        "name": "SBI Small Cap Fund - Regular Plan - Growth",
        "folio": "55667788 / 01",
        "isin": "INF200K01RD0",
        "transactions": [
            ("01-Jun-2021", "Purchase",           "20000.00",   "285.714",  "70.0000",   "285.714"),
            ("01-Sep-2021", "SIP Purchase",        "3000.00",    "38.961",  "77.0000",   "324.675"),
            ("01-Dec-2021", "SIP Purchase",        "3000.00",    "36.145",  "83.0000",   "360.820"),
            ("01-Mar-2022", "SIP Purchase",        "3000.00",    "33.708",  "89.0000",   "394.528"),
            ("01-Jun-2022", "SIP Purchase",        "3000.00",    "31.579",  "95.0000",   "426.107"),
            ("01-Sep-2022", "SIP Purchase",        "3000.00",    "29.703", "101.0000",   "455.810"),
            ("01-Dec-2022", "SIP Purchase",        "3000.00",    "28.037", "107.0000",   "483.847"),
            ("01-Mar-2023", "SIP Purchase",        "3000.00",    "26.549", "113.0000",   "510.396"),
            ("01-Jun-2023", "SIP Purchase",        "3000.00",    "25.210", "119.0000",   "535.606"),
            ("01-Sep-2023", "SIP Purchase",        "3000.00",    "24.000", "125.0000",   "559.606"),
            ("01-Dec-2023", "SIP Purchase",        "3000.00",    "22.901", "131.0000",   "582.507"),
            ("01-Mar-2024", "SIP Purchase",        "3000.00",    "21.898", "137.0000",   "604.405"),
        ],
        "closing_units": "604.405",
        "nav_date": "15-Mar-2026",
        "current_nav": "158.2500",
    },
]


def build_cams_pdf(output: str) -> None:
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>CAMS - Computer Age Management Services</b>", styles["Title"]))
    story.append(Paragraph("Consolidated Account Statement", styles["Heading2"]))
    story.append(Paragraph("Period: 01-Jan-2020 To 15-Mar-2026", styles["Normal"]))
    story.append(Paragraph("Investor: Shivangi Singh | PAN: ABCPS1234Z", styles["Normal"]))
    story.append(Spacer(1, 8*mm))

    for fund in FUNDS:
        story.append(Paragraph(f"<b>{fund['name']}</b>", styles["Heading3"]))
        story.append(Paragraph(f"Folio No: {fund['folio']} / ISIN: {fund['isin']}", styles["Normal"]))
        story.append(Spacer(1, 3*mm))
        _add_txn_table(story, fund)
        story.append(Paragraph(f"Closing Unit Balance: {fund['closing_units']}", styles["Normal"]))
        story.append(Paragraph(f"NAV on {fund['nav_date']}: INR {fund['current_nav']}", styles["Normal"]))
        story.append(Spacer(1, 8*mm))

    doc.build(story)


def build_kfintech_pdf(output: str) -> None:
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>KFin Technologies Private Limited</b>", styles["Title"]))
    story.append(Paragraph("Consolidated Account Statement", styles["Heading2"]))
    story.append(Paragraph("Period: 01-Jan-2020 To 15-Mar-2026", styles["Normal"]))
    story.append(Paragraph("Investor: Shivangi Singh | PAN: ABCPS1234Z", styles["Normal"]))
    story.append(Spacer(1, 8*mm))

    for fund in FUNDS:
        # KFintech: Folio No BEFORE fund name
        story.append(Paragraph(f"Folio No: {fund['folio'].split('/')[0].strip()}", styles["Normal"]))
        story.append(Paragraph(f"<b>{fund['name']}</b>", styles["Heading3"]))
        story.append(Paragraph(f"ISIN: {fund['isin']}", styles["Normal"]))
        story.append(Spacer(1, 3*mm))
        _add_txn_table(story, fund)
        story.append(Paragraph(f"Closing Balance: {fund['closing_units']}", styles["Normal"]))
        story.append(Paragraph(f"NAV as on {fund['nav_date']}: INR {fund['current_nav']}", styles["Normal"]))
        story.append(Spacer(1, 8*mm))

    doc.build(story)


def _add_txn_table(story, fund):
    headers = ["Date", "Description", "Amount (₹)", "Units", "NAV (₹)", "Balance Units"]
    rows = [headers] + [list(txn) for txn in fund["transactions"]]
    t = Table(rows, colWidths=[25*mm, 55*mm, 25*mm, 22*mm, 22*mm, 28*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4f46e5")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    from reportlab.platypus import Spacer as _S
    story.append(_S(1, 3*mm))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate mock CAS PDF for NiveshNetra")
    parser.add_argument("--format", choices=["cams", "kfintech"], default="cams",
                        help="Statement format to generate (default: cams)")
    args = parser.parse_args()

    try:
        from reportlab.lib.pagesizes import A4  # noqa: F401
    except ImportError:
        print("Installing reportlab...")
        os.system("pip install reportlab")

    if args.format == "kfintech":
        output = "mock_kfintech_statement.pdf"
        build_kfintech_pdf(output)
    else:
        output = "mock_cams_statement.pdf"
        build_cams_pdf(output)

    print(f"✅ Created: {output}")
    size_kb = os.path.getsize(output) // 1024
    print(f"   Size: {size_kb} KB")
    print(f"\nNow upload '{output}' to NiveshNetra at http://localhost:5173")
