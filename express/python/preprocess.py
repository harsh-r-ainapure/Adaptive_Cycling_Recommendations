import pandas as pd
import numpy as np

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
    "elevation_loss": "Elevation Loss",
})


df = df_activity.copy()

df["Activity Date"] = pd.to_datetime(df["Activity Date"])

df = df.sort_values("Activity Date").reset_index(drop=True)

df = df[df["Moving Time"] > 0]
df = df[df["Distance"] > 0]
df = df[df["Average Watts"] > 0]

cols = [
    "Average Speed"
]

for col in cols:
    df[col] = df[col].replace(
        0,
        df[col].median()
    )

df["Average Cadence"] = (
    df["Average Cadence"]
        .interpolate()
        .bfill()
        .ffill()
)
cursor = conn.cursor()

query = """
UPDATE activities
SET
    activity_date = %s,
    distance = %s,
    moving_time = %s,
    elapsed_time = %s,
    average_speed = %s,
    average_power = %s,
    average_hr = %s,
    max_hr = %s,
    average_cadence = %s,
    elevation_gain = %s,
    elevation_loss = %s
WHERE id = %s;
"""

for _, row in df.iterrows():

    cursor.execute(
        query,
        (
            row["Activity Date"],
            row["Distance"],
            row["Moving Time"],
            row["Elapsed Time"],
            row["Average Speed"],
            row["Average Watts"],
            row["Average Heart Rate"],
            row["Max Heart Rate"],
            row["Average Cadence"],
            row["Elevation Gain"],
            row["Elevation Loss"],
            row["Activity UUID"]
        )
    )

conn.commit()

cursor.close()

