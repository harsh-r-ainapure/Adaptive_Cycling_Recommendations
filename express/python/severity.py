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

query1 = """
SELECT *
FROM activities
WHERE user_id = %s
ORDER BY activity_date
"""

df_activity = pd.read_sql_query(query1, conn, params=(user_id,))

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

df_features = pd.read_sql_query(query2, conn, params=(user_id,))

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

query3 =""" SELECT
    p.*
FROM predictions p
JOIN activities a
ON p.activity_id = a.id
WHERE a.user_id = %s
ORDER BY a.activity_date;
"""

df_predictions = pd.read_sql_query(query3, conn, params=(user_id,))

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



df["Activity Date"] = pd.to_datetime(
    df["Activity Date"]
)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True) 

def variation (df):
    variation_list = []
    for i in range(0,len(df)):
      curr_date = df.loc[i,"Activity Date"]
      cut_off_date = curr_date - pd.Timedelta(days=150)
      rides = df.iloc[:i+1]

      rides = rides[
      rides["Activity Date"] >= cut_off_date
      ]

      var=abs(
      rides["Average Watts"]
      - rides["Baseline_Pow"]
      ).median()

      variation_list.append(max(var,1))

    return variation_list

df["Variation"] = variation(df)

df["Severity"] = (df["Capacity_Deviation"] / df["Variation"])

df["Percent_Change"] = (
    df["Capacity_Deviation"]
    / df["Baseline_Pow"]
)



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
conn.close()

print(f"Updated {len(df)} prediction rows.")