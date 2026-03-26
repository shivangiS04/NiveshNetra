"""
Generates a 6-fund mock CAS PDF specifically for the hackathon MF X-Ray scenario.
Three large-cap funds share Reliance, HDFC Bank, Infosys — demonstrating overlap detection.

Usage:
    python generate_mock_statement_6fund.py                    # CAMS format
    python generate_mock_statement_6fund.py --format kfintech  # KFintech format
"""

import argparse
import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# 6 funds across 4 AMCs:
# Large Cap (3): Mirae, Axis, Kotak  — all hold Reliance, HDFC Bank, Infosys
# Flexi Cap (1): Parag Parikh
# Small Cap (1): SBI Small Cap
# Mid Cap (1): HDFC Mid Cap
FUNDS = [
    {
        "name": "Mirae Asset Large Cap Fund - Regular Plan - Growth",
        "folio": "12345678 / 01",
        "isin": "INF769K01010",
        "transactions": [
            ("01-Jan-2022", "Purchase",      "50000.00",  "1428.571",  "35.0000",  "1428.571"),
            ("01-Feb-2022", "SIP Purchase",   "5000.00",   "138.504",  "36.1000",  "1567.075"),
            ("01-Mar-2022", "SIP Purchase",   "5000.00",   "131.926",  "37.9000",  "1699.001"),
            ("01-Jun-2022", "SIP Purchase",   "5000.00",   "121.951",  "41.0000",  "1820.952"),
            ("01-Sep-2022", "SIP Purchase",   "5000.00",   "113.636",  "44.0000",  "1934.588"),
            ("01-Dec-2022", "SIP Purchase",   "5000.00",   "106.383",  "47.0000",  "2040.971"),
            ("01-Mar-2023", "SIP Purchase",   "5000.00",   "100.000",  "50.0000",  "2140.971"),
            ("01-Jun-2023", "SIP Purchase",   "5000.00",    "94.340",  "53.0000",  "2235.311"),
            ("01-Sep-2023", "SIP Purchase",   "5000.00",    "89.286",  "56.0000",  "2324.597"),
            ("01-Dec-2023", "SIP Purchase",   "5000.00",    "84.746",  "59.0000",  "2409.343"),
            ("01-Mar-2024", "SIP Purchase",   "5000.00",    "80.645",  "62.0000",  "2489.988"),
        ],
        "closing_units": "2489.988",
        "nav_date": "15-Mar-2026",
        "current_nav": "68.5000",
    },
    {
        "name": "Axis Bluechip Fund - Regular Plan - Growth",
        "folio": "98765432 / 01",
        "isin": "INF846K01131",
        "transactions": [
            ("15-Mar-2021", "Purchase",      "100000.00",  "2631.579",  "38.0000",  "2631.579"),
            ("15-Jun-2021", "SIP Purchase",   "10000.00",   "243.309",  "41.1000",  "2874.888"),
            ("15-Sep-2021", "SIP Purchase",   "10000.00",   "232.558",  "43.0000",  "3107.446"),
            ("15-Dec-2021", "SIP Purchase",   "10000.00",   "222.222",  "45.0000",  "3329.668"),
            ("15-Mar-2022", "SIP Purchase",   "10000.00",   "212.766",  "47.0000",  "3542.434"),
            ("15-Jun-2022", "SIP Purchase",   "10000.00",   "204.082",  "49.0000",  "3746.516"),
            ("20-Aug-2023", "Redemption",    "-50000.00",  "-833.333",  "60.0000",  "2913.183"),
            ("15-Sep-2023", "SIP Purchase",   "10000.00",   "163.934",  "61.0000",  "3077.117"),
            ("15-Dec-2023", "SIP Purchase",   "10000.00",   "158.730",  "63.0000",  "3235.847"),
            ("15-Mar-2024", "SIP Purchase",   "10000.00",   "153.846",  "65.0000",  "3389.693"),
        ],
        "closing_units": "3389.693",
        "nav_date": "15-Mar-2026",
        "current_nav": "82.3000",
    },
    {
        "name": "Kotak Flexi Cap Fund - Regular Plan - Growth",
        "folio": "77665544 / 01",
        "isin": "INF174K01LS2",
        "transactions": [
            ("01-Apr-2021", "Purchase",       "75000.00",  "1875.000",  "40.0000",  "1875.000"),
            ("01-Jul-2021", "SIP Purchase",    "8000.00",   "184.615",  "43.3500",  "2059.615"),
            ("01-Oct-2021", "SIP Purchase",    "8000.00",   "172.043",  "46.5000",  "2231.658"),
            ("01-Jan-2022", "SIP Purchase",    "8000.00",   "160.000",  "50.0000",  "2391.658"),
            ("01-Apr-2022", "SIP Purchase",    "8000.00",   "149.533",  "53.5000",  "2541.191"),
            ("01-Jul-2022", "SIP Purchase",    "8000.00",   "140.351",  "57.0000",  "2681.542"),
            ("01-Oct-2022", "SIP Purchase",    "8000.00",   "132.231",  "60.5000",  "2813.773"),
            ("01-Jan-2023", "SIP Purchase",    "8000.00",   "125.000",  "64.0000",  "2938.773"),
            ("01-Apr-2023", "SIP Purchase",    "8000.00",   "117.647",  "68.0000",  "3056.420"),
            ("01-Jul-2023", "SIP Purchase",    "8000.00",   "111.111",  "72.0000",  "3167.531"),
            ("01-Oct-2023", "SIP Purchase",    "8000.00",   "105.263",  "76.0000",  "3272.794"),
            ("01-Jan-2024", "SIP Purchase",    "8000.00",   "100.000",  "80.0000",  "3372.794"),
        ],
        "closing_units": "3372.794",
        "nav_date": "15-Mar-2026",
        "current_nav": "91.5000",
    },
    {
        "name": "Parag Parikh Flexi Cap Fund - Regular Plan - Growth",
        "folio": "11223344 / 01",
        "isin": "INF879O01019",
        "transactions": [
            ("01-Apr-2020", "Purchase",       "25000.00",   "892.857",  "28.0000",   "892.857"),
            ("01-Jul-2020", "SIP Purchase",    "5000.00",   "161.290",  "31.0000",  "1054.147"),
            ("01-Oct-2020", "SIP Purchase",    "5000.00",   "147.059",  "34.0000",  "1201.206"),
            ("01-Jan-2021", "SIP Purchase",    "5000.00",   "135.135",  "37.0000",  "1336.341"),
            ("01-Apr-2021", "SIP Purchase",    "5000.00",   "125.000",  "40.0000",  "1461.341"),
            ("01-Jul-2021", "SIP Purchase",    "5000.00",   "115.741",  "43.2000",  "1577.082"),
            ("01-Oct-2021", "SIP Purchase",    "5000.00",   "107.527",  "46.5000",  "1684.609"),
            ("01-Jan-2022", "SIP Purchase",    "5000.00",   "100.000",  "50.0000",  "1784.609"),
            ("01-Apr-2022", "SIP Purchase",    "5000.00",    "93.458",  "53.5000",  "1878.067"),
            ("01-Jul-2022", "SIP Purchase",    "5000.00",    "87.719",  "57.0000",  "1965.786"),
            ("01-Jan-2023", "SIP Purchase",    "5000.00",    "78.125",  "64.0000",  "2043.911"),
            ("01-Jul-2023", "SIP Purchase",    "5000.00",    "69.444",  "72.0000",  "2113.355"),
            ("01-Jan-2024", "SIP Purchase",    "5000.00",    "62.500",  "80.0000",  "2175.855"),
        ],
        "closing_units": "2175.855",
        "nav_date": "15-Mar-2026",
        "current_nav": "95.7500",
    },
    {
        "name": "SBI Small Cap Fund - Regular Plan - Growth",
        "folio": "55667788 / 01",
        "isin": "INF200K01RD0",
        "transactions": [
            ("01-Jun-2021", "Purchase",       "20000.00",   "285.714",  "70.0000",   "285.714"),
            ("01-Sep-2021", "SIP Purchase",    "3000.00",    "38.961",  "77.0000",   "324.675"),
            ("01-Dec-2021", "SIP Purchase",    "3000.00",    "36.145",  "83.0000",   "360.820"),
            ("01-Mar-2022", "SIP Purchase",    "3000.00",    "33.708",  "89.0000",   "394.528"),
            ("01-Jun-2022", "SIP Purchase",    "3000.00",    "31.579",  "95.0000",   "426.107"),
            ("01-Sep-2022", "SIP Purchase",    "3000.00",    "29.703", "101.0000",   "455.810"),
            ("01-Dec-2022", "SIP Purchase",    "3000.00",    "28.037", "107.0000",   "483.847"),
            ("01-Mar-2023", "SIP Purchase",    "3000.00",    "26.549", "113.0000",   "510.396"),
            ("01-Jun-2023", "SIP Purchase",    "3000.00",    "25.210", "119.0000",   "535.606"),
            ("01-Sep-2023", "SIP Purchase",    "3000.00",    "24.000", "125.0000",   "559.606"),
            ("01-Dec-2023", "SIP Purchase",    "3000.00",    "22.901", "131.0000",   "582.507"),
            ("01-Mar-2024", "SIP Purchase",    "3000.00",    "21.898", "137.0000",   "604.405"),
        ],
        "closing_units": "604.405",
        "nav_date": "15-Mar-2026",
        "current_nav": "158.2500",
    },
    {
        "name": "HDFC Mid-Cap Opportunities Fund - Regular Plan - Growth",
        "folio": "33445566 / 01",
        "isin": "INF179K01BB8",
        "transactions": [
            ("15-Feb-2022", "Purchase",       "30000.00",   "600.000",  "50.0000",   "600.000"),
            ("15-May-2022", "SIP Purchase",    "5000.00",    "94.340",  "53.0000",   "694.340"),
            ("15-Aug-2022", "SIP Purchase",    "5000.00",    "89.286",  "56.0000",   "783.626"),
            ("15-Nov-2022", "SIP Purchase",    "5000.00",    "84.746",  "59.0000",   "868.372"),
            ("15-Feb-2023", "SIP Purchase",    "5000.00",    "80.645",  "62.0000",   "949.017"),
            ("15-May-2023", "SIP Purchase",    "5000.00",    "76.923",  "65.0000",  "1025.940"),
            ("15-Aug-2023", "SIP Purchase",    "5000.00",    "73.529",  "68.0000",  "1099.469"),
            ("15-Nov-2023", "SIP Purchase",    "5000.00",    "70.423",  "71.0000",  "1169.892"),
            ("15-Feb-2024", "SIP Purchase",    "5000.00",    "67.568",  "74.0000",  "1237.460"),
            ("15-May-2024", "SIP Purchase",    "5000.00",    "64.935",  "77.0000",  "1302.395"),
        ],
        "closing_units": "1302.395",
        "nav_date": "15-Mar-2026",
        "current_nav": "112.7500",
    },
]


def build_cams_pdf(output: str) -> None:
    doc = SimpleDocTemplate(
        output, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>CAMS - Computer Age Management Services</b>", styles["Title"]))
    story.append(Paragraph("Consolidated Account Statement", styles["Heading2"]))
    story.append(Paragraph("Period: 01-Jan-2020 To 15-Mar-2026", styles["Normal"]))
    story.append(Paragraph("Investor: Rahul Sharma | PAN: EFGRS9012Y", styles["Normal"]))
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
        output, pagesize=A4,
        rightMargin=15*mm, leftMargin=15*mm,
        topMargin=15*mm, bottomMargin=15*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("<b>KFin Technologies Private Limited</b>", styles["Title"]))
    story.append(Paragraph("Consolidated Account Statement", styles["Heading2"]))
    story.append(Paragraph("Period: 01-Jan-2020 To 15-Mar-2026", styles["Normal"]))
    story.append(Paragraph("Investor: Rahul Sharma | PAN: EFGRS9012Y", styles["Normal"]))
    story.append(Spacer(1, 8*mm))

    for fund in FUNDS:
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
    headers = ["Date", "Description", "Amount (Rs)", "Units", "NAV (Rs)", "Balance Units"]
    rows = [headers] + [list(txn) for txn in fund["transactions"]]
    t = Table(rows, colWidths=[25*mm, 55*mm, 25*mm, 22*mm, 22*mm, 28*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eff6ff")]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#e5e7eb")),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(t)
    from reportlab.platypus import Spacer as _S
    story.append(_S(1, 3*mm))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate 6-fund overlap test PDF for NiveshNetra")
    parser.add_argument("--format", choices=["cams", "kfintech"], default="cams")
    args = parser.parse_args()

    if args.format == "kfintech":
        output = "mock_kfintech_6fund.pdf"
        build_kfintech_pdf(output)
    else:
        output = "mock_cams_6fund.pdf"
        build_cams_pdf(output)

    print(f"Created: {output}")
    print(f"Size: {os.path.getsize(output) // 1024} KB")
    print(f"\nThis PDF has 6 funds across 4 AMCs.")
    print("Mirae, Axis, and Kotak all hold Reliance Industries, HDFC Bank, and Infosys.")
    print(f"\nUpload '{output}' to NiveshNetra at http://localhost:5173")
