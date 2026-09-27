import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

ML_SERVICE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    ML_SERVICE_DIR
    / "data"
    / "processed"
    / "master_project_dataset_clean.csv"
)

OUTPUT_DIR = (
    ML_SERVICE_DIR
    / "data"
    / "processed"
)

OUTPUT_PATH = (
    OUTPUT_DIR
    / "ml_project_timeline_features.csv"
)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


def months_between(date1, date2):
    """
    Calculate approximate difference in months between two dates.
    """

    return (
        (date2.dt.year - date1.dt.year) * 12
        + (date2.dt.month - date1.dt.month)
    )


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # 1. LOAD DATASET
    # ========================================================

    print_section("1. LOADING DATASET")

    print(f"ML SERVICE DIRECTORY:\n{ML_SERVICE_DIR}\n")
    print(f"DATASET PATH:\n{DATASET_PATH}\n")

    if not DATASET_PATH.exists():

        raise FileNotFoundError(
            f"Dataset not found:\n{DATASET_PATH}"
        )

    df = pd.read_csv(DATASET_PATH)

    print("Dataset loaded successfully.")

    print(f"\nTotal records: {len(df):,}")
    print(f"Total columns: {len(df.columns)}")


    # ========================================================
    # 2. REQUIRED COLUMN VALIDATION
    # ========================================================

    print_section("2. VALIDATING REQUIRED COLUMNS")

    required_columns = [

        "canonical_id",

        "project_name",
        "state",

        "report_month",

        "physical_progress",
        "cumulative_expenditure",

        "original_cost",
        "revised_cost",

        "original_approval_date",
        "revised_approval_date",

        "original_target_date",
        "revised_target_date"
    ]


    missing_columns = []

    for column in required_columns:

        if column not in df.columns:

            missing_columns.append(column)

            print(f"[MISSING] {column}")

        else:

            print(f"[FOUND]   {column}")


    if missing_columns:

        raise ValueError(
            f"\nMissing required columns:\n{missing_columns}"
        )


    print("\nAll required columns are available.")


    # ========================================================
    # 3. DATA TYPE PREPARATION
    # ========================================================

    print_section("3. PREPARING DATA TYPES")


    numeric_columns = [

        "physical_progress",
        "cumulative_expenditure",

        "original_cost",
        "revised_cost"
    ]


    for column in numeric_columns:

        print(f"Converting to numeric: {column}")

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    date_columns = [

        "report_month",

        "original_approval_date",
        "revised_approval_date",

        "original_target_date",
        "revised_target_date"
    ]


    for column in date_columns:

        print(f"Converting to datetime: {column}")

        df[column] = pd.to_datetime(
            df[column],
            errors="coerce"
        )


    # ========================================================
    # 4. SORT DATASET
    # ========================================================

    print_section("4. SORTING PROJECT TIMELINES")


    df = df.sort_values(

        by=[

            "canonical_id",
            "report_month"
        ]

    ).reset_index(drop=True)


    print(
        "Dataset sorted by canonical_id and report_month."
    )


    # ========================================================
    # 5. CREATE BASIC PROJECT TIMELINE FEATURES
    # ========================================================

    print_section(
        "5. CREATING BASIC TIMELINE FEATURES"
    )


    # Snapshot number

    df["snapshot_number"] = (

        df.groupby("canonical_id")

        .cumcount()

        + 1
    )


    # Previous report month

    df["previous_report_month"] = (

        df.groupby("canonical_id")

        ["report_month"]

        .shift(1)
    )


    # Timeline gap

    df["timeline_gap_months"] = (

        (df["report_month"].dt.year
         - df["previous_report_month"].dt.year)

        * 12

        +

        (df["report_month"].dt.month
         - df["previous_report_month"].dt.month)

    )


    # Flag irregular gaps

    df["irregular_timeline_gap_flag"] = (

        df["timeline_gap_months"] > 1

    ).astype(int)


    # First observation month

    df["first_observation_month"] = (

        df.groupby("canonical_id")

        ["report_month"]

        .transform("min")
    )


    # Months since first observation

    df["months_since_first_observation"] = (

        (df["report_month"].dt.year
         - df["first_observation_month"].dt.year)

        * 12

        +

        (df["report_month"].dt.month
         - df["first_observation_month"].dt.month)

    )


    print(
        "Basic timeline features created."
    )


    # ========================================================
    # 6. PHYSICAL PROGRESS FEATURES
    # ========================================================

    print_section(
        "6. CREATING PHYSICAL PROGRESS FEATURES"
    )


    # Previous progress

    df["previous_physical_progress"] = (

        df.groupby("canonical_id")

        ["physical_progress"]

        .shift(1)
    )


    # Progress change

    df["progress_change"] = (

        df["physical_progress"]

        -

        df["previous_physical_progress"]
    )


    # Progress decrease flag

    df["progress_decrease_flag"] = (

        df["progress_change"] < 0

    ).astype(int)


    # Large progress jump flag

    PROGRESS_JUMP_THRESHOLD = 20


    df["large_progress_jump_flag"] = (

        df["progress_change"]

        > PROGRESS_JUMP_THRESHOLD

    ).astype(int)


    # Progress change per month

    df["progress_rate_per_month"] = (

        df["progress_change"]

        /

        df["timeline_gap_months"]
    )


    # Replace infinite values

    df["progress_rate_per_month"] = (

        df["progress_rate_per_month"]

        .replace(

            [np.inf, -np.inf],

            np.nan
        )
    )


    # Overall average progress rate

    df["average_progress_rate"] = (

        df["physical_progress"]

        /

        df["months_since_first_observation"]

        .replace(0, np.nan)
    )


    print(
        "Physical progress features created."
    )


    # ========================================================
    # 7. CUMULATIVE EXPENDITURE FEATURES
    # ========================================================

    print_section(
        "7. CREATING EXPENDITURE FEATURES"
    )


    # Previous expenditure

    df["previous_cumulative_expenditure"] = (

        df.groupby("canonical_id")

        ["cumulative_expenditure"]

        .shift(1)
    )


    # Absolute expenditure change

    df["expenditure_change"] = (

        df["cumulative_expenditure"]

        -

        df["previous_cumulative_expenditure"]
    )


    # Expenditure decrease

    df["expenditure_decrease_flag"] = (

        df["expenditure_change"] < 0

    ).astype(int)


    # Expenditure percentage change

    df["expenditure_percent_change"] = (

        df["expenditure_change"]

        /

        df["previous_cumulative_expenditure"]

        .replace(0, np.nan)

        * 100
    )


    # Massive expenditure jump

    EXPENDITURE_JUMP_THRESHOLD = 200


    df["massive_expenditure_jump_flag"] = (

        df["expenditure_percent_change"]

        > EXPENDITURE_JUMP_THRESHOLD

    ).astype(int)


    print(
        "Expenditure features created."
    )


    # ========================================================
    # 8. COST FEATURES
    # ========================================================

    print_section(
        "8. CREATING COST FEATURES"
    )


    # Cost difference

    df["cost_difference"] = (

        df["revised_cost"]

        -

        df["original_cost"]
    )


    # Cost overrun percentage

    df["cost_overrun_percentage"] = (

        df["cost_difference"]

        /

        df["original_cost"]

        .replace(0, np.nan)

        * 100
    )


    # Cost ratio

    df["revised_to_original_cost_ratio"] = (

        df["revised_cost"]

        /

        df["original_cost"]

        .replace(0, np.nan)
    )


    # Previous original cost

    df["previous_original_cost"] = (

        df.groupby("canonical_id")

        ["original_cost"]

        .shift(1)
    )


    # Original cost change

    df["original_cost_change"] = (

        df["original_cost"]

        -

        df["previous_original_cost"]
    )


    # Original cost changed flag

    df["original_cost_change_flag"] = (

        df["original_cost_change"]

        .fillna(0)

        != 0

    ).astype(int)


    # Previous revised cost

    df["previous_revised_cost"] = (

        df.groupby("canonical_id")

        ["revised_cost"]

        .shift(1)
    )


    # Revised cost change

    df["revised_cost_change"] = (

        df["revised_cost"]

        -

        df["previous_revised_cost"]
    )


    # Revised cost change flag

    df["revised_cost_change_flag"] = (

        df["revised_cost_change"]

        .fillna(0)

        != 0

    ).astype(int)


    print(
        "Cost features created."
    )


    # ========================================================
    # 9. EXPENDITURE RATIO FEATURES
    # ========================================================

    print_section(
        "9. CREATING EXPENDITURE RATIO FEATURES"
    )


    # Expenditure vs original cost

    df["expenditure_to_original_cost_ratio"] = (

        df["cumulative_expenditure"]

        /

        df["original_cost"]

        .replace(0, np.nan)
    )


    # Expenditure vs revised cost

    df["expenditure_to_revised_cost_ratio"] = (

        df["cumulative_expenditure"]

        /

        df["revised_cost"]

        .replace(0, np.nan)
    )


    # Expenditure percentage

    df["expenditure_percentage"] = (

        df["expenditure_to_revised_cost_ratio"]

        * 100
    )


    # Spending ahead of progress

    df["expenditure_progress_gap"] = (

        df["expenditure_percentage"]

        -

        df["physical_progress"]
    )


    print(
        "Expenditure ratio features created."
    )


    # ========================================================
    # 10. APPROVAL DATE FEATURES
    # ========================================================

    print_section(
        "10. CREATING APPROVAL DATE FEATURES"
    )


    # Effective approval date:
    #
    # Prefer revised approval date
    # Otherwise use original approval date


    df["effective_approval_date"] = (

        df["revised_approval_date"]

        .combine_first(

            df["original_approval_date"]
        )
    )


    # Project age

    df["project_age_months"] = (

        (df["report_month"].dt.year
         - df["effective_approval_date"].dt.year)

        * 12

        +

        (df["report_month"].dt.month
         - df["effective_approval_date"].dt.month)

    )


    # Flag missing approval date

    df["missing_approval_date_flag"] = (

        df["effective_approval_date"]

        .isna()

    ).astype(int)


    print(
        "Approval date features created."
    )


    # ========================================================
    # 11. TARGET DATE FEATURES
    # ========================================================

    print_section(
        "11. CREATING SCHEDULE FEATURES"
    )


    # Effective target date:
    #
    # Prefer revised target date.
    # Otherwise use original target date.


    df["effective_target_date"] = (

        df["revised_target_date"]

        .combine_first(

            df["original_target_date"]
        )
    )


    # Months until target

    df["months_until_target"] = (

        (df["effective_target_date"].dt.year
         - df["report_month"].dt.year)

        * 12

        +

        (df["effective_target_date"].dt.month
         - df["report_month"].dt.month)

    )


    # Project is past target

    df["past_target_date_flag"] = (

        df["months_until_target"] < 0

    ).astype(int)


    # Target date missing

    df["missing_target_date_flag"] = (

        df["effective_target_date"]

        .isna()

    ).astype(int)


    # ========================================================
    # ORIGINAL VS REVISED TARGET DATE
    # ========================================================


    df["schedule_extension_months"] = (

        (df["revised_target_date"].dt.year
         - df["original_target_date"].dt.year)

        * 12

        +

        (df["revised_target_date"].dt.month
         - df["original_target_date"].dt.month)

    )


    # Schedule extension flag

    df["schedule_extension_flag"] = (

        df["schedule_extension_months"] > 0

    ).astype(int)


    # Schedule revision available

    df["schedule_revision_available_flag"] = (

        df["revised_target_date"]

        .notna()

    ).astype(int)


    print(
        "Schedule features created."
    )


    # ========================================================
    # 12. COMPLETION FEATURES
    # ========================================================

    print_section(
        "12. CREATING COMPLETION FEATURES"
    )


    # Completed project flag

    df["completed_flag"] = (

        df["physical_progress"] >= 100

    ).astype(int)


    # Previous completion status

    df["previous_completed_flag"] = (

        df.groupby("canonical_id")

        ["completed_flag"]

        .shift(1)

        .fillna(0)
    )


    # Completed then dropped

    df["completed_then_progress_decreased_flag"] = (

        (

            (df["previous_physical_progress"] >= 100)

            &

            (df["physical_progress"] < 100)

        )

    ).astype(int)


    print(
        "Completion features created."
    )


    # ========================================================
    # 13. DATA QUALITY / ANOMALY SCORE
    # ========================================================

    print_section(
        "13. CREATING ANOMALY FEATURES"
    )


    # Negative expenditure

    df["negative_expenditure_flag"] = (

        df["cumulative_expenditure"] < 0

    ).astype(int)


    # Progress out of valid range

    df["invalid_progress_flag"] = (

        (

            df["physical_progress"] < 0

        )

        |

        (

            df["physical_progress"] > 100

        )

    ).astype(int)


    # Missing key values

    df["missing_progress_flag"] = (

        df["physical_progress"]

        .isna()

    ).astype(int)


    df["missing_expenditure_flag"] = (

        df["cumulative_expenditure"]

        .isna()

    ).astype(int)


    # ========================================================
    # ANOMALY SCORE
    # ========================================================
    #
    # This is NOT an ML target.
    #
    # It is a data quality feature.
    #
    # The model can learn whether unstable
    # project reporting correlates with risk.
    #
    # ========================================================


    anomaly_columns = [

        "progress_decrease_flag",

        "large_progress_jump_flag",

        "expenditure_decrease_flag",

        "massive_expenditure_jump_flag",

        "original_cost_change_flag",

        "revised_cost_change_flag",

        "irregular_timeline_gap_flag",

        "completed_then_progress_decreased_flag",

        "negative_expenditure_flag",

        "invalid_progress_flag"
    ]


    df["anomaly_score"] = (

        df[anomaly_columns]

        .sum(axis=1)
    )


    print(
        "Anomaly features created."
    )


    # ========================================================
    # 14. PROJECT-LEVEL CUMULATIVE FEATURES
    # ========================================================

    print_section(
        "14. CREATING CUMULATIVE PROJECT FEATURES"
    )


    # Number of progress decreases
    # seen so far for each project


    df["cumulative_progress_decreases"] = (

        df.groupby("canonical_id")

        ["progress_decrease_flag"]

        .cumsum()
    )


    # Number of expenditure decreases
    # seen so far


    df["cumulative_expenditure_decreases"] = (

        df.groupby("canonical_id")

        ["expenditure_decrease_flag"]

        .cumsum()
    )


    # Number of cost revisions


    df["cumulative_cost_revisions"] = (

        df.groupby("canonical_id")

        ["revised_cost_change_flag"]

        .cumsum()
    )


    # Number of schedule extensions


    df["cumulative_schedule_extension_records"] = (

        df.groupby("canonical_id")

        ["schedule_extension_flag"]

        .cumsum()
    )


    # Cumulative anomaly count


    df["cumulative_anomaly_score"] = (

        df.groupby("canonical_id")

        ["anomaly_score"]

        .cumsum()
    )


    print(
        "Cumulative project features created."
    )


    # ========================================================
    # 15. SAFE VALUE CLEANING
    # ========================================================

    print_section(
        "15. CLEANING INFINITE VALUES"
    )


    numeric_columns = (

        df

        .select_dtypes(

            include=[np.number]
        )

        .columns
    )


    df[numeric_columns] = (

        df[numeric_columns]

        .replace(

            [np.inf, -np.inf],

            np.nan
        )
    )


    print(
        "Infinite values replaced with NaN."
    )


    # ========================================================
    # 16. DATASET OVERVIEW
    # ========================================================

    print_section(
        "16. FEATURE DATASET OVERVIEW"
    )


    print(

        f"Total records: {len(df):,}"

    )


    print(

        f"Unique projects: "
        f"{df['canonical_id'].nunique():,}"

    )


    print(

        f"Total columns: "
        f"{len(df.columns)}"

    )


    print("\nNew ML features include:")


    feature_columns = [

        "snapshot_number",

        "timeline_gap_months",

        "months_since_first_observation",

        "previous_physical_progress",

        "progress_change",

        "progress_decrease_flag",

        "large_progress_jump_flag",

        "progress_rate_per_month",

        "average_progress_rate",

        "previous_cumulative_expenditure",

        "expenditure_change",

        "expenditure_percent_change",

        "expenditure_decrease_flag",

        "massive_expenditure_jump_flag",

        "cost_difference",

        "cost_overrun_percentage",

        "revised_to_original_cost_ratio",

        "original_cost_change",

        "revised_cost_change",

        "expenditure_to_original_cost_ratio",

        "expenditure_to_revised_cost_ratio",

        "expenditure_percentage",

        "expenditure_progress_gap",

        "project_age_months",

        "months_until_target",

        "past_target_date_flag",

        "schedule_extension_months",

        "schedule_extension_flag",

        "completed_flag",

        "anomaly_score",

        "cumulative_anomaly_score"
    ]


    for column in feature_columns:

        print(f"  - {column}")


    # ========================================================
    # 17. SAVE FEATURE DATASET
    # ========================================================

    print_section(
        "17. SAVING ML FEATURE DATASET"
    )


    OUTPUT_DIR.mkdir(

        parents=True,

        exist_ok=True
    )


    df.to_csv(

        OUTPUT_PATH,

        index=False
    )


    print(

        f"ML feature dataset saved successfully:\n"
        f"{OUTPUT_PATH}"
    )


    # ========================================================
    # 18. CREATE FEATURE REPORT
    # ========================================================

    print_section(
        "18. CREATING FEATURE REPORT"
    )


    report_rows = []


    for column in df.columns:


        report_rows.append({

            "column": column,

            "data_type": str(df[column].dtype),

            "missing_count": int(

                df[column]

                .isna()

                .sum()
            ),

            "missing_percentage": round(

                df[column]

                .isna()

                .mean()

                * 100,

                2
            )

        })


    feature_report = pd.DataFrame(

        report_rows
    )


    feature_report_path = (

        OUTPUT_DIR

        / "ml_feature_report.csv"
    )


    feature_report.to_csv(

        feature_report_path,

        index=False
    )


    print(

        f"Feature report saved:\n"
        f"{feature_report_path}"
    )


    # ========================================================
    # COMPLETE
    # ========================================================

    print_section(
        "ML FEATURE ENGINEERING COMPLETE"
    )


    print(
        "Generated files:"
    )


    print(
        f"\n1. {OUTPUT_PATH.name}"
    )


    print(
        f"2. {feature_report_path.name}"
    )


    print(
        "\nREADY FOR MACHINE LEARNING."
    )


if __name__ == "__main__":

    main()