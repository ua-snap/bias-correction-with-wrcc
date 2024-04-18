# Bias Correction with WRCC Data

## About

## Run It

You can run this locally. Activate the environment.

Then run these commands in sequence to get the station data, compute the degree days, and execute the bias correction. There is a lot of API pinging, so this might take 5 minutes.

```sh
python scrape_all_stations.py
python run_all_dd.py
python bias_correct_with_wrcc.py
```

## Debug It

Scrape a single station using the WRCC ID - weird, one-off station configs are a probably failure mode.

````sh
python wrcc_station_scraper.py ak0280```
````
