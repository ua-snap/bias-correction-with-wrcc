import pandas as pd
import numpy as np
import requests
import copy

metrics = {
    "heating": "Heating Degree Days Climatology",
    "freezing_index": "Air Freezing Index Climatology",
    "thawing_index": "Air Thawing Index Climatology",
    "below_zero": "Degree Days Below 0F Climatology",
}
wrcc_yr_threshold = 20


def get_latlons_from_snap_api():
    response = requests.get("https://earthmaps.io/places/communities")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None


def fetch_lat_lon_id(community_lookup, community_name):
    for item in community_lookup:
        if item["name"] == community_name:
            return pd.Series((item["latitude"], item["longitude"], item["id"]))
    return pd.Series((None, None, None))


def get_historical_degree_days_from_api(metric, lat, lon):
    historical_request = (
        f"http://development.earthmaps.io/degree_days/{metric}/{lat}/{lon}/1981/2010"
    )

    historical_response = requests.get(historical_request)
    if historical_response.status_code == 200:
        historical = historical_response.json()
        degree_day_climos = {}

        for model, scenarios in historical.items():
            for scenario, years in scenarios.items():
                total = 0
                count = 0
                for year, values in years.items():
                    total += values["dd"]
                    count += 1
                degree_day_climos[f"{model} {scenario} {metrics[metric]}"] = round(
                    total / count
                )
        return degree_day_climos
    else:
        print(f"Request failed with status code {historical_response.status_code}")
        return None


def get_future_degree_days_from_api(metric, lat, lon):
    future_request = (
        f"http://development.earthmaps.io/degree_days/{metric}/{lat}/{lon}/2020/2099"
    )

    future_response = requests.get(future_request)
    if future_response.status_code == 200:
        return future_response.json()
    else:
        print(f"Request failed with status code {future_response.status_code}")
        return None


def bias_correct_future_projections(climo_df, future_df):
    # Create a new DataFrame to store the bias corrected future projections
    # This DataFrame will have the same columns as the future_df
    # but with the values replaced with the bias corrected values
    # we need to iterate over each row in the both climo_df and future_df (these will have the same index)
    # and then we need to iterate through the nested dict in the future_df that contains projecte values for each model, scenario, and year
    # and then look up the climo value for that model, scenario, and metric in the climo_df
    # and then calculate the bias corrected value by adding the difference between the climo value and the modeled value to the projected value
    # and then replace the projected value with the bias corrected value in the future_df
    # and then return the future_df

    bias_corrected_df = copy.deepcopy(future_df)
    for metric in metrics:
        for index, row in future_df.iterrows():
            wrcc_climo = climo_df.loc[index, f"WRCC {metrics[metric]}"]
            for model, scenarios in row[f"biased {metric} futures"].items():
                for scenario, years in scenarios.items():
                    model_scenario_climo = climo_df.loc[
                        index, f"{model} {scenario} {metrics[metric]}"
                    ]
                    for year, values in years.items():
                        corrected_value = wrcc_climo + (
                            values["dd"] - model_scenario_climo
                        )
                        # replace the projected value with the bias corrected value
                        bias_corrected_df.loc[index, f"biased {metric} futures"][model][
                            scenario
                        ][year] = corrected_value
    # rename the columns in bias_corrected_df to remove the 'biased' prefix
    bias_corrected_df.columns = [
        col.replace("biased ", "bias_corrected") for col in bias_corrected_df.columns
    ]
    return bias_corrected_df


if __name__ == "__main__":
    # get precomputed WRCC degree day climatologies
    wrcc_df = pd.read_csv("degree_day_metrics.csv")
    # drop those where record is not long enough
    wrcc_df = wrcc_df[
        wrcc_df["Median Years of Observations"] >= wrcc_yr_threshold
    ].rename(columns={"Unnamed: 0": "WRCC ID"})

    # add in the SNAP community info so we can ping the API
    station_lu = pd.read_csv("station_lookup.csv")
    snap_df = pd.merge(station_lu, wrcc_df)
    communities = get_latlons_from_snap_api()
    snap_df[["SNAP Lat", "SNAP Lon", "SNAP ID"]] = snap_df["SNAP Name"].apply(
        lambda x: fetch_lat_lon_id(communities, x)
    )

    # grab historical degree days climo value from the API
    for k in metrics.keys():
        snap_df[f"historical {k}"] = snap_df.apply(
            lambda row: get_historical_degree_days_from_api(
                k, row["SNAP Lat"], row["SNAP Lon"]
            ),
            axis=1,
        )
        snap_df = snap_df.join(
            pd.DataFrame(snap_df[f"historical {k}"].to_list(), index=snap_df.index)
        )
        snap_df = snap_df.drop(columns=[f"historical {k}"])

    # get the future projections from the API
    # don't strictly need a new dataframe here but it makes for easier debug
    future_projections_df = snap_df[
        ["WRCC Name", "SNAP Name", "WRCC ID", "SNAP Lat", "SNAP Lon", "SNAP ID"]
    ]
    for metric in metrics:
        # will have columns like biased freezing_index futures containing the full nested dict json response from the snap data api
        future_projections_df[f"biased {metric} futures"] = future_projections_df.apply(
            lambda row: get_future_degree_days_from_api(
                metric, row["SNAP Lat"], row["SNAP Lon"]
            ),
            axis=1,
        )

    # bias correct the future projections
    bias_corrected_df = bias_correct_future_projections(snap_df, future_projections_df)
    # for each metric, write the bias corrected nested dict to a JSON file
    for metric in metrics:
        bias_corrected_df[
            [
                f"WRCC Name",
                f"SNAP Name",
                f"WRCC ID",
                f"SNAP ID",
                f"bias corrected {metric} futures",
            ]
        ].to_json(f"bias_corrected_{metric}_future_projections.json", orient="records")
        future_projections_df[
            [
                f"WRCC Name",
                f"SNAP Name",
                f"WRCC ID",
                f"SNAP ID",
                f"biased {metric} futures",
            ]
        ].to_json(f"uncorrected_{metric}_future_projections.json", orient="records")

    bias_corrected_df.to_csv("bias_corrected_future_projections.csv")
    future_projections_df.to_csv("uncorrected_future_projections.csv")
