import unittest
from decimal import Decimal

import pandas as pd
from aggregation.daily.compute import get_aggregate_stats
from aggregation.daily.dao import BookTickerDailyRowData


class TestDailyAggregateFromRaw(unittest.TestCase):
    def test_get_aggregate_stats(self):
        raw_data = pd.DataFrame(
            {
                "timestamp": [
                    "1234567890.12345",
                    "1234567891.12345",
                    "1696885192.12345",
                ],
                "bid_price": [Decimal(10), Decimal(30), Decimal(20)],
                "ask_price": [Decimal(12), Decimal(30), Decimal(24)],
            }
        )

        expected = BookTickerDailyRowData(
            open=Decimal("11"),
            high=Decimal("30"),
            low=Decimal("11"),
            close=Decimal("22"),
            spread_min=Decimal("0"),
            spread_max=Decimal("4"),
            num_samples=3,
            bid_mean=Decimal("20"),
            bid_variance=Decimal("100"),
            ask_mean=Decimal("22"),
            ask_variance=Decimal("90"),
            mid_mean=Decimal("21"),
            mid_variance=Decimal("92.5"),
        )
        actual = get_aggregate_stats(raw_data)

        self.assertEqual(expected, actual)
