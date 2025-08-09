# src/models/train_model_nolag.py
import json
from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from lightgbm import LGBMRegressor, early_stopping
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
MODELS = Path("models")
MODELS.mkdir(parents=True, exist_ok=True)



# --- load processed features created earlier (train_features.parquet) ---
df = pd.read_parquet(PROCESSED / "train_features.parquet")

if "date" in df.columns:
    df["date_year"] = df["date"].dt.year
    df["date_month"] = df["date"].dt.month
    df["date_day"] = df["date"].dt.day
    df["dayofweek"] = df["date"].dt.dayofweek
    df["quarter"] = df["date"].dt.quarter


# --- Drop lag/rolling features (we'll not use them in this model) ---
drop_prefixes = ("lag_", "rolling_")
cols_to_drop = [c for c in df.columns if c.startswith(drop_prefixes)]
df = df.drop(columns=cols_to_drop, errors="ignore")

# --- Drop or keep IDs consistently (model shouldn't be given raw string IDs) ---
# We'll keep columns needed for mapping (item_id, store_id) and derive meta later
# Ensure target exists
if "sales" not in df.columns:
    raise RuntimeError("train_features.parquet must contain 'sales' column")

# --- OPTIONAL: sample for quick dev; remove/comment out for full train ---
df = df.sample(frac=0.2, random_state=42)

# --- Prepare X,y (drop columns that shouldn't be features) ---
drop_non_features = ["id", "d","date"]  # if present - adapt as needed
X = df.drop(columns=drop_non_features + ["sales"], errors="ignore")
y = df["sales"]

# --- Save the final training feature list (ordered) ---
feature_cols = X.columns.tolist()
with open(MODELS / "feature_columns_nolag.json", "w", encoding="utf-8") as f:
    json.dump(feature_cols, f, indent=2)
print("Saved feature list:", len(feature_cols))

# --- Save category levels (for consistent encoding in API) ---
cat_cols = [c for c in X.columns if X[c].dtype.name == "category" or X[c].dtype == object]
cat_mappings = {}
for c in cat_cols:
    # convert to string categories and save ordered list
    X[c] = X[c].astype(str)
    levels = list(X[c].astype("category").cat.categories)
    cat_mappings[c] = levels
with open(MODELS / "cat_mappings_nolag.json", "w", encoding="utf-8") as f:
    json.dump(cat_mappings, f, indent=2)
print("Saved categorical mappings for:", list(cat_mappings.keys()))

# --- Convert categorical columns to codes before training ---
for c, levels in cat_mappings.items():
    X[c] = pd.Categorical(X[c], categories=levels).codes

# --- train/valid split ---
X_train, X_valid, y_train, y_valid = train_test_split(X, y, test_size=0.2, random_state=42)

# save validation sets for evaluation
X_valid.to_parquet(PROCESSED / "X_valid_nolag.parquet", index=False)
pd.DataFrame({"sales": y_valid}).to_parquet(PROCESSED / "y_valid_nolag.parquet", index=False)

# --- train model ---
model = LGBMRegressor(
    objective="regression",
    metric="rmse",
    boosting_type="gbdt",
    learning_rate=0.05,
    num_leaves=31,
    n_estimators=300,
    verbosity=-1
)
model.fit(X_train, y_train, eval_set=[(X_valid, y_valid)],
          callbacks=[early_stopping(stopping_rounds=30)])

# --- evaluate ---
y_pred = model.predict(X_valid)
rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
mae = mean_absolute_error(y_valid, y_pred)
print(f"Validation RMSE: {rmse:.4f}, MAE: {mae:.4f}")

# --- persist model ---
joblib.dump(model, MODELS / "baseline_lightgbm_nolag.joblib")
print("Saved model to models/baseline_lightgbm_nolag.joblib")
