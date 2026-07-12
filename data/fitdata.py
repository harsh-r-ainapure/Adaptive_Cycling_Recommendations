from fitparse import FitFile
import os
import pandas as pd

folder = r"C:/Users/HARSH/OneDrive/Documents/fit"

fit_files = []

for file in os.listdir(folder):

    if file.endswith(".fit"):

        full_path = os.path.join(folder, file)

        fit_files.append(full_path)

print(f"Total FIT files: {len(fit_files)}")

data = {
    "File": [],
    "Date": [],
    "Distance": []
}

failed_files = []

for i, address in enumerate(fit_files):

    print(f"Processing {i+1}/{len(fit_files)} : {os.path.basename(address)}")

    try:

        fitfile = FitFile(address)

        start_time = None
        total_distance = None

        for record in fitfile.get_messages('session'):

            for record_data in record:

                if record_data.name == "start_time":
                    start_time = record_data.value

                if record_data.name == "total_distance":
                    total_distance = record_data.value

        data["File"].append(os.path.basename(address))
        data["Date"].append(start_time)
        data["Distance"].append(total_distance)

    except Exception as e:

        print(f"Error parsing file: {os.path.basename(address)}")
        print(e)

        failed_files.append(address)

fit_df = pd.DataFrame(data)

fit_df.to_csv("Fit.csv", index=False)

print("\nParsing Complete")
print(f"Successful files: {len(fit_df)}")
print(f"Failed files: {len(failed_files)}")

print("\nFailed Files:")
for file in failed_files:
    print(file)

print("\nPreview:")
print(fit_df.head())

