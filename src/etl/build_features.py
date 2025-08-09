import pandas as pd
import numpy as np
from pathlib import Path

RAW_PATH = Path("data/raw")
PROCESSED_PATH = Path("data/processed")

def load_data():
    calendar = pd.read_csv(RAW_PATH / "calendar.csv")
    sales = pd.read_csv(RAW_PATH / "sales_train_validation.csv")
    prices = pd.read_csv(RAW_PATH / "sell_prices.csv")
    sales = sales.head(5000)
    return calendar, sales, prices


def preprocess_input(raw_df: pd.DataFrame) -> pd.DataFrame:
    """
    Takes raw input from FastAPI and applies the exact same preprocessing
    as was done during training, so the number and order of features match.
    """

    # Example: These steps should match your training steps
    # 1. Convert date to datetime
    raw_df["date"] = pd.to_datetime(raw_df["date"])

    # 2. Extract date parts (must match training exactly)
    raw_df["year"] = raw_df["date"].dt.year
    raw_df["month"] = raw_df["date"].dt.month
    raw_df["day"] = raw_df["date"].dt.day

    # 3. Encode categoricals (must match training order and encoding)
    categorical_cols = ["store_id", "item_id"]
    for col in categorical_cols:
        raw_df[col] = raw_df[col].astype("category").cat.codes

    # 4. Drop original date column if model didn’t use it
    raw_df = raw_df.drop(columns=["date"])

    # 5. Ensure column order matches training
    # (Get your training column list from train_model.py)
    expected_columns = [
        "store_id", "item_id", "year", "month", "day"
        # plus all other features used in training
    ]
    raw_df = raw_df[expected_columns]

    return raw_df

def melt_sales(sales):
    # Convert from wide to long format
    id_vars = sales.columns[:6]
    value_vars = sales.columns[6:]
    sales_long = sales.melt(id_vars=id_vars, value_vars=value_vars,
                            var_name="d", value_name="sales")
    return sales_long

def merge_data(sales_long, calendar, prices):
    df = sales_long.merge(calendar, on="d", how="left")
    df = df.merge(prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")
    return df

def feature_engineering(df):
    # Convert date to datetime
    df["date"] = pd.to_datetime(df["date"])
    
    # Time features
    df["dayofweek"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["year"] = df["date"].dt.year

    # Lag features
    for lag in [7, 14, 28]:
        df[f"lag_{lag}"] = df.groupby(["id"])["sales"].shift(lag)

    # Rolling means
    for window in [7, 28]:
        df[f"rolling_mean_{window}"] = (
            df.groupby(["id"])["sales"].shift(1).rolling(window).mean()
        )

    return df

def save_processed(df):
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_PATH / "train_features.parquet", index=False)

if __name__ == "__main__":
    calendar, sales, prices = load_data()
    sales_long = melt_sales(sales)
    df = merge_data(sales_long, calendar, prices)
    df = feature_engineering(df)
    save_processed(df)
    print(f"Processed data saved to {PROCESSED_PATH / 'train_features.parquet'}")
