import pandas as pd
import numpy as np
from fitparse import FitFile
import os

# -----------------------------
# LOAD FIT METADATA
# -----------------------------

df = pd.read_csv("data/Fit.csv", encoding="utf-8")

df["Date"] = pd.to_datetime(df["Date"])

df = df.sort_values("Date", ascending=True).reset_index(drop=True)

# meters → km
df["Distance"] = df["Distance"] / 1000

df["Date"] = df["Date"].dt.date

# -----------------------------
# LOAD CLEANED RIDE DATASET
# -----------------------------

df_og = pd.read_csv("data/Cleaned_testing_data.csv", encoding="utf-8")

df_og["Activity Date"] = pd.to_datetime(df_og["Activity Date"])

df_og["Activity Date"] = df_og["Activity Date"].dt.date

# -----------------------------
# MATCH FIT FILES
# -----------------------------

matched = {
    "final_fit": []
}

for i, row in df.iterrows():

    for j, roow in df_og.iterrows():

        if (
            row["Date"] == roow["Activity Date"]
            and np.isclose(row["Distance"], roow["Distance"], atol=3.0)
        ):

            matched["final_fit"].append(row["File"])

            print("Matched:", row["File"])

            break

# -----------------------------
# UNIQUE MATCHED FILES
# -----------------------------

unique_matches = list(set(matched["final_fit"]))

print("\nTotal Matches:", len(matched["final_fit"]))

print("Unique Matches:", len(unique_matches))

# -----------------------------
# PARSE RAW TELEMETRY
# -----------------------------

fit_folder = r"C:/Users/HARSH/OneDrive/Documents/fit"

all_ride_dfs = []

for i, filename in enumerate(unique_matches):

    print(f"\nProcessing Ride {i+1}/{len(unique_matches)}")

    full_path = os.path.join(fit_folder, filename)

    fit_data = {

        "ride_id": [],

        "timestamp": [],

        "position_lat": [],
        "position_long": [],

        "altitude": [],
        "enhanced_altitude": [],

        "distance": [],

        "speed": [],
        "enhanced_speed": [],

        "heart_rate": [],

        "cadence": [],
        "fractional_cadence": [],

        "power": [],
        "accumulated_power": [],

        "temperature": []
    }

    try:

        fitfile = FitFile(full_path)

        for record in fitfile.get_messages('record'):

            # temporary dictionary for ONE record
            row_data = {

                "ride_id": filename,

                "timestamp": None,

                "position_lat": None,
                "position_long": None,

                "altitude": None,
                "enhanced_altitude": None,

                "distance": None,

                "speed": None,
                "enhanced_speed": None,

                "heart_rate": None,

                "cadence": None,
                "fractional_cadence": None,

                "power": None,
                "accumulated_power": None,

                "temperature": None
            }

            for record_data in record:

                field_name = record_data.name

                if field_name in row_data:

                    row_data[field_name] = record_data.value

            # append one full row
            for key in fit_data.keys():

                fit_data[key].append(row_data[key])

        # create dataframe for THIS ride
        df_ride = pd.DataFrame(fit_data)

        all_ride_dfs.append(df_ride)

        print(f"Ride rows: {len(df_ride)}")

    except Exception as e:

        print(f"Error parsing {filename}")
        print(e)

# -----------------------------
# COMBINE ALL RIDES
# -----------------------------

final_df = pd.concat(all_ride_dfs, ignore_index=True)

print("\nFinal Combined Shape:")
print(final_df.shape)

print(final_df.head())

# -----------------------------
# SAVE FINAL TELEMETRY CSV
# -----------------------------

final_df.to_csv("All_Ride_Telemetry.csv", index=False)

print("\nTelemetry CSV Saved")