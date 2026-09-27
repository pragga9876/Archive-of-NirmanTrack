import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# PATH CONFIGURATION
# ============================================================

ML_SERVICE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    ML_SERVICE_DIR
    / "data"
    / "processed"
    / "ml_project_timeline_features.csv"
)

OUTPUT_DIR = (
    ML_SERVICE_DIR
    / "data"
    / "model_datasets"
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "time_series_progress_dataset.csv"
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


# ============================================================
# MAIN
# ============================================================

def main():

    # ========================================================
    # 1. LOADING DATASET
    # ========================================================

    print_section("1. LOADING TIME SERIES FEATURE DATASET")

    print("\nML SERVICE DIRECTORY:")
    print(ML_SERVICE_DIR)

    print("\nINPUT FILE:")
    print(INPUT_FILE)

    print("\nOUTPUT DIRECTORY:")
    print(OUTPUT_DIR)

    if not INPUT_FILE.exists():

        print("\nERROR: Input dataset not found.")

        print("\nExpected:")
        print(INPUT_FILE)

        sys.exit(1)


    df = pd.read_csv(INPUT_FILE)

    print("\nDataset loaded successfully.")

    print(f"\nTotal records: {len(df):,}")
    print(f"Total columns: {len(df.columns):,}")


    # ========================================================
    # 2. VALIDATING REQUIRED COLUMNS
    # ========================================================

    print_section("2. VALIDATING REQUIRED COLUMNS")

    required_columns = [

        "canonical_id",

        "report_month",

        "physical_progress",

        "cumulative_expenditure",

        "original_cost",

        "revised_cost"

    ]


    missing_columns = []


    for column in required_columns:

        if column in df.columns:

            print(f"[FOUND]   {column}")

        else:

            print(f"[MISSING] {column}")

            missing_columns.append(column)


    if missing_columns:

        print("\nERROR: Required columns missing.")

        sys.exit(1)


    print("\nAll required columns found.")


    # ========================================================
    # 3. DATA TYPE PREPARATION
    # ========================================================

    print_section("3. PREPARING DATA TYPES")


    print("Converting report_month to datetime...")


    df["report_month"] = pd.to_datetime(
        df["report_month"],
        errors="coerce"
    )


    numeric_columns = [

        "physical_progress",

        "cumulative_expenditure",

        "original_cost",

        "revised_cost"

    ]


    for column in numeric_columns:

        print(f"Converting {column} to numeric...")

        df[column] = pd.to_numeric(
            df[column],
            errors="coerce"
        )


    # ========================================================
    # 4. REMOVING INVALID RECORDS
    # ========================================================

    print_section("4. REMOVING INVALID TIME SERIES RECORDS")


    initial_records = len(df)


    df = df.dropna(

        subset=[

            "canonical_id",

            "report_month",

            "physical_progress"

        ]

    )


    removed_records = initial_records - len(df)


    print(f"\nRecords removed: {removed_records:,}")

    print(f"Records remaining: {len(df):,}")


    # ========================================================
    # 5. SORTING PROJECT TIMELINES
    # ========================================================

    print_section("5. SORTING PROJECT TIMELINES")


    df = df.sort_values(

        by=[

            "canonical_id",

            "report_month"

        ]

    ).reset_index(drop=True)


    print("\nDataset sorted by:")

    print("  1. canonical_id")

    print("  2. report_month")


    # ========================================================
    # 6. CHECKING DUPLICATES
    # ========================================================

    print_section("6. CHECKING PROJECT-MONTH DUPLICATES")


    duplicate_count = df.duplicated(

        subset=[

            "canonical_id",

            "report_month"

        ]

    ).sum()


    print(f"\nDuplicate project-month records: {duplicate_count:,}")


    if duplicate_count > 0:

        print("\nRemoving duplicate records...")

        df = df.drop_duplicates(

            subset=[

                "canonical_id",

                "report_month"

            ],

            keep="last"

        )


    # ========================================================
    # 7. CREATING NEXT SNAPSHOT TARGET
    # ========================================================

    print_section("7. CREATING NEXT SNAPSHOT FORECASTING TARGET")


    grouped = df.groupby("canonical_id")


    # --------------------------------------------------------
    # NEXT PHYSICAL PROGRESS
    # --------------------------------------------------------

    df["next_physical_progress"] = (

        grouped["physical_progress"]

        .shift(-1)

    )


    # --------------------------------------------------------
    # NEXT REPORT MONTH
    # --------------------------------------------------------

    df["next_report_month"] = (

        grouped["report_month"]

        .shift(-1)

    )


    # --------------------------------------------------------
    # TIME UNTIL NEXT OBSERVATION
    # --------------------------------------------------------

    df["months_to_next_snapshot"] = (

        (

            df["next_report_month"]

            -

            df["report_month"]

        )

        .dt.days

        /

        30.44

    )


    print("\nNext snapshot targets created.")


    # ========================================================
    # 8. CREATING TIME SERIES LAG FEATURES
    # ========================================================

    print_section("8. CREATING TIME SERIES LAG FEATURES")


    # --------------------------------------------------------
    # PROGRESS LAG
    # --------------------------------------------------------

    if "previous_physical_progress" not in df.columns:

        df["previous_physical_progress"] = (

            grouped["physical_progress"]

            .shift(1)

        )


    # --------------------------------------------------------
    # EXPENDITURE LAG
    # --------------------------------------------------------

    if "previous_cumulative_expenditure" not in df.columns:

        df["previous_cumulative_expenditure"] = (

            grouped["cumulative_expenditure"]

            .shift(1)

        )


    print("\nLag features available.")


    # ========================================================
    # 9. CREATING NEXT PROGRESS CHANGE TARGET
    # ========================================================

    print_section("9. CREATING PROGRESS CHANGE TARGET")


    df["next_progress_change"] = (

        df["next_physical_progress"]

        -

        df["physical_progress"]

    )


    print("\nCreated:")

    print("  - next_progress_change")


    # ========================================================
    # 10. CREATING PROJECT HISTORY FEATURES
    # ========================================================

    print_section("10. CREATING PROJECT HISTORY FEATURES")


    # --------------------------------------------------------
    # NUMBER OF OBSERVATIONS SO FAR
    # --------------------------------------------------------

    df["observations_so_far"] = (

        grouped

        .cumcount()

        +

        1

    )


    # --------------------------------------------------------
    # MAXIMUM PROGRESS SO FAR
    # --------------------------------------------------------

    df["max_progress_so_far"] = (

        grouped["physical_progress"]

        .cummax()

    )


    # --------------------------------------------------------
    # EXPENDITURE MAX SO FAR
    # --------------------------------------------------------

    df["max_expenditure_so_far"] = (

        grouped["cumulative_expenditure"]

        .cummax()

    )


    # --------------------------------------------------------
    # PROJECT INITIAL PROGRESS
    # --------------------------------------------------------

    df["initial_progress"] = (

        grouped["physical_progress"]

        .transform("first")

    )


    print("\nHistorical features created.")


    # ========================================================
    # 11. FILTERING RECORDS WITH FUTURE TARGET
    # ========================================================

    print_section("11. FILTERING FORECASTABLE RECORDS")


    initial_records = len(df)


    forecasting_df = df.dropna(

        subset=[

            "next_physical_progress",

            "next_report_month"

        ]

    ).copy()


    removed_records = (

        initial_records

        -

        len(forecasting_df)

    )


    print(

        f"\nRecords without future observations removed: "

        f"{removed_records:,}"

    )


    print(

        f"Forecasting records remaining: "

        f"{len(forecasting_df):,}"

    )


    # ========================================================
    # 12. DEFINING FORECASTING FEATURES
    # ========================================================

    print_section("12. DEFINING TIME SERIES FORECASTING FEATURES")


    candidate_features = [

        # ----------------------------------------------------
        # TIME FEATURES
        # ----------------------------------------------------

        "snapshot_number",

        "timeline_gap_months",

        "months_since_first_observation",

        "project_age_months",

        "observations_so_far",

        "months_to_next_snapshot",


        # ----------------------------------------------------
        # PROGRESS FEATURES
        # ----------------------------------------------------

        "physical_progress",

        "previous_physical_progress",

        "progress_change",

        "progress_rate_per_month",

        "average_progress_rate",

        "max_progress_so_far",

        "initial_progress",


        # ----------------------------------------------------
        # EXPENDITURE FEATURES
        # ----------------------------------------------------

        "cumulative_expenditure",

        "previous_cumulative_expenditure",

        "expenditure_change",

        "expenditure_percent_change",

        "max_expenditure_so_far",


        # ----------------------------------------------------
        # COST FEATURES
        # ----------------------------------------------------

        "original_cost",

        "revised_cost",

        "cost_difference",

        "cost_overrun_percentage",

        "revised_to_original_cost_ratio",


        # ----------------------------------------------------
        # EXPENDITURE RATIO FEATURES
        # ----------------------------------------------------

        "expenditure_to_original_cost_ratio",

        "expenditure_to_revised_cost_ratio",

        "expenditure_percentage",

        "expenditure_progress_gap",


        # ----------------------------------------------------
        # SCHEDULE FEATURES
        # ----------------------------------------------------

        "months_until_target",

        "past_target_date_flag",

        "schedule_extension_months",

        "schedule_extension_flag",


        # ----------------------------------------------------
        # PROJECT STATE
        # ----------------------------------------------------

        "completed_flag",


        # ----------------------------------------------------
        # ANOMALY FEATURES
        # ----------------------------------------------------

        "anomaly_score",

        "cumulative_anomaly_score"

    ]


    available_features = []


    for feature in candidate_features:

        if feature in forecasting_df.columns:

            available_features.append(feature)

            print(f"[FOUND]   {feature}")

        else:

            print(f"[SKIPPED] {feature}")


    print(

        f"\nAvailable forecasting features: "

        f"{len(available_features)}"

    )


    # ========================================================
    # 13. SELECTING OUTPUT COLUMNS
    # ========================================================

    print_section("13. BUILDING FINAL TIME SERIES DATASET")


    identifier_columns = [

        "canonical_id",

        "report_month",

        "next_report_month"

    ]


    target_columns = [

        "next_physical_progress",

        "next_progress_change"

    ]


    final_columns = (

        identifier_columns

        +

        available_features

        +

        target_columns

    )


    forecasting_df = (

        forecasting_df[final_columns]

        .copy()

    )


    print(

        f"\nFinal dataset records: "

        f"{len(forecasting_df):,}"

    )


    print(

        f"Final dataset columns: "

        f"{len(forecasting_df.columns):,}"

    )


    print(

        f"Unique projects: "

        f"{forecasting_df['canonical_id'].nunique():,}"

    )


    # ========================================================
    # 14. CHECKING TARGET STATISTICS
    # ========================================================

    print_section("14. FORECAST TARGET ANALYSIS")


    print("\nNEXT PHYSICAL PROGRESS:")

    print(

        forecasting_df[

            "next_physical_progress"

        ].describe()

    )


    print("\nNEXT PROGRESS CHANGE:")

    print(

        forecasting_df[

            "next_progress_change"

        ].describe()

    )


    # ========================================================
    # 15. TIME RANGE ANALYSIS
    # ========================================================

    print_section("15. TIME RANGE ANALYSIS")


    print(

        "\nCurrent snapshot range:"

    )


    print(

        forecasting_df[

            "report_month"

        ].min()

    )


    print("to")


    print(

        forecasting_df[

            "report_month"

        ].max()

    )


    print(

        "\nFuture target range:"

    )


    print(

        forecasting_df[

            "next_report_month"

        ].min()

    )


    print("to")


    print(

        forecasting_df[

            "next_report_month"

        ].max()

    )


    # ========================================================
    # 16. MISSING VALUE ANALYSIS
    # ========================================================

    print_section("16. MISSING VALUE ANALYSIS")


    missing_summary = (

        forecasting_df

        .isna()

        .sum()

        .reset_index()

    )


    missing_summary.columns = [

        "column",

        "missing_values"

    ]


    missing_summary[

        "missing_percentage"

    ] = (

        missing_summary[

            "missing_values"

        ]

        /

        len(forecasting_df)

        *

        100

    )


    missing_summary = (

        missing_summary

        .sort_values(

            "missing_values",

            ascending=False

        )

    )


    print("\nTop missing value columns:")


    print(

        missing_summary

        .head(15)

        .to_string(index=False)

    )


    # ========================================================
    # 17. SAVING DATASET
    # ========================================================

    print_section("17. SAVING TIME SERIES FORECASTING DATASET")


    OUTPUT_DIR.mkdir(

        parents=True,

        exist_ok=True

    )


    forecasting_df.to_csv(

        OUTPUT_FILE,

        index=False

    )


    print("\nDataset saved successfully:")

    print(OUTPUT_FILE)


    # ========================================================
    # 18. SAVING FEATURE LIST
    # ========================================================

    print_section("18. SAVING TIME SERIES FEATURE LIST")


    feature_file = (

        OUTPUT_DIR

        /

        "time_series_forecasting_features.csv"

    )


    feature_df = pd.DataFrame({

        "feature":

            available_features

    })


    feature_df.to_csv(

        feature_file,

        index=False

    )


    print("\nFeature list saved:")

    print(feature_file)


    # ========================================================
    # 19. SAVING DATASET REPORT
    # ========================================================

    print_section("19. CREATING TIME SERIES DATASET REPORT")


    report_data = [

        {

            "dataset":

                "time_series_progress_forecasting",

            "records":

                len(forecasting_df),

            "projects":

                forecasting_df[

                    "canonical_id"

                ].nunique(),

            "features":

                len(available_features),

            "target":

                "next_physical_progress",

            "target_type":

                "time_series_regression"

        }

    ]


    report_df = pd.DataFrame(

        report_data

    )


    print("\n")

    print(

        report_df

        .to_string(

            index=False

        )

    )


    report_file = (

        OUTPUT_DIR

        /

        "time_series_dataset_report.csv"

    )


    report_df.to_csv(

        report_file,

        index=False

    )


    print("\nReport saved:")

    print(report_file)


    # ========================================================
    # COMPLETE
    # ========================================================

    print_section(

        "TIME SERIES DATASET PREPARATION COMPLETE"

    )


    print(

        "\nGenerated files:"

    )


    print(

        "\n1. Time Series Forecasting Dataset"

    )


    print(OUTPUT_FILE)


    print(

        "\n2. Time Series Feature List"

    )


    print(feature_file)


    print(

        "\n3. Time Series Dataset Report"

    )


    print(report_file)


    print(

        "\nREADY FOR TIME-AWARE MODEL TRAINING."

    )


if __name__ == "__main__":

    main()