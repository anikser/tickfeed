import argparse
import asyncio
import logging
from datetime import date
from pathlib import Path
from typing import Dict

import pandas as pd
from aggregation.daily.compute import get_aggregate_stats
from aggregation.daily.dao import (
    BookTickerDailyDao,
    BookTickerDailyRowData,
    BookTickerDailyRowKey,
)
from raw.util import FileKey, get_raw_data


def backfill_daily_aggregate_stats(args: argparse.Namespace):
    logging.basicConfig(filename=args.logging_path, level=args.logging_level)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_backfill_daily_aggregate_stats(args))


async def _backfill_daily_aggregate_stats(args: argparse.Namespace):
    stats = get_aggregate_stats_from_raw(
        args.dir, args.start_date, args.end_date, args.exchange, args.symbol
    )

    async with BookTickerDailyDao() as dao:
        # For better performance, we can batch these upserts
        for key, stat in stats.items():
            await dao.upsert(key, stat)


def get_aggregate_stats_from_raw(
    raw_dir: Path,
    start_date: date,
    end_date: date,
    exchange: str,
    symbol: str,
) -> dict[BookTickerDailyRowKey, BookTickerDailyRowData]:
    stats = {}
    for day in pd.date_range(start_date, end_date):
        file_key = FileKey(exchange, symbol, day.date())
        key = BookTickerDailyRowKey(exchange, symbol, day.date())

        data = get_raw_data(raw_dir, file_key)
        stats[key] = get_aggregate_stats(data)
    return stats


def define_backfill_daily_aggregate_cmd(parser):
    parser.add_argument(
        "--logging-path",
        "-l",
        type=Path,
        help="If set, will write logs to this file. Defaults to local directory.",
        default="booktickwriter.log",
    )
    parser.add_argument(
        "--logging-level",
        "-v",
        type=logging.getLevelName,
        help="The logging level. Defaults to INFO.",
        default=logging.INFO,
    )
    parser.add_argument(
        "--dir", "-i", type=Path, required=True, help="Raw directory path"
    )
    parser.add_argument(
        "--exchange", "-e", type=str, required=True, help="Exchange name"
    )
    parser.add_argument("--symbol", "-s", type=str, required=True, help="Symbol name")
    parser.add_argument("--start-date", type=str, required=True, help="Date")
    parser.add_argument("--end-date", type=str, required=True, help="Date")

    parser.set_defaults(command=backfill_daily_aggregate_stats)
