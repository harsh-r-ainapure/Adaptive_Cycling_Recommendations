import pandas as pd
import numpy as np
import os
import sys
from dotenv import load_dotenv
import psycopg2

load_dotenv()

db_url = os.getenv("SUPABASE_DB_URL")
if not db_url:
    print("Error: SUPABASE_DB_URL environment variable is not set.")
    sys.exit(1)

try:
    conn = psycopg2.connect(db_url)
except Exception as e:
    print(f"Database connection failed: {e}")
    sys.exit(1)

user_id = sys.argv[1] if len(sys.argv) > 1 else None
if not user_id:
    print("Error: User ID argument missing for severity.py.")
    conn.close()
    sys.exit(1)

query1 = """
SELECT *
FROM activities
WHERE user_id = %s
ORDER BY activity_date
"""

try:
    df_activity = pd.read_sql_query(query1, conn, params=(user_id,))  # type: ignore
except Exception as e:
    print(f"Failed to query activities: {e}")
    conn.close()
    sys.exit(0)

if df_activity.empty:
    print("No activity records found for this user. Skipping severity analysis.")
    conn.close()
    sys.exit(0)

df_activity = df_activity.rename(columns={
    "id": "Activity UUID",
    "intervals_activity_id": "Activity ID",
    "activity_date": "Activity Date",
    "distance": "Distance",
    "moving_time": "Moving Time",
    "elapsed_time": "Elapsed Time",
    "average_speed": "Average Speed",
    "average_hr": "Average Heart Rate",
    "max_hr": "Max Heart Rate",
    "average_cadence": "Average Cadence",
    "average_power": "Average Watts",
    "elevation_gain": "Elevation Gain",
})

query2 = """
SELECT
    af.*
FROM activity_features af
JOIN activities a
ON af.activity_id = a.id
WHERE a.user_id = %s
ORDER BY a.activity_date;
"""

try:
    df_features = pd.read_sql_query(query2, conn, params=(user_id,))  # type: ignore
except Exception as e:
    print(f"Failed to query activity features: {e}")
    conn.close()
    sys.exit(0)

if df_features.empty:
    print("No feature records found for this user. Skipping severity analysis.")
    conn.close()
    sys.exit(0)

df_features = df_features.rename(columns={
    "gradient": "Gradient",
    "rel_speed": "Rel Speed",
    "hr_sd": "HR SD",
    "ele_sd": "ELE SD",
    "cadence_sd": "cadence_sd",
    "cadence_ratio": "Cadence Ratio",
    "heart_ratio": "Heart Ratio",
    "ele_ratio": "ELE Ratio",
    "hr_recovery_slope": "HR_Recovery_Slope",
    "rolling_percent": "Rolling_Percent",
    "stopping_percent": "Stopping_Percent",
    "power_zone_percent": "Power_Zone_Percent",
    "recovery_zone_percent": "Recovery_Zone_Percent",
    "baseline_hr": "baseline_hr"
})

query3 = """ SELECT
    p.*
FROM predictions p
JOIN activities a
ON p.activity_id = a.id
WHERE a.user_id = %s
ORDER BY a.activity_date;
"""

try:
    df_predictions = pd.read_sql_query(query3, conn, params=(user_id,))  # type: ignore
except Exception as e:
    print(f"Failed to query predictions: {e}")
    conn.close()
    sys.exit(0)

if df_predictions.empty:
    print("No prediction records found for this user. Skipping severity analysis.")
    conn.close()
    sys.exit(0)

df_predictions = df_predictions.rename(columns={
    "estimated_power": "Estimated Power",
    "fatigue": "Fatigue",
    "cumulative_fatigue": "Cumulative_Fatigue",
    "baseline_power": "Baseline_Pow",
    "baseline_hr": "Baseline_HR",
    "baseline_distance": "Baseline_Dist",
    "baseline_elevation": "Baseline_Ele",
    "current_capacity": "Current_Capacity",
    "capacity_deviation": "Capacity_Deviation",
})

df = (
    df_activity
    .merge(
        df_features,
        left_on="Activity UUID",
        right_on="activity_id",
        how="inner"
    )
    .merge(
        df_predictions,
        left_on="Activity UUID",
        right_on="activity_id",
        how="inner"
    )
)

if df.empty:
    print("Merged dataset is empty. Nothing to process for severity.")
    conn.close()
    sys.exit(0)

df["Activity Date"] = pd.to_datetime(
    df["Activity Date"]
)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True) 

def variation(df):
    variation_list = []
    for i in range(0, len(df)):
        curr_date = df.loc[i, "Activity Date"]
        cut_off_date = curr_date - pd.Timedelta(days=150)
        rides = df.iloc[:i+1]

        rides = rides[
            rides["Activity Date"] >= cut_off_date
        ]

        if rides.empty or "Average Watts" not in rides.columns or "Baseline_Pow" not in rides.columns:
            variation_list.append(1.0)
            continue

        diffs = abs(rides["Average Watts"] - rides["Baseline_Pow"])
        if diffs.dropna().empty:
            var = 1.0
        else:
            var = diffs.median()
            if pd.isna(var):
                var = 1.0

        variation_list.append(max(float(var), 1.0))

    return variation_list

df["Variation"] = variation(df)

# Safeguard against division by zero
df["Variation"] = df["Variation"].replace(0, 1.0).fillna(1.0)
df["Baseline_Pow"] = df["Baseline_Pow"].replace(0, 1e-6).fillna(1e-6)

df["Severity"] = df["Capacity_Deviation"] / df["Variation"]
df["Percent_Change"] = df["Capacity_Deviation"] / df["Baseline_Pow"]

try:
    cursor = conn.cursor()

    query4 = """
    UPDATE predictions
    SET
        variation = %s,
        severity = %s,
        percent_change = %s
    WHERE activity_id = %s;
    """

    for _, row in df.iterrows():
        cursor.execute(
            query4,
            (
                float(row["Variation"]),
                float(row["Severity"]),
                float(row["Percent_Change"]),
                row["Activity UUID"]
            )
        )

    conn.commit()
    cursor.close()
    print(f"Updated {len(df)} prediction rows.")
except Exception as e:
    print(f"Database update failed: {e}")
    if 'conn' in locals() and conn:
        conn.rollback()
finally:
    if 'conn' in locals() and conn:
        conn.close()