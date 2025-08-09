import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.metrics import mean_squared_error, mean_absolute_error

# --- Load model ---
print("Loading model...")
model = joblib.load("models/baseline_lightgbm.joblib")

# --- Load processed data ---
print("Loading processed data...")
X_valid = pd.read_parquet("data/processed/X_valid.parquet")
y_valid = pd.read_parquet("data/processed/y_valid.parquet")["sales"]

# --- Run predictions ---
print("Making predictions...")
y_pred = model.predict(X_valid)

# # Separate features and target
# y_true = df["sales"]
# X = df.drop(columns=["sales"])

# # --- Run predictions ---
# print("Making predictions...")
# y_pred = model.predict(X)

# --- Calculate metrics ---
rmse = np.sqrt(mean_squared_error(y_valid, y_pred))
mae = mean_absolute_error(y_valid, y_pred)
mape = np.mean(np.abs((y_valid - y_pred) / y_valid)) * 100

# Save metrics to file
metrics_df = pd.DataFrame({
    "RMSE": [rmse],
    "MAE": [mae],
    "MAPE (%)": [mape]
})
metrics_df.to_csv("reports/metrics.csv", index=False)

print("\nModel Evaluation:")
print(metrics_df)

# --- Plot Actual vs Predicted ---
plt.figure(figsize=(10, 5))
plt.scatter(y_valid[:500], y_pred[:500], alpha=0.5)
plt.xlabel("Actual Sales")
plt.ylabel("Predicted Sales")
plt.title("Actual vs Predicted Sales (Sample)")
plt.grid(True)
plt.savefig("reports/figures/actual_vs_predicted.png", dpi=300)
plt.close()

print("Evaluation complete. Metrics and plots saved in 'reports/'.")
