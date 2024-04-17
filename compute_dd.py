"""Module for computing degree day metrics from scraped WRCC station data."""


def summarize_year_dd(temp_ds, temp_threshold, count_days_below_threshold):
    """Summarize the degree days for a year.

    Use boolean variable (`count_days_below_threshold`) to specify that the degree days
    below the threshold should be counted (case for heating, below 0 F, and freezing index.

    Args:
        temp_ds (pandas.Series): Daily average temperature data in F.
        temp_threshold (int): Temperature threshold in F.
        count_days_below_threshold (bool): Whether to count days below the threshold.
    Returns:
        int: Cumulative degree days.
    """
    dd_count = 0
    for day_temp in temp_ds:
        if count_days_below_threshold:
            degree_delta = temp_threshold - day_temp
        else:
            # Otherwise, count degree days above some threshold
            degree_delta = day_temp - temp_threshold
        if degree_delta < 0:
            degree_delta = 0
        dd_count += degree_delta
    return int(round(dd_count))


def compute_cumulative_freezing_index(temp_ds):
    air_freezing_index = summarize_year_dd(temp_ds, 32, True)
    return air_freezing_index


def compute_cumulative_heating_degree_days(temp_ds):
    heating_degree_days = summarize_year_dd(temp_ds, 65, True)
    return heating_degree_days


def compute_cumulative_degree_days_below_0F(temp_ds):
    degree_days_below0F = summarize_year_dd(temp_ds, 0, True)
    return degree_days_below0F


def compute_cumulative_thawing_index(temp_ds):
    air_thawing_index = summarize_year_dd(temp_ds, 32, False)
    return air_thawing_index
