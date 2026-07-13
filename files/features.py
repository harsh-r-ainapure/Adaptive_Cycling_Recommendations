import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import xgboost as xg
import numpy as np

# LOAD DATA

df = pd.read_csv(
    "data/Cleaned_testing_data.csv",
    encoding="utf-8"
)

df_fit = pd.read_csv(
    "data/All_Ride_Telemetry.csv",
    encoding="utf-8"
)

fit_meta = pd.read_csv(
    "data/Fit.csv",
    encoding="utf-8"
)

print(df_fit.columns.tolist())
print(df_fit["power"].describe())
print(
    (df_fit["power"] == 0).sum()
)

# PREP FIT METADATA

fit_meta["Date"] = pd.to_datetime(
    fit_meta["Date"]
)

fit_meta["Date"] = (
    fit_meta["Date"].dt.date
)

fit_meta["Distance"] = (
    fit_meta["Distance"] / 1000
)

# PREP ORIGINAL DATASET

df = df[
    df["Activity ID"] != 790
]

df = df[
    df["Activity ID"] != 789
]

df["Activity Date"] = pd.to_datetime(
    df["Activity Date"]
)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True)

df["Activity Date"] = (
    df["Activity Date"].dt.date
)

# CREATE TRUE FIT TO RIDE MAPPING

fit_meta = fit_meta.sort_values(
    "Date"
).reset_index(drop=True)

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True)

mapping = {
    "ride_id": [],
    "Activity ID": []
}

#  Prevent duplicate assignments 
used_activity_ids = set()

for i, row in fit_meta.iterrows():

    best_match = None
    best_error = np.inf

    for j, roow in df.iterrows():

        #  Skip already used rides 
        if roow["Activity ID"] in used_activity_ids:
            continue

        #  Match same date
        if row["Date"] == roow["Activity Date"]:

            distance_error = abs(
                row["Distance"]
                -
                roow["Distance"]
            )

            #  Accept only close distances 
            if distance_error <= 1:

                
                if distance_error < best_error:

                    best_error = distance_error
                    best_match = roow["Activity ID"]

    # Save best match
    if best_match is not None:

        mapping["ride_id"].append(
            row["File"]
        )

        mapping["Activity ID"].append(
            best_match
        )

        used_activity_ids.add(
            best_match
        )

mapping_df = pd.DataFrame(mapping)

# MERGE TRUE IDS INTO TELEMETRY

df_fit = df_fit.merge(

    mapping_df,

    on="ride_id",

    how="left"

)

power_check = (
    df_fit
    .groupby("Activity ID")
    .agg(
        Total_Seconds=("power", "size"),
        Nonzero_Power_Seconds=("power", lambda x: (x > 0).sum()),
        Mean_Power=("power", "mean"),
        Max_Power=("power", "max")
    )
    .reset_index()
)

# Percentage with real power
power_check["Power_Availability_Percent"] = (
    power_check["Nonzero_Power_Seconds"]
    /
    (power_check["Total_Seconds"] + 1e-6)
) * 100

#  Add ride dates 
power_check = power_check.merge(
    df[
        ["Activity ID", "Activity Date"]
    ],
    on="Activity ID",
    how="left"
)

print(
    power_check.sort_values(
        "Activity Date"
    ).tail(100)
)

valid_id = power_check[power_check["Power_Availability_Percent"]>10]["Activity ID"]
df  = df[df["Activity ID"].isin(valid_id)]
df_fit = df_fit[df_fit["Activity ID"].isin(valid_id)]

df.info()
df_fit.info()

df = df.sort_values(
    "Activity Date"
).reset_index(drop=True)

# FEATURE ENGINEERING

df["VAM"] = (

    df["Elevation Gain"]

    /

    (
        (df["Moving Time"] + 1e-6)
        / 3600
    )

) * df["Average Grade"]


df["Rel Speed"] = (
    df["Max Speed"]
    /
    df["Average Speed"]
)

# HR SD FEATURE

hr_sd = (

    df_fit.groupby(
        "Activity ID"
    )["heart_rate"]

    .std()

    .reset_index()

)

hr_sd = hr_sd.rename(
    columns={
        "heart_rate": "HR SD"
    }
)

df = df.merge(

    hr_sd,

    on="Activity ID",

    how="left"

)

ele_sd =( df_fit.groupby("Activity ID")["altitude"].std().reset_index())
ele_sd = ele_sd.rename(columns={"altitude":"ELE SD"})
df = df.merge(
    ele_sd,
    on="Activity ID",
    how="left"
)

cadence_sd = (df_fit.groupby("Activity ID")["cadence"].std().reset_index())
cadence_sd = cadence_sd.rename(columns={"cadence":"cadence_sd"})
df = df.merge(
    cadence_sd,
    on="Activity ID",
    how="left"
)


df_fit["ELE_ROLL_AVG"] =  (
    df_fit.groupby("Activity ID")["altitude"]
    .rolling(window=20, min_periods=1)
    .mean()
    .reset_index(level=0, drop=True)
)

df_fit["DIST_ROLL_AVG"] = (
    df_fit.groupby("Activity ID")["distance"]
    .rolling(window=20, min_periods=1)
    .mean()
    .reset_index(level=0, drop=True)
)

df_fit["ELE_DIFF"] = (
    df_fit.groupby("Activity ID")["ELE_ROLL_AVG"]
    .diff()
)

df_fit["DIST_DIFF"] = (
    df_fit.groupby("Activity ID")["DIST_ROLL_AVG"]
    .diff()
)

df_fit["Gradient"] = (
    df_fit["ELE_DIFF"]
    /
    (df_fit["DIST_DIFF"] + 1e-6)
) * 100

#  Remove infinities 
df_fit["Gradient"] = df_fit["Gradient"].replace(
    [np.inf, -np.inf],
    np.nan
)

df_fit["Gradient"] = (df_fit["Gradient"].fillna(df_fit.groupby("Activity ID")["Gradient"].transform(lambda x: x.fillna(
    x.rolling(20,min_periods=1,center=True).median()
))))

df_fit["Gradient"] = df_fit["Gradient"].clip(upper=8,lower=-8)

df_fit["Gradient"] = df_fit["Gradient"] * df_fit["enhanced_speed"]

gradient_feature = (
    df_fit.groupby("Activity ID")["Gradient"]
    .std()
    .reset_index()
)

# Merge into main dataframe 
df = df.merge(
    gradient_feature,
    on="Activity ID",
    how="left"
)


CAD_subset_start = (
    (
        df_fit["cadence"]
        /
        (df_fit["heart_rate"] + 1e-6)
    )
    .groupby(df_fit["Activity ID"])
    .apply(
        lambda x:
        x.iloc[
            int(len(x)*0.10):
            int(len(x)*0.20)
        ].median()
    )
)

CAD_subset_end = (
    (
        df_fit["cadence"]
        /
        (df_fit["heart_rate"] + 1e-6)
    )
    .groupby(df_fit["Activity ID"])
    .apply(
        lambda x:
        x.iloc[
            int(len(x)*0.85):
            int(len(x)*0.95)
        ].median()
    )
)

CAD_diff = (
    (
        CAD_subset_start
        -
        CAD_subset_end
    )
    /
    CAD_subset_start
) * 100

CAD_diff = CAD_diff.clip(
    lower=-100,
    upper=100
)

CAD_diff = CAD_diff.reset_index(
    name="Cadence_Drift"
)

df = df.merge(
    CAD_diff,
    on="Activity ID",
    how="left"
)

# WORKING HR

working_hr = (
    df_fit[
        (
            (df_fit["cadence"] > 0)
            &
            (df_fit["enhanced_speed"] > 3)
        )
    ]
    .groupby("Activity ID")["heart_rate"]
    .mean()
    .reset_index(name="Working_HR")
)


# ROLLING / COASTING FEATURES

rolling_mask = (
    (df_fit["cadence"] == 0)
    &
    (df_fit["enhanced_speed"] > 3)
)

#  Rolling seconds
rolling_seconds = (
    df_fit[rolling_mask]
    .groupby("Activity ID")
    .size()
    .reset_index(name="Rolling_Seconds")
)

#  Total telemetry seconds 
total_seconds = (
    df_fit
    .groupby("Activity ID")
    .size()
    .reset_index(name="Total_Seconds")
)

#  Merge totals 
rolling_features = rolling_seconds.merge(
    total_seconds,
    on="Activity ID",
    how="left"
)

#  Rolling percentage 
rolling_features["Rolling_Percent"] = (
    rolling_features["Rolling_Seconds"]
    /
    (rolling_features["Total_Seconds"] + 1e-6)
) * 100



rolling_blocks = df_fit[rolling_mask].copy()

hr_recovery_slope = (
    rolling_blocks
    .groupby("Activity ID")[["heart_rate"]]
    .apply(
        lambda x:
        (
            x["heart_rate"].iloc[-1]
            -
            x["heart_rate"].iloc[0]
        )
        /
        (len(x) + 1e-6)
    )
    .reset_index(name="HR_Recovery_Slope")
)
# Merge slope
rolling_features = rolling_features.merge(
    hr_recovery_slope,
    on="Activity ID",
    how="left"
)

rolling_features = rolling_features[
    [
        "Activity ID",
        "Rolling_Percent",
        "HR_Recovery_Slope"
    ]
]

#  Merge into main dataframe 
df = df.merge(
    rolling_features,
    on="Activity ID",
    how="left"
)


df["Rolling_Percent"] = (
    df["Rolling_Percent"]
    .fillna(0)
)

df["HR_Recovery_Slope"] = (
    df["HR_Recovery_Slope"]
    .fillna(
        df["HR_Recovery_Slope"].mean()
    )
)

stopping_mask = (
    (df_fit["cadence"] == 0)
    &
    (df_fit["enhanced_speed"] < 0.5)
)

#  Stopping seconds 
stopping_seconds = (
    df_fit[stopping_mask]
    .groupby("Activity ID")
    .size()
    .reset_index(name="Stopping_Seconds")
)

#  Merge totals 
stopping_features = stopping_seconds.merge(
    total_seconds,
    on="Activity ID",
    how="left"
)

# Stopping percentage 
stopping_features["Stopping_Percent"] = (
    stopping_features["Stopping_Seconds"]
    /
    (stopping_features["Total_Seconds"] + 1e-6)
) * 100

stopping_hr = (
    df_fit[stopping_mask]
    .groupby("Activity ID")["heart_rate"]
    .mean()
    .reset_index(name="Stopping_HR")
)

# Merge HRs 
stopping_features = stopping_features.merge(
    stopping_hr,
    on="Activity ID",
    how="left"
)

stopping_features = stopping_features.merge(
    working_hr,
    on="Activity ID",
    how="left"
)

# HR recovery percentage 
stopping_features["Stop_HR_Recovery_Percent"] = (
    (
        stopping_features["Working_HR"]
        -
        stopping_features["Stopping_HR"]
    )
    /
    (stopping_features["Working_HR"] + 1e-6)
) * 100


stopping_features = stopping_features[
    [
        "Activity ID",
        "Stopping_Percent",
        "Stop_HR_Recovery_Percent"
    ]
]

df = df.merge(
    stopping_features,
    on="Activity ID",
    how="left"
)

df["Stopping_Percent"] = (
    df["Stopping_Percent"]
    .fillna(0)
)

df["Stop_HR_Recovery_Percent"] = (
    df["Stop_HR_Recovery_Percent"]
    .fillna(
        df["Stop_HR_Recovery_Percent"].mean()
    )
)


# Convert 'Activity Date' back to a true pandas datetime object
# otherwise rolling('56D') expects an integer row count and throws an error
df["Activity Date"] = pd.to_datetime(df["Activity Date"])

# Ensure perfect chronological ordering for calendar windowing
df = df.sort_values("Activity Date").reset_index(drop=True)

# 56-day true calendar rolling baseline metric saved directly to df
df["baseline_hr"] = (
    df
    .rolling(
        window="56D",
        on="Activity Date",
        min_periods=5
    )["Average Heart Rate"]
    .median()
)

# Backfill initial edge rows where the historical 5-ride cutoff hasn't been met yet
df["baseline_hr"] = df["baseline_hr"].fillna(df["Average Heart Rate"].median())

# Merge the clean baseline column into the telemetry dataframe for stream matching
df_fit = df_fit.merge(
    df[["Activity ID", "baseline_hr"]],
    on="Activity ID",
    how="left"
)

# Quantify relative cardiorespiratory stress index
df_fit["Relative_HR"] = df_fit["heart_rate"] / (df_fit["baseline_hr"] + 1e-6)

# Map zone boundaries using individual historical strain context
recovery_zone = (
    (df_fit["Relative_HR"] < 1.05)
    .groupby(df_fit["Activity ID"])
    .mean() * 100
).reset_index(name="Recovery_Zone_Percent")

power_zone = (
    (df_fit["Relative_HR"] >= 1.05)
    .groupby(df_fit["Activity ID"])
    .mean() * 100
).reset_index(name="Power_Zone_Percent")

# Merge zone distribution profiles into main dataframe
df = df.merge(recovery_zone, on="Activity ID", how="left").fillna({"Recovery_Zone_Percent": 0})
df = df.merge(power_zone, on="Activity ID", how="left").fillna({"Power_Zone_Percent": 0})

df["Gradient"] = df["Gradient"].fillna(0)
df["ELE SD"] = df["ELE SD"].fillna(0)
df["Cadence_Drift"] = df["Cadence_Drift"].fillna(df["Cadence_Drift"].median())                                     

df = df.replace(
    [np.inf, -np.inf],
    np.nan
)

df.to_csv("data/final_features.csv", index=False)