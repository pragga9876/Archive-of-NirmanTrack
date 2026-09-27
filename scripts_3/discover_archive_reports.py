import csv
import re
from pathlib import Path
from urllib.parse import urljoin

import requests


# ============================================================
# CONFIGURATION
# ============================================================

BASE_URL = "https://paimana-proj.mospi.gov.in"

API_URL = (
    f"{BASE_URL}/ReportPage/ArchiveReport"
)

OUTPUT_DIR = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "archive"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "archive_report_index.csv"
)


# ============================================================
# FETCH ARCHIVE REPORT LIST
# ============================================================

print("=" * 90)
print("DISCOVERING PAIMANA ARCHIVE REPORTS")
print("=" * 90)


params = {
    "type": "N",
    "month": 1,
    "quater": 0,
    "ReportType": "N",
}


print("\nRequesting archive...")

response = requests.get(
    API_URL,
    params=params,
    timeout=30,
)

print("\nStatus Code:", response.status_code)
print(
    "Content-Type:",
    response.headers.get("Content-Type"),
)


response.raise_for_status()


# ============================================================
# PARSE JSON RESPONSE
# ============================================================

data = response.json()


if "html" not in data:
    raise ValueError(
        "Expected 'html' field was not found "
        "in API response."
    )


html = data["html"]


print("\nArchive HTML received.")

print(
    "HTML length:",
    len(html),
)


# ============================================================
# EXTRACT TABLE ROWS
# ============================================================

row_pattern = re.compile(
    r"<tr>(.*?)</tr>",
    re.DOTALL,
)

rows = row_pattern.findall(html)


print(
    "\nRows detected:",
    len(rows),
)


# ============================================================
# EXTRACT REPORT INFORMATION
# ============================================================

reports = []


for row in rows:

    # Skip table header
    if "<th>" in row:
        continue


    # --------------------------------------------------------
    # FINANCIAL YEAR
    # --------------------------------------------------------

    year_match = re.search(
        r"<td>(\d{4}-\d{2})</td>",
        row,
    )


    if not year_match:
        continue


    financial_year = (
        year_match.group(1)
    )


    # --------------------------------------------------------
    # ALL TABLE CELLS
    # --------------------------------------------------------

    cells = re.findall(
        r"<td[^>]*>(.*?)</td>",
        row,
        re.DOTALL,
    )


    if len(cells) < 3:
        continue


    # --------------------------------------------------------
    # REPORT LABEL
    # --------------------------------------------------------

    report_label = re.sub(
        r"<.*?>",
        "",
        cells[2],
    )

    report_label = (
        report_label
        .replace("&nbsp;", " ")
        .strip()
    )


    # --------------------------------------------------------
    # PDF LINK
    # --------------------------------------------------------

    link_match = re.search(
        r"href=['\"]([^'\"]+)['\"]",
        row,
    )


    if not link_match:
        continue


    pdf_relative_url = (
        link_match.group(1)
    )


    # Normalize ../ path
    pdf_url = urljoin(
        API_URL,
        pdf_relative_url,
    )


    # --------------------------------------------------------
    # EXTRACT PDF ID
    # --------------------------------------------------------

    id_match = re.search(
        r"id=(\d+)",
        pdf_relative_url,
    )


    if not id_match:
        continue


    pdf_id = (
        id_match.group(1)
    )


    # --------------------------------------------------------
    # DETERMINE REPORT TYPE
    # --------------------------------------------------------

    if report_label.upper().startswith("Q"):
        report_type = "quarterly"

    elif report_label.upper() == "NO DATA":
        report_type = "unknown"

    else:
        report_type = "monthly"


    # --------------------------------------------------------
    # SAVE RECORD
    # --------------------------------------------------------

    reports.append(
        {
            "financial_year": financial_year,
            "report_label": report_label,
            "report_type": report_type,
            "pdf_id": pdf_id,
            "pdf_url": pdf_url,
        }
    )


# ============================================================
# REMOVE DUPLICATES
# ============================================================

unique_reports = {}


for report in reports:

    unique_reports[
        report["pdf_id"]
    ] = report


reports = list(
    unique_reports.values()
)


# ============================================================
# SORT REPORTS
# ============================================================

reports.sort(
    key=lambda x: (
        x["financial_year"],
        x["report_label"],
    )
)


# ============================================================
# DISPLAY SUMMARY
# ============================================================

print("\n" + "=" * 90)
print("ARCHIVE DISCOVERY SUMMARY")
print("=" * 90)


print(
    "\nTotal reports discovered:",
    len(reports),
)


financial_years = sorted(
    set(
        report["financial_year"]
        for report in reports
    )
)


print(
    "\nFinancial years discovered:",
    len(financial_years),
)


print(
    "\nFinancial year range:"
)


if financial_years:

    print(
        financial_years[0],
        "to",
        financial_years[-1],
    )


# ============================================================
# REPORT TYPE COUNTS
# ============================================================

type_counts = {}


for report in reports:

    report_type = (
        report["report_type"]
    )

    type_counts[
        report_type
    ] = (
        type_counts.get(
            report_type,
            0,
        )
        + 1
    )


print(
    "\nReport type counts:"
)


for report_type, count in (
    type_counts.items()
):

    print(
        f"  {report_type}: {count}"
    )


# ============================================================
# PREVIEW
# ============================================================

print("\n" + "=" * 90)
print("FIRST 20 REPORTS")
print("=" * 90)


for report in reports[:20]:

    print()

    print(
        "Financial Year:",
        report["financial_year"],
    )

    print(
        "Label:",
        report["report_label"],
    )

    print(
        "Type:",
        report["report_type"],
    )

    print(
        "PDF ID:",
        report["pdf_id"],
    )

    print(
        "URL:",
        report["pdf_url"],
    )


# ============================================================
# SAVE CSV
# ============================================================

print("\n" + "=" * 90)
print("SAVING ARCHIVE INDEX")
print("=" * 90)


fieldnames = [

    "financial_year",

    "report_label",

    "report_type",

    "pdf_id",

    "pdf_url",

]


with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8",
) as file:

    writer = csv.DictWriter(
        file,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    writer.writerows(
        reports
    )


print(
    "\nSaved successfully:"
)

print(
    OUTPUT_FILE
)


print(
    "\nTotal indexed reports:",
    len(reports),
)


print("\nDONE.")