import argparse
import os
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import NamedTuple

import pandas as pd

FILE_FORMAT = "{exchange}_{symbol}_{date}_raw.csv"
DATE_FORMAT = "%Y%m%d"

# Consider pulling this out into a config
RAW_COLUMNS_TO_WRITE = [
    ("b", "bid_price"),
    ("B", "bid_size"),
    ("a", "ask_price"),
    ("A", "ask_size"),
]


# We could use BookTickerDailyRowKey in place of this,
# but it is better to separate out our raw and aggregate data logic
class FileKey(NamedTuple):
    exchange: str
    symbol: str
    date: date


def get_raw_data_from_path(path: Path):
    df = pd.read_csv(
        path,
        dtype={
            "timestamp": "string",
            **{data_col: "string" for _, data_col in RAW_COLUMNS_TO_WRITE},
        },
    )
    for _, data_col in RAW_COLUMNS_TO_WRITE:
        df[data_col] = df[data_col].apply(Decimal)
    return df


def get_raw_data(raw_dir: Path, key: FileKey):
    file_path = get_raw_file_path(raw_dir, key)
    return get_raw_data_from_path(file_path)


def get_raw_file_path(out_dir: Path, key: FileKey) -> Path:
    parent = out_dir / key.symbol / key.exchange
    if not os.path.exists(parent):
        os.makedirs(parent)
    return (
        out_dir
        / key.symbol
        / key.exchange
        / FILE_FORMAT.format(
            exchange=key.exchange,
            symbol=key.symbol,
            date=key.date.strftime(DATE_FORMAT),
        )
    )
