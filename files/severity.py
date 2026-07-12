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

df.to_csv("data/final_features.csv", index=False)
