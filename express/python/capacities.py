import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import xgboost as xg
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict
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
    print("Error: User ID argument missing for capacities.py.")
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
    print("No activity records found for this user. Skipping capacities analysis.")
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
    print("No feature records found for this user. Skipping capacities analysis.")
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
    print("No prediction records found for this user. Skipping capacities analysis.")
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
    print("Merged dataset is empty. Nothing to process for capacities.")
    conn.close()
    sys.exit(0)

df["Activity Date"] = pd.to_datetime(
    df["Activity Date"]
)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True)

def baseline_capp(df):
    baseline_pow_list = []
    baseline_dist_list = []
    baseline_ele_list = []
    baseline_HR_list = []
    overlap = 0
    for i in range(0, len(df)):
        curr_date = df.loc[i, "Activity Date"]
        cut_off_date = curr_date - pd.Timedelta(days=150)
        rides = df.iloc[:i+1]

        rides = rides[
            rides["Activity Date"] >= cut_off_date
        ]
        
        if rides.empty:
            baseline_pow_list.append(df.loc[i, "Average Watts"])
            baseline_dist_list.append(df.loc[i, "Distance"])
            baseline_ele_list.append(df.loc[i, "Elevation Gain"])
            baseline_HR_list.append(df.loc[i, "Average Heart Rate"])
            continue

        n_val = min(3, len(rides))
        min_fatigue_rides = rides.nsmallest(n_val, "Fatigue")
        max_power_rides = rides.nlargest(n_val, "Average Watts")
        has_overlap = min_fatigue_rides.index.isin(max_power_rides.index).any()
        
        if has_overlap:
            overlap += 1
            common_rides = min_fatigue_rides[
                min_fatigue_rides.index.isin(max_power_rides.index)
            ]
            if common_rides.empty:
                common_rides = min_fatigue_rides
            baseline_pow_list.append(common_rides["Average Watts"].mean())
            baseline_dist_list.append(common_rides["Distance"].mean())
            baseline_ele_list.append(common_rides["Elevation Gain"].mean())
            baseline_HR_list.append(common_rides["Average Heart Rate"].median())
        else:
            baseline = min_fatigue_rides.nlargest(1, "Average Watts")
            if baseline.empty:
                baseline = rides.iloc[[-1]]
            baseline_pow_list.append(baseline.iloc[0]["Average Watts"])
            baseline_dist_list.append(baseline.iloc[0]["Distance"])
            baseline_ele_list.append(baseline.iloc[0]["Elevation Gain"])
            baseline_HR_list.append(baseline.iloc[0]["Average Heart Rate"])
            
    return baseline_pow_list, baseline_dist_list, baseline_ele_list, baseline_HR_list, overlap

baseline_pow_list, baseline_dist_list, baseline_ele_list, baseline_HR_list, overlap = baseline_capp(df)

df["Baseline_Pow"] = baseline_pow_list
df["Baseline_Dist"] = baseline_dist_list
df["Baseline_Ele"] = baseline_ele_list
df["Baseline_HR"] = baseline_HR_list

print("Overlap", overlap)

df["Current_Capacity"] = (
    df["Baseline_Pow"]
    - df["Cumulative_Fatigue"]
)

df["Capacity_Deviation"] = (
    df["Current_Capacity"]
    - df["Baseline_Pow"]
)

try:
    cursor = conn.cursor()

    query4 = """
    UPDATE predictions
    SET
        baseline_power = %s,
        baseline_hr = %s,
        baseline_distance = %s,
        baseline_elevation = %s,
        current_capacity = %s,
        capacity_deviation = %s
    WHERE activity_id = %s;
    """

    for _, row in df.iterrows():
        cursor.execute(
            query4,
            (
                float(row["Baseline_Pow"]),
                float(row["Baseline_HR"]),
                float(row["Baseline_Dist"]),
                float(row["Baseline_Ele"]),
                float(row["Current_Capacity"]),
                float(row["Capacity_Deviation"]),
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