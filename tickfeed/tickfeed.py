import argparse
from datetime import date

from aggregation.daily.dao import get_daily_aggregate_stats
from feed.listener import define_start_feed_listener_cmd
from raw.backfill import define_backfill_daily_aggregate_cmd


def define_print_daily_data_cmd(parser):
    parser.add_argument("--exchange", "-e", type=str, nargs="+", help="Exchange name")
    parser.add_argument("--symbol", "-s", type=str, nargs="+", help="Symbol name")
    parser.add_argument(
        "--start-date", type=date.fromisoformat, required=True, help="Date"
    )
    parser.add_argument(
        "--end-date", type=date.fromisoformat, required=True, help="Date"
    )

    parser.set_defaults(command=print_daily_data)


def print_daily_data(args: argparse.Namespace):
    stats = get_daily_aggregate_stats(
        args.symbol, args.exchange, args.start_date, args.end_date
    )
    print(stats)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tick feed CLI")

    subparsers = parser.add_subparsers(title="Commands", dest="command")

    print_daily_data_parser = subparsers.add_parser(
        "data", help="Print the daily aggregated stats for a date range"
    )
    define_print_daily_data_cmd(print_daily_data_parser)

    start_listener_parser = subparsers.add_parser(
        "listen", help="Start book ticker feed listener"
    )
    define_start_feed_listener_cmd(start_listener_parser)

    backfill_daily_aggregate_parser = subparsers.add_parser(
        name="backfill", help="Backfill daily aggregate stats"
    )
    define_backfill_daily_aggregate_cmd(backfill_daily_aggregate_parser)

    args = parser.parse_args()

    argsdict = vars(args)
    command = argsdict.pop("command")
    if command:
        command(args)
    else:
        parser.print_help()
