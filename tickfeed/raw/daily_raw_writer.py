from pathlib import Path

from aggregation.daily.compute import get_aggregate_stats
from aggregation.daily.dao import BookTickerDailyDao, BookTickerDailyRowKey
from raw.util import FileKey, get_raw_data


class DailyAggregateStatsWriter:
    def __init__(self, raw_dir: Path):
        self._raw_dir = raw_dir

    async def __call__(self, file_key: FileKey):
        key = BookTickerDailyRowKey(file_key.exchange, file_key.symbol, file_key.date)
        data = get_raw_data(self._raw_dir, file_key)
        stats = get_aggregate_stats(data)
        async with BookTickerDailyDao() as dao:
            await dao.upsert(key, stats)
