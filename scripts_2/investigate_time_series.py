import pandas as pd
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    BASE_DIR
    / "data"
    / "processed"
    / "ml_project_timeline_features.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
    / "time_series"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPER FUNCTION
# ============================================================

def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# 1. LOAD DATASET
# ============================================================

print_section("1. LOADING TIME SERIES DATASET")

print(f"ML SERVICE DIRECTORY:\n{BASE_DIR}\n")

print(f"INPUT FILE:\n{INPUT_FILE}\n")

print(f"OUTPUT DIRECTORY:\n{OUTPUT_DIR}\n")


if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"\nDataset not found:\n{INPUT_FILE}\n"
    )


df = pd.read_csv(INPUT_FILE)

print("Dataset loaded successfully.\n")

print(f"Total records: {len(df):,}")
print(f"Total columns: {len(df.columns):,}")


# ============================================================
# 2. VALIDATE REQUIRED COLUMNS
# ============================================================

print_section("2. VALIDATING REQUIRED COLUMNS")


required_columns = [

    "canonical_id",

    "report_month",

    "physical_progress",

    "cumulative_expenditure"

]


missing_columns = []


for column in required_columns:

    if column in df.columns:

        print(f"[FOUND]   {column}")

    else:

        print(f"[MISSING] {column}")

        missing_columns.append(column)


if missing_columns:

    raise ValueError(

        "\nRequired columns missing:\n"

        + "\n".join(missing_columns)

    )


print("\nAll required columns found.")


# ============================================================
# 3. PREPARE DATA TYPES
# ============================================================

print_section("3. PREPARING DATA TYPES")


print("Converting report_month to datetime...")

df["report_month"] = pd.to_datetime(

    df["report_month"],

    errors="coerce"

)


print("Converting physical_progress to numeric...")

df["physical_progress"] = pd.to_numeric(

    df["physical_progress"],

    errors="coerce"

)


print("Converting cumulative_expenditure to numeric...")

df["cumulative_expenditure"] = pd.to_numeric(

    df["cumulative_expenditure"],

    errors="coerce"

)


# ============================================================
# 4. REMOVE INVALID TIME RECORDS
# ============================================================

print_section("4. CHECKING TIME DATA QUALITY")


invalid_dates = df["report_month"].isna().sum()


print(

    f"Records with invalid report_month: "

    f"{invalid_dates:,}"

)


df = df.dropna(

    subset=[

        "canonical_id",

        "report_month"

    ]

)


print(

    f"\nRecords remaining: {len(df):,}"

)


# ============================================================
# 5. SORT PROJECT TIMELINES
# ============================================================

print_section("5. SORTING PROJECT TIMELINES")


df = df.sort_values(

    [

        "canonical_id",

        "report_month"

    ]

).reset_index(drop=True)


print(

    "Dataset sorted by:\n"

    "  1. canonical_id\n"

    "  2. report_month"

)


# ============================================================
# 6. DATASET TIME RANGE
# ============================================================

print_section("6. DATASET TIME RANGE")


min_date = df["report_month"].min()

max_date = df["report_month"].max()


print(

    f"Earliest reporting month: "

    f"{min_date}"

)


print(

    f"Latest reporting month: "

    f"{max_date}"

)


print(

    f"\nTotal unique reporting months: "

    f"{df['report_month'].nunique()}"

)


# ============================================================
# 7. PROJECT TIMELINE LENGTH ANALYSIS
# ============================================================

print_section("7. PROJECT TIMELINE LENGTH ANALYSIS")


timeline_lengths = (

    df

    .groupby("canonical_id")

    .size()

    .reset_index(

        name="number_of_observations"

    )

)


print(

    timeline_lengths[

        "number_of_observations"

    ].describe()

)


# ============================================================
# 8. TIMELINE LENGTH DISTRIBUTION
# ============================================================

print_section("8. TIMELINE LENGTH DISTRIBUTION")


timeline_distribution = (

    timeline_lengths

    ["number_of_observations"]

    .value_counts()

    .sort_index()

    .reset_index()

)


timeline_distribution.columns = [

    "observations",

    "number_of_projects"

]


print(

    timeline_distribution.to_string(

        index=False

    )

)


timeline_distribution.to_csv(

    OUTPUT_DIR

    / "timeline_length_distribution.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'timeline_length_distribution.csv'}"

)


# ============================================================
# 9. PROJECT TIME RANGE ANALYSIS
# ============================================================

print_section("9. PROJECT TIME RANGE ANALYSIS")


project_time_range = (

    df

    .groupby("canonical_id")

    .agg(

        first_month=(

            "report_month",

            "min"

        ),

        last_month=(

            "report_month",

            "max"

        ),

        observations=(

            "report_month",

            "count"

        )

    )

    .reset_index()

)


project_time_range[

    "timeline_span_days"

] = (

    project_time_range[

        "last_month"

    ]

    -

    project_time_range[

        "first_month"

    ]

).dt.days


project_time_range[

    "timeline_span_months"

] = (

    project_time_range[

        "timeline_span_days"

    ]

    /

    30.44

).round(2)


print(

    project_time_range[

        "timeline_span_months"

    ].describe()

)


project_time_range.to_csv(

    OUTPUT_DIR

    / "project_time_ranges.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'project_time_ranges.csv'}"

)


# ============================================================
# 10. CHECK MONTHLY CONTINUITY
# ============================================================

print_section("10. CHECKING MONTHLY CONTINUITY")


df[

    "previous_report_month"

] = (

    df

    .groupby(

        "canonical_id"

    )

    ["report_month"]

    .shift(1)

)


df[

    "month_gap_days"

] = (

    df[

        "report_month"

    ]

    -

    df[

        "previous_report_month"

    ]

).dt.days


df[

    "month_gap_months"

] = (

    df[

        "month_gap_days"

    ]

    /

    30.44

)


gaps = df[

    df[

        "month_gap_months"

    ]

    > 1.5

]


print(

    f"Records with timeline gaps > 1.5 months: "

    f"{len(gaps):,}"

)


print(

    f"Projects affected: "

    f"{gaps['canonical_id'].nunique():,}"

)


gaps.to_csv(

    OUTPUT_DIR

    / "timeline_gaps.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'timeline_gaps.csv'}"

)


# ============================================================
# 11. OBSERVATIONS PER REPORTING MONTH
# ============================================================

print_section("11. OBSERVATIONS PER REPORTING MONTH")


monthly_counts = (

    df

    .groupby(

        "report_month"

    )

    .size()

    .reset_index(

        name="records"

    )

)


print(

    monthly_counts.to_string(

        index=False

    )

)


monthly_counts.to_csv(

    OUTPUT_DIR

    / "monthly_record_counts.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'monthly_record_counts.csv'}"

)


# ============================================================
# 12. PHYSICAL PROGRESS TIME SERIES SUMMARY
# ============================================================

print_section("12. PHYSICAL PROGRESS TIME SERIES SUMMARY")


progress_summary = (

    df

    .groupby(

        "report_month"

    )

    ["physical_progress"]

    .agg(

        [

            "count",

            "mean",

            "median",

            "min",

            "max",

            "std"

        ]

    )

    .reset_index()

)


print(

    progress_summary.to_string(

        index=False

    )

)


progress_summary.to_csv(

    OUTPUT_DIR

    / "monthly_progress_summary.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'monthly_progress_summary.csv'}"

)


# ============================================================
# 13. EXPENDITURE TIME SERIES SUMMARY
# ============================================================

print_section("13. EXPENDITURE TIME SERIES SUMMARY")


expenditure_summary = (

    df

    .groupby(

        "report_month"

    )

    ["cumulative_expenditure"]

    .agg(

        [

            "count",

            "mean",

            "median",

            "min",

            "max",

            "std"

        ]

    )

    .reset_index()

)


print(

    expenditure_summary.to_string(

        index=False

    )

)


expenditure_summary.to_csv(

    OUTPUT_DIR

    / "monthly_expenditure_summary.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'monthly_expenditure_summary.csv'}"

)


# ============================================================
# 14. DUPLICATE PROJECT MONTH CHECK
# ============================================================

print_section("14. CHECKING DUPLICATE PROJECT-MONTH RECORDS")


duplicates = df[

    df.duplicated(

        subset=[

            "canonical_id",

            "report_month"

        ],

        keep=False

    )

]


print(

    f"Duplicate project-month records: "

    f"{len(duplicates):,}"

)


if len(duplicates) > 0:

    duplicates.to_csv(

        OUTPUT_DIR

        / "duplicate_project_month_records.csv",

        index=False

    )


    print(

        "\nSaved:\n"

        f"{OUTPUT_DIR / 'duplicate_project_month_records.csv'}"

    )


# ============================================================
# 15. MISSING VALUE ANALYSIS
# ============================================================

print_section("15. TIME SERIES MISSING VALUE ANALYSIS")


missing_summary = pd.DataFrame(

    {

        "column": [

            "physical_progress",

            "cumulative_expenditure"

        ],

        "missing_records": [

            df[

                "physical_progress"

            ].isna().sum(),

            df[

                "cumulative_expenditure"

            ].isna().sum()

        ]

    }

)


missing_summary[

    "missing_percentage"

] = (

    missing_summary[

        "missing_records"

    ]

    /

    len(df)

    *

    100

).round(4)


print(

    missing_summary.to_string(

        index=False

    )

)


missing_summary.to_csv(

    OUTPUT_DIR

    / "time_series_missing_values.csv",

    index=False

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'time_series_missing_values.csv'}"

)


# ============================================================
# 16. BUILD TIME SERIES DATA QUALITY SUMMARY
# ============================================================

print_section("16. BUILDING TIME SERIES DATA QUALITY SUMMARY")


summary = pd.DataFrame(

    [

        {

            "metric":

            "total_records",

            "value":

            len(df)

        },

        {

            "metric":

            "unique_projects",

            "value":

            df[

                "canonical_id"

            ].nunique()

        },

        {

            "metric":

            "unique_reporting_months",

            "value":

            df[

                "report_month"

            ].nunique()

        },

        {

            "metric":

            "earliest_report_month",

            "value":

            min_date

        },

        {

            "metric":

            "latest_report_month",

            "value":

            max_date

        },

        {

            "metric":

            "projects_with_timeline_gaps",

            "value":

            gaps[

                "canonical_id"

            ].nunique()

        },

        {

            "metric":

            "timeline_gap_records",

            "value":

            len(gaps)

        },

        {

            "metric":

            "duplicate_project_month_records",

            "value":

            len(duplicates)

        }

    ]

)


summary.to_csv(

    OUTPUT_DIR

    / "time_series_summary.csv",

    index=False

)


print(

    summary.to_string(

        index=False

    )

)


print(

    "\nSaved:\n"

    f"{OUTPUT_DIR / 'time_series_summary.csv'}"

)


# ============================================================
# COMPLETE
# ============================================================

print_section(

    "TIME SERIES INVESTIGATION COMPLETE"

)


print(

    "Generated reports:\n"

)


for file in sorted(

    OUTPUT_DIR.glob("*.csv")

):

    print(

        f"  - {file.name}"

    )


print(

    "\nDONE."

)