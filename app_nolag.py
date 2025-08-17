# app.py (or app_nolag.py)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib, json
import pandas as pd
from pathlib import Path

MODELS = Path("models")
# BASE_DIR = Path(__file__).resolve().parent
DATA_RAW = Path("data/raw")
# DATA_RAW = BASE_DIR / "data" / "raw"
# DATA_PROCESSED = BASE_DIR / "data" / "processed"

# Load model + artifacts
model = joblib.load(MODELS / "baseline_lightgbm_nolag.joblib")
with open(MODELS / "feature_columns_nolag.json", "r", encoding="utf-8") as f:
    TRAIN_COLS = json.load(f)
with open(MODELS / "cat_mappings_nolag.json", "r", encoding="utf-8") as f:
    CAT_MAPS = json.load(f)

# Preload lookups
calendar = pd.read_csv(DATA_RAW / "calendar.csv")  # has date, wm_yr_wk, event_name_1, ...
sell_prices = pd.read_csv(DATA_RAW / "sell_prices.csv")  # has store_id,item_id,wm_yr_wk,sell_price

# create item->meta lookup from original processed dataset if needed
# we assume train_features.parquet has columns item_id, dept_id, cat_id, state_id
meta = pd.read_parquet("data/processed/train_features.parquet")[["item_id","dept_id","cat_id","store_id","state_id"]].drop_duplicates()
# meta = pd.read_parquet(DATA_PROCESSED / "train_features.parquet")[["item_id","dept_id","cat_id","store_id","state_id"]].drop_duplicates()

meta = meta.drop_duplicates(subset=["item_id"])
item_to_meta = meta.set_index("item_id").to_dict(orient="index")

# item_to_meta = meta.set_index("item_id").to_dict(orient="index")

app = FastAPI(title="Retail Forecasting (no-lag)")

class PredictionRequest(BaseModel):
    features: dict  # minimal input: {"store_id":"CA_1","item_id":"FOODS_1_001","date":"2016-05-01"}

def preprocess_input(raw_df: pd.DataFrame) -> pd.DataFrame:
    # raw_df is one or more rows
    df = raw_df.copy()
    # 1) ensure date is datetime
    df["date"] = pd.to_datetime(df["date"])

    # 2) derive mapping fields from item_id and store_id using meta lookup
    def fill_meta_row(row):
        item = row.get("item_id")
        if item in item_to_meta:
            row["dept_id"] = item_to_meta[item]["dept_id"]
            row["cat_id"] = item_to_meta[item]["cat_id"]
            row["state_id"] = item_to_meta[item]["state_id"]
            row["store_id"] = row.get("store_id", item_to_meta[item]["store_id"])
        return row
    df = df.apply(fill_meta_row, axis=1)

    # 3) merge calendar info (by date)
    cal = calendar.copy()
    cal["date"] = pd.to_datetime(cal["date"])
    df = df.merge(cal, on="date", how="left")  # brings wm_yr_wk, event_name_1/2, snap flags, etc.

    # 4) merge sell_price by store_id,item_id,wm_yr_wk
    df = df.merge(sell_prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")

    # 5) create date parts used in training (match names in feature_columns_nolag.json)
    df["date_year"] = df["date"].dt.year
    df["date_month"] = df["date"].dt.month
    df["date_day"] = df["date"].dt.day
    df["dayofweek"] = df["date"].dt.dayofweek
    df["quarter"] = df["date"].dt.quarter
    df["wday"] = df["date"].dt.weekday  # if training had wday

    # 6) Fill missing sell_price (if any) with -1 or median
    df["sell_price"] = df["sell_price"].fillna(-1)

    # 7) Ensure categorical columns have same categories (use CAT_MAPS)
    for col, levels in CAT_MAPS.items():
        if col in df.columns:
            # convert to string then set categories with the trained levels
            df[col] = pd.Categorical(df[col].astype(str), categories=levels).codes
        else:
            # if a mapped column is missing, create it with -1 codes
            df[col] = -1

    # 8) Some numeric columns might be floats/int already; ensure columns exist
    # 9) Reorder columns to match training
    missing = [c for c in TRAIN_COLS if c not in df.columns]
    if missing:
        # for missing numeric features (like those requiring history) fill with 0 or -1
        for m in missing:
            df[m] = -1
    df = df[TRAIN_COLS]
    return df

@app.post("/predict")
def predict(req: PredictionRequest):
    try:
        raw_df = pd.DataFrame([req.features])
        X = preprocess_input(raw_df)
        preds = model.predict(X)
        return {"prediction": round(preds[0])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def root():
    return {"status": "ok"}
