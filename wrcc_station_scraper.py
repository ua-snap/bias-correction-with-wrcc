"""Scrape WRCC station data and write to CSV."""

import urllib.request
import csv
import re
import argparse
import os

from bs4 import BeautifulSoup


# regex for tabular data oh my
p = re.compile(
    r"^\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*([\-]?\d*[\.]?[\d]*)\s*$"
)


def get_station_data(station_id):
    """Get station data from WRCC.

    Note that WRCC is in the process of updating their data portal (spring 2024), so this URL might not work in the future.

    Args:
        station_id (str): WRCC station ID.
    Returns:
        list: List of strings containing tabular data.
    """
    # url is for 1981-2010 normals
    url = f"https://wrcc.dri.edu/cgi-bin/cliNORM2010t.pl?{station_id}"
    f = urllib.request.urlopen(url)
    html_doc = f.read()
    soup = BeautifulSoup(html_doc, "html.parser")
    site_rows = soup.pre.contents[0].splitlines()
    site_rows = site_rows[3:]  # number header lines may vary - beware
    return site_rows


def write_wrcc_data_to_csv(site_rows, station_id):
    """Write WRCC station data to CSV.

    Args:
        site_rows (list): List of strings containing tabular data.
        station_id (str): WRCC station ID.
    Returns:
        None
    """
    if not os.path.exists("wrcc_station_csvs"):
        os.makedir("wrcc_station_csvs")
    with open("station_lookup.csv", newline="") as csvfile:
        reader = csv.reader(csvfile, delimiter=",")
        for row in reader:
            out_csv_filename = station_id + ".csv"
            with open("wrcc_station_csvs/%s" % out_csv_filename, "w") as output_csvfile:
                writer = csv.writer(output_csvfile, delimiter=",")
                writer.writerow(
                    [
                        "doy",
                        "month",
                        "day",
                        "tmax",
                        "num_years",
                        "tmin",
                        "num_years",
                        "precip",
                        "num_years",
                        "sdmax",
                        "sdmin",
                    ]
                )
                for site_row in site_rows:
                    matches = p.match(site_row)
                    # example row:
                    #   349 12 14   39.4  26.   31.3  26.  0.637  26.  6.079  6.576
                    if matches:
                        writer.writerow(
                            [
                                matches.group(1),
                                matches.group(2),
                                matches.group(3),
                                matches.group(4),
                                matches.group(5),
                                matches.group(6),
                                matches.group(7),
                                matches.group(8),
                                matches.group(9),
                                matches.group(10),
                                matches.group(11),
                            ]
                        )
            break


def scrape_and_write_station_data(station_id):
    """Scrape WRCC station data and write to CSV."""
    station_data = get_station_data(station_id)
    write_wrcc_data_to_csv(station_data, station_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("station_id", help="Station ID")
    args = parser.parse_args()
    scrape_and_write_station_data(args.station_id)
