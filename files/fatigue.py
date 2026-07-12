import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import xgboost as xg
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import cross_val_predict

df = pd.read_csv("data/final_features.csv")

# -----------------------------
# MODEL
# -----------------------------

df["Cadence Ratio"] = (df["Average Cadence"] / (df["cadence_sd"] + 1e-6))
df["Heart Ratio"] = (df["Average Heart Rate"] / (df["HR SD"] + 1e-6))
df["ELE Ratio"] = (df["Elevation Gain"] / (df["ELE SD"] + 1e-6))

df["ELE Ratio"] = df["ELE Ratio"].fillna(0)

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


results = cross_val_predict(
    model,
    X,
    Y,
    cv=5
)

model.fit(X, Y)

error = mean_absolute_error(
    Y,
    results
)

print("Error :", error)

scores = cross_val_score(
    model,
    X,
    Y,
    cv=5,
    scoring="r2"
)

print("CV Scores :", scores)
print("Mean CV Score :", scores.mean())



# -----------------------------
# FEATURE IMPORTANCE
# -----------------------------

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

df["Estimated Power"] = results
print(feature_importance)

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

df.to_csv("data/final_features.csv", index=False)






   




