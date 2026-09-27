import numpy as np
import pandas as pd
from pathlib import Path


# ============================================================
# CONFIGURATION
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
    / "model_datasets"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_section(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


def safe_numeric(series):
    """
    Safely convert a pandas Series to numeric.
    Invalid values become NaN.
    """

    return pd.to_numeric(series, errors="coerce")


# ============================================================
# 1. LOAD FEATURE DATASET
# ============================================================

print_section("1. LOADING ML FEATURE DATASET")

print(f"ML SERVICE DIRECTORY:\n{BASE_DIR}")
print(f"\nINPUT FILE:\n{INPUT_FILE}")
print(f"\nOUTPUT DIRECTORY:\n{OUTPUT_DIR}")

if not INPUT_FILE.exists():

    raise FileNotFoundError(
        f"\nFeature dataset not found:\n{INPUT_FILE}\n\n"
        "Run prepare_ml_features.py first."
    )


df = pd.read_csv(INPUT_FILE)

print("\nML feature dataset loaded successfully.")

print(f"\nTotal records: {len(df):,}")
print(f"Total columns: {len(df.columns):,}")


# ============================================================
# 2. VALIDATE REQUIRED COLUMNS
# ============================================================

print_section("2. VALIDATING REQUIRED COLUMNS")


required_columns = [

    "canonical_id",

    "report_month",

    "physical_progress",

    "cumulative_expenditure",

    "original_cost",

    "revised_cost",

    "original_target_date",

    "revised_target_date",

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
        "\nRequired columns are missing:\n"
        + "\n".join(missing_columns)
    )


print("\nAll required columns found.")


# ============================================================
# 3. PREPARE DATA TYPES
# ============================================================

print_section("3. PREPARING DATA TYPES")


numeric_columns = [

    "physical_progress",

    "cumulative_expenditure",

    "original_cost",

    "revised_cost",

]


for column in numeric_columns:

    print(f"Converting to numeric: {column}")

    df[column] = safe_numeric(df[column])


date_columns = [

    "report_month",

    "original_target_date",

    "revised_target_date",

]


for column in date_columns:

    print(f"Converting to datetime: {column}")

    df[column] = pd.to_datetime(
        df[column],
        errors="coerce"
    )


# ============================================================
# 4. SORT PROJECT TIMELINES
# ============================================================

print_section("4. SORTING PROJECT TIMELINES")


df = df.sort_values(

    by=[

        "canonical_id",

        "report_month",

    ]

).reset_index(drop=True)


print("Dataset sorted by canonical_id and report_month.")


print(f"\nUnique projects: {df['canonical_id'].nunique():,}")

print(
    f"Reporting months: "
    f"{df['report_month'].nunique():,}"
)


# ============================================================
# 5. CREATE EFFECTIVE TARGET DATE
# ============================================================

print_section("5. CREATING EFFECTIVE TARGET DATE")


# If a revised target date exists,
# it is more relevant than the original target date.

df["effective_target_date"] = (

    df["revised_target_date"]

    .combine_first(

        df["original_target_date"]

    )

)


missing_effective_target = (

    df["effective_target_date"]

    .isna()

    .sum()

)


print(
    "Records without an effective target date: "
    f"{missing_effective_target:,}"
)


# ============================================================
# 6. CREATE CURRENT DELAY LABEL
# ============================================================

print_section("6. CREATING DELAY LABEL")


# A project is considered currently delayed when:
#
# 1. The reporting month is after the effective target date
#
# AND
#
# 2. Physical progress is less than 100%
#
# This represents an observable project status.

df["current_delay_label"] = np.where(

    (

        df["report_month"]

        > df["effective_target_date"]

    )

    &

    (

        df["physical_progress"]

        < 100

    ),

    1,

    0

)


# Records without a valid target date should not
# automatically be considered "not delayed".

df.loc[

    df["effective_target_date"].isna(),

    "current_delay_label"

] = np.nan


print(
    "Delayed records: "
    f"{int(df['current_delay_label'].sum()):,}"
)


print(
    "Non-delayed records: "
    f"{int((df['current_delay_label'] == 0).sum()):,}"
)


print(
    "Records without delay label: "
    f"{int(df['current_delay_label'].isna().sum()):,}"
)


# ============================================================
# 7. CREATE FUTURE SNAPSHOT FEATURES
# ============================================================

print_section("7. CREATING FUTURE SNAPSHOT TARGETS")


project_groups = (

    df.groupby(

        "canonical_id",

        group_keys=False

    )

)


# ------------------------------------------------------------
# NEXT PHYSICAL PROGRESS
# ------------------------------------------------------------

df["next_physical_progress"] = (

    project_groups["physical_progress"]

    .shift(-1)

)


# ------------------------------------------------------------
# NEXT REPORT MONTH
# ------------------------------------------------------------

df["next_report_month"] = (

    project_groups["report_month"]

    .shift(-1)

)


# ------------------------------------------------------------
# NEXT PROGRESS CHANGE
# ------------------------------------------------------------

df["next_progress_change"] = (

    df["next_physical_progress"]

    -

    df["physical_progress"]

)


# ------------------------------------------------------------
# NEXT CUMULATIVE EXPENDITURE
# ------------------------------------------------------------

df["next_cumulative_expenditure"] = (

    project_groups["cumulative_expenditure"]

    .shift(-1)

)


# ------------------------------------------------------------
# NEXT EXPENDITURE CHANGE
# ------------------------------------------------------------

df["next_expenditure_change"] = (

    df["next_cumulative_expenditure"]

    -

    df["cumulative_expenditure"]

)


print(
    "Records with future progress target: "
    f"{df['next_physical_progress'].notna().sum():,}"
)


# ============================================================
# 8. CREATE FUTURE DELAY PREDICTION TARGET
# ============================================================

print_section("8. CREATING FUTURE DELAY TARGET")


# We predict whether the project will be delayed
# at its NEXT AVAILABLE OBSERVATION.
#
# Future information is used ONLY to create
# the target label.
#
# It will NOT be included as an input feature.


df["future_delay_label"] = np.nan


valid_future_target = (

    df["next_report_month"].notna()

    &

    df["effective_target_date"].notna()

    &

    df["next_physical_progress"].notna()

)


df.loc[

    valid_future_target,

    "future_delay_label"

] = np.where(

    (

        df.loc[
            valid_future_target,
            "next_report_month"
        ]

        >

        df.loc[
            valid_future_target,
            "effective_target_date"
        ]

    )

    &

    (

        df.loc[
            valid_future_target,
            "next_physical_progress"
        ]

        < 100

    ),

    1,

    0

)


print(
    "Records with future delay target: "
    f"{df['future_delay_label'].notna().sum():,}"
)


print(
    "Future delayed records: "
    f"{int((df['future_delay_label'] == 1).sum()):,}"
)


print(
    "Future non-delayed records: "
    f"{int((df['future_delay_label'] == 0).sum()):,}"
)


# ============================================================
# 9. CREATE RISK SCORE
# ============================================================

print_section("9. CREATING PROJECT RISK SCORE")


# ------------------------------------------------------------
# RISK COMPONENT 1
# PROJECT HAS PASSED TARGET DATE
# ------------------------------------------------------------

df["risk_past_target"] = np.where(

    (

        df["effective_target_date"].notna()

    )

    &

    (

        df["report_month"]

        >

        df["effective_target_date"]

    )

    &

    (

        df["physical_progress"]

        < 100

    ),

    1,

    0

)


# ------------------------------------------------------------
# RISK COMPONENT 2
# PROGRESS DECREASE
# ------------------------------------------------------------

if "progress_decrease_flag" in df.columns:

    df["risk_progress_decrease"] = (

        df["progress_decrease_flag"]

        .fillna(0)

    )

else:

    df["risk_progress_decrease"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 3
# NO RECENT PROGRESS
# ------------------------------------------------------------

if "progress_change" in df.columns:

    df["risk_no_progress"] = np.where(

        (

            df["progress_change"]

            <= 0

        )

        &

        (

            df["physical_progress"]

            < 100

        ),

        1,

        0

    )

else:

    df["risk_no_progress"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 4
# SLOW PROJECT PROGRESS
# ------------------------------------------------------------

df["risk_low_progress"] = np.where(

    df["physical_progress"] < 25,

    1,

    0

)


# ------------------------------------------------------------
# RISK COMPONENT 5
# LARGE PROGRESS JUMP
# ------------------------------------------------------------

if "large_progress_jump_flag" in df.columns:

    df["risk_large_progress_jump"] = (

        df["large_progress_jump_flag"]

        .fillna(0)

    )

else:

    df["risk_large_progress_jump"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 6
# EXPENDITURE DECREASE
# ------------------------------------------------------------

if "expenditure_decrease_flag" in df.columns:

    df["risk_expenditure_decrease"] = (

        df["expenditure_decrease_flag"]

        .fillna(0)

    )

else:

    df["risk_expenditure_decrease"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 7
# SCHEDULE EXTENSION
# ------------------------------------------------------------

if "schedule_extension_flag" in df.columns:

    df["risk_schedule_extension"] = (

        df["schedule_extension_flag"]

        .fillna(0)

    )

else:

    df["risk_schedule_extension"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 8
# HIGH COST OVERRUN
# ------------------------------------------------------------

if "cost_overrun_percentage" in df.columns:

    df["risk_high_cost_overrun"] = np.where(

        df["cost_overrun_percentage"]

        >= 25,

        1,

        0

    )

else:

    df["risk_high_cost_overrun"] = 0


# ------------------------------------------------------------
# RISK COMPONENT 9
# EXPENDITURE / PROGRESS MISMATCH
# ------------------------------------------------------------

if "expenditure_progress_gap" in df.columns:

    df["risk_expenditure_progress_gap"] = np.where(

        df["expenditure_progress_gap"]

        >= 25,

        1,

        0

    )

else:

    df["risk_expenditure_progress_gap"] = 0


# ============================================================
# 10. CALCULATE RISK SCORE
# ============================================================

print_section("10. CALCULATING RISK SCORE")


# Weighted risk score.
#
# Higher weights are assigned to stronger
# project risk signals.


df["risk_score"] = (

    df["risk_past_target"] * 3

    +

    df["risk_progress_decrease"] * 2

    +

    df["risk_no_progress"] * 2

    +

    df["risk_low_progress"] * 1

    +

    df["risk_large_progress_jump"] * 1

    +

    df["risk_expenditure_decrease"] * 1

    +

    df["risk_schedule_extension"] * 2

    +

    df["risk_high_cost_overrun"] * 2

    +

    df["risk_expenditure_progress_gap"] * 2

)


print(
    "Minimum risk score: "
    f"{df['risk_score'].min():.0f}"
)


print(
    "Maximum risk score: "
    f"{df['risk_score'].max():.0f}"
)


print(
    "Average risk score: "
    f"{df['risk_score'].mean():.2f}"
)


# ============================================================
# 11. CREATE RISK CLASSIFICATION LABEL
# ============================================================

print_section("11. CREATING RISK CLASSIFICATION LABEL")


# Risk classification:
#
# 0 - 2  -> LOW
#
# 3 - 5  -> MEDIUM
#
# 6+     -> HIGH


def classify_risk(score):

    if score <= 2:

        return "LOW"

    elif score <= 5:

        return "MEDIUM"

    else:

        return "HIGH"


df["risk_label"] = (

    df["risk_score"]

    .apply(classify_risk)

)


print("\nRisk distribution:")

print(

    df["risk_label"]

    .value_counts()

)


# ============================================================
# 12. DEFINE COMMON INPUT FEATURES
# ============================================================

print_section("12. DEFINING MODEL INPUT FEATURES")


# These are features available at the CURRENT snapshot.
#
# Future columns and target columns are NOT included.


candidate_features = [

    # --------------------------------------------------------
    # PROJECT TIMELINE
    # --------------------------------------------------------

    "snapshot_number",

    "timeline_gap_months",

    "months_since_first_observation",

    "project_age_months",


    # --------------------------------------------------------
    # PHYSICAL PROGRESS
    # --------------------------------------------------------

    "physical_progress",

    "previous_physical_progress",

    "progress_change",

    "progress_rate_per_month",

    "average_progress_rate",


    # --------------------------------------------------------
    # EXPENDITURE
    # --------------------------------------------------------

    "cumulative_expenditure",

    "previous_cumulative_expenditure",

    "expenditure_change",

    "expenditure_percent_change",


    # --------------------------------------------------------
    # COST
    # --------------------------------------------------------

    "original_cost",

    "revised_cost",

    "cost_difference",

    "cost_overrun_percentage",

    "revised_to_original_cost_ratio",

    "original_cost_change",

    "revised_cost_change",


    # --------------------------------------------------------
    # EXPENDITURE RATIOS
    # --------------------------------------------------------

    "expenditure_to_original_cost_ratio",

    "expenditure_to_revised_cost_ratio",

    "expenditure_percentage",

    "expenditure_progress_gap",


    # --------------------------------------------------------
    # SCHEDULE
    # --------------------------------------------------------

    "months_until_target",

    "past_target_date_flag",

    "schedule_extension_months",

    "schedule_extension_flag",


    # --------------------------------------------------------
    # COMPLETION
    # --------------------------------------------------------

    "completed_flag",


    # --------------------------------------------------------
    # DATA QUALITY / ANOMALY
    # --------------------------------------------------------

    "anomaly_score",

    "cumulative_anomaly_score",

]


available_features = []


for feature in candidate_features:

    if feature in df.columns:

        available_features.append(feature)

        print(f"[FOUND]   {feature}")

    else:

        print(f"[SKIPPED] {feature}")


print(
    f"\nAvailable model features: "
    f"{len(available_features)}"
)


# ============================================================
# 13. REMOVE TARGET LEAKAGE COLUMNS
# ============================================================

print_section("13. CHECKING FOR DATA LEAKAGE")


# Columns that contain future information.
#
# These must NEVER be used as model inputs.


future_columns = [

    "next_physical_progress",

    "next_report_month",

    "next_progress_change",

    "next_cumulative_expenditure",

    "next_expenditure_change",

]


for column in future_columns:

    if column in available_features:

        available_features.remove(column)


print(
    "Future information columns excluded "
    "from model inputs."
)


print("\nFinal input features:")


for feature in available_features:

    print(f"  - {feature}")


# ============================================================
# 14. CREATE DELAY PREDICTION DATASET
# ============================================================

print_section("14. CREATING DELAY PREDICTION DATASET")


delay_dataset = (

    df[

        [

            "canonical_id",

            "project_name",

            "state",

            "report_month",

        ]

        +

        available_features

        +

        [

            "future_delay_label"

        ]

    ]

    .copy()

)


# Keep only rows with a valid target.

delay_dataset = (

    delay_dataset

    .dropna(

        subset=[

            "future_delay_label"

        ]

    )

)


delay_dataset[

    "future_delay_label"

] = (

    delay_dataset[

        "future_delay_label"

    ]

    .astype(int)

)


delay_output_file = (

    OUTPUT_DIR

    / "delay_prediction_dataset.csv"

)


delay_dataset.to_csv(

    delay_output_file,

    index=False

)


print(
    f"Delay dataset records: "
    f"{len(delay_dataset):,}"
)


print(
    f"Delay dataset projects: "
    f"{delay_dataset['canonical_id'].nunique():,}"
)


print("\nDelay target distribution:")

print(

    delay_dataset[

        "future_delay_label"

    ]

    .value_counts()

)


print(
    f"\nSaved:\n{delay_output_file}"
)


# ============================================================
# 15. CREATE RISK CLASSIFICATION DATASET
# ============================================================

print_section("15. CREATING RISK CLASSIFICATION DATASET")


risk_dataset = (

    df[

        [

            "canonical_id",

            "project_name",

            "state",

            "report_month",

        ]

        +

        available_features

        +

        [

            "risk_score",

            "risk_label",

        ]

    ]

    .copy()

)


risk_output_file = (

    OUTPUT_DIR

    / "risk_classification_dataset.csv"

)


risk_dataset.to_csv(

    risk_output_file,

    index=False

)


print(
    f"Risk dataset records: "
    f"{len(risk_dataset):,}"
)


print(
    f"Risk dataset projects: "
    f"{risk_dataset['canonical_id'].nunique():,}"
)


print("\nRisk target distribution:")

print(

    risk_dataset[

        "risk_label"

    ]

    .value_counts()

)


print(
    f"\nSaved:\n{risk_output_file}"
)


# ============================================================
# 16. CREATE PROGRESS FORECASTING DATASET
# ============================================================

print_section("16. CREATING PROGRESS FORECASTING DATASET")


progress_dataset = (

    df[

        [

            "canonical_id",

            "project_name",

            "state",

            "report_month",

        ]

        +

        available_features

        +

        [

            "next_physical_progress",

            "next_progress_change",

        ]

    ]

    .copy()

)


# Keep only rows where
# the next progress value exists.

progress_dataset = (

    progress_dataset

    .dropna(

        subset=[

            "next_physical_progress"

        ]

    )

)


progress_output_file = (

    OUTPUT_DIR

    / "progress_forecasting_dataset.csv"

)


progress_dataset.to_csv(

    progress_output_file,

    index=False

)


print(
    f"Progress forecasting records: "
    f"{len(progress_dataset):,}"
)


print(
    f"Progress forecasting projects: "
    f"{progress_dataset['canonical_id'].nunique():,}"
)


print(
    "\nTarget statistics:"
)


print(

    progress_dataset[

        "next_physical_progress"

    ]

    .describe()

)


print(
    f"\nSaved:\n{progress_output_file}"
)


# ============================================================
# 17. CREATE DATASET REPORT
# ============================================================

print_section("17. CREATING MODEL DATASET REPORT")


report_rows = []


# ------------------------------------------------------------
# DELAY DATASET
# ------------------------------------------------------------

report_rows.append({

    "dataset":

        "delay_prediction_dataset",

    "records":

        len(delay_dataset),

    "projects":

        delay_dataset[

            "canonical_id"

        ].nunique(),

    "target":

        "future_delay_label",

    "target_type":

        "binary_classification",

})


# ------------------------------------------------------------
# RISK DATASET
# ------------------------------------------------------------

report_rows.append({

    "dataset":

        "risk_classification_dataset",

    "records":

        len(risk_dataset),

    "projects":

        risk_dataset[

            "canonical_id"

        ].nunique(),

    "target":

        "risk_label",

    "target_type":

        "multiclass_classification",

})


# ------------------------------------------------------------
# PROGRESS DATASET
# ------------------------------------------------------------

report_rows.append({

    "dataset":

        "progress_forecasting_dataset",

    "records":

        len(progress_dataset),

    "projects":

        progress_dataset[

            "canonical_id"

        ].nunique(),

    "target":

        "next_physical_progress",

    "target_type":

        "regression",

})


report_df = pd.DataFrame(

    report_rows

)


report_output_file = (

    OUTPUT_DIR

    / "model_dataset_report.csv"

)


report_df.to_csv(

    report_output_file,

    index=False

)


print(

    report_df.to_string(

        index=False

    )

)


print(
    f"\nSaved:\n{report_output_file}"
)


# ============================================================
# 18. SAVE FEATURE LIST
# ============================================================

print_section("18. SAVING MODEL FEATURE LIST")


feature_report = pd.DataFrame({

    "feature":

        available_features

})


feature_output_file = (

    OUTPUT_DIR

    / "model_input_features.csv"

)


feature_report.to_csv(

    feature_output_file,

    index=False

)


print(

    f"Saved:\n{feature_output_file}"

)


# ============================================================
# 19. FINAL SUMMARY
# ============================================================

print_section("MODEL DATASET PREPARATION COMPLETE")


print(

    "Generated model datasets:\n"

)


print(

    "1. Delay Prediction Dataset"

)


print(

    f"   {delay_output_file}"

)


print(

    "\n2. Risk Classification Dataset"

)


print(

    f"   {risk_output_file}"

)


print(

    "\n3. Progress Forecasting Dataset"

)


print(

    f"   {progress_output_file}"

)


print(

    "\n4. Model Dataset Report"

)


print(

    f"   {report_output_file}"

)


print(

    "\n5. Model Input Feature List"

)


print(

    f"   {feature_output_file}"

)


print("\nDATASETS READY FOR MODEL TRAINING.")

print("DONE.")