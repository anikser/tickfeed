import asyncio
from datetime import date
from decimal import Decimal
from typing import NamedTuple, NotRequired, Optional, TypedDict

import asyncpg
import pandas as pd


class BookTickerDailyRowKey(NamedTuple):
    exchange: str
    symbol: str
    date: date


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


# Integrate with secrets manager
postgres_cfg = {
    "host": "127.0.0.1",
    "user": "tickfeedwriter",
    "db": "research",
    "table": "tickfeed.bookticker_daily",
    "pw": "password",
}


class BookTickerDailyDao:
    # def __init__(self, postgres_cfg: dict):
    def __init__(self):
        self.conn: Optional[asyncpg.Connection] = None
        self.table = postgres_cfg["table"]

    async def _connect(self):
        if self.conn is None:
            self.conn = await asyncpg.connect(
                user=postgres_cfg["user"],
                password=postgres_cfg["pw"],
                database=postgres_cfg["db"],
                host=postgres_cfg["host"],
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        if self.conn is not None:
            await self.conn.close()

    async def upsert(self, key: BookTickerDailyRowKey, data: BookTickerDailyRowData):
        # NamedTyple._asdict() maps the field names to their values
        # https://docs.python.org/3/library/collections.html#collections.somenamedtuple._asdict

        key_columns, key_values = zip(*key._asdict().items())
        data_columns, data_values = zip(*data.items())

        all_values = key_values + data_values

        # Consider using asyncpg paramerized queries
        insert_statement = f"""
            INSERT INTO {self.table} 
            ({','.join(key_columns + data_columns)}) 
            VALUES 
            ({','.join([f'${i}' for i in range(1, len(all_values) + 1)])})
            ON CONFLICT ({','.join(key_columns)}) DO UPDATE SET
            
            {', '.join([f'{col_name} = ${i+len(key_columns) + 1}' for i, col_name in enumerate(data_columns)])}
        """
        await self._connect()
        if self.conn != None:
            async with self.conn.transaction():
                await self.conn.execute(insert_statement, *all_values)
        else:
            raise RuntimeError("Failed to establish connection with database")

    async def select(
        self, symbols: list[str], exchanges: list[str], start_date: date, end_date: date
    ) -> pd.DataFrame:
        """
        Returns all rows in the table that match the given criteria. start_date and end_date are inclusive.
        """
        columns = list(BookTickerDailyRowKey._fields) + list(
            BookTickerDailyRowData.__annotations__.keys()
        )
        select_statement = f"""
            SELECT {','.join(columns)} from {self.table}
            WHERE symbol = ANY($1) AND exchange = ANY($2) AND date >= $3 AND date <= $4
        """
        await self._connect()
        if self.conn != None:
            data = await self.conn.fetch(
                select_statement, symbols, exchanges, start_date, end_date
            )
            return pd.DataFrame(data, columns=columns)
        else:
            raise RuntimeError("Failed to establish connection with database")


def get_daily_aggregate_stats(
    symbols: list[str], exchanges: list[str], start_date: date, end_date: date
):
    async def _get_daily_aggregate_stats():
        async with BookTickerDailyDao() as dao:
            return await dao.select(symbols, exchanges, start_date, end_date)

    return asyncio.run(_get_daily_aggregate_stats())
