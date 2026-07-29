import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
import xgboost as xg
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import cross_val_score

df = pd.read_csv("data/final_features.csv")

# -----------------------------
# MODEL
# -----------------------------

df["Cadence Ratio"] = (df["Average Cadence"] / (df["cadence_sd"] + 1e-6))
df["Heart Ratio"] = (df["Average Heart Rate"] / (df["HR SD"] + 1e-6))
df["ELE Ratio"] = (df["Elevation Gain"] / (df["ELE SD"] + 1e-6))

df["ELE Ratio"] = df["ELE Ratio"].fillna(0)

df.info()

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

X_train, X_test, Y_train, Y_test = train_test_split(

    X,
    Y,

    test_size=0.2,

    random_state=42

)


model = xg.XGBRegressor(
max_depth=5,       
    learning_rate=0.05, 
    subsample=0.8,     
    random_state=42

)

model.fit(
    X_train,
    Y_train
)

results = model.predict(X_test)

error = mean_absolute_error(
    Y_test,
    results
)

print("Error :", error)

print(
    "Score :",
    model.score(X_test, Y_test)
)

# FEATURE IMPORTANCE

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

print(feature_importance)





