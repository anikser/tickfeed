# TickFeed

## Pre-requisites

1. Postgres

2. Python >= 3.11

3. An environment with requirements.txt satisfied. An environment manager (e.g venv, conda) is recommended.

## Setup

1. Execute the sql files in `ddl/`` in Postgres.
2. Configure postgres connectivity in `postgres_cfg`` in `tickfeed/aggregation/daily/dao.py`. 
    - Proper practice would be to move this out to a config file (e.g. JSON, YAML, TOML), and pass the path in as a command line argument. The password should not be checked in, and should integrate with a standardized secret management system/convention.

## CLI

This tool's functionality is exposed in a CLI (`tickfeed.py`) There are three commands exposed.

1. `listen`
    - This starts the feed listener, registering callbacks that:
        1. Write each update's raw data to flat files
        2. Upon crossing over to the next UTC day, calculates aggregate statistics for the previous day and writes a row to the `bookticker_daily` table.
2. `backfill`
    - This accepts an exchange, symbol, and date range, and backfills the daily aggregate statistics from raw data.
    - The typical use case for this is to populate new columns added to `bookticker_daily`, but it can also be used in the case of some database failure.
3. `data`
    - This accepts a list of exchanges, symbols, and a date range, and prints the summary of the resulting DataFrame constructed from querying the table. 
    - This demonstrates the functionality of the wrapper `aggregation.daily.dao.BookTickerDailyDao`/`aggregation.daily.dao.get_daily_aggregate_stats`

## Supported Statistics

The set of currently supported statistics computed for each day's samples can be found in aggregation.daily.dao.BookTickerDailyRowData:
```python
class BookTickerDailyRowData(TypedDict):
    open: NotRequired[Decimal]
    high: NotRequired[Decimal]
    low: NotRequired[Decimal]
    close: NotRequired[Decimal]
    spread_min: NotRequired[Decimal]
    spread_max: NotRequired[Decimal]
    num_samples: NotRequired[int]
    bid_mean: NotRequired[Decimal]
    bid_variance: NotRequired[Decimal]
    ask_mean: NotRequired[Decimal]
    ask_variance: NotRequired[Decimal]
    mid_mean: NotRequired[Decimal]
    mid_variance: NotRequired[Decimal]
```

open, low, high, and close are all estimated by the mid-market price. The variance for bid, ask, and mid are calculated as the sample variance.

Incorporating additional second-order statistics is straightforward -- we simply need to alter the table, add a new field to this object, and write the function to compute it in aggregation.daily.compute.