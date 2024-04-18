import pandas as pd
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
    """Get the SNAP community info from the API.

    Args:
        None
    Returns:
        dict: JSON response of SNAP-Communities(TM) from the API
    """
    response = requests.get("https://earthmaps.io/places/communities")
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Request failed with status code {response.status_code}")
        return None


def fetch_lat_lon_id(community_lookup, community_name):
    """Fetch the latitude, longitude, and ID for a given community if the name is in the lookup table that xrefs WRCC stations."""
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
    """Execute the delta bias correction for all metrics.

    CP Note: Most explicit implementation I could come up with, lots of deep nesting within the DataFrames and within the JSONs so beware. I sort of hate this function.
    Args:
        climo_df (pd.DataFrame): containing the WRCC climatologies
        future_df (pd.DataFrame): containing the future projections
    Returns:
        pd.DataFrame: containing the bias corrected future projections
    """
    bias_corrected_df = copy.deepcopy(future_df)
    # input data has columns for all metrics
    for metric in metrics:
        bc_outputs = []
        # climo_df, future_df have same index - iterating through locations
        for index, row in future_df.iterrows():
            # look up WRCC climo value for the metric
            wrcc_climo = climo_df.loc[index, f"WRCC {metrics[metric]}"]
            # initialize a new output dict
            output = {}
            for model in row[f"biased {metric} futures"].keys():
                output[model] = {}
                for scenario in row[f"biased {metric} futures"][model].keys():
                    output[model][scenario] = {}
                    # look up climo value for this model, scenario, and metric
                    model_scenario_climo = climo_df.loc[
                        index, f"{model} {scenario} {metrics[metric]}"
                    ]
                    for year in row[f"biased {metric} futures"][model][scenario].keys():
                        output[model][scenario][year] = {}
                        # calculate the bias corrected value
                        original_value = row[f"biased {metric} futures"][model][
                            scenario
                        ][year]["dd"]
                        # here be the important maths
                        bc_value = wrcc_climo + (original_value - model_scenario_climo)
                        if bc_value < 0:
                            bc_value = 0
                        output[model][scenario][year]["dd"] = int(bc_value)
            bc_outputs.append(output)
        bias_corrected_df[f"bias corrected {metric} futures"] = bc_outputs
    # remove the columns containing the original biased data
    for metric in metrics:
        bias_corrected_df = bias_corrected_df.drop(columns=[f"biased {metric} futures"])
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
    ].copy()
    for metric in metrics:
        # ping SNAP API for futures with full nested json pingpingping
        future_projections_df[f"biased {metric} futures"] = future_projections_df.apply(
            lambda row: get_future_degree_days_from_api(
                metric, row["SNAP Lat"], row["SNAP Lon"]
            ),
            axis=1,
        )

    # bias correct the future projections, this func runs all metrics
    bias_corrected_df = bias_correct_future_projections(snap_df, future_projections_df)
    for metric in metrics:
        # write both uncorrected and bias corrected nested dicts to JSON
        bias_corrected_df[
            [
                f"SNAP ID",
                f"bias corrected {metric} futures",
            ]
        ].to_json(f"bias_corrected_{metric}_future_projections.json", orient="records")

        future_projections_df[
            [
                f"SNAP ID",
                f"biased {metric} futures",
            ]
        ].to_json(f"uncorrected_{metric}_future_projections.json", orient="records")
    # saving these not required, but useful for debugging
    bias_corrected_df.to_csv("bias_corrected_future_projections.csv")
    future_projections_df.to_csv("uncorrected_future_projections.csv")
