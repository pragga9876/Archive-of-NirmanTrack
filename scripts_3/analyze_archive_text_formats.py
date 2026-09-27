from pathlib import Path
import re


# =============================================================================
# PATH CONFIGURATION
# =============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INSPECTION_DIR = (
    BASE_DIR
    / "data"
    / "archive"
    / "format_inspection"
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def print_matches(text, pattern, label, flags=re.IGNORECASE, limit=10):

    matches = list(re.finditer(pattern, text, flags))

    print(f"\n{label}")
    print("-" * 80)

    print(f"Matches found: {len(matches)}")

    for i, match in enumerate(matches[:limit], start=1):

        start = max(0, match.start() - 200)
        end = min(len(text), match.end() + 400)

        snippet = text[start:end]

        print(f"\nMATCH {i}")
        print(snippet.replace("\n", " "))


# =============================================================================
# ANALYZE FILE
# =============================================================================

def analyze_file(file_path):

    print("\n")
    print("=" * 100)
    print(f"ANALYZING: {file_path.name}")
    print("=" * 100)

    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore"
    )

    print("\nFILE STATISTICS")
    print("-" * 80)

    print(f"Characters: {len(text):,}")
    print(f"Lines: {len(text.splitlines()):,}")

    print("\nFIRST 2000 CHARACTERS")
    print("-" * 80)

    print(text[:2000])

    # -------------------------------------------------------------------------
    # PROJECT KEYWORDS
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Project\s+Name",
        "PROJECT NAME"
    )

    print_matches(
        text,
        r"Name\s+of\s+(the\s+)?Project",
        "NAME OF PROJECT"
    )

    # -------------------------------------------------------------------------
    # COST KEYWORDS
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Original\s+(Estimated\s+)?Cost",
        "ORIGINAL COST"
    )

    print_matches(
        text,
        r"Revised\s+(Estimated\s+)?Cost",
        "REVISED COST"
    )

    print_matches(
        text,
        r"Anticipated\s+Cost",
        "ANTICIPATED COST"
    )

    # -------------------------------------------------------------------------
    # EXPENDITURE
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Cumulative\s+Expenditure",
        "CUMULATIVE EXPENDITURE"
    )

    print_matches(
        text,
        r"Expenditure\s+Incurred",
        "EXPENDITURE INCURRED"
    )

    print_matches(
        text,
        r"Total\s+Expenditure",
        "TOTAL EXPENDITURE"
    )

    # -------------------------------------------------------------------------
    # PROGRESS
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Physical\s+Progress",
        "PHYSICAL PROGRESS"
    )

    print_matches(
        text,
        r"Progress\s*\(\s*%\s*\)",
        "PROGRESS PERCENTAGE"
    )

    # -------------------------------------------------------------------------
    # DATES
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Date\s+of\s+Completion",
        "DATE OF COMPLETION"
    )

    print_matches(
        text,
        r"Original\s+Date\s+of\s+Completion",
        "ORIGINAL COMPLETION DATE"
    )

    print_matches(
        text,
        r"Revised\s+Date\s+of\s+Completion",
        "REVISED COMPLETION DATE"
    )

    print_matches(
        text,
        r"Likely\s+Date\s+of\s+Completion",
        "LIKELY COMPLETION DATE"
    )

    # -------------------------------------------------------------------------
    # PROJECT CODE
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Project\s+Code",
        "PROJECT CODE"
    )

    # -------------------------------------------------------------------------
    # COMMON TABLE WORDS
    # -------------------------------------------------------------------------

    print_matches(
        text,
        r"Cost\s+Overrun",
        "COST OVERRUN"
    )

    print_matches(
        text,
        r"Time\s+Overrun",
        "TIME OVERRUN"
    )


# =============================================================================
# MAIN
# =============================================================================

def main():

    print("=" * 100)
    print("PAIMANA ARCHIVE TEXT FORMAT ANALYSIS")
    print("=" * 100)

    if not INSPECTION_DIR.exists():

        print("\nERROR: Inspection directory not found.")

        print(f"\nExpected directory:")
        print(INSPECTION_DIR)

        return

    files = sorted(
        INSPECTION_DIR.glob("*.txt")
    )

    print(f"\nInspection files found: {len(files)}")

    if not files:

        print("\nNo text files found.")
        return

    for file_path in files:

        analyze_file(file_path)

    print("\n")
    print("=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)


if __name__ == "__main__":
    main()