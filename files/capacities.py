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

df.to_csv("data/final_features.csv", index=False)



   
