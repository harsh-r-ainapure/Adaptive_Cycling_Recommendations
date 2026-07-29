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

def baseline_capp (df):
    baseline_pow_list = []
    baseline_dist_list = []
    baseline_ele_list = []
    baseline_HR_list = []
    overlap = 0
    for i in range(0,len(df)):
        curr_date = df.loc[i,"Activity Date"]
        cut_off_date = curr_date - pd.Timedelta(days=150)
        rides = df.iloc[:i+1]

        rides = rides[
        rides["Activity Date"] >= cut_off_date
         ]
        
        min_fatigue_rides = rides.nsmallest(3, "Fatigue")
        max_power_rides = rides.nlargest(3, "Average Watts")
        has_overlap = min_fatigue_rides.index.isin(max_power_rides.index).any()
        if has_overlap :
            overlap+=1
            common_rides =  min_fatigue_rides[
            min_fatigue_rides.index.isin(max_power_rides.index)
            ]
            baseline_pow_list.append(common_rides["Average Watts"].mean())
            baseline_dist_list.append(common_rides["Distance"].mean())
            baseline_ele_list.append(common_rides["Elevation Gain"].mean())
            baseline_HR_list.append(common_rides["Average Heart Rate"].median())
        else :
            baseline = min_fatigue_rides.nlargest(1,"Average Watts")
            baseline_pow_list.append(baseline.iloc[0]["Average Watts"])
            baseline_dist_list.append(baseline.iloc[0]["Distance"])
            baseline_ele_list.append(baseline.iloc[0]["Elevation Gain"])
            baseline_HR_list.append(baseline.iloc[0]["Average Heart Rate"])
    return baseline_pow_list , baseline_dist_list , baseline_ele_list , baseline_HR_list , overlap

baseline_pow_list, baseline_dist_list, baseline_ele_list, baseline_HR_list, overlap = baseline_capp(df)

df["Baseline_Pow"] = baseline_pow_list
df["Baseline_Dist"] = baseline_dist_list
df["Baseline_Ele"] = baseline_ele_list
df["Baseline_HR"] = baseline_HR_list

print("Overlap" , overlap)

df["Current_Capacity"] = (
    df["Baseline_Pow"]
    - df["Cumulative_Fatigue"]
)

df["Capacity_Deviation"] = (
    df["Current_Capacity"]
    - df["Baseline_Pow"]
)

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
conn.close()

print(f"Updated {len(df)} prediction rows.")



   
