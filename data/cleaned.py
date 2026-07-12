import pandas as pd;
import numpy as np;


df=pd.read_csv("data/activities.csv",encoding="utf-8")

print(df.columns.to_list())

print(df.shape)

print(df.isnull().sum())

print(df.describe())

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
    'Relative Effort',
    'Average Temperature',
    'Average Cadence',
    'Wind Speed',
    'Weather Temperature',
    'Weather Pressure',
    'Average Elapsed Speed',
    'Max Speed'
]

df = df[cols_needed]




df=df[df["Activity Type"]=="Ride"]



df = df.dropna(subset=["Average Watts"])

df["Average Temperature"] = df["Average Temperature"].fillna(
    df["Average Temperature"].rolling(5, min_periods=1).median()
)

# df = df.drop(columns=[
#     "Max Heart Rate",
#     "Average Heart Rate",
#     # "Relative Effort",
#     "Activity ID"
# ])

df["Activity Date"]=pd.to_datetime(df["Activity Date"])


df=df[df["Moving Time"]>0]
df = df[df["Distance"] > 0]
df = df[df["Average Watts"] > 0]

cols = ["Average Speed", "Max Speed", "Max Grade"]

for col in cols:
    df[col] = df[col].replace(0, df[col].median())
 
df = df.sort_values("Activity Date", ascending=True).reset_index(drop=True)

df["Activity ID"] = range(len(df), 0, -1)


from scipy import stats

# Remove missing values
distance = df['Distance'].dropna()

# Population mean from your descriptive statistics
mu = 27.33

# One-sample t-test
t_stat, p_value = stats.ttest_1samp(distance, popmean=mu)

print("T-statistic:", t_stat)
print("P-value:", p_value)

alpha = 0.05

if p_value < alpha:
    print("Reject H0")
else:
    print("Fail to reject H0")


# # df.to_csv("data/Cleaned_data.csv",index=False)




