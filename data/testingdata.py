import pandas as pd;
import numpy as np;
from sklearn.preprocessing import MinMaxScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt


df=pd.read_csv("data/activities.csv",encoding="utf-8")

# print(df.columns.to_list())

cols_needed = [
    'Activity ID',
    'Activity Date',
    'Activity Type',
    'Elapsed Time',
    'Moving Time',
    'Distance',
    'Max Heart Rate',
    'Average Heart Rate',
    'Relative Effort',
    'Max Speed',
    'Average Speed',
    'Elevation Gain',
    'Elevation Loss',
    'Elevation Low',
    'Elevation High',
    'Max Grade',
    'Average Grade',
    'Average Watts',
    'Wind Speed',
    'Average Temperature',
    'Average Cadence'
    
]

df = df[cols_needed]



df=df[df["Activity Type"]=="Ride"]



df = df.dropna(subset=["Average Watts"])

df=df.dropna(subset=["Relative Effort"])

df["Average Temperature"] = df["Average Temperature"].fillna(
    df["Average Temperature"].rolling(5, min_periods=1).median()
)

df["Average Temperature"] = df["Average Temperature"].fillna(
    df["Average Temperature"].median()
)

df["Wind Speed"] = df["Wind Speed"].interpolate()

df["Wind Speed"] = df["Wind Speed"].bfill()

df["Wind Speed"] = df["Wind Speed"].ffill()

df["Average Cadence"] = df["Average Cadence"].interpolate()



df["Activity Date"]=pd.to_datetime(df["Activity Date"])


df=df[df["Moving Time"]>0]
df = df[df["Distance"] > 0]
df = df[df["Average Watts"] > 0]
df = df[df["Max Heart Rate"] > 0]
df = df[df["Average Heart Rate"] > 0]

cols = ["Average Speed", "Max Speed", "Max Grade"]

for col in cols:
    df[col] = df[col].replace(0, df[col].median())
 
df = df.sort_values("Activity Date", ascending=True).reset_index(drop=True)





# df.info()

print(df.head())

# df.to_csv("data/Cleaned_testing_data.csv",index=False)

