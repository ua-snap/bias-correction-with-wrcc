"""A runner script to scrape all WRCC stations in the station_lookup.csv file."""

import pandas as pd
import time

from wrcc_station_scraper import scrape_and_write_station_data

df = pd.read_csv("station_lookup.csv")

for station_id in df["WRCC ID"]:
    try:
        scrape_and_write_station_data(station_id)
    except Exception as e:
        print(f"Failed to scrape station {station_id}: {e}")
        continue
    time.sleep(1)  # be nice to the server
