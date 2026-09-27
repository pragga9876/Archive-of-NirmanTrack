import json
import re
import sys
from pathlib import Path

import pdfplumber


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_DIR = BASE_DIR / "data" / "input"
PROCESSED_DIR = BASE_DIR / "data" / "processed"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# PDF CONFIGURATION
# ============================================================

PDF_FILES = list(INPUT_DIR.glob("*.pdf"))

if not PDF_FILES:
    print("ERROR: No PDF file found in data/input/")
    sys.exit(1)

PDF_PATH = PDF_FILES[0]

OUTPUT_PATH = PROCESSED_DIR / "projects.json"


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def clean_text(value):
    """Clean whitespace and safely handle None."""

    if value is None:
        return None

    value = str(value)
    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)

    value = value.strip()

    return value if value else None


def clean_number(value):
    """Convert a numeric string to float."""

    if value is None:
        return None

    value = clean_text(value)

    if not value:
        return None

    value = value.replace(",", "")
    value = value.replace("₹", "")

    try:
        return float(value)

    except ValueError:
        return None


def is_blank(value):
    """Check whether a value is empty."""

    return clean_text(value) is None


# ============================================================
# STATE / SECTOR CLEANING
# ============================================================

def clean_context_value(value):
    """
    Clean State or Sector values.

    Rejects:
    - Grand Total
    - Total
    - Header text
    """

    value = clean_text(value)

    if not value:
        return None

    lower_value = value.lower()

    invalid_values = [
        "grand total",
        "total",
        "state",
        "sector",
        "state/ut",
        "state / ut",
    ]

    if lower_value in invalid_values:
        return None

    return value


# ============================================================
# PROJECT DETAILS PARSER
# ============================================================

def parse_project_details(value):

    result = {
        "project_name": None,
        "agency": None,
        "project_code": None
    }

    if not value:
        return result

    lines = [
        line.strip()
        for line in str(value).split("\n")
        if line.strip()
    ]

    project_name_lines = []

    for line in lines:

        line = line.strip()

        # ====================================================
        # PROJECT CODE
        #
        # Examples:
        #
        # (N24001251)
        # N24001251
        # ====================================================

        code_match = re.fullmatch(
            r"\(?([A-Za-z]{1,6}\d{4,})\)?",
            line
        )

        if code_match:

            possible_code = code_match.group(1)

            # A project code normally contains letters + digits
            if re.search(r"[A-Za-z]", possible_code) and \
               re.search(r"\d", possible_code):

                result["project_code"] = possible_code
                continue


        # ====================================================
        # AGENCY
        #
        # Examples:
        #
        # (NHIDCL)
        # (MoRTH)
        # (IOCL)
        # (AAI)
        # ====================================================

        agency_match = re.fullmatch(
            r"\(([A-Za-z][A-Za-z0-9 .&/-]*)\)",
            line
        )

        if agency_match:

            possible_agency = agency_match.group(1).strip()

            # Do not mistake project code for agency
            if not re.fullmatch(
                r"[A-Za-z]{1,6}\d{4,}",
                possible_agency
            ):

                result["agency"] = possible_agency
                continue


        # ====================================================
        # PROJECT NAME
        # ====================================================

        project_name_lines.append(line)


    project_name = clean_text(
        " ".join(project_name_lines)
    )

    result["project_name"] = project_name

    return result


# ============================================================
# DATE PARSERS
# ============================================================

def normalize_date(value):
    """
    Convert:

    3-2019
    03-2019
    3/2019
    03/2019

    into:

    03/2019
    """

    if not value:
        return None

    value = clean_text(value)

    if not value:
        return None

    match = re.fullmatch(
        r"(\d{1,2})[-/](\d{4})",
        value
    )

    if not match:
        return None

    month = int(match.group(1))
    year = int(match.group(2))

    if month < 1 or month > 12:
        return None

    return f"{month:02d}/{year}"


def parse_approval_date(value):

    if not value:
        return None

    value = clean_text(value)

    if not value:
        return None

    # Direct date
    date = normalize_date(value)

    if date:
        return date

    # Sometimes date may contain line breaks
    for line in str(value).split("\n"):

        date = normalize_date(line)

        if date:
            return date

    return None


# ============================================================
# COMMISSIONING DATE PARSER
# ============================================================

def parse_commissioning_dates(value):
    """
    Example:

    4/2022
    (5/2022)
    {12/2023}

    Returns:

    {
        "original_completion": "04/2022",
        "revised_completion": "05/2022",
        "anticipated_completion": "12/2023"
    }
    """

    result = {
        "original_completion": None,
        "revised_completion": None,
        "anticipated_completion": None
    }

    if not value:
        return result

    lines = [
        line.strip()
        for line in str(value).split("\n")
        if line.strip()
    ]

    for line in lines:

        # ====================================================
        # ANTICIPATED DATE
        #
        # {12/2025}
        # ====================================================

        anticipated_match = re.fullmatch(
            r"\{(.+?)\}",
            line
        )

        if anticipated_match:

            inside = anticipated_match.group(1).strip()

            if inside.upper() != "N.A.":

                result["anticipated_completion"] = (
                    normalize_date(inside)
                )

            continue


        # ====================================================
        # REVISED DATE
        #
        # (4/2025)
        # ====================================================

        revised_match = re.fullmatch(
            r"\((.+?)\)",
            line
        )

        if revised_match:

            inside = revised_match.group(1).strip()

            if inside.upper() != "N.A.":

                result["revised_completion"] = (
                    normalize_date(inside)
                )

            continue


        # ====================================================
        # ORIGINAL DATE
        # ====================================================

        date = normalize_date(line)

        if date:

            result["original_completion"] = date


    return result


# ============================================================
# COST PARSER
# ============================================================

def parse_costs(value):
    """
    Example:

    332.20
    (348.92)
    {348.92}

    Returns:

    {
        "original_cost": 332.20,
        "revised_cost": 348.92,
        "anticipated_cost": 348.92
    }
    """

    result = {
        "original_cost": None,
        "revised_cost": None,
        "anticipated_cost": None
    }

    if not value:
        return result

    lines = [
        line.strip()
        for line in str(value).split("\n")
        if line.strip()
    ]

    for line in lines:

        # ====================================================
        # ANTICIPATED COST
        # ====================================================

        anticipated_match = re.fullmatch(
            r"\{(.+?)\}",
            line
        )

        if anticipated_match:

            inside = anticipated_match.group(1).strip()

            if inside.upper() != "N.A.":

                result["anticipated_cost"] = (
                    clean_number(inside)
                )

            continue


        # ====================================================
        # REVISED COST
        # ====================================================

        revised_match = re.fullmatch(
            r"\((.+?)\)",
            line
        )

        if revised_match:

            inside = revised_match.group(1).strip()

            if inside.upper() != "N.A.":

                result["revised_cost"] = (
                    clean_number(inside)
                )

            continue


        # ====================================================
        # ORIGINAL COST
        # ====================================================

        number = clean_number(line)

        if number is not None:

            result["original_cost"] = number


    return result


# ============================================================
# PROJECT ROW VALIDATION
# ============================================================

def is_project_row(row):
    """
    A valid project row has a numeric serial number
    in column index 2.
    """

    if not row:
        return False

    if len(row) < 9:
        return False

    sl_no = clean_text(row[2])

    if not sl_no:
        return False

    if sl_no.lower() == "total":
        return False

    return sl_no.isdigit()


# ============================================================
# HEADER DETECTION
# ============================================================

def is_header_row(row):

    joined_row = " ".join(
        clean_text(cell) or ""
        for cell in row
    ).lower()

    header_keywords = [
        "project name",
        "sl no",
        "approval",
        "completion",
        "physical progress"
    ]

    matches = sum(
        keyword in joined_row
        for keyword in header_keywords
    )

    return matches >= 2


# ============================================================
# TOTAL ROW DETECTION
# ============================================================

def is_total_row(row):

    joined_row = " ".join(
        clean_text(cell) or ""
        for cell in row
    ).lower()

    if "grand total" in joined_row:
        return True

    sl_no = clean_text(row[2])

    if sl_no and sl_no.isdigit():
        return False

    if re.fullmatch(r"total", joined_row.strip()):
        return True

    if "total" in joined_row:
        return True

    return False


# ============================================================
# DETECT TABLE NUMBER
# ============================================================

def detect_table_number(page_text):

    patterns = [

        r"Table:-\s*(\d+)\.",

        r"Table\s*[:-]\s*(\d+)",

        r"TABLE\s*[:-]\s*(\d+)",

        r"Table\s+(\d+)",

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            page_text,
            re.IGNORECASE
        )

        if match:

            return int(
                match.group(1)
            )

    return None


# ============================================================
# UPDATE CONTEXT
# ============================================================

def update_context(
    row,
    current_state,
    current_sector
):
    """
    State and Sector are merged vertically in the PDF.

    pdfplumber usually returns:

    First row:
        ARUNACHAL PRADESH | CIVIL AVIATION | 1

    Following rows:
        None | None | 2
        None | None | 3

    Therefore we preserve the previous context.
    """

    if len(row) < 2:

        return (
            current_state,
            current_sector
        )


    # ========================================================
    # STATE
    # ========================================================

    state_value = clean_context_value(
        row[0]
    )

    if state_value:

        # Do not accidentally treat a serial number
        # or random numeric value as state
        if not state_value.isdigit():

            current_state = state_value


    # ========================================================
    # SECTOR
    # ========================================================

    sector_value = clean_context_value(
        row[1]
    )

    if sector_value:

        if not sector_value.isdigit():

            current_sector = sector_value


    return (
        current_state,
        current_sector
    )


# ============================================================
# MAIN PROJECT EXTRACTION
# ============================================================

def extract_projects():

    print("=" * 100)
    print("NIRMANTRACK PROJECT EXTRACTION")
    print("=" * 100)

    print()
    print(f"PDF: {PDF_PATH.name}")

    projects = []

    current_state = None
    current_sector = None

    active_table = None


    with pdfplumber.open(PDF_PATH) as pdf:

        total_pages = len(pdf.pages)

        print(f"Total Pages: {total_pages}")
        print()


        # ====================================================
        # PROCESS EACH PAGE
        # ====================================================

        for page_number, page in enumerate(
            pdf.pages,
            start=1
        ):

            page_text = page.extract_text() or ""


            # ====================================================
            # DETECT NEW TABLE
            # ====================================================

            detected_table = detect_table_number(
                page_text
            )


            if detected_table is not None:

                # ------------------------------------------------
                # TABLE 6 OR TABLE 7
                # ------------------------------------------------

                if detected_table in [6, 7]:

                    # Only reset context if this is a genuinely
                    # different table.
                    #
                    # This prevents resetting state/sector
                    # on continuation pages.
                    if detected_table != active_table:

                        current_state = None
                        current_sector = None

                        print(
                            f"Starting Table {detected_table} "
                            f"at PDF page {page_number}"
                        )

                    active_table = detected_table


                # ------------------------------------------------
                # OTHER TABLE
                # ------------------------------------------------

                else:

                    active_table = None
                    current_state = None
                    current_sector = None


            # ====================================================
            # SKIP NON-PROJECT TABLES
            # ====================================================

            if active_table not in [6, 7]:

                continue


            # ====================================================
            # EXTRACT TABLES
            # ====================================================

            tables = page.extract_tables()

            if not tables:

                continue


            # ====================================================
            # PROCESS EACH TABLE
            # ====================================================

            for table in tables:

                if not table:

                    continue


                # ====================================================
                # PROCESS EACH ROW
                # ====================================================

                for row in table:

                    if not row:

                        continue


                    if len(row) < 9:

                        continue


                    # ====================================================
                    # SKIP HEADER
                    # ====================================================

                    if is_header_row(row):

                        continue


                    # ====================================================
                    # SKIP TOTAL ROW
                    # ====================================================

                    if is_total_row(row):

                        continue


                    # ====================================================
                    # UPDATE STATE / SECTOR CONTEXT
                    #
                    # IMPORTANT:
                    #
                    # This happens BEFORE project validation.
                    #
                    # Therefore context rows can update the
                    # current State/Sector.
                    # ====================================================

                    (
                        current_state,
                        current_sector
                    ) = update_context(

                        row,

                        current_state,

                        current_sector
                    )


                    # ====================================================
                    # VALIDATE PROJECT ROW
                    # ====================================================

                    if not is_project_row(row):

                        continue


                    # ====================================================
                    # SERIAL NUMBER
                    # ====================================================

                    sl_no = clean_text(
                        row[2]
                    )


                    # ====================================================
                    # PROJECT DETAILS
                    # ====================================================

                    project_details = (
                        parse_project_details(
                            row[3]
                        )
                    )


                    # ====================================================
                    # APPROVAL DATE
                    # ====================================================

                    approval_date = (
                        parse_approval_date(
                            row[4]
                        )
                    )


                    # ====================================================
                    # COMMISSIONING DATES
                    # ====================================================

                    commissioning_dates = (
                        parse_commissioning_dates(
                            row[5]
                        )
                    )


                    # ====================================================
                    # COSTS
                    # ====================================================

                    costs = parse_costs(
                        row[6]
                    )


                    # ====================================================
                    # CUMULATIVE EXPENDITURE
                    # ====================================================

                    cumulative_expenditure = (
                        clean_number(
                            row[7]
                        )
                    )


                    # ====================================================
                    # PHYSICAL PROGRESS
                    # ====================================================

                    physical_progress = (
                        clean_number(
                            row[8]
                        )
                    )


                    # ====================================================
                    # BUILD PROJECT OBJECT
                    # ====================================================

                    project = {

                        "table_number":
                            active_table,

                        "serial_number":
                            int(sl_no),

                        "state":
                            current_state,

                        "sector":
                            current_sector,

                        "project_name":
                            project_details[
                                "project_name"
                            ],

                        "agency":
                            project_details[
                                "agency"
                            ],

                        "project_code":
                            project_details[
                                "project_code"
                            ],

                        "approval_date":
                            approval_date,

                        "original_completion":
                            commissioning_dates[
                                "original_completion"
                            ],

                        "revised_completion":
                            commissioning_dates[
                                "revised_completion"
                            ],

                        "anticipated_completion":
                            commissioning_dates[
                                "anticipated_completion"
                            ],

                        "original_cost":
                            costs[
                                "original_cost"
                            ],

                        "revised_cost":
                            costs[
                                "revised_cost"
                            ],

                        "anticipated_cost":
                            costs[
                                "anticipated_cost"
                            ],

                        "cumulative_expenditure":
                            cumulative_expenditure,

                        "physical_progress":
                            physical_progress,

                        "source_page":
                            page_number
                    }


                    projects.append(project)


    return projects


# ============================================================
# SAVE PROJECTS
# ============================================================

def save_projects(projects):

    output = {

        "total_projects":
            len(projects),

        "projects":
            projects
    }


    with open(

        OUTPUT_PATH,

        "w",

        encoding="utf-8"

    ) as file:


        json.dump(

            output,

            file,

            indent=4,

            ensure_ascii=False

        )


# ============================================================
# DISPLAY EXTRACTION SUMMARY
# ============================================================

def display_summary(projects):

    print()

    print("=" * 100)
    print("EXTRACTION COMPLETE")
    print("=" * 100)

    print()

    print(
        f"Projects Extracted: {len(projects)}"
    )


    # ========================================================
    # FIRST PROJECT
    # ========================================================

    if projects:

        print()
        print("FIRST PROJECT:")
        print()

        print(

            json.dumps(

                projects[0],

                indent=4,

                ensure_ascii=False

            )

        )


    # ========================================================
    # LAST PROJECT
    # ========================================================

    if projects:

        print()
        print("LAST PROJECT:")
        print()

        print(

            json.dumps(

                projects[-1],

                indent=4,

                ensure_ascii=False

            )

        )


    # ========================================================
    # CONTEXT STATISTICS
    # ========================================================

    missing_state = sum(

        1

        for project in projects

        if not project.get("state")

    )


    missing_sector = sum(

        1

        for project in projects

        if not project.get("sector")

    )


    print()

    print("-" * 100)

    print(
        f"Projects Missing State: {missing_state}"
    )

    print(
        f"Projects Missing Sector: {missing_sector}"
    )

    print("-" * 100)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    projects = extract_projects()


    # ========================================================
    # DISPLAY RESULTS
    # ========================================================

    display_summary(
        projects
    )


    # ========================================================
    # SAVE JSON
    # ========================================================

    save_projects(
        projects
    )


    print()

    print(
        f"Saved to: {OUTPUT_PATH}"
    )


    print()

    print("=" * 100)
    print("DONE")
    print("=" * 100)