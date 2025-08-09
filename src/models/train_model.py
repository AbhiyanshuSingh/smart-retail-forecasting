import pandas as pd
import lightgbm as lgb
from lightgbm import LGBMRegressor, early_stopping
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from joblib import dump
from pathlib import Path
import numpy as np
import json

PROCESSED_PATH = Path("data/processed")
MODELS_PATH = Path("models")
MODELS_PATH.mkdir(exist_ok=True)

def load_data():
    df = pd.read_parquet(PROCESSED_PATH / "train_features.parquet")
    return df

def prepare_features(df):
    # Drop non-numeric & target leakage columns
    drop_cols = ["id", "item_id", "dept_id", "cat_id", "store_id", "state_id", "date", "d", "wm_yr_wk"]
    features = df.drop(columns=drop_cols, errors="ignore")
    # Separate target
    target = df["sales"]
    df = df.drop(columns=["sales"])

    # Handle datetime columns in-place
    for col in df.columns:
        if np.issubdtype(df[col].dtype, np.datetime64):
            df[col + "_year"] = df[col].dt.year
            df[col + "_month"] = df[col].dt.month
            df[col + "_day"] = df[col].dt.day
            del df[col]

    # Encode object columns one-by-one
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype("category").cat.codes

    return df, target

def train_baseline(X_train, y_train, X_valid, y_valid):
    model = LGBMRegressor(
        objective="regression",
        metric="rmse",
        boosting_type="gbdt",
        learning_rate=0.05,
        num_leaves=31,
        n_estimators=200
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_valid, y_valid)],
        callbacks=[early_stopping(stopping_rounds=20)]
    )
    return model

if __name__ == "__main__":
    print("Loading data...")
    df = load_data()

    df = df.sample(frac=0.05, random_state=42)  # 5% of data

    print("Preparing features...")
    X, y = prepare_features(df)

    # --- Save training feature list for later comparison ---
    FEATURE_COLS_PATH = "models/feature_columns.json"
    feature_cols = X.columns.tolist()
    with open(FEATURE_COLS_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_cols, f, indent=2)
    print(f"Saved training feature columns to {FEATURE_COLS_PATH}")


    print("Splitting data...")
    X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)
    # --- Save validation set for later evaluation ---
    print("Saving validation data for evaluation...")
    X_valid.to_parquet("data/processed/X_valid.parquet")
    pd.DataFrame({"sales": y_valid}).to_parquet("data/processed/y_valid.parquet")


    print("Training model...")
    model = train_baseline(X_train, y_train, X_valid, y_valid)
    


    print("Evaluating model...")
    y_pred = model.predict(X_valid)
    rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
    print(f"Validation RMSE: {rmse:.4f}")

    print("Saving model...")
    dump(model, MODELS_PATH / "baseline_lightgbm.joblib")

    print("✅ Step 5 complete — model saved to models/baseline_lightgbm.joblib")
