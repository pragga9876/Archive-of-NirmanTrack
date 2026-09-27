import re
import sys
from pathlib import Path

import pdfplumber


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "input"

PDF_FILES = list(INPUT_DIR.glob("*.pdf"))

if not PDF_FILES:
    print("ERROR: No PDF found in data/input/")
    sys.exit(1)

PDF_PATH = PDF_FILES[0]


# ============================================================
# CONFIGURATION
# ============================================================

START_PAGE = 18
END_PAGE = 50


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 100)
    print("NIRMANTRACK STATE / SECTOR STRUCTURE DEBUG")
    print("=" * 100)

    print()
    print(f"PDF: {PDF_PATH.name}")
    print(f"Inspecting PDF pages {START_PAGE} to {END_PAGE}")

    print()

    with pdfplumber.open(PDF_PATH) as pdf:

        total_pages = len(pdf.pages)

        end_page = min(END_PAGE, total_pages)

        for page_number in range(
            START_PAGE,
            end_page + 1
        ):

            page = pdf.pages[
                page_number - 1
            ]

            text = page.extract_text() or ""

            print()
            print("=" * 100)
            print(
                f"PDF PAGE {page_number}"
            )
            print("=" * 100)

            lines = text.splitlines()

            for index, line in enumerate(
                lines,
                start=1
            ):

                line = line.strip()

                if not line:
                    continue


                # ====================================================
                # PRINT LINES THAT MAY REPRESENT
                # TABLE / STATE / SECTOR HEADERS
                # ====================================================

                possible_heading = False


                # Table markers
                if re.search(
                    r"Table:-?\s*\d+",
                    line,
                    re.IGNORECASE
                ):

                    possible_heading = True


                # State-related text
                if re.search(
                    r"\bSTATE\b",
                    line,
                    re.IGNORECASE
                ):

                    possible_heading = True


                # Grand total
                if re.search(
                    r"GRAND\s+TOTAL",
                    line,
                    re.IGNORECASE
                ):

                    possible_heading = True


                # Lines containing only uppercase words
                # These often correspond to State/Sector headers.
                letters_only = re.sub(
                    r"[^A-Za-z ]",
                    "",
                    line
                ).strip()


                if (
                    letters_only
                    and len(letters_only) >= 3
                    and letters_only == letters_only.upper()
                    and len(line) < 100
                ):

                    possible_heading = True


                if possible_heading:

                    print(
                        f"[Line {index:03d}] {line}"
                    )


    print()
    print("=" * 100)
    print("DEBUG COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()