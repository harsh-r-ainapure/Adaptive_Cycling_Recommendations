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
    print("Error: User ID argument missing for recommendation.py.")
    conn.close()
    sys.exit(1)

query3 = """
SELECT
    a.activity_date,
    a.distance,
    a.elevation_gain,
    p.*
FROM predictions p
JOIN activities a
ON p.activity_id = a.id
WHERE a.user_id = %s
ORDER BY a.activity_date;
"""

try:
    df_predictions = pd.read_sql_query(
        query3,
        conn,  # type: ignore
        params=(user_id,)
    )
except Exception as e:
    print(f"Failed to query predictions for recommendation: {e}")
    conn.close()
    sys.exit(0)

if df_predictions.empty:
    print("No prediction records found for this user. Skipping recommendations.")
    conn.close()
    sys.exit(0)

df_predictions = df_predictions.rename(columns={
    "activity_date": "Activity Date",
    "distance": "Last_Ride_Dist",
    "elevation_gain": "Last_Ride_Ele",
    "estimated_power": "Estimated Power",
    "fatigue": "Fatigue",
    "cumulative_fatigue": "Cumulative_Fatigue",
    "baseline_power": "Baseline_Pow",
    "baseline_hr": "Baseline_HR",
    "baseline_distance": "Baseline_Dist",
    "baseline_elevation": "Baseline_Ele",
    "current_capacity": "Current_Capacity",
    "capacity_deviation": "Capacity_Deviation",
    "variation": "Variation",
    "severity": "Severity",
    "percent_change": "Percent_Change",
})

df = df_predictions.copy()

df["Activity Date"] = pd.to_datetime(df["Activity Date"])

df = (
    df.sort_values("Activity Date")
      .reset_index(drop=True)
)

if df.empty:
    print("Processed dataframe is empty. Nothing to recommend.")
    conn.close()
    sys.exit(0)

latest = df.iloc[-1]

curr_date = latest["Activity Date"]
cut_off_date = curr_date - pd.Timedelta(days=150)

history = df[df["Activity Date"] >= cut_off_date].copy()

# Safeguard baseline distance and elevation against zero or NaN to prevent division by zero
df["Baseline_Dist"] = df["Baseline_Dist"].replace(0, 1.0).fillna(1.0)
df["Baseline_Ele"] = df["Baseline_Ele"].replace(0, 1.0).fillna(1.0)
history["Baseline_Dist"] = history["Baseline_Dist"].replace(0, 1.0).fillna(1.0)
history["Baseline_Ele"] = history["Baseline_Ele"].replace(0, 1.0).fillna(1.0)

history["Dist_Load_Ratio"] = (
    history["Last_Ride_Dist"] / history["Baseline_Dist"]
)

history["Ele_Load_Ratio"] = np.where(
    history["Baseline_Ele"] > 0,
    history["Last_Ride_Ele"] / history["Baseline_Ele"],
    1
)

history["Dist_Recovery_Raw"] = 2 - history["Dist_Load_Ratio"]
history["Ele_Recovery_Raw"] = 2 - history["Ele_Load_Ratio"]

MIN_RIDES_FOR_PERCENTILE = 10

HARD_FLOOR = 0.5
HARD_CEIL = 1.5

if len(history) >= MIN_RIDES_FOR_PERCENTILE:

    dist_low = max(
        history["Dist_Recovery_Raw"].quantile(0.05),
        HARD_FLOOR
    )
    dist_high = min(
        history["Dist_Recovery_Raw"].quantile(0.95),
        HARD_CEIL
    )

    ele_low = max(
        history["Ele_Recovery_Raw"].quantile(0.05),
        HARD_FLOOR
    )
    ele_high = min(
        history["Ele_Recovery_Raw"].quantile(0.95),
        HARD_CEIL
    )

else:

    dist_low, dist_high = HARD_FLOOR, HARD_CEIL
    ele_low, ele_high = HARD_FLOOR, HARD_CEIL

S = abs(latest["Severity"]) if not pd.isna(latest["Severity"]) else 0.0

Distance_Weight = 1 / (S + 1)
Elevation_Weight = S / (S + 1)

base_dist = float(latest["Baseline_Dist"]) if not pd.isna(latest["Baseline_Dist"]) else 1.0
base_ele = float(latest["Baseline_Ele"]) if not pd.isna(latest["Baseline_Ele"]) else 1.0
base_hr = float(latest["Baseline_HR"]) if not pd.isna(latest["Baseline_HR"]) else 120.0
last_dist = float(latest["Last_Ride_Dist"]) if not pd.isna(latest["Last_Ride_Dist"]) else 0.0
last_ele = float(latest["Last_Ride_Ele"]) if not pd.isna(latest["Last_Ride_Ele"]) else 0.0
pct_change = float(latest["Percent_Change"]) if not pd.isna(latest["Percent_Change"]) else 0.0

Dist_Load_Ratio = last_dist / base_dist
Ele_Load_Ratio = last_ele / base_ele if base_ele > 0 else 1.0

Dist_Recovery_Factor = np.clip(
    2 - Dist_Load_Ratio,
    dist_low,
    dist_high
)

Ele_Recovery_Factor = np.clip(
    2 - Ele_Load_Ratio,
    ele_low,
    ele_high
)

severity_mean = history["Severity"].mean()
severity_std = history["Severity"].std()

if pd.isna(severity_std) or severity_std == 0:
    severity_std = 1.0

SEVERITY_BAND = 1.0

severity_low = severity_mean - SEVERITY_BAND * severity_std
severity_high = severity_mean + SEVERITY_BAND * severity_std

ALPHA_BASE = 0.4
ALPHA_SHRUNK = 0.2
ALPHA_EXPANDED = 0.6

ENDURANCE_THRESHOLD_KM = 110

latest_severity = float(latest["Severity"]) if not pd.isna(latest["Severity"]) else 0.0
is_out_of_band = (
    latest_severity < severity_low
    or latest_severity > severity_high
)

is_endurance_ride = last_dist > ENDURANCE_THRESHOLD_KM

if is_endurance_ride:
    Alpha = ALPHA_EXPANDED
elif is_out_of_band:
    Alpha = ALPHA_SHRUNK
else:
    Alpha = ALPHA_BASE

Chronic_Dist_Term = 1 + pct_change * Distance_Weight
Chronic_Ele_Term = 1 + pct_change * Elevation_Weight

Recommended_Dist = (
    base_dist
    *
    (
        (1 - Alpha) * Chronic_Dist_Term
        +
        Alpha * Dist_Recovery_Factor
    )
)

Recommended_Ele = (
    base_ele
    *
    (
        (1 - Alpha) * Chronic_Ele_Term
        +
        Alpha * Ele_Recovery_Factor
    )
)

Recommended_HR = round(
    base_hr
    *
    (1 + 0.5 * pct_change)
)

Recommended_Dist = round(Recommended_Dist)
Recommended_Ele = round(Recommended_Ele)

print("Severity :", latest_severity)
print("Percent Change :", pct_change)

print("Baseline Distance :", base_dist)
print("Baseline Elevation :", base_ele)
print("Baseline HR :", base_hr)

print("Last Ride Distance :", last_dist)
print("Last Ride Elevation :", last_ele)

print("Rides in 150-day window :", len(history))
print("Dist clip bounds :", dist_low, dist_high)
print("Ele clip bounds :", ele_low, ele_high)

print("Alpha (acute weight) :", Alpha)

print("Chronic Dist Term :", Chronic_Dist_Term)
print("Dist Recovery Factor :", Dist_Recovery_Factor)

print("Chronic Ele Term :", Chronic_Ele_Term)
print("Ele Recovery Factor :", Ele_Recovery_Factor)

print("Recommended Distance :", Recommended_Dist)
print("Recommended Elevation :", Recommended_Ele)
print("Recommended HR :", Recommended_HR)

try:
    cursor = conn.cursor()

    query4 = """
    INSERT INTO recommendations (
        activity_id,
        recommended_distance,
        recommended_elevation,
        recommended_hr
    )
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (activity_id)
    DO UPDATE SET
        recommended_distance = EXCLUDED.recommended_distance,
        recommended_elevation = EXCLUDED.recommended_elevation,
        recommended_hr = EXCLUDED.recommended_hr;
    """

    cursor.execute(
        query4,
        (
            latest["activity_id"],
            float(Recommended_Dist),
            float(Recommended_Ele),
            float(Recommended_HR)
        )
    )

    conn.commit()
    cursor.close()
    print("Recommendation saved successfully....")
except Exception as e:
    print(f"Database recommendation save failed: {e}")
    if 'conn' in locals() and conn:
        conn.rollback()
finally:
    if 'conn' in locals() and conn:
        conn.close()