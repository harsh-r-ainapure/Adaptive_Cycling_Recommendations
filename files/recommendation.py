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

df["Percent_Change"] = (
    df["Capacity_Deviation"]
    / df["Baseline_Pow"]
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

df.to_csv("data/final_features.csv", index=False)


