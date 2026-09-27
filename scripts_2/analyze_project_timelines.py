import pandas as pd
import numpy as np
from pathlib import Path
import random


# ============================================================
# PATH CONFIGURATION
# ============================================================

# Current file:
# ml-service/scripts_2/analyze_project_timelines.py
#
# parent      -> scripts_2
# parent.parent -> ml-service

ML_SERVICE_DIR = Path(__file__).resolve().parent.parent


DATA_PATH = (
    ML_SERVICE_DIR
    / "data"
    / "processed"
    / "master_project_dataset_clean.csv"
)


OUTPUT_DIR = (
    ML_SERVICE_DIR
    / "data"
    / "analysis"
)


OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

RANDOM_SEED = 42

random.seed(RANDOM_SEED)


# Expected reporting periods based on your dataset:
#
# July 2025 to July 2026
#
# Missing PDFs:
# September 2025
# March 2026

EXPECTED_MONTHS = [
    "2025-07",
    "2025-08",
    "2025-10",
    "2025-11",
    "2025-12",
    "2026-01",
    "2026-02",
    "2026-04",
    "2026-05",
    "2026-06",
    "2026-07",
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


def column_exists(df, column_name):
    """
    Check whether a column exists in the dataframe.
    """

    return column_name in df.columns


def safe_numeric(df, column_name):
    """
    Convert a column to numeric if it exists.
    """

    if column_name in df.columns:

        df[column_name] = pd.to_numeric(
            df[column_name],
            errors="coerce"
        )


def safe_datetime(df, column_name):
    """
    Convert a column to datetime if it exists.
    """

    if column_name in df.columns:

        df[column_name] = pd.to_datetime(
            df[column_name],
            errors="coerce"
        )


def get_existing_columns(df, requested_columns):
    """
    Return only columns that actually exist.
    """

    return [
        column
        for column in requested_columns
        if column in df.columns
    ]


def print_column_warning(column_name):
    """
    Print a warning when an expected column does not exist.
    """

    print(
        f"WARNING: Column '{column_name}' "
        f"does not exist. Skipping this analysis."
    )


# ============================================================
# LOAD DATASET
# ============================================================

print_section("LOADING DATASET")


print(f"ML SERVICE DIRECTORY:\n{ML_SERVICE_DIR}")

print(f"\nDATASET PATH:\n{DATA_PATH}")

print(f"\nOUTPUT DIRECTORY:\n{OUTPUT_DIR}")


if not DATA_PATH.exists():

    print("\nERROR: Dataset not found.")

    print(
        "\nExpected dataset location:"
    )

    print(DATA_PATH)

    raise SystemExit(1)


try:

    df = pd.read_csv(
        DATA_PATH,
        low_memory=False
    )

except Exception as error:

    print(
        "\nERROR: Could not load CSV."
    )

    print(error)

    raise SystemExit(1)


print(
    "\nDataset loaded successfully."
)


# ============================================================
# 1. RAW DATASET INSPECTION
# ============================================================

print_section("1. RAW DATASET INSPECTION")


print(
    f"Dataset shape: {df.shape}"
)

print(
    f"Total rows: {len(df):,}"
)

print(
    f"Total columns: {len(df.columns):,}"
)


print("\nCOLUMN NAMES:")

for index, column in enumerate(
    df.columns,
    start=1
):

    print(
        f"{index}. {column}"
    )


print("\nDATA TYPES:")

print(
    df.dtypes.to_string()
)


print("\nFIRST 3 ROWS:")

print(
    df.head(3).to_string()
)


# ============================================================
# 2. EXPECTED COLUMN CHECK
# ============================================================

print_section("2. EXPECTED COLUMN CHECK")


expected_columns = [

    "canonical_id",

    "month",

    "report_month",

    "project_name",

    "state",

    "physical_progress",

    "cumulative_expenditure",

    "original_cost",

    "revised_cost",

    "original_approval_date",

    "revised_approval_date",

    "original_target_date",

    "revised_target_date",
]


print("Checking expected ML timeline columns...\n")


available_expected_columns = []

missing_expected_columns = []


for column in expected_columns:

    if column in df.columns:

        print(
            f"[FOUND]   {column}"
        )

        available_expected_columns.append(
            column
        )

    else:

        print(
            f"[MISSING] {column}"
        )

        missing_expected_columns.append(
            column
        )


print(
    f"\nExpected columns found: "
    f"{len(available_expected_columns)}"
)


print(
    f"Expected columns missing: "
    f"{len(missing_expected_columns)}"
)


# ============================================================
# 3. DATA TYPE PREPARATION
# ============================================================

print_section("3. DATA TYPE PREPARATION")


numeric_columns = [

    "physical_progress",

    "cumulative_expenditure",

    "original_cost",

    "revised_cost",
]


for column in numeric_columns:

    if column in df.columns:

        print(
            f"Converting to numeric: {column}"
        )

        safe_numeric(
            df,
            column
        )

    else:

        print_column_warning(
            column
        )


date_columns = [

    "report_month",

    "original_approval_date",

    "revised_approval_date",

    "original_target_date",

    "revised_target_date",
]


for column in date_columns:

    if column in df.columns:

        print(
            f"Converting to datetime: {column}"
        )

        safe_datetime(
            df,
            column
        )

    else:

        print_column_warning(
            column
        )


# ============================================================
# 4. MONTH PREPARATION
# ============================================================

print_section("4. MONTH PREPARATION")


if "month" in df.columns:

    df["month"] = (
        df["month"]
        .astype(str)
        .str.strip()
    )

    print(
        "Using existing 'month' column."
    )


elif "report_month" in df.columns:

    df["month"] = (
        df["report_month"]
        .dt.strftime("%Y-%m")
    )

    print(
        "Created 'month' from 'report_month'."
    )


else:

    print(
        "WARNING: Neither 'month' nor "
        "'report_month' exists."
    )


# ============================================================
# 5. SORT DATA
# ============================================================

print_section("5. SORTING DATA")


if (
    "canonical_id" in df.columns
    and "report_month" in df.columns
):

    df = df.sort_values(

        [
            "canonical_id",
            "report_month",
        ]

    ).reset_index(drop=True)


    print(
        "Dataset sorted by canonical_id "
        "and report_month."
    )


elif (
    "canonical_id" in df.columns
    and "month" in df.columns
):

    df = df.sort_values(

        [
            "canonical_id",
            "month",
        ]

    ).reset_index(drop=True)


    print(
        "Dataset sorted by canonical_id "
        "and month."
    )


else:

    print(
        "WARNING: Could not sort project timelines."
    )


# ============================================================
# 6. DATASET OVERVIEW
# ============================================================

print_section("6. DATASET OVERVIEW")


print(
    f"Total records: {len(df):,}"
)


if "canonical_id" in df.columns:

    unique_projects = (
        df["canonical_id"]
        .nunique()
    )

    print(
        f"Unique projects: "
        f"{unique_projects:,}"
    )

else:

    unique_projects = None

    print_column_warning(
        "canonical_id"
    )


if "month" in df.columns:

    unique_months = sorted(

        df["month"]
        .dropna()
        .unique()

    )

    print(
        f"Reporting periods: "
        f"{len(unique_months)}"
    )


    print(
        "\nAvailable reporting months:"
    )


    for month in unique_months:

        print(
            f"  - {month}"
        )


else:

    unique_months = []

    print_column_warning(
        "month"
    )


print(
    "\nExpected reporting months:"
)


for month in EXPECTED_MONTHS:

    print(
        f"  - {month}"
    )


if unique_months:

    missing_report_months = sorted(

        set(EXPECTED_MONTHS)

        -

        set(unique_months)

    )


    print(
        "\nMissing expected months:"
    )


    if missing_report_months:

        for month in missing_report_months:

            print(
                f"  - {month}"
            )

    else:

        print(
            "  None"
        )


# ============================================================
# 7. SNAPSHOT ANALYSIS
# ============================================================

print_section("7. SNAPSHOT ANALYSIS")


snapshot_counts = None


if "canonical_id" in df.columns:

    snapshot_counts = (

        df.groupby("canonical_id")
        .size()
        .rename("snapshot_count")

    )


    print(
        f"Minimum snapshots/project: "
        f"{snapshot_counts.min()}"
    )


    print(
        f"Maximum snapshots/project: "
        f"{snapshot_counts.max()}"
    )


    print(
        f"Average snapshots/project: "
        f"{snapshot_counts.mean():.2f}"
    )


    print(
        f"Median snapshots/project: "
        f"{snapshot_counts.median():.2f}"
    )


    print(
        "\nSnapshot count distribution:"
    )


    print(

        snapshot_counts
        .value_counts()
        .sort_index()
        .to_string()

    )


    snapshot_counts.to_csv(

        OUTPUT_DIR
        / "snapshot_counts_per_project.csv",

        header=True

    )


    print(

        "\nSaved: "
        "snapshot_counts_per_project.csv"

    )


else:

    print_column_warning(
        "canonical_id"
    )


# ============================================================
# 8. DUPLICATE PROJECT-MONTH ANALYSIS
# ============================================================

print_section("8. DUPLICATE PROJECT-MONTH ANALYSIS")


if (
    "canonical_id" in df.columns
    and "month" in df.columns
):

    duplicates = df[

        df.duplicated(

            subset=[
                "canonical_id",
                "month",
            ],

            keep=False

        )

    ]


    duplicate_count = len(
        duplicates
    )


    print(

        f"Duplicate project-month rows: "
        f"{duplicate_count:,}"

    )


    if duplicate_count > 0:

        duplicates.to_csv(

            OUTPUT_DIR
            / "duplicate_project_month_records.csv",

            index=False

        )


        print(

            "Saved duplicate records to: "
            "duplicate_project_month_records.csv"

        )


    else:

        print(
            "No duplicate project-month "
            "records found."
        )


else:

    print(
        "Skipping duplicate analysis."
    )


# ============================================================
# 9. MISSING VALUE ANALYSIS
# ============================================================

print_section("9. MISSING VALUE ANALYSIS")


missing_values = (

    df.isna()
    .sum()
    .sort_values(
        ascending=False
    )

)


missing_percentage = (

    df.isna()
    .mean()
    .mul(100)
    .sort_values(
        ascending=False
    )

)


missing_report = pd.DataFrame({

    "missing_count":
        missing_values,

    "missing_percentage":
        missing_percentage,

})


print(

    missing_report.to_string()

)


missing_report.to_csv(

    OUTPUT_DIR
    / "missing_value_report.csv"

)


print(

    "\nSaved: "
    "missing_value_report.csv"

)


# ============================================================
# 10. PROJECT APPEARANCE ANALYSIS
# ============================================================

print_section("10. PROJECT APPEARANCE ANALYSIS")


if (
    "canonical_id" in df.columns
    and snapshot_counts is not None
):

    appearance_report = pd.DataFrame({

        "snapshot_count":
            snapshot_counts,

    })


    if "report_month" in df.columns:

        first_month = (

            df.groupby(
                "canonical_id"
            )[
                "report_month"
            ]
            .min()

        )


        last_month = (

            df.groupby(
                "canonical_id"
            )[
                "report_month"
            ]
            .max()

        )


        appearance_report[
            "first_report_month"
        ] = first_month


        appearance_report[
            "last_report_month"
        ] = last_month


        appearance_report[
            "first_month"
        ] = (

            appearance_report[
                "first_report_month"
            ]
            .dt.strftime("%Y-%m")

        )


        appearance_report[
            "last_month"
        ] = (

            appearance_report[
                "last_report_month"
            ]
            .dt.strftime("%Y-%m")

        )


    elif "month" in df.columns:

        first_month = (

            df.groupby(
                "canonical_id"
            )[
                "month"
            ]
            .min()

        )


        last_month = (

            df.groupby(
                "canonical_id"
            )[
                "month"
            ]
            .max()

        )


        appearance_report[
            "first_month"
        ] = first_month


        appearance_report[
            "last_month"
        ] = last_month


    if snapshot_counts is not None:

        full_snapshot_projects = (

            snapshot_counts
            == len(EXPECTED_MONTHS)

        ).sum()


        print(

            "Projects appearing in all "
            f"{len(EXPECTED_MONTHS)} expected periods: "

            f"{full_snapshot_projects:,}"

        )


        fewer_snapshot_projects = (

            snapshot_counts
            < len(EXPECTED_MONTHS)

        ).sum()


        print(

            "Projects with fewer than "
            f"{len(EXPECTED_MONTHS)} snapshots: "

            f"{fewer_snapshot_projects:,}"

        )


    appearance_report.to_csv(

        OUTPUT_DIR
        / "project_appearance_report.csv"

    )


    print(

        "\nSaved: "
        "project_appearance_report.csv"

    )


else:

    print(
        "Skipping project appearance analysis."
    )


# ============================================================
# 11. PHYSICAL PROGRESS ANALYSIS
# ============================================================

print_section("11. PHYSICAL PROGRESS ANALYSIS")


if "physical_progress" in df.columns:

    progress = df[
        "physical_progress"
    ]


    print(

        f"Missing progress values: "
        f"{progress.isna().sum():,}"

    )


    print(

        f"Minimum progress: "
        f"{progress.min():.2f}"

    )


    print(

        f"Maximum progress: "
        f"{progress.max():.2f}"

    )


    print(

        f"Average progress: "
        f"{progress.mean():.2f}"

    )


    print(

        f"Median progress: "
        f"{progress.median():.2f}"

    )


    if "canonical_id" in df.columns:

        projects_reaching_100 = (

            df.loc[

                df[
                    "physical_progress"
                ] >= 100,

                "canonical_id"

            ]
            .nunique()

        )


        print(

            "\nProjects reaching "
            "100% progress: "

            f"{projects_reaching_100:,}"

        )


        # --------------------------------------------
        # Previous progress
        # --------------------------------------------

        df[
            "previous_progress"
        ] = (

            df.groupby(
                "canonical_id"
            )[
                "physical_progress"
            ]
            .shift(1)

        )


        # --------------------------------------------
        # Progress change
        # --------------------------------------------

        df[
            "progress_change"
        ] = (

            df[
                "physical_progress"
            ]

            -

            df[
                "previous_progress"
            ]

        )


        decreasing_progress_rows = df[

            df[
                "progress_change"
            ] < 0

        ]


        decreasing_projects = (

            decreasing_progress_rows[
                "canonical_id"
            ]
            .nunique()

        )


        print(

            "Projects with decreasing "
            "physical progress: "

            f"{decreasing_projects:,}"

        )


        if len(
            decreasing_progress_rows
        ) > 0:

            decreasing_progress_rows.to_csv(

                OUTPUT_DIR
                / "decreasing_progress_records.csv",

                index=False

            )


            print(

                "Saved: "
                "decreasing_progress_records.csv"

            )


else:

    print_column_warning(
        "physical_progress"
    )


# ============================================================
# 12. ORIGINAL COST STABILITY
# ============================================================

print_section("12. ORIGINAL COST STABILITY")


if (
    "canonical_id" in df.columns
    and "original_cost" in df.columns
):

    original_cost_unique = (

        df.groupby(
            "canonical_id"
        )[
            "original_cost"
        ]
        .nunique()

    )


    projects_original_cost_changed = (

        original_cost_unique > 1

    ).sum()


    print(

        "Projects where original cost "
        "changes over time: "

        f"{projects_original_cost_changed:,}"

    )


    stable_original_cost_projects = (

        original_cost_unique == 1

    ).sum()


    print(

        "Projects with stable original cost: "

        f"{stable_original_cost_projects:,}"

    )


else:

    print(
        "Skipping original cost stability analysis."
    )


# ============================================================
# 13. REVISED COST ANALYSIS
# ============================================================

print_section("13. REVISED COST ANALYSIS")


revision_counts = None


if (
    "canonical_id" in df.columns
    and "revised_cost" in df.columns
):

    revised_cost_unique = (

        df.groupby(
            "canonical_id"
        )[
            "revised_cost"
        ]
        .nunique()

    )


    projects_with_cost_changes = (

        revised_cost_unique > 1

    ).sum()


    print(

        "Projects with revised cost changes: "

        f"{projects_with_cost_changes:,}"

    )


    # --------------------------------------------
    # Previous revised cost
    # --------------------------------------------

    df[
        "previous_revised_cost"
    ] = (

        df.groupby(
            "canonical_id"
        )[
            "revised_cost"
        ]
        .shift(1)

    )


    # --------------------------------------------
    # Cost change
    # --------------------------------------------

    df[
        "revised_cost_change"
    ] = (

        df[
            "revised_cost"
        ]

        -

        df[
            "previous_revised_cost"
        ]

    )


    cost_increase_rows = df[

        df[
            "revised_cost_change"
        ] > 0

    ]


    cost_decrease_rows = df[

        df[
            "revised_cost_change"
        ] < 0

    ]


    cost_increase_projects = (

        cost_increase_rows[
            "canonical_id"
        ]
        .nunique()

    )


    cost_decrease_projects = (

        cost_decrease_rows[
            "canonical_id"
        ]
        .nunique()

    )


    print(

        "Projects with revised cost increases: "

        f"{cost_increase_projects:,}"

    )


    print(

        "Projects with revised cost decreases: "

        f"{cost_decrease_projects:,}"

    )


    # --------------------------------------------
    # Cost revision events
    # --------------------------------------------

    revision_counts = (

        df.assign(

            cost_revision_event=(

                df[
                    "revised_cost_change"
                ]
                .fillna(0)

                != 0

            )

        )

        .groupby(
            "canonical_id"
        )[
            "cost_revision_event"
        ]

        .sum()

        .rename(
            "cost_revision_count"
        )

    )


    print(

        "\nCost revision count distribution:"
    )


    print(

        revision_counts
        .value_counts()
        .sort_index()
        .to_string()

    )


    revision_counts.to_csv(

        OUTPUT_DIR
        / "cost_revision_counts.csv",

        header=True

    )


    print(

        "\nSaved: "
        "cost_revision_counts.csv"

    )


    # --------------------------------------------
    # Save all projects with cost changes
    # --------------------------------------------

    projects_with_cost_changes_df = df[

        df[
            "canonical_id"
        ].isin(

            revision_counts[

                revision_counts > 0

            ].index

        )

    ]


    projects_with_cost_changes_df.to_csv(

        OUTPUT_DIR
        / "projects_with_cost_changes.csv",

        index=False

    )


    print(

        "Saved: "
        "projects_with_cost_changes.csv"

    )


else:

    print(
        "Skipping revised cost analysis."
    )


# ============================================================
# 14. CUMULATIVE EXPENDITURE ANALYSIS
# ============================================================

print_section("14. CUMULATIVE EXPENDITURE ANALYSIS")


if (
    "canonical_id" in df.columns
    and "cumulative_expenditure" in df.columns
):

    expenditure = df[
        "cumulative_expenditure"
    ]


    print(

        f"Missing expenditure values: "
        f"{expenditure.isna().sum():,}"

    )


    print(

        f"Minimum expenditure: "
        f"{expenditure.min():.2f}"

    )


    print(

        f"Maximum expenditure: "
        f"{expenditure.max():.2f}"

    )


    # --------------------------------------------
    # Previous expenditure
    # --------------------------------------------

    df[
        "previous_expenditure"
    ] = (

        df.groupby(
            "canonical_id"
        )[
            "cumulative_expenditure"
        ]
        .shift(1)

    )


    # --------------------------------------------
    # Expenditure change
    # --------------------------------------------

    df[
        "expenditure_change"
    ] = (

        df[
            "cumulative_expenditure"
        ]

        -

        df[
            "previous_expenditure"
        ]

    )


    negative_expenditure_rows = df[

        df[
            "expenditure_change"
        ] < 0

    ]


    negative_expenditure_projects = (

        negative_expenditure_rows[
            "canonical_id"
        ]
        .nunique()

    )


    print(

        "Projects with decreasing "
        "cumulative expenditure: "

        f"{negative_expenditure_projects:,}"

    )


    if len(
        negative_expenditure_rows
    ) > 0:

        negative_expenditure_rows.to_csv(

            OUTPUT_DIR
            / "decreasing_expenditure_records.csv",

            index=False

        )


        print(

            "Saved: "
            "decreasing_expenditure_records.csv"

        )


else:

    print(
        "Skipping expenditure analysis."
    )


# ============================================================
# 15. DATE STABILITY ANALYSIS
# ============================================================

print_section("15. DATE STABILITY ANALYSIS")


date_change_columns = [

    "original_approval_date",

    "revised_approval_date",

    "original_target_date",

    "revised_target_date",

]


if "canonical_id" in df.columns:

    for column in date_change_columns:

        if column in df.columns:

            unique_date_counts = (

                df.groupby(
                    "canonical_id"
                )[
                    column
                ]
                .nunique()

            )


            changed_projects = (

                unique_date_counts > 1

            ).sum()


            print(

                f"{column}: "

                f"{changed_projects:,} "

                "projects with changes"

            )


        else:

            print_column_warning(
                column
            )


else:

    print_column_warning(
        "canonical_id"
    )


# ============================================================
# 16. SCHEDULE REVISION ANALYSIS
# ============================================================

print_section("16. SCHEDULE REVISION ANALYSIS")


if (
    "original_target_date" in df.columns
    and "revised_target_date" in df.columns
    and "canonical_id" in df.columns
):

    valid_date_rows = df[

        df[
            "original_target_date"
        ].notna()

        &

        df[
            "revised_target_date"
        ].notna()

    ].copy()


    valid_date_rows[
        "schedule_extension_days"
    ] = (

        valid_date_rows[
            "revised_target_date"
        ]

        -

        valid_date_rows[
            "original_target_date"
        ]

    ).dt.days


    projects_with_extension = (

        valid_date_rows.loc[

            valid_date_rows[
                "schedule_extension_days"
            ] > 0,

            "canonical_id"

        ]
        .nunique()

    )


    print(

        "Projects with positive "
        "schedule extension: "

        f"{projects_with_extension:,}"

    )


    projects_with_earlier_target = (

        valid_date_rows.loc[

            valid_date_rows[
                "schedule_extension_days"
            ] < 0,

            "canonical_id"

        ]
        .nunique()

    )


    print(

        "Projects with earlier "
        "revised target date: "

        f"{projects_with_earlier_target:,}"

    )


    same_target_projects = (

        valid_date_rows.loc[

            valid_date_rows[
                "schedule_extension_days"
            ] == 0,

            "canonical_id"

        ]
        .nunique()

    )


    print(

        "Projects with unchanged "
        "target date: "

        f"{same_target_projects:,}"

    )


    valid_date_rows.to_csv(

        OUTPUT_DIR
        / "schedule_revision_analysis.csv",

        index=False

    )


    print(

        "\nSaved: "
        "schedule_revision_analysis.csv"

    )


else:

    print(
        "Skipping schedule revision analysis."
    )


# ============================================================
# 17. RANDOM PROJECT TIMELINES
# ============================================================

print_section("17. RANDOM PROJECT TIMELINES")


if "canonical_id" in df.columns:

    project_ids = (

        df[
            "canonical_id"
        ]
        .dropna()
        .unique()
        .tolist()

    )


    sample_size = min(
        10,
        len(project_ids)
    )


    sample_projects = random.sample(

        project_ids,

        sample_size

    )


    timeline_columns = [

        "month",

        "report_month",

        "physical_progress",

        "cumulative_expenditure",

        "original_cost",

        "revised_cost",

        "original_target_date",

        "revised_target_date",

    ]


    available_timeline_columns = (

        get_existing_columns(

            df,

            timeline_columns

        )

    )


    for project_id in sample_projects:

        project_data = df[

            df[
                "canonical_id"
            ] == project_id

        ].copy()


        print("\n")
        print("-" * 90)

        print(
            f"PROJECT ID: {project_id}"
        )


        if "project_name" in df.columns:

            project_name = (

                project_data[
                    "project_name"
                ]
                .iloc[0]

            )


            print(
                f"PROJECT NAME: "
                f"{project_name}"
            )


        if "state" in df.columns:

            project_state = (

                project_data[
                    "state"
                ]
                .iloc[0]

            )


            print(
                f"STATE: "
                f"{project_state}"
            )


        print("-" * 90)


        print(

            project_data[
                available_timeline_columns
            ]
            .to_string(
                index=False
            )

        )


else:

    print(
        "Skipping random project timeline analysis."
    )


# ============================================================
# 18. SAMPLE COST REVISION TIMELINES
# ============================================================

print_section("18. SAMPLE COST REVISION TIMELINES")


if (
    revision_counts is not None
    and "canonical_id" in df.columns
):

    revision_project_ids = (

        revision_counts[

            revision_counts > 0

        ]

        .index

        .tolist()

    )


    sample_revision_size = min(

        10,

        len(
            revision_project_ids
        )

    )


    if sample_revision_size > 0:

        sample_revision_projects = (

            random.sample(

                revision_project_ids,

                sample_revision_size

            )

        )


        revision_timeline_columns = [

            "month",

            "report_month",

            "original_cost",

            "revised_cost",

            "revised_cost_change",

            "cumulative_expenditure",

            "physical_progress",

        ]


        available_revision_columns = (

            get_existing_columns(

                df,

                revision_timeline_columns

            )

        )


        for project_id in sample_revision_projects:

            project_data = df[

                df[
                    "canonical_id"
                ] == project_id

            ].copy()


            print("\n")
            print("-" * 90)

            print(
                f"PROJECT ID: {project_id}"
            )


            if "project_name" in df.columns:

                print(

                    "PROJECT NAME: "

                    f"{project_data['project_name'].iloc[0]}"

                )


            print("-" * 90)


            print(

                project_data[
                    available_revision_columns
                ]

                .to_string(
                    index=False
                )

            )


    else:

        print(
            "No projects with revised "
            "cost changes found."
        )


else:

    print(
        "Skipping cost revision "
        "timeline analysis."
    )


# ============================================================
# 19. SAMPLE PROJECTS REACHING 100% PROGRESS
# ============================================================

print_section(
    "19. SAMPLE 100% PROGRESS PROJECT TIMELINES"
)


if (
    "canonical_id" in df.columns
    and "physical_progress" in df.columns
):

    completed_like_projects = (

        df.loc[

            df[
                "physical_progress"
            ] >= 100,

            "canonical_id"

        ]

        .dropna()

        .unique()

        .tolist()

    )


    print(

        "Number of projects reaching "
        "100% progress: "

        f"{len(completed_like_projects):,}"

    )


    sample_completed_size = min(

        10,

        len(
            completed_like_projects
        )

    )


    if sample_completed_size > 0:

        sample_completed_projects = (

            random.sample(

                completed_like_projects,

                sample_completed_size

            )

        )


        completed_timeline_columns = [

            "month",

            "report_month",

            "physical_progress",

            "cumulative_expenditure",

            "original_cost",

            "revised_cost",

            "original_target_date",

            "revised_target_date",

        ]


        available_completed_columns = (

            get_existing_columns(

                df,

                completed_timeline_columns

            )

        )


        for project_id in sample_completed_projects:

            project_data = df[

                df[
                    "canonical_id"
                ] == project_id

            ].copy()


            print("\n")
            print("-" * 90)

            print(
                f"PROJECT ID: {project_id}"
            )


            if "project_name" in df.columns:

                print(

                    "PROJECT NAME: "

                    f"{project_data['project_name'].iloc[0]}"

                )


            print("-" * 90)


            print(

                project_data[
                    available_completed_columns
                ]

                .to_string(
                    index=False
                )

            )


    else:

        print(
            "No projects reaching "
            "100% physical progress found."
        )


else:

    print(
        "Skipping 100% progress analysis."
    )


# ============================================================
# 20. PROJECT SUMMARY
# ============================================================

print_section("20. BUILDING PROJECT SUMMARY")


if "canonical_id" in df.columns:

    aggregation_dictionary = {}


    # --------------------------------------------------------
    # Project metadata
    # --------------------------------------------------------

    if "project_name" in df.columns:

        aggregation_dictionary[
            "project_name"
        ] = "first"


    if "state" in df.columns:

        aggregation_dictionary[
            "state"
        ] = "first"


    # --------------------------------------------------------
    # Reporting timeline
    # --------------------------------------------------------

    if "report_month" in df.columns:

        aggregation_dictionary[
            "report_month"
        ] = ["min", "max"]


    # --------------------------------------------------------
    # Physical progress
    # --------------------------------------------------------

    if "physical_progress" in df.columns:

        aggregation_dictionary[
            "physical_progress"
        ] = ["first", "last", "max"]


    # --------------------------------------------------------
    # Costs
    # --------------------------------------------------------

    if "original_cost" in df.columns:

        aggregation_dictionary[
            "original_cost"
        ] = ["first", "last"]


    if "revised_cost" in df.columns:

        aggregation_dictionary[
            "revised_cost"
        ] = ["first", "last"]


    # --------------------------------------------------------
    # Expenditure
    # --------------------------------------------------------

    if "cumulative_expenditure" in df.columns:

        aggregation_dictionary[
            "cumulative_expenditure"
        ] = ["first", "last", "max"]


    # --------------------------------------------------------
    # Build summary
    # --------------------------------------------------------

    if aggregation_dictionary:

        project_summary = (

            df.groupby(
                "canonical_id"
            )

            .agg(
                aggregation_dictionary
            )

        )


        # Flatten multi-level columns

        project_summary.columns = [

            "_".join(

                [
                    str(part)

                    for part in column

                    if part

                ]

            )

            for column in project_summary.columns

        ]


        project_summary = (

            project_summary
            .reset_index()

        )


        # --------------------------------------------
        # Add snapshot count
        # --------------------------------------------

        if snapshot_counts is not None:

            snapshot_dataframe = (

                snapshot_counts
                .reset_index()

            )


            project_summary = (

                project_summary
                .merge(

                    snapshot_dataframe,

                    on="canonical_id",

                    how="left"

                )

            )


        # --------------------------------------------
        # Add revision counts
        # --------------------------------------------

        if revision_counts is not None:

            revision_dataframe = (

                revision_counts
                .reset_index()

            )


            project_summary = (

                project_summary
                .merge(

                    revision_dataframe,

                    on="canonical_id",

                    how="left"

                )

            )


        # --------------------------------------------
        # Save summary
        # --------------------------------------------

        summary_path = (

            OUTPUT_DIR

            / "project_summary.csv"

        )


        project_summary.to_csv(

            summary_path,

            index=False

        )


        print(

            f"Project summary saved to:\n"
            f"{summary_path}"

        )


        print(

            f"\nSummary projects: "
            f"{len(project_summary):,}"

        )


    else:

        print(
            "No columns available for "
            "project summary."
        )


else:

    print(
        "Skipping project summary."
    )


# ============================================================
# 21. SAVE DATASET COLUMN REPORT
# ============================================================

print_section("21. SAVING DATASET COLUMN REPORT")


column_report = pd.DataFrame({

    "column_name":
        df.columns,

    "data_type":
        df.dtypes.astype(str).values,

    "missing_count":
        df.isna().sum().values,

    "missing_percentage":
        (
            df.isna()
            .mean()
            .mul(100)
            .values
        ),

})


column_report.to_csv(

    OUTPUT_DIR
    / "dataset_column_report.csv",

    index=False

)


print(

    "Saved: "
    "dataset_column_report.csv"

)


# ============================================================
# FINAL SUMMARY
# ============================================================

print_section("ANALYSIS COMPLETE")


print(
    "Dataset timeline analysis completed."
)


print(
    f"\nAnalysis outputs saved to:"
)


print(
    OUTPUT_DIR
)


print(
    "\nGenerated analysis files:"
)


for file in sorted(
    OUTPUT_DIR.glob("*.csv")
):

    print(
        f"  - {file.name}"
    )


print("\nDONE.")