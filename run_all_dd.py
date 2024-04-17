"""Runner script to compute degree day metrics for all stations in the WRCC dataset."""

import os
import pandas as pd
import compute_dd

csv_dir = "wrcc_station_csvs"

results = pd.DataFrame()
for filename in os.listdir(csv_dir):
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(os.path.join(csv_dir, filename))

            # compute the average of the 'tmax' and 'tmin' columns
            temp_ds = df[["tmax", "tmin"]].mean(axis=1)
            # compute the degree day metrics
            freezing_index = compute_dd.compute_cumulative_freezing_index(temp_ds)
            heating_degree_days = compute_dd.compute_cumulative_heating_degree_days(
                temp_ds
            )
            degree_days_below0F = compute_dd.compute_cumulative_degree_days_below_0F(
                temp_ds
            )
            thawing_index = compute_dd.compute_cumulative_thawing_index(temp_ds)

            station_id = filename.split(".")[0]
            results.loc[station_id, "WRCC Air Freezing Index Climatology"] = (
                freezing_index
            )
            results.loc[station_id, "WRCC Heating Degree Days Climatology"] = (
                heating_degree_days
            )
            results.loc[station_id, "WRCC Degree Days Below 0F Climatology"] = (
                degree_days_below0F
            )
            results.loc[station_id, "WRCC Air Thawing Index Climatology"] = (
                thawing_index
            )
            # will use this column to discard stations with insufficient data
            results.loc[station_id, "Median Years of Observations"] = (
                df["num_years"].median().astype(int)
            )
        except Exception as e:
            print(f"Failed to compute degree day metrics for station {filename}: {e}")
            continue

# write all results to a CSV file
results.to_csv("degree_day_metrics.csv")
