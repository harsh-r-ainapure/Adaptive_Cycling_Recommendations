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
from fitparse import FitFile
from dotenv import load_dotenv
import psycopg2

load_dotenv()

conn = psycopg2.connect(
    os.getenv("SUPABASE_DB_URL")
)

user_id = sys.argv[1]

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

df_predictions = pd.read_sql_query(
    query3,
    conn,
    params=(user_id,)
)

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

latest = df.iloc[-1]

curr_date = latest["Activity Date"]
cut_off_date = curr_date - pd.Timedelta(days=150)

history = df[df["Activity Date"] >= cut_off_date].copy()

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

S = abs(latest["Severity"])

Distance_Weight = 1 / (S + 1)

Elevation_Weight = S / (S + 1)

Dist_Load_Ratio = latest["Last_Ride_Dist"] / latest["Baseline_Dist"]

Ele_Load_Ratio = (
    latest["Last_Ride_Ele"] / latest["Baseline_Ele"]
    if latest["Baseline_Ele"] > 0
    else 1
)

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
    severity_std = 1

SEVERITY_BAND = 1.0

severity_low = severity_mean - SEVERITY_BAND * severity_std
severity_high = severity_mean + SEVERITY_BAND * severity_std

ALPHA_BASE = 0.4
ALPHA_SHRUNK = 0.2
ALPHA_EXPANDED = 0.6

ENDURANCE_THRESHOLD_KM = 110

is_out_of_band = (
    latest["Severity"] < severity_low
    or latest["Severity"] > severity_high
)

is_endurance_ride = latest["Last_Ride_Dist"] > ENDURANCE_THRESHOLD_KM

if is_endurance_ride:
    Alpha = ALPHA_EXPANDED
elif is_out_of_band:
    Alpha = ALPHA_SHRUNK
else:
    Alpha = ALPHA_BASE

Chronic_Dist_Term = 1 + latest["Percent_Change"] * Distance_Weight
Chronic_Ele_Term = 1 + latest["Percent_Change"] * Elevation_Weight

Recommended_Dist = (
    latest["Baseline_Dist"]
    *
    (
        (1 - Alpha) * Chronic_Dist_Term
        +
        Alpha * Dist_Recovery_Factor
    )
)

Recommended_Ele = (
    latest["Baseline_Ele"]
    *
    (
        (1 - Alpha) * Chronic_Ele_Term
        +
        Alpha * Ele_Recovery_Factor
    )
)

Recommended_HR = round(
    latest["Baseline_HR"]
    *
    (1 + 0.5 * latest["Percent_Change"])
)

Recommended_Dist = round(
    Recommended_Dist
)

Recommended_Ele = round(
    Recommended_Ele
)

print("Severity :", latest["Severity"])
print("Percent Change :", latest["Percent_Change"])

print("Baseline Distance :", latest["Baseline_Dist"])
print("Baseline Elevation :", latest["Baseline_Ele"])
print("Baseline HR :", latest["Baseline_HR"])

print("Last Ride Distance :", latest["Last_Ride_Dist"])
print("Last Ride Elevation :", latest["Last_Ride_Ele"])

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
cursor = None
conn.close()

print("Recommendation saved successfully.")
