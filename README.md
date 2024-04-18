# Bias Correction with WRCC Data

## About

Bias correct SNAP Data API degree day values via the delta method using Western Regional Climate Cooperative (WRCC) historical station data. This code will emit a nested JSON that mimics a typical SNAP Data API response.

## Run It

You can run this locally. Activate (and create if needed) the environment.

```sh
conda env create -f environment.yml
conda activate wrcc_bias_correct
```

Then run these commands in sequence to get the station data, compute the degree days, and execute the bias correction. There is a lot of API pinging, so this might take 5 minutes.

```sh
python scrape_all_stations.py
python run_all_dd.py
python bias_correct_with_wrcc.py
```

Then we need to clean up the JSON dump from Pandas like so:

```sh
python reformat_json_for_api.py
```

## Debug It

Scrape a single station using the WRCC ID - weird, one-off station configs are a probably failure mode.

````sh
python wrcc_station_scraper.py ak0280```
````
