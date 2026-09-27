import json
from pathlib import Path
from collections import Counter


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECTS_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "projects.json"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_missing(value):

    if value is None:
        return True

    if isinstance(value, str):
        return value.strip() == ""

    return False


def get_missing_projects(projects, field):

    return [
        project
        for project in projects
        if is_missing(project.get(field))
    ]


# ============================================================
# LOAD PROJECTS
# ============================================================

def load_projects():

    if not PROJECTS_FILE.exists():

        raise FileNotFoundError(
            f"\nprojects.json not found:\n{PROJECTS_FILE}"
        )

    with open(
        PROJECTS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        data = json.load(file)


    # --------------------------------------------------------
    # CASE 1:
    # JSON is directly a list of projects
    #
    # [
    #     {...},
    #     {...}
    # ]
    # --------------------------------------------------------

    if isinstance(data, list):

        return data


    # --------------------------------------------------------
    # CASE 2:
    # JSON is a dictionary containing projects
    #
    # {
    #     "projects": [...],
    #     "metadata": {...}
    # }
    # --------------------------------------------------------

    if isinstance(data, dict):

        print()
        print("JSON ROOT STRUCTURE: Dictionary")
        print(f"Available Keys: {list(data.keys())}")
        print()

        if "projects" in data:

            projects = data["projects"]

            if isinstance(projects, list):

                return projects

            raise ValueError(
                "\nThe 'projects' key exists, "
                "but its value is not a list.\n"
                f"Found type: {type(projects).__name__}"
            )


        # ----------------------------------------------------
        # FALLBACK:
        # Look for a list value containing project records
        # ----------------------------------------------------

        for key, value in data.items():

            if isinstance(value, list):

                if len(value) == 0:

                    continue

                if isinstance(value[0], dict):

                    print(
                        f"Using '{key}' as the project list."
                    )

                    return value


        raise ValueError(
            "\nCould not find a project list in projects.json.\n"
            f"Available keys: {list(data.keys())}"
        )


    # --------------------------------------------------------
    # INVALID STRUCTURE
    # --------------------------------------------------------

    raise ValueError(
        "\nUnexpected JSON structure.\n"
        f"Root type: {type(data).__name__}"
    )


# ============================================================
# VALIDATE PROJECT RECORD STRUCTURE
# ============================================================

def validate_record_structure(projects):

    print("-" * 100)
    print("PROJECT RECORD STRUCTURE")
    print("-" * 100)

    if not projects:

        raise ValueError(
            "No project records found."
        )

    invalid_records = []

    for index, project in enumerate(projects):

        if not isinstance(project, dict):

            invalid_records.append({
                "index": index,
                "type": type(project).__name__,
                "value": project
            })


    print(f"Total Records: {len(projects)}")

    print(
        f"Valid Dictionary Records: "
        f"{len(projects) - len(invalid_records)}"
    )

    print(
        f"Invalid Records: "
        f"{len(invalid_records)}"
    )


    if invalid_records:

        print()
        print("INVALID RECORD EXAMPLES:")

        for record in invalid_records[:10]:

            print(record)

        raise ValueError(
            "\nSome project records are not dictionaries."
        )


    print()

    print("Sample Project Keys:")

    print(
        list(projects[0].keys())
    )

    print()


# ============================================================
# FIELD COMPLETENESS
# ============================================================

def validate_field_completeness(projects):

    print("-" * 100)
    print("FIELD COMPLETENESS")
    print("-" * 100)

    fields = [

        "table_number",
        "serial_number",

        "state",
        "sector",

        "project_name",
        "agency",
        "project_code",

        "approval_date",

        "original_completion",
        "revised_completion",
        "anticipated_completion",

        "original_cost",
        "revised_cost",
        "anticipated_cost",

        "cumulative_expenditure",
        "physical_progress",

        "source_page",

    ]


    results = {}


    for field in fields:

        missing_projects = get_missing_projects(
            projects,
            field
        )

        missing_count = len(
            missing_projects
        )

        present_count = (
            len(projects)
            - missing_count
        )

        percentage = (
            present_count
            / len(projects)
            * 100
        )


        results[field] = {

            "present": present_count,

            "missing": missing_count,

            "percentage": percentage,

        }


        print(

            f"{field:<30}"

            f"Present: {present_count:<6}"

            f"Missing: {missing_count:<6}"

            f"({percentage:.2f}%)"

        )


    print()

    return results


# ============================================================
# TABLE DISTRIBUTION
# ============================================================

def validate_table_distribution(projects):

    print("-" * 100)
    print("TABLE DISTRIBUTION")
    print("-" * 100)


    table_counter = Counter()


    for project in projects:

        table_number = project.get(
            "table_number"
        )

        table_counter[
            table_number
        ] += 1


    for table_number, count in sorted(

        table_counter.items(),

        key=lambda item:
        (
            item[0] is None,
            item[0]
        )

    ):

        print(

            f"Table {table_number}: "
            f"{count} projects"

        )


    print()


# ============================================================
# STATE DISTRIBUTION
# ============================================================

def validate_state_distribution(projects):

    print("-" * 100)
    print("STATE DISTRIBUTION")
    print("-" * 100)


    state_counter = Counter()


    for project in projects:

        state = project.get(
            "state"
        )


        if not is_missing(state):

            state_counter[
                state.strip()
            ] += 1


    print(
        f"Unique States: "
        f"{len(state_counter)}"
    )

    print()


    for state, count in state_counter.most_common():

        print(

            f"{state:<45}"

            f"{count}"

        )


    print()


# ============================================================
# SECTOR DISTRIBUTION
# ============================================================

def validate_sector_distribution(projects):

    print("-" * 100)
    print("SECTOR DISTRIBUTION")
    print("-" * 100)


    sector_counter = Counter()


    for project in projects:

        sector = project.get(
            "sector"
        )


        if not is_missing(sector):

            sector_counter[
                sector.strip()
            ] += 1


    print(

        f"Unique Sectors: "
        f"{len(sector_counter)}"

    )

    print()


    for sector, count in sector_counter.most_common():

        print(

            f"{sector:<45}"

            f"{count}"

        )


    print()


# ============================================================
# AGENCY DISTRIBUTION
# ============================================================

def validate_agency_distribution(projects):

    print("-" * 100)
    print("AGENCY DISTRIBUTION")
    print("-" * 100)


    agency_counter = Counter()


    for project in projects:

        agency = project.get(
            "agency"
        )


        if not is_missing(agency):

            agency_counter[
                agency.strip()
            ] += 1


    print(

        f"Unique Agencies: "
        f"{len(agency_counter)}"

    )

    print()


    print("TOP 20 AGENCIES:")

    print()


    for agency, count in agency_counter.most_common(20):

        print(

            f"{agency:<45}"

            f"{count}"

        )


    print()


# ============================================================
# DUPLICATE PROJECT CODES
# ============================================================

def validate_duplicate_project_codes(projects):

    print("-" * 100)
    print("DUPLICATE PROJECT CODES")
    print("-" * 100)


    project_code_counter = Counter()


    for project in projects:

        project_code = project.get(
            "project_code"
        )


        if not is_missing(project_code):

            project_code_counter[
                project_code.strip()
            ] += 1


    duplicates = {


        code: count


        for code, count

        in project_code_counter.items()


        if count > 1

    }


    print(

        f"Duplicate Project Codes: "
        f"{len(duplicates)}"

    )


    if duplicates:

        print()

        print("FIRST 20 DUPLICATES:")

        print()


        for code, count in list(

            duplicates.items()

        )[:20]:

            print(

                f"{code:<30}"

                f"{count} occurrences"

            )


    else:

        print()

        print(
            "No duplicate project codes found."
        )


    print()


    return duplicates


# ============================================================
# PHYSICAL PROGRESS VALIDATION
# ============================================================

def validate_physical_progress(projects):

    print("-" * 100)
    print("PHYSICAL PROGRESS VALIDATION")
    print("-" * 100)


    invalid_projects = []


    for project in projects:

        progress = project.get(
            "physical_progress"
        )


        if progress is None:

            continue


        if not isinstance(
            progress,
            (int, float)
        ):

            invalid_projects.append(
                project
            )

            continue


        if progress < 0 or progress > 100:

            invalid_projects.append(
                project
            )


    print(

        f"Invalid Physical Progress Values: "
        f"{len(invalid_projects)}"

    )


    if invalid_projects:

        print()

        print(
            "FIRST 10 INVALID PROJECTS:"
        )

        print()


        for project in invalid_projects[:10]:

            print(

                f"Project Code: "
                f"{project.get('project_code')}"

            )

            print(

                f"Project Name: "
                f"{project.get('project_name')}"

            )

            print(

                f"Physical Progress: "
                f"{project.get('physical_progress')}"

            )

            print()


    print()


    return invalid_projects


# ============================================================
# NEGATIVE NUMERIC VALUES
# ============================================================

def validate_numeric_values(projects):

    print("-" * 100)
    print("NEGATIVE COST / EXPENDITURE VALIDATION")
    print("-" * 100)


    numeric_fields = [

        "original_cost",

        "revised_cost",

        "anticipated_cost",

        "cumulative_expenditure",

    ]


    negative_values = []


    for project in projects:

        for field in numeric_fields:

            value = project.get(field)


            if isinstance(
                value,
                (int, float)
            ):

                if value < 0:

                    negative_values.append({

                        "project_code":
                            project.get(
                                "project_code"
                            ),

                        "project_name":
                            project.get(
                                "project_name"
                            ),

                        "field":
                            field,

                        "value":
                            value,

                    })


    print(

        f"Negative Numeric Values: "
        f"{len(negative_values)}"

    )


    if negative_values:

        print()

        print(
            "FIRST 10 NEGATIVE VALUES:"
        )

        print()


        for item in negative_values[:10]:

            print(item)


    print()


    return negative_values


# ============================================================
# MISSING STATE EXAMPLES
# ============================================================

def show_missing_state_examples(projects):

    print("-" * 100)
    print("MISSING STATE EXAMPLES")
    print("-" * 100)


    missing_states = get_missing_projects(

        projects,

        "state"

    )


    print(

        f"Projects Missing State: "
        f"{len(missing_states)}"

    )

    print()


    for project in missing_states[:10]:

        print(

            f"Serial Number: "
            f"{project.get('serial_number')}"

        )

        print(

            f"Project Name: "
            f"{project.get('project_name')}"

        )

        print(

            f"Project Code: "
            f"{project.get('project_code')}"

        )

        print(

            f"Sector: "
            f"{project.get('sector')}"

        )

        print(

            f"Table: "
            f"{project.get('table_number')}"

        )

        print(

            f"Source Page: "
            f"{project.get('source_page')}"

        )

        print()


    return missing_states


# ============================================================
# MISSING SECTOR EXAMPLES
# ============================================================

def show_missing_sector_examples(projects):

    print("-" * 100)
    print("MISSING SECTOR EXAMPLES")
    print("-" * 100)


    missing_sectors = get_missing_projects(

        projects,

        "sector"

    )


    print(

        f"Projects Missing Sector: "
        f"{len(missing_sectors)}"

    )

    print()


    for project in missing_sectors[:10]:

        print(

            f"Serial Number: "
            f"{project.get('serial_number')}"

        )

        print(

            f"Project Name: "
            f"{project.get('project_name')}"

        )

        print(

            f"Project Code: "
            f"{project.get('project_code')}"

        )

        print(

            f"State: "
            f"{project.get('state')}"

        )

        print(

            f"Table: "
            f"{project.get('table_number')}"

        )

        print(

            f"Source Page: "
            f"{project.get('source_page')}"

        )

        print()


    return missing_sectors


# ============================================================
# MAIN VALIDATION
# ============================================================

def validate_projects(projects):

    print("=" * 100)

    print(
        "NIRMANTRACK PROJECT DATA VALIDATION"
    )

    print("=" * 100)

    print()


    print(

        f"Total Projects Loaded: "
        f"{len(projects)}"

    )

    print()


    # --------------------------------------------------------
    # 1. RECORD STRUCTURE
    # --------------------------------------------------------

    validate_record_structure(
        projects
    )


    # --------------------------------------------------------
    # 2. FIELD COMPLETENESS
    # --------------------------------------------------------

    field_results = (
        validate_field_completeness(
            projects
        )
    )


    # --------------------------------------------------------
    # 3. TABLE DISTRIBUTION
    # --------------------------------------------------------

    validate_table_distribution(
        projects
    )


    # --------------------------------------------------------
    # 4. STATE DISTRIBUTION
    # --------------------------------------------------------

    validate_state_distribution(
        projects
    )


    # --------------------------------------------------------
    # 5. SECTOR DISTRIBUTION
    # --------------------------------------------------------

    validate_sector_distribution(
        projects
    )


    # --------------------------------------------------------
    # 6. AGENCY DISTRIBUTION
    # --------------------------------------------------------

    validate_agency_distribution(
        projects
    )


    # --------------------------------------------------------
    # 7. DUPLICATE PROJECT CODES
    # --------------------------------------------------------

    duplicates = (
        validate_duplicate_project_codes(
            projects
        )
    )


    # --------------------------------------------------------
    # 8. PHYSICAL PROGRESS
    # --------------------------------------------------------

    invalid_progress = (
        validate_physical_progress(
            projects
        )
    )


    # --------------------------------------------------------
    # 9. NUMERIC VALUES
    # --------------------------------------------------------

    negative_values = (
        validate_numeric_values(
            projects
        )
    )


    # --------------------------------------------------------
    # 10. MISSING STATES
    # --------------------------------------------------------

    missing_states = (
        show_missing_state_examples(
            projects
        )
    )


    print()


    # --------------------------------------------------------
    # 11. MISSING SECTORS
    # --------------------------------------------------------

    missing_sectors = (
        show_missing_sector_examples(
            projects
        )
    )


    print()


    # ========================================================
    # FINAL SUMMARY
    # ========================================================

    print("=" * 100)

    print(
        "VALIDATION SUMMARY"
    )

    print("=" * 100)

    print()


    print(
        f"Total Projects: "
        f"{len(projects)}"
    )


    print(
        f"Missing State: "
        f"{len(missing_states)}"
    )


    print(
        f"Missing Sector: "
        f"{len(missing_sectors)}"
    )


    print(
        f"Missing Project Name: "
        f"{field_results['project_name']['missing']}"
    )


    print(
        f"Missing Agency: "
        f"{field_results['agency']['missing']}"
    )


    print(
        f"Missing Project Code: "
        f"{field_results['project_code']['missing']}"
    )


    print(
        f"Duplicate Project Codes: "
        f"{len(duplicates)}"
    )


    print(
        f"Invalid Progress Values: "
        f"{len(invalid_progress)}"
    )


    print(
        f"Negative Numeric Values: "
        f"{len(negative_values)}"
    )


    print()

    print("=" * 100)

    print(
        "VALIDATION COMPLETE"
    )

    print("=" * 100)


# ============================================================
# MAIN
# ============================================================

def main():

    projects = load_projects()


    print()

    print(
        f"Loaded {len(projects)} "
        f"project records."
    )

    print()


    validate_projects(
        projects
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()