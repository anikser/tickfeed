# This is an incomplete, alternative solution.
# If storing large quantities of raw data is not desired, we can store aggregate stats alone, and compute them as samples come in.

# from datetime import datetime
# from decimal import Decimal
# from functools import lru_cache
# from typing import Any, Callable, NamedTuple, Tuple, TypedDict

# import asyncpg
# from cryptofeed.types import Ticker

# from aggregation.dao import BookTickerDailyRowData, BookTickerDailyRowKey

# # Integrate with secrets manager
# postgres_cfg = {
#     "host": "127.0.0.1",
#     "user": "cryptofeedwriter",
#     "db": "research",
#     "table": "cryptofeed.bookticker",
#     "pw": "password",
# }

# postgres_column_map = {
#     "symbol": "symbol",
#     "bid": "bid",
#     "ask": "ask",
#     "timestamp": "timestamp",
# }
# POSTGRES_DATE_FORMAT = "%Y-%m-%d"


# class DailySamplingPostgresWriter:
#     def __init__(self, postgres_cfg: dict):
#         self.conn = None
#         self.table = postgres_cfg["table"]
#         self._row_cache: dict[BookTickerDailyRowKey, SampleStreamProcessor] = {}
#         self.running = True

#     async def __call__(self, data: Ticker, timestamp_received: float):
#         date = datetime.utcfromtimestamp(data.timestamp).strftime(POSTGRES_DATE_FORMAT)
#         key = BookTickerDailyRowKey(data.exchange, data.symbol, date)
#         if key in self._row_cache:
#             self._row_cache[key].process_next_sample(data)
#         else:
#             # Maybe evict previous date from cache
#             previous_row = self.get_current_data_row(key)
#             if not previous_row:
#                 mid = (data["bid"] + data["ask"]) / Decimal(2)
#                 # TODO: Branch if time > next open, then:
#                 # 1. Set close on last row
#                 # 2. Create new row with open = mid

#                 previous_row = BookTickerDailyRowData(
#                     high=mid,
#                     low=mid,
#                     open=mid,  # FIXME: only populate this if the timestamp is reasonably close to open
#                     spread_min=data["ask"] - data["bid"],
#                     spread_max=data["ask"] - data["bid"],
#                     num_samples=Decimal(1),
#                     bid_mean=data["bid"],
#                     bid_variance=0,
#                     ask_mean=data["ask"],
#                     ask_variance=0,
#                     mid_mean=data["mid"],
#                     mid_variance=0,
#                 )

#             self._row_cache[key] = SampleStreamProcessor(previous_row)

#         processor = self._row_cache[key]
#         diff = processor.get_row_diff()
#         if diff:
#             await self._write(key, diff)

#     async def get_current_data_row(
#         self, key: BookTickerDailyRowKey
#     ) -> BookTickerDailyRowData:
#         if self.conn is None:
#             await self._connect()
#         if key in self._row_cache:
#             return self._row_cache[key]
#         else:
#             select_query = f"SELECT {','.join(BookTickerDailyRowData.__annotations__.keys())} from {self.table}"
#             data = await self.conn.fetchrow(select_query)

#             self._row_cache[key] = data
#             # TODO: maybe evict previous date from cache
#             return data

#     async def _stop(self):
#         self.running = False
#         await self.conn.close()


# class SampleStreamProcessor:
#     def __init__(self, curent_row: BookTickerDailyRowData):
#         # We shift next to current on the first sample
#         self.data_column_function_names = [
#             col
#             for col in BookTickerDailyRowData.__annotations__.keys()
#             if col in dir(self)
#         ]
#         self.previous_row: BookTickerDailyRowData = {}
#         self.next_row = curent_row

#     def process_next_sample(self, data: Ticker) -> BookTickerDailyRowData:
#         self.previous_row: BookTickerDailyRowData = self.next_row
#         self.next_row: BookTickerDailyRowData = {}
#         self.sample = data
#         self.mid = (data["bid"] + data["ask"]) / Decimal(2)

#         # We define a function per column, and call it to populate the next row.
#         # This is a bit of a hack to avoid writing boilerplate
#         # We only return a column value if it has changed
#         return {
#             col_name: getattr(self, col_name)()
#             for col_name in BookTickerDailyRowData.__annotations__.keys()
#             if col_name not in self.previous_row
#             or self.previous_row[col_name] == getattr(self, col_name)()
#         }

#     def _cache(func: Callable) -> Decimal:
#         def wrapper(self, *args, **kwargs):
#             if func.__name__ not in self.next_row:
#                 self.next_row[func] = func(*args, **kwargs)
#             return self.next_row[func]

#         return wrapper

#     @_cache
#     def high(self) -> Decimal:
#         return max(self.previous_row["high"], self.mid)

#     @_cache
#     def low(self) -> Decimal:
#         return min(self.previous_row["low"], self.mid)

#     @_cache
#     def spread_min(self) -> Decimal:
#         return min(
#             self.previous_row["spread_min"], self.sample["ask"] - self.sample["bid"]
#         )

#     @_cache
#     def spread_max(self) -> Decimal:
#         return max(
#             self.previous_row["spread_max"], self.sample["ask"] - self.sample["bid"]
#         )

#     @_cache
#     def num_samples(self) -> Decimal:
#         self.num_samples = self.previous_row["num_samples"] + 1
#         return self.num_samples

#     # Can probably reduce some code duplication here at the cost of some performance
#     @_cache
#     def bid_mean(self) -> Decimal:
#         return (
#             self.previous_row["bid_mean"]
#             + (self.sample["bid"] - self.previous_row["bid_mean"]) / self.num_samples()
#         )

#     @_cache
#     def bid_variance(self) -> Decimal:
#         return self.previous_row["bid_variance"] + (
#             self.sample["bid"] - self.previous_row["bid_mean"]
#         ) * (self.sample["bid"] - self.bid_mean())

#     @_cache
#     def ask_mean(self) -> Decimal:
#         return (
#             self.previous_row["ask_mean"]
#             + (self.sample["ask"] - self.previous_row["ask_mean"]) / self.num_samples()
#         )

#     @_cache
#     def ask_variance(self) -> Decimal:
#         return self.previous_row["ask_variance"] + (
#             self.sample["ask"] - self.previous_row["ask_mean"]
#         ) * (self.sample["ask"] - self.ask_mean())

#     @_cache
#     def mid_mean(self) -> Decimal:
#         return (
#             self.previous_row["mid_mean"]
#             + (self.mid - self.previous_row["mid_mean"]) / self.num_samples()
#         )

#     @_cache
#     def mid_variance(self) -> Decimal:
#         return self.previous_row["mid_variance"] + (
#             self.mid - self.previous_row["mid_mean"]
#         ) * (self.mid - self.mid_mean())
