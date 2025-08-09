from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import pandas as pd
import uvicorn
from src.etl.build_features import preprocess_input  # Import preprocessing
from typing import Dict, Any
from starlette.responses import JSONResponse

# Initialize FastAPI app
app = FastAPI(title="Retail Sales Forecasting API", version="1.0")

# Load model & preprocessing info
MODEL_PATH = "models/baseline_lightgbm.joblib"
model = joblib.load(MODEL_PATH)

# Example: Categorical encoding info (if needed later)
# We could store these during training for reproducibility

# # Request body format
# class PredictionRequest(BaseModel):
#     features: dict  # Example: {"store_id": 1, "item_id": 42, "weekday": 3, ...}

class PredictionRequest(BaseModel):
    features: Dict[str, Any]


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Retail Forecasting API is running!"}



@app.post("/debug/preprocess")
def debug_preprocess(request: PredictionRequest):
    # Convert request to df
    raw_df = pd.DataFrame([request.features])
    # Apply the SAME preprocessing function (must be the one used for training)
    processed_df = preprocess_input(raw_df.copy())
    cols = processed_df.columns.tolist()
    # optionally return a small sample of processed data
    sample = processed_df.head(1).to_dict(orient="records")[0]
    return JSONResponse({"columns": cols, "sample_row": sample})


# Prediction endpoint
@app.post("/predict")
def predict(request: PredictionRequest):
    # Convert input to DataFrame
    input_df = pd.DataFrame([request.features])

    # # Apply same preprocessing steps as training
    # for col in input_df.select_dtypes(include=["object"]).columns:
    #     input_df[col] = input_df[col].astype("category").cat.codes

    # if "date" in input_df.columns:
    #     input_df["date"] = pd.to_datetime(input_df["date"]).astype("int64") // 10**9

    # Apply preprocessing
    processed_df = preprocess_input(input_df)

    print(processed_df.columns.tolist())


    # # Make prediction
    # prediction = model.predict(input_df)[0]

    # return {"prediction": float(prediction)}

    # Make prediction
    prediction = model.predict(processed_df)
    return {"prediction": prediction.tolist()}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
