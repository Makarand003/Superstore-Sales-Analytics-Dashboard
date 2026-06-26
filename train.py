from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error
from statsmodels.tsa.statespace.sarimax import SARIMAX


DATE_COLUMNS = ["Order Date", "Ship Date"]


def load_data(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="latin1")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    cleaned = df.copy()
    for column in DATE_COLUMNS:
        cleaned[column] = pd.to_datetime(cleaned[column], format="%d/%m/%Y", errors="coerce")

    cleaned["Postal Code"] = cleaned["Postal Code"].fillna(0).astype(int).astype(str)
    cleaned["Ship Delay Days"] = (cleaned["Ship Date"] - cleaned["Order Date"]).dt.days
    cleaned = cleaned.dropna(subset=["Order Date", "Ship Date", "Sales"])
    cleaned = cleaned[cleaned["Sales"] >= 0].reset_index(drop=True)
    return cleaned


def build_daily_sales(df: pd.DataFrame) -> pd.DataFrame:
    daily = (
        df.groupby("Order Date", as_index=False)
        .agg(Sales=("Sales", "sum"), Orders=("Order ID", "nunique"))
        .sort_values("Order Date")
    )

    full_index = pd.date_range(daily["Order Date"].min(), daily["Order Date"].max(), freq="D")
    daily = (
        daily.set_index("Order Date")
        .reindex(full_index)
        .rename_axis("Order Date")
        .fillna({"Sales": 0, "Orders": 0})
        .reset_index()
    )
    return daily


def train_forecast_model(daily_sales: pd.DataFrame, test_days: int = 30):
    series = daily_sales.set_index("Order Date")["Sales"].asfreq("D")
    train = series.iloc[:-test_days]
    test = series.iloc[-test_days:]

    model = SARIMAX(
        train,
        order=(1, 1, 1),
        seasonal_order=(1, 1, 1, 7),
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    fitted_model = model.fit(disp=False)
    forecast = fitted_model.forecast(steps=len(test))

    metrics = {
        "mae": float(mean_absolute_error(test, forecast)),
        "rmse": float(np.sqrt(mean_squared_error(test, forecast))),
        "test_days": int(test_days),
    }
    return fitted_model, forecast, test, metrics


def save_outputs(
    cleaned: pd.DataFrame,
    daily_sales: pd.DataFrame,
    model,
    metrics: dict,
    processed_dir: Path,
    model_dir: Path,
) -> None:
    processed_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)

    cleaned.to_csv(processed_dir / "cleaned_superstore.csv", index=False)
    daily_sales.to_csv(processed_dir / "daily_sales.csv", index=False)
    joblib.dump({"model": model, "metrics": metrics}, model_dir / "sales_forecast_sarimax.joblib")


def main() -> None:
    parser = argparse.ArgumentParser(description="Train the Superstore daily sales forecasting model.")
    parser.add_argument("--data-path", default="data/raw/train.csv", help="Path to the raw Superstore CSV.")
    parser.add_argument("--processed-dir", default="data/processed", help="Where cleaned data files are written.")
    parser.add_argument("--model-dir", default="models", help="Where the trained model artifact is written.")
    parser.add_argument("--test-days", type=int, default=30, help="Number of trailing days used for evaluation.")
    args = parser.parse_args()

    raw = load_data(args.data_path)
    cleaned = clean_data(raw)
    daily_sales = build_daily_sales(cleaned)
    model, _, _, metrics = train_forecast_model(daily_sales, test_days=args.test_days)
    save_outputs(cleaned, daily_sales, model, metrics, Path(args.processed_dir), Path(args.model_dir))

    print("Training complete")
    print(f"Rows after cleaning: {len(cleaned):,}")
    print(f"Daily sales range: {daily_sales['Order Date'].min().date()} to {daily_sales['Order Date'].max().date()}")
    print(f"MAE: {metrics['mae']:.2f}")
    print(f"RMSE: {metrics['rmse']:.2f}")


if __name__ == "__main__":
    main()
