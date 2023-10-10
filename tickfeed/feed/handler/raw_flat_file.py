# Write raw data in flat files partitioned by symbol, exchange, and UTC date
# Storing all the raw data for every day may get expensive
# Consider setting up a batch job to archive (e.g. gzip) older files

import asyncio
import csv
import os
from datetime import date, datetime
from pathlib import Path
from typing import IO, Any, Awaitable, Callable, NamedTuple, Optional

from cryptofeed.types import Ticker
from raw.util import RAW_COLUMNS_TO_WRITE, FileKey, get_raw_file_path


class FileWriterKey(NamedTuple):
    exchange: str
    symbol: str


class FileWriterMeta(NamedTuple):
    file: IO[Any]
    date: date
    lock: asyncio.Lock = asyncio.Lock()


class RawFlatFileWriter:
    _files: dict[FileWriterKey, FileWriterMeta] = {}

    def __init__(
        self,
        out_dir: Path,
        daily_file_callback: Optional[Callable[[FileKey], Awaitable[None]]] = None,
    ):
        self._out_dir = out_dir
        self._daily_file_callback = daily_file_callback

    # Can make this generic across different data types
    async def __call__(self, data: Ticker, timestamp_received: float):
        date = datetime.utcfromtimestamp(data.timestamp).date()
        file_meta = self._get_file(data.exchange, data.symbol, date)
        # If we crash without exiting gracefully, the file may be left in a bad state (e.g. mid-way through a row).
        # Consider implementing a recovery mechanism.
        async with file_meta.lock:
            writer = csv.writer(file_meta.file)
            writer.writerow(
                [data.timestamp]
                + [data.raw[raw_col] for raw_col, _ in RAW_COLUMNS_TO_WRITE]
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        for file_meta in self._files.values():
            async with file_meta.lock:
                file_meta.file.flush()
                file_meta.file.close()

    def _get_file(self, exchange: str, symbol: str, date: date) -> FileWriterMeta:
        key = FileKey(exchange, symbol, date)
        cache_key = FileWriterKey(exchange, symbol)
        if cache_key not in self._files:
            return self._open_file(key, cache_key)
        else:
            file_meta = self._files[cache_key]
            # Keep only one file descriptor open for each FileWriterKey.
            if file_meta.date != date:
                file_meta.file.flush()
                file_meta.file.close()
                if self._daily_file_callback:
                    self._daily_file_callback(key)
                file_meta = self._open_file(key, cache_key)
            return file_meta

    def _open_file(self, key: FileKey, cache_key: FileWriterKey) -> FileWriterMeta:
        file_path = get_raw_file_path(self._out_dir, key)
        existing_file = file_path.exists() and os.path.getsize(file_path) > 0
        file = open(file_path, "a")
        if not existing_file:
            writer = csv.writer(file)
            writer.writerow(
                ["timestamp"] + [col_name for _, col_name in RAW_COLUMNS_TO_WRITE]
            )

        file_meta = FileWriterMeta(file, key.date)
        self._files[cache_key] = file_meta
        return file_meta
