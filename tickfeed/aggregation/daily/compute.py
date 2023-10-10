from decimal import Decimal

import pandas as pd
from aggregation.daily.dao import BookTickerDailyRowData


def get_aggregate_stats(
    df: pd.DataFrame,
) -> BookTickerDailyRowData:
    # Sort in case any data has come out of order
    # Right now, this is only relevant for open/close, and might not be necessary
    df = df.sort_values("timestamp")

    df["spread"] = df["ask_price"] - df["bid_price"]
    df["mid_price"] = (df["ask_price"] + df["bid_price"]).apply(
        lambda x: x / Decimal(2)
    )

    num_samples = Decimal(len(df))

    # The use of decimals here might be overkill
    bid_mean = df["bid_price"].sum() / num_samples
    df["bid_residual_sq"] = (df["bid_price"] - bid_mean) ** Decimal(2)

    ask_mean = df["ask_price"].sum() / num_samples
    df["ask_residual_sq"] = (df["ask_price"] - bid_mean) ** Decimal(2)

    mid_mean = df["mid_price"].sum() / num_samples
    df["mid_residual_sq"] = (df["mid_price"] - bid_mean) ** Decimal(2)

    return BookTickerDailyRowData(
        open=df["mid_price"].iloc[0],
        high=df["mid_price"].max(),
        low=df["mid_price"].min(),
        close=df["mid_price"].iloc[-1],
        spread_min=df["spread"].min(),
        spread_max=df["spread"].max(),
        num_samples=len(df),
        bid_mean=bid_mean,
        bid_variance=df["bid_residual_sq"].sum() / Decimal(num_samples - 1),
        ask_mean=ask_mean,
        ask_variance=df["ask_residual_sq"].sum() / Decimal(num_samples - 1),
        mid_mean=mid_mean,
        mid_variance=df["mid_residual_sq"].sum() / Decimal(num_samples - 1),
    )
