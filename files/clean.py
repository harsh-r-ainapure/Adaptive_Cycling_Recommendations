import pandas as pd

df = pd.read_csv("data/final_features.csv")

print("Before:", len(df))

df = df.iloc[:214]

print("After:", len(df))

df.to_csv(
    "data/final_features.csv",
    index=False
)

print("Done")