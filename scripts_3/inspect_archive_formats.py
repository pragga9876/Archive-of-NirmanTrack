import os
import re
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pdfplumber
import requests


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

ARCHIVE_INDEX = (
    BASE_DIR
    / "data"
    / "archive"
    / "archive_report_index.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "archive"
    / "format_inspection"
)


# =============================================================================
# CONFIGURATION
# =============================================================================

# We only inspect a few representative reports.
# This is NOT the full extraction pipeline.

TARGET_FINANCIAL_YEARS = [
    "2001-02",
    "2005-06",
    "2010-11",
    "2015-16",
    "2020-21",
    "2024-25",
    "2025-26",
]

MAX_PAGES_PER_REPORT = 8

REQUEST_TIMEOUT = 60


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def sanitize_filename(value):
    """
    Convert a string into a safe filename.
    """

    value = str(value)

    value = re.sub(
        r'[<>:"/\\|?*]',
        "_",
        value
    )

    value = re.sub(
        r"\s+",
        "_",
        value
    )

    return value


def download_pdf_to_temp(url):
    """
    Download PDF into a temporary file.

    The file will be deleted after processing.
    """

    response = requests.get(
        url,
        timeout=REQUEST_TIMEOUT
    )

    response.raise_for_status()

    content_type = (
        response.headers
        .get("Content-Type", "")
        .lower()
    )

    if "pdf" not in content_type:
        print(
            f"[WARNING] Unexpected content type: "
            f"{content_type}"
        )

    temp_file = tempfile.NamedTemporaryFile(
        suffix=".pdf",
        delete=False
    )

    temp_file.write(response.content)

    temp_file.close()

    return Path(temp_file.name)


def extract_pdf_sample(pdf_path):
    """
    Extract text from the first few pages of a PDF.
    """

    extracted_pages = []

    with pdfplumber.open(pdf_path) as pdf:

        total_pages = len(pdf.pages)

        pages_to_extract = min(
            total_pages,
            MAX_PAGES_PER_REPORT
        )

        for page_number in range(pages_to_extract):

            page = pdf.pages[page_number]

            try:
                text = page.extract_text()

            except Exception as error:

                text = (
                    f"[TEXT EXTRACTION ERROR: "
                    f"{error}]"
                )

            extracted_pages.append(
                {
                    "page": page_number + 1,
                    "text": text
                }
            )

    return total_pages, extracted_pages


def save_text_sample(
    financial_year,
    report_label,
    report_url,
    total_pages,
    extracted_pages
):
    """
    Save extracted PDF text into a small text file.
    """

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    filename = (
        f"{sanitize_filename(financial_year)}_"
        f"{sanitize_filename(report_label)}.txt"
    )

    output_path = OUTPUT_DIR / filename

    with open(
        output_path,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("=" * 100)
        file.write("\n")

        file.write(
            f"FINANCIAL YEAR: "
            f"{financial_year}\n"
        )

        file.write(
            f"REPORT LABEL: "
            f"{report_label}\n"
        )

        file.write(
            f"PDF URL: "
            f"{report_url}\n"
        )

        file.write(
            f"TOTAL PDF PAGES: "
            f"{total_pages}\n"
        )

        file.write("=" * 100)
        file.write("\n\n")

        for page_data in extracted_pages:

            file.write(
                f"\n{'#' * 40}\n"
            )

            file.write(
                f"PAGE "
                f"{page_data['page']}\n"
            )

            file.write(
                f"{'#' * 40}\n\n"
            )

            text = page_data["text"]

            if text:
                file.write(text)

            else:
                file.write(
                    "[NO TEXT EXTRACTED]"
                )

            file.write("\n\n")

    return output_path


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("\n")

    print("=" * 100)
    print("INSPECTING HISTORICAL PAIMANA REPORT FORMATS")
    print("=" * 100)

    print("\nARCHIVE INDEX:")

    print(
        ARCHIVE_INDEX
    )

    print("\nOUTPUT DIRECTORY:")

    print(
        OUTPUT_DIR
    )

    print("\n")

    # -------------------------------------------------------------------------
    # CHECK INDEX
    # -------------------------------------------------------------------------

    if not ARCHIVE_INDEX.exists():

        print(
            "[ERROR] Archive index not found."
        )

        print(
            "\nExpected:"
        )

        print(
            ARCHIVE_INDEX
        )

        sys.exit(1)


    # -------------------------------------------------------------------------
    # LOAD INDEX
    # -------------------------------------------------------------------------

    print("=" * 100)
    print("1. LOADING ARCHIVE INDEX")
    print("=" * 100)

    archive_df = pd.read_csv(
        ARCHIVE_INDEX
    )

    print(
        f"\nTotal indexed reports: "
        f"{len(archive_df):,}"
    )

    print(
        "\nColumns:"
    )

    for column in archive_df.columns:

        print(
            f"  - {column}"
        )


    # -------------------------------------------------------------------------
    # IDENTIFY COLUMN NAMES
    # -------------------------------------------------------------------------

    print("\n")

    print("=" * 100)
    print("2. IDENTIFYING INDEX COLUMNS")
    print("=" * 100)

    print(
        "\nAvailable columns:"
    )

    print(
        archive_df.columns.tolist()
    )


    # Try to automatically find likely columns.

    year_column = None

    for candidate in [

        "financial_year",
        "FinancialYear",
        "financialYear",
        "year"

    ]:

        if candidate in archive_df.columns:

            year_column = candidate

            break


    label_column = None

    for candidate in [

        "label",
        "month_quarter",
        "report_label",
        "Label"

    ]:

        if candidate in archive_df.columns:

            label_column = candidate

            break


    type_column = None

    for candidate in [

        "report_type",
        "type",
        "ReportType"

    ]:

        if candidate in archive_df.columns:

            type_column = candidate

            break


    url_column = None

    for candidate in [

        "pdf_url",
        "url",
        "PDF_URL",
        "download_url"

    ]:

        if candidate in archive_df.columns:

            url_column = candidate

            break


    print("\nDetected columns:")

    print(
        f"Financial Year: "
        f"{year_column}"
    )

    print(
        f"Label: "
        f"{label_column}"
    )

    print(
        f"Report Type: "
        f"{type_column}"
    )

    print(
        f"PDF URL: "
        f"{url_column}"
    )


    if year_column is None:

        print(
            "\n[ERROR] Could not identify "
            "financial year column."
        )

        sys.exit(1)


    if url_column is None:

        print(
            "\n[ERROR] Could not identify "
            "PDF URL column."
        )

        sys.exit(1)


    # -------------------------------------------------------------------------
    # FILTER MONTHLY REPORTS
    # -------------------------------------------------------------------------

    print("\n")

    print("=" * 100)
    print("3. SELECTING REPRESENTATIVE REPORTS")
    print("=" * 100)


    selected_reports = []


    for financial_year in TARGET_FINANCIAL_YEARS:

        year_reports = archive_df[
            archive_df[year_column].astype(str)
            == financial_year
        ].copy()


        if len(year_reports) == 0:

            print(
                f"\n[WARNING] No report found "
                f"for {financial_year}"
            )

            continue


        # Prefer monthly reports.

        if type_column is not None:

            monthly_reports = year_reports[
                year_reports[type_column]
                .astype(str)
                .str.lower()
                == "monthly"
            ]

            if len(monthly_reports) > 0:

                year_reports = monthly_reports


        # Prefer April if available.

        if label_column is not None:

            april_reports = year_reports[
                year_reports[label_column]
                .astype(str)
                .str.lower()
                == "april"
            ]

            if len(april_reports) > 0:

                selected_report = (
                    april_reports.iloc[0]
                )

            else:

                selected_report = (
                    year_reports.iloc[0]
                )

        else:

            selected_report = (
                year_reports.iloc[0]
            )


        selected_reports.append(
            selected_report
        )


    print(
        f"\nReports selected: "
        f"{len(selected_reports)}"
    )


    # -------------------------------------------------------------------------
    # PROCESS REPORTS
    # -------------------------------------------------------------------------

    print("\n")

    print("=" * 100)
    print("4. DOWNLOADING AND INSPECTING REPORTS")
    print("=" * 100)


    successful_reports = 0

    failed_reports = []


    for index, report in enumerate(
        selected_reports,
        start=1
    ):

        financial_year = str(
            report[year_column]
        )


        if label_column is not None:

            report_label = str(
                report[label_column]
            )

        else:

            report_label = "Unknown"


        report_url = str(
            report[url_column]
        )


        print("\n")

        print("-" * 100)

        print(
            f"REPORT {index}/"
            f"{len(selected_reports)}"
        )

        print("-" * 100)

        print(
            f"Financial Year: "
            f"{financial_year}"
        )

        print(
            f"Label: "
            f"{report_label}"
        )

        print(
            f"URL:"
        )

        print(
            report_url
        )


        pdf_path = None


        try:

            # -------------------------------------------------------------
            # DOWNLOAD
            # -------------------------------------------------------------

            print(
                "\nDownloading temporarily..."
            )

            pdf_path = (
                download_pdf_to_temp(
                    report_url
                )
            )


            pdf_size_mb = (
                pdf_path.stat().st_size
                / (1024 * 1024)
            )


            print(
                f"Downloaded: "
                f"{pdf_size_mb:.2f} MB"
            )


            # -------------------------------------------------------------
            # EXTRACT
            # -------------------------------------------------------------

            print(
                "Extracting text..."
            )


            total_pages, extracted_pages = (

                extract_pdf_sample(
                    pdf_path
                )

            )


            print(
                f"Total pages: "
                f"{total_pages}"
            )


            # -------------------------------------------------------------
            # SAVE
            # -------------------------------------------------------------

            output_path = (

                save_text_sample(

                    financial_year=
                    financial_year,

                    report_label=
                    report_label,

                    report_url=
                    report_url,

                    total_pages=
                    total_pages,

                    extracted_pages=
                    extracted_pages

                )

            )


            print(
                "\n[SUCCESS]"
            )

            print(
                "Text sample saved:"
            )

            print(
                output_path
            )


            successful_reports += 1


        except Exception as error:

            print(
                f"\n[FAILED] "
                f"{financial_year} "
                f"{report_label}"
            )

            print(
                f"Error: {error}"
            )


            failed_reports.append(

                {
                    "financial_year":
                    financial_year,

                    "label":
                    report_label,

                    "error":
                    str(error)
                }

            )


        finally:

            # -------------------------------------------------------------
            # DELETE TEMP PDF
            # -------------------------------------------------------------

            if pdf_path is not None:

                if pdf_path.exists():

                    try:

                        os.remove(
                            pdf_path
                        )

                        print(
                            "\nTemporary PDF deleted."
                        )

                    except Exception as error:

                        print(
                            "\n[WARNING] "
                            "Could not delete "
                            "temporary PDF."
                        )

                        print(
                            error
                        )


    # -------------------------------------------------------------------------
    # SUMMARY
    # -------------------------------------------------------------------------

    print("\n")

    print("=" * 100)
    print("INSPECTION COMPLETE")
    print("=" * 100)

    print(
        f"\nSuccessful reports: "
        f"{successful_reports}"
    )

    print(
        f"Failed reports: "
        f"{len(failed_reports)}"
    )


    if failed_reports:

        print(
            "\nFAILED REPORTS:"
        )

        for failed_report in failed_reports:

            print(
                "\n"
                f"Financial Year: "
                f"{failed_report['financial_year']}"
            )

            print(
                f"Label: "
                f"{failed_report['label']}"
            )

            print(
                f"Error: "
                f"{failed_report['error']}"
            )


    print(
        "\nInspection files:"
    )

    print(
        OUTPUT_DIR
    )

    print("\nDONE.")


# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":

    main()