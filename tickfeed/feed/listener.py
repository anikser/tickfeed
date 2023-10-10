import argparse
import asyncio
import logging
from decimal import Decimal
from pathlib import Path
from typing import Any, Callable

from common.constants import SUPPORTED_TICKERS
from cryptofeed import FeedHandler
from cryptofeed.defines import TICKER
from cryptofeed.exchanges import BinanceUS
from feed.handler.raw_flat_file import RawFlatFileWriter
from feed.handler.util import FanoutFeedCallback
from raw.daily_raw_writer import DailyAggregateStatsWriter


def start_feed_listener(args: argparse.Namespace):
    logging.basicConfig(filename=args.logging_path, level=args.logging_level)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(setup_feed_listener(args))
    loop.run_forever()


async def setup_feed_listener(args: argparse.Namespace):
    fh = FeedHandler()

    daily_stats_writer = DailyAggregateStatsWriter(args.raw_output_dir)
    # If we have more context manager callbacks, we can use AsyncExitStack
    async with RawFlatFileWriter(
        args.raw_output_dir, daily_file_callback=daily_stats_writer
    ) as raw_writer:
        ticker_callbacks: list[Callable] = [raw_writer]
        if __debug__:

            async def feed_debug_cb(data: Any, timestamp: float):
                print(f"Data: {data.raw} received at ts {timestamp}")

            ticker_callbacks.append(feed_debug_cb)
        ticker_cb = {TICKER: FanoutFeedCallback(ticker_callbacks)}

        for ticker in SUPPORTED_TICKERS:
            fh.add_feed(
                BinanceUS(symbols=[ticker], channels=[TICKER], callbacks=ticker_cb)
            )

        fh.run(start_loop=False)


def define_start_feed_listener_cmd(parser):
    parser.add_argument(
        "--raw-output-dir",
        "-o",
        type=Path,
        help="If set, will write raw data to this directory",
    )
    parser.add_argument(
        "--logging-path",
        "-l",
        type=Path,
        help="If set, will write logs to this file. Defaults to local directory.",
        default="feedlistener.log",
    )
    parser.add_argument(
        "--logging-level",
        "-v",
        type=logging.getLevelName,
        help="The logging level. Defaults to INFO.",
        default=logging.INFO,
    )

    parser.set_defaults(command=start_feed_listener)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Book ticker feed listener")
    define_start_feed_listener_cmd(parser)
    args = parser.parse_args()
    start_feed_listener(args)
