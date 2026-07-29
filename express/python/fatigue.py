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

df = df_activity.merge(
    df_features,
    left_on="Activity UUID",
    right_on="activity_id",
    how="inner"
)


X = df[[
    "Gradient",
    "Average Cadence",
    "Average Heart Rate",
    "Rel Speed",
    "HR SD",
    "Heart Ratio",
    "Cadence Ratio",
    "ELE Ratio",
    "HR_Recovery_Slope",
    "Rolling_Percent",
    "Stopping_Percent",
    "Power_Zone_Percent",
    "Recovery_Zone_Percent",
    "baseline_hr",
]]

Y = df["Average Watts"]

model = xg.XGBRegressor(
max_depth=5,       
    learning_rate=0.05, 
    subsample=0.8,     
    random_state=42

)

model.fit(X, Y)

print(X.dtypes)

print(df[[
    "Heart Ratio",
    "Cadence Ratio",
    "ELE Ratio"
]].head(10))

df["Estimated Power"] = model.predict(X)

importance = model.feature_importances_

feature_importance = pd.DataFrame({

    "Feature": X.columns,

    "Importance": importance

})

feature_importance = (
    feature_importance
    .sort_values(
        by="Importance",
        ascending=False
    )
)


df["Fatigue"] = (((df["Estimated Power"] - df["Average Watts"])))

print(df["Fatigue"])

outliers = df[
    abs(df["Fatigue"]) > 24
]

print(
    outliers[
        [
            "Activity Date",
            "Distance",
            "Moving Time",
            "Average Watts",
            "Estimated Power",
            "Fatigue"
        ]
    ]
)

print(
    outliers["Distance"].describe()
)

print(
    outliers["Moving Time"].describe()
)


df["Activity Date"] = pd.to_datetime(
    df["Activity Date"]
)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True)

def cum_fat_cal (df,k=0.15) :
 
 cum_fat = []
 for i in range(0,len(df)):
   curr_date = df.loc[i,"Activity Date"]
   cut_off_date = curr_date - pd.Timedelta(days=14)
   rides = df.iloc[:i+1]

   rides = rides[
    rides["Activity Date"] >= cut_off_date
    ]
   
   days = (curr_date - rides["Activity Date"]).dt.days
   
   fatigue_sum = 0
   for j in range (0,len(rides)):
     decay = np.exp(-k * days.iloc[j])
     fatigue_sum += (
                rides.iloc[j]["Fatigue"]
                * decay
            )
   cum_fat.append(fatigue_sum)
            
 return cum_fat 

df["Cumulative_Fatigue"] = (
    cum_fat_cal(df)
)

print(
    df[
        [
            "Activity Date",
            "Fatigue",
            "Cumulative_Fatigue"
        ]
    ]
)

print(
    df["Cumulative_Fatigue"].describe()
)

print(
    df.loc[
        df["Cumulative_Fatigue"].idxmin()
    ]
)

print(
    df.loc[
        df["Cumulative_Fatigue"].idxmax()
    ]
)

print(
    (abs(df["Fatigue"]) > 24).sum()
)

print(
    (abs(df["Fatigue"]) > 24).mean()
)

idx = df["Cumulative_Fatigue"].idxmin()

print(
    df.loc[idx-10:idx,
        [
            "Activity Date",
            "Average Watts",
            "Estimated Power",
            "Fatigue",
            "Cumulative_Fatigue"
        ]
    ]
)

cursor = conn.cursor()

query4 = """
INSERT INTO predictions (
    activity_id,
    estimated_power,
    fatigue,
    cumulative_fatigue
)
VALUES (%s, %s, %s, %s)
ON CONFLICT (activity_id)
DO UPDATE SET
    estimated_power = EXCLUDED.estimated_power,
    fatigue = EXCLUDED.fatigue,
    cumulative_fatigue = EXCLUDED.cumulative_fatigue;
"""

for _, row in df.iterrows():
    cursor.execute(
        query4,
        (
            row["Activity UUID"],
            float(row["Estimated Power"]),
            float(row["Fatigue"]),
            float(row["Cumulative_Fatigue"])
        )
    )

conn.commit()

cursor.close()
conn.close()

print(f"Saved {len(df)} prediction rows.")








   




