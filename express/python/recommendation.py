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

S = abs(latest["Severity"])

Distance_Weight = 1 / (S + 1)

Elevation_Weight = S / (S + 1)

Recommended_Dist = (
    latest["Baseline_Dist"]
    *
    (
        1 +
        latest["Percent_Change"] * Distance_Weight
    )
)

Recommended_Ele = (
    latest["Baseline_Ele"]
    *
    (
        1 +
        latest["Percent_Change"] * Elevation_Weight
    )
)

Recommended_HR = round(
    latest["Baseline_HR"]
    *
    (1 + latest["Percent_Change"])
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
conn.close()

print("Recommendation saved successfully.")

