import json
import requests

# load training columns
with open("models/feature_columns_nolag.json", "r", encoding="utf-8") as f:
    train_cols = json.load(f)

# call debug endpoint - change sample payload if needed
payload = {
    "features": {
        "store_id": "CA_1",
        "item_id": "FOODS_1_001",
        "date": "2016-05-01"
        # include any additional raw fields your preprocess expects
    }
}

resp = requests.post("http://127.0.0.1:8000/debug/preprocess", json=payload)
resp.raise_for_status()
data = resp.json()
pre_cols = data["columns"]

# Comparisons
missing_in_pre = [c for c in train_cols if c not in pre_cols]
extra_in_pre = [c for c in pre_cols if c not in train_cols]
same_order = train_cols == pre_cols

print("Training cols count:", len(train_cols))
print("Preprocess cols count:", len(pre_cols))
print("Missing (in training but not produced):", missing_in_pre[:30])
print("Extra (produced but not in training):", extra_in_pre[:30])
print("Order matches exactly:", same_order)
