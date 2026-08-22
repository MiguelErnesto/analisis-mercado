from __future__ import annotations

import pandas as pd


FEATURE_COLS = [
    "dow",
    "month",
    "is_weekend",
    "is_holiday",
    "promo_rate",
    "lag_7",
    "lag_28",
    "rolling_mean_7",
]


def daily_sales(sales: pd.DataFrame) -> pd.DataFrame:
    daily = (
        sales.groupby("date", as_index=False)
        .agg(
            revenue=("revenue", "sum"),
            qty=("qty", "sum"),
            promo_rate=("promo", "mean"),
        )
        .sort_values("date")
        .reset_index(drop=True)
    )
    daily["date"] = pd.to_datetime(daily["date"])
    return daily


def add_features(daily: pd.DataFrame, holidays: pd.Series, value_col: str = "revenue") -> pd.DataFrame:
    df = daily.copy()
    holiday_set = set(pd.to_datetime(holidays).dt.normalize())
    df["dow"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["dow"] >= 5).astype(int)
    df["is_holiday"] = df["date"].dt.normalize().isin(holiday_set).astype(int)
    df["lag_7"] = df[value_col].shift(7)
    df["lag_28"] = df[value_col].shift(28)
    df["rolling_mean_7"] = df[value_col].shift(1).rolling(7).mean()
    return df


def train_ready(daily: pd.DataFrame, holidays: pd.Series, value_col: str = "revenue") -> pd.DataFrame:
    return add_features(daily, holidays, value_col).dropna(subset=FEATURE_COLS).reset_index(drop=True)
