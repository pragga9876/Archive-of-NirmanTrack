import pandas as pd
import numpy as np
from pathlib import Path


# ============================================================
# PATH CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "data"
    / "processed"
    / "master_project_dataset_clean.csv"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "analysis"
    / "anomalies"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# DISPLAY CONFIGURATION
# ============================================================

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_header(title):
    print("\n")
    print("=" * 90)
    print(title)
    print("=" * 90)


def save_csv(dataframe, filename):
    output_path = OUTPUT_DIR / filename
    dataframe.to_csv(output_path, index=False)

    print(f"Saved: {filename}")

    return output_path


def safe_percentage_change(current, previous):
    """
    Calculate percentage change safely.

    Formula:

        ((current - previous) / previous) * 100

    Returns NaN when previous value is zero or missing.
    """

    if pd.isna(current) or pd.isna(previous):
        return np.nan

    if previous == 0:
        return np.nan

    return ((current - previous) / abs(previous)) * 100


# ============================================================
# LOAD DATASET
# ============================================================

print_header("LOADING DATASET")

print(f"ML SERVICE DIRECTORY:\n{BASE_DIR}\n")

print(f"DATASET PATH:\n{DATASET_PATH}\n")

print(f"OUTPUT DIRECTORY:\n{OUTPUT_DIR}\n")


if not DATASET_PATH.exists():

    raise FileNotFoundError(
        f"\nDataset not found.\n\n"
        f"Expected location:\n"
        f"{DATASET_PATH}"
    )


df = pd.read_csv(DATASET_PATH)


print("Dataset loaded successfully.")


# ============================================================
# REQUIRED COLUMN CHECK
# ============================================================

print_header("1. REQUIRED COLUMN CHECK")


required_columns = [

    "canonical_id",
    "project_name",
    "state",
    "month",
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
# DATA TYPE PREPARATION
# ============================================================

print_header("2. DATA TYPE PREPARATION")


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


# ============================================================
# SORT DATASET
# ============================================================

print_header("3. SORTING DATASET")


df = df.sort_values(

    by=[
        "canonical_id",
        "report_month"
    ]

).reset_index(drop=True)


print(
    "Dataset sorted by "
    "canonical_id and report_month."
)


# ============================================================
# BASIC DATASET INFORMATION
# ============================================================

print_header("4. DATASET OVERVIEW")


print(f"Total records: {len(df):,}")

print(
    f"Unique projects: "
    f"{df['canonical_id'].nunique():,}"
)

print(
    f"Reporting months: "
    f"{df['month'].nunique():,}"
)


# ============================================================
# CREATE TIMELINE FEATURES
# ============================================================

print_header("5. CREATING TIMELINE DIFFERENCE FEATURES")


project_group = df.groupby(
    "canonical_id",
    group_keys=False
)


# ------------------------------------------------------------
# PREVIOUS VALUES
# ------------------------------------------------------------

df["previous_report_month"] = project_group[
    "report_month"
].shift(1)


df["previous_progress"] = project_group[
    "physical_progress"
].shift(1)


df["previous_expenditure"] = project_group[
    "cumulative_expenditure"
].shift(1)


df["previous_original_cost"] = project_group[
    "original_cost"
].shift(1)


df["previous_revised_cost"] = project_group[
    "revised_cost"
].shift(1)


# ------------------------------------------------------------
# MONTH GAP
# ------------------------------------------------------------

df["month_gap"] = (

    (
        df["report_month"].dt.year
        -
        df["previous_report_month"].dt.year
    ) * 12

    +

    (
        df["report_month"].dt.month
        -
        df["previous_report_month"].dt.month
    )

)


# ------------------------------------------------------------
# PROGRESS CHANGE
# ------------------------------------------------------------

df["progress_change"] = (

    df["physical_progress"]

    -

    df["previous_progress"]

)


# ------------------------------------------------------------
# EXPENDITURE CHANGE
# ------------------------------------------------------------

df["expenditure_change"] = (

    df["cumulative_expenditure"]

    -

    df["previous_expenditure"]

)


# ------------------------------------------------------------
# COST CHANGE
# ------------------------------------------------------------

df["original_cost_change"] = (

    df["original_cost"]

    -

    df["previous_original_cost"]

)


df["revised_cost_change"] = (

    df["revised_cost"]

    -

    df["previous_revised_cost"]

)


# ------------------------------------------------------------
# SAFE EXPENDITURE PERCENTAGE CHANGE
# ------------------------------------------------------------

df["expenditure_percentage_change"] = df.apply(

    lambda row:

    safe_percentage_change(

        row["cumulative_expenditure"],

        row["previous_expenditure"]

    ),

    axis=1

)


print("Timeline features created successfully.")


# ============================================================
# 1. NEGATIVE EXPENDITURE ANALYSIS
# ============================================================

print_header("6. NEGATIVE EXPENDITURE ANALYSIS")


negative_expenditure = df[

    df["cumulative_expenditure"] < 0

].copy()


print(

    f"Negative expenditure records: "
    f"{len(negative_expenditure):,}"

)


if not negative_expenditure.empty:

    negative_expenditure = negative_expenditure[

        [

            "canonical_id",
            "project_name",
            "state",

            "month",
            "report_month",

            "cumulative_expenditure",

            "original_cost",
            "revised_cost",

            "physical_progress"

        ]

    ]


    save_csv(

        negative_expenditure,

        "negative_expenditure_records.csv"

    )


else:

    print(
        "No negative expenditure records found."
    )


# ============================================================
# 2. DECREASING PHYSICAL PROGRESS
# ============================================================

print_header("7. DECREASING PHYSICAL PROGRESS ANALYSIS")


decreasing_progress = df[

    df["progress_change"] < 0

].copy()


print(

    f"Records with decreasing progress: "
    f"{len(decreasing_progress):,}"

)


print(

    f"Projects affected: "
    f"{decreasing_progress['canonical_id'].nunique():,}"

)


if not decreasing_progress.empty:

    decreasing_progress = decreasing_progress[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "month_gap",

            "previous_progress",
            "physical_progress",

            "progress_change",

            "cumulative_expenditure",

            "original_cost",
            "revised_cost"

        ]

    ]


    decreasing_progress = decreasing_progress.sort_values(

        by="progress_change"

    )


    save_csv(

        decreasing_progress,

        "progress_decrease_records.csv"

    )


# ============================================================
# 3. LARGE PROGRESS JUMPS
# ============================================================

print_header("8. LARGE PHYSICAL PROGRESS JUMP ANALYSIS")


# ------------------------------------------------------------
# THRESHOLD
# ------------------------------------------------------------

PROGRESS_JUMP_THRESHOLD = 20


large_progress_jumps = df[

    df["progress_change"].abs()

    >=

    PROGRESS_JUMP_THRESHOLD

].copy()


print(

    f"Threshold: {PROGRESS_JUMP_THRESHOLD} "
    f"percentage points"

)


print(

    f"Large progress jump records: "
    f"{len(large_progress_jumps):,}"

)


print(

    f"Projects affected: "
    f"{large_progress_jumps['canonical_id'].nunique():,}"

)


if not large_progress_jumps.empty:

    large_progress_jumps = large_progress_jumps[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "month_gap",

            "previous_progress",
            "physical_progress",

            "progress_change",

            "cumulative_expenditure",

            "original_cost",
            "revised_cost"

        ]

    ]


    large_progress_jumps = large_progress_jumps.sort_values(

        by="progress_change",

        key=lambda column: column.abs(),

        ascending=False

    )


    save_csv(

        large_progress_jumps,

        "large_progress_jump_records.csv"

    )


# ============================================================
# 4. DECREASING CUMULATIVE EXPENDITURE
# ============================================================

print_header("9. DECREASING CUMULATIVE EXPENDITURE ANALYSIS")


decreasing_expenditure = df[

    df["expenditure_change"] < 0

].copy()


print(

    f"Records with decreasing expenditure: "
    f"{len(decreasing_expenditure):,}"

)


print(

    f"Projects affected: "
    f"{decreasing_expenditure['canonical_id'].nunique():,}"

)


if not decreasing_expenditure.empty:

    decreasing_expenditure = decreasing_expenditure[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "month_gap",

            "previous_expenditure",
            "cumulative_expenditure",

            "expenditure_change",
            "expenditure_percentage_change",

            "physical_progress",

            "original_cost",
            "revised_cost"

        ]

    ]


    decreasing_expenditure = decreasing_expenditure.sort_values(

        by="expenditure_change"

    )


    save_csv(

        decreasing_expenditure,

        "expenditure_decrease_records.csv"

    )


# ============================================================
# 5. MASSIVE EXPENDITURE JUMP ANALYSIS
# ============================================================

print_header("10. MASSIVE EXPENDITURE JUMP ANALYSIS")


# ------------------------------------------------------------
# THRESHOLD
# ------------------------------------------------------------

EXPENDITURE_PERCENTAGE_THRESHOLD = 200


massive_expenditure_jumps = df[

    df["expenditure_percentage_change"].abs()

    >=

    EXPENDITURE_PERCENTAGE_THRESHOLD

].copy()


print(

    f"Percentage threshold: "
    f"{EXPENDITURE_PERCENTAGE_THRESHOLD}%"

)


print(

    f"Massive expenditure jump records: "
    f"{len(massive_expenditure_jumps):,}"

)


print(

    f"Projects affected: "
    f"{massive_expenditure_jumps['canonical_id'].nunique():,}"

)


if not massive_expenditure_jumps.empty:

    massive_expenditure_jumps = massive_expenditure_jumps[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "month_gap",

            "previous_expenditure",
            "cumulative_expenditure",

            "expenditure_change",
            "expenditure_percentage_change",

            "physical_progress",

            "original_cost",
            "revised_cost"

        ]

    ]


    massive_expenditure_jumps = massive_expenditure_jumps.sort_values(

        by="expenditure_percentage_change",

        key=lambda column: column.abs(),

        ascending=False

    )


    save_csv(

        massive_expenditure_jumps,

        "massive_expenditure_jump_records.csv"

    )


# ============================================================
# 6. EXTREME EXPENDITURE OUTLIERS
# ============================================================

print_header("11. EXTREME EXPENDITURE OUTLIER ANALYSIS")


expenditure_values = df[
    "cumulative_expenditure"
].dropna()


Q1 = expenditure_values.quantile(0.25)

Q3 = expenditure_values.quantile(0.75)


IQR = Q3 - Q1


LOWER_BOUND = Q1 - (3 * IQR)

UPPER_BOUND = Q3 + (3 * IQR)


print(f"Q1: {Q1:.2f}")

print(f"Q3: {Q3:.2f}")

print(f"IQR: {IQR:.2f}")

print(f"Lower bound: {LOWER_BOUND:.2f}")

print(f"Upper bound: {UPPER_BOUND:.2f}")


extreme_expenditure_outliers = df[

    (

        df["cumulative_expenditure"]
        <
        LOWER_BOUND

    )

    |

    (

        df["cumulative_expenditure"]
        >
        UPPER_BOUND

    )

].copy()


print(

    f"\nExtreme expenditure outliers: "
    f"{len(extreme_expenditure_outliers):,}"

)


if not extreme_expenditure_outliers.empty:

    extreme_expenditure_outliers = extreme_expenditure_outliers[

        [

            "canonical_id",
            "project_name",
            "state",

            "report_month",

            "cumulative_expenditure",

            "previous_expenditure",

            "expenditure_change",

            "expenditure_percentage_change",

            "physical_progress",

            "original_cost",
            "revised_cost"

        ]

    ]


    extreme_expenditure_outliers = (

        extreme_expenditure_outliers

        .sort_values(

            by="cumulative_expenditure",

            ascending=False

        )

    )


    save_csv(

        extreme_expenditure_outliers,

        "extreme_expenditure_outliers.csv"

    )


# ============================================================
# 7. ORIGINAL COST CHANGES
# ============================================================

print_header("12. ORIGINAL COST CHANGE ANALYSIS")


original_cost_changes = df[

    df["original_cost_change"] != 0

].copy()


original_cost_changes = original_cost_changes[

    original_cost_changes[
        "original_cost_change"
    ].notna()

]


print(

    f"Original cost change records: "
    f"{len(original_cost_changes):,}"

)


print(

    f"Projects affected: "
    f"{original_cost_changes['canonical_id'].nunique():,}"

)


if not original_cost_changes.empty:

    original_cost_changes = original_cost_changes[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "previous_original_cost",
            "original_cost",

            "original_cost_change",

            "revised_cost",

            "physical_progress"

        ]

    ]


    save_csv(

        original_cost_changes,

        "original_cost_change_records.csv"

    )


# ============================================================
# 8. REVISED COST CHANGES
# ============================================================

print_header("13. REVISED COST CHANGE ANALYSIS")


revised_cost_changes = df[

    df["revised_cost_change"] != 0

].copy()


revised_cost_changes = revised_cost_changes[

    revised_cost_changes[
        "revised_cost_change"
    ].notna()

]


print(

    f"Revised cost change records: "
    f"{len(revised_cost_changes):,}"

)


print(

    f"Projects affected: "
    f"{revised_cost_changes['canonical_id'].nunique():,}"

)


if not revised_cost_changes.empty:

    revised_cost_changes = revised_cost_changes[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "previous_revised_cost",
            "revised_cost",

            "revised_cost_change",

            "original_cost",

            "physical_progress"

        ]

    ]


    save_csv(

        revised_cost_changes,

        "revised_cost_change_records.csv"

    )


# ============================================================
# 9. SUSPICIOUS COST RATIOS
# ============================================================

print_header("14. COST RATIO ANALYSIS")


df["cost_ratio"] = (

    df["revised_cost"]

    /

    df["original_cost"]

)


# ------------------------------------------------------------
# EXTREME COST INCREASE
# ------------------------------------------------------------

EXTREME_COST_INCREASE_RATIO = 2.0


extreme_cost_increase = df[

    df["cost_ratio"]

    >=

    EXTREME_COST_INCREASE_RATIO

].copy()


print(

    f"Projects/records where revised cost "
    f"is at least "
    f"{EXTREME_COST_INCREASE_RATIO}x "
    f"original cost: "

    f"{len(extreme_cost_increase):,}"

)


if not extreme_cost_increase.empty:

    extreme_cost_increase = extreme_cost_increase[

        [

            "canonical_id",
            "project_name",
            "state",

            "report_month",

            "original_cost",
            "revised_cost",

            "cost_ratio",

            "physical_progress",

            "cumulative_expenditure"

        ]

    ]


    extreme_cost_increase = (

        extreme_cost_increase

        .sort_values(

            by="cost_ratio",

            ascending=False

        )

    )


    save_csv(

        extreme_cost_increase,

        "extreme_cost_increase_records.csv"

    )


# ============================================================
# 10. PHYSICAL PROGRESS RANGE VALIDATION
# ============================================================

print_header("15. PHYSICAL PROGRESS RANGE VALIDATION")


invalid_progress = df[

    (

        df["physical_progress"] < 0

    )

    |

    (

        df["physical_progress"] > 100

    )

].copy()


print(

    f"Invalid progress records "
    f"(<0 or >100): "

    f"{len(invalid_progress):,}"

)


if not invalid_progress.empty:

    invalid_progress = invalid_progress[

        [

            "canonical_id",
            "project_name",
            "state",

            "report_month",

            "physical_progress",

            "cumulative_expenditure",

            "original_cost",
            "revised_cost"

        ]

    ]


    save_csv(

        invalid_progress,

        "invalid_progress_records.csv"

    )


# ============================================================
# 11. IRREGULAR TIMELINE GAP ANALYSIS
# ============================================================

print_header("16. IRREGULAR TIMELINE GAP ANALYSIS")


irregular_gaps = df[

    df["month_gap"] > 1

].copy()


print(

    f"Timeline gaps greater than 1 month: "
    f"{len(irregular_gaps):,}"

)


print(

    f"Projects affected: "
    f"{irregular_gaps['canonical_id'].nunique():,}"

)


if not irregular_gaps.empty:

    irregular_gaps = irregular_gaps[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "month_gap",

            "previous_progress",
            "physical_progress",

            "progress_change",

            "previous_expenditure",
            "cumulative_expenditure",

            "expenditure_change"

        ]

    ]


    irregular_gaps = irregular_gaps.sort_values(

        by="month_gap",

        ascending=False

    )


    save_csv(

        irregular_gaps,

        "irregular_timeline_gaps.csv"

    )


# ============================================================
# 12. COMPLETED PROJECT INCONSISTENCIES
# ============================================================

print_header("17. COMPLETED PROJECT INCONSISTENCY ANALYSIS")


# ------------------------------------------------------------
# A project reaches 100%
# Then later falls below 100%
# ------------------------------------------------------------


completed_projects = []


for project_id, group in df.groupby("canonical_id"):

    group = group.sort_values("report_month")

    progress_values = group["physical_progress"]

    reached_completion = False


    for index, progress in progress_values.items():

        if pd.isna(progress):

            continue


        if progress >= 100:

            reached_completion = True


        elif reached_completion and progress < 100:

            completed_projects.append(index)


completed_then_decreased = df.loc[

    completed_projects

].copy()


print(

    f"Records occurring after a project reached "
    f"100% and later dropped below 100%: "

    f"{len(completed_then_decreased):,}"

)


if not completed_then_decreased.empty:

    completed_then_decreased = completed_then_decreased[

        [

            "canonical_id",
            "project_name",
            "state",

            "previous_report_month",
            "report_month",

            "previous_progress",
            "physical_progress",

            "progress_change",

            "cumulative_expenditure"

        ]

    ]


    save_csv(

        completed_then_decreased,

        "completed_then_progress_decreased.csv"

    )


# ============================================================
# 13. CREATE PROJECT-LEVEL ANOMALY SUMMARY
# ============================================================

print_header("18. BUILDING PROJECT-LEVEL ANOMALY SUMMARY")


project_anomaly_summary = (


    df.groupby("canonical_id")

    .agg(

        project_name=(

            "project_name",

            "first"

        ),

        state=(

            "state",

            "first"

        ),

        snapshots=(

            "canonical_id",

            "size"

        ),

        negative_expenditure_count=(

            "cumulative_expenditure",

            lambda x: (x < 0).sum()

        ),

        progress_decrease_count=(

            "progress_change",

            lambda x: (x < 0).sum()

        ),

        largest_progress_drop=(

            "progress_change",

            "min"

        ),

        large_progress_jump_count=(

            "progress_change",

            lambda x:

            (

                x.abs()

                >=

                PROGRESS_JUMP_THRESHOLD

            ).sum()

        ),

        expenditure_decrease_count=(

            "expenditure_change",

            lambda x: (x < 0).sum()

        ),

        largest_expenditure_drop=(

            "expenditure_change",

            "min"

        ),

        massive_expenditure_jump_count=(

            "expenditure_percentage_change",

            lambda x:

            (

                x.abs()

                >=

                EXPENDITURE_PERCENTAGE_THRESHOLD

            ).sum()

        ),

        original_cost_change_count=(

            "original_cost_change",

            lambda x:

            (

                x.notna()

                &

                (x != 0)

            ).sum()

        ),

        revised_cost_change_count=(

            "revised_cost_change",

            lambda x:

            (

                x.notna()

                &

                (x != 0)

            ).sum()

        ),

        max_month_gap=(

            "month_gap",

            "max"

        )

    )

    .reset_index()

)


# ------------------------------------------------------------
# ANOMALY SCORE
# ------------------------------------------------------------


project_anomaly_summary["anomaly_score"] = (

    project_anomaly_summary[
        "negative_expenditure_count"
    ]

    +

    project_anomaly_summary[
        "progress_decrease_count"
    ]

    +

    project_anomaly_summary[
        "large_progress_jump_count"
    ]

    +

    project_anomaly_summary[
        "expenditure_decrease_count"
    ]

    +

    project_anomaly_summary[
        "massive_expenditure_jump_count"
    ]

)


project_anomaly_summary = (

    project_anomaly_summary

    .sort_values(

        by="anomaly_score",

        ascending=False

    )

)


save_csv(

    project_anomaly_summary,

    "project_anomaly_summary.csv"

)


print(

    f"Projects in anomaly summary: "
    f"{len(project_anomaly_summary):,}"

)


# ============================================================
# 14. DATA QUALITY SUMMARY
# ============================================================

print_header("19. DATA QUALITY SUMMARY")


data_quality_summary = pd.DataFrame(

    {

        "metric": [

            "total_records",

            "total_projects",

            "negative_expenditure_records",

            "progress_decrease_records",

            "large_progress_jump_records",

            "expenditure_decrease_records",

            "massive_expenditure_jump_records",

            "extreme_expenditure_outliers",

            "original_cost_change_records",

            "revised_cost_change_records",

            "invalid_progress_records",

            "irregular_timeline_gap_records",

            "completed_then_progress_decreased_records"

        ],

        "count": [

            len(df),

            df["canonical_id"].nunique(),

            len(negative_expenditure),

            len(decreasing_progress),

            len(large_progress_jumps),

            len(decreasing_expenditure),

            len(massive_expenditure_jumps),

            len(extreme_expenditure_outliers),

            len(original_cost_changes),

            len(revised_cost_changes),

            len(invalid_progress),

            len(irregular_gaps),

            len(completed_then_decreased)

        ]

    }

)


save_csv(

    data_quality_summary,

    "data_quality_summary.csv"

)


print("\n")

print(

    data_quality_summary.to_string(

        index=False

    )

)


# ============================================================
# COMPLETE
# ============================================================

print_header("ANOMALY INVESTIGATION COMPLETE")


print(

    "All anomaly investigation reports "
    "have been generated."

)


print(f"\nOutput directory:\n{OUTPUT_DIR}")


print("\nGenerated reports:")


for file in sorted(

    OUTPUT_DIR.glob("*.csv")

):

    print(f"  - {file.name}")


print("\nDONE.")