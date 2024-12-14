from fastapi import FastAPI, Depends
from pydantic import BaseModel
from typing import List, Optional
import json
from pathlib import Path
from metrics import calculate_metrics
from utils import get_fx_rates, get_prices, submit_metrics
import requests
from decimal import Decimal

# Set inputs from challenge
START_DATE = "2023-01-01"
END_DATE = "2024-11-10"
TARGET_CURRENCY = "USD"

# Dependency to load positions
def load_positions():
    file_path = Path("tech-challenge-2024-positions.json")
    with file_path.open() as f:
        return json.load(f)

# Define the Position model
class Position(BaseModel):
    id: int
    open_date: str
    close_date: Optional[str] = None
    open_price: float
    close_price: Optional[float] = None
    quantity: float
    transaction_costs: float
    instrument_id: int
    instrument_currency: str
    open_transaction_type: str
    close_transaction_type: Optional[str] = None

# Initialize FastAPI
app = FastAPI()

# @app.get("/test-fxrates")
# def test_api(positions: List[Position] = Depends(load_positions),
#     target_currency: str = TARGET_CURRENCY,
#     start_date: str = START_DATE,
#     end_date: str = END_DATE
# ):
#     parsed_positions = [Position(**pos) for pos in positions]
#     return get_fx_rates(parsed_positions, start_date, end_date, target_currency)

# @app.get("/test-prices")
# def test_api(positions: List[Position] = Depends(load_positions),
#     target_currency: str = TARGET_CURRENCY,
#     start_date: str = START_DATE,
#     end_date: str = END_DATE
# ):
#     parsed_positions = [Position(**pos) for pos in positions]
#     return get_prices(parsed_positions, start_date, end_date)

# Calculate endpoint
@app.post("/calculate")
async def calculate(
    positions: List[Position] = Depends(load_positions),
    target_currency: str = TARGET_CURRENCY,
    start_date: str = START_DATE,
    end_date: str = END_DATE
):
    # Parse positions to the Pydantic model
    parsed_positions = [Position(**pos) for pos in positions]

    # Fetch required data
    fx_rates = get_fx_rates(parsed_positions, start_date, end_date, target_currency)
    prices = get_prices(parsed_positions, start_date, end_date)
    
    # Calculate metrics
    metrics = calculate_metrics(parsed_positions, fx_rates, prices, start_date, end_date, target_currency)

    # # Round the metrics for positions and basket
    # def round_metrics(data):
    #     if isinstance(data, list):  
    #         return [round(value, 8) if isinstance(value, (int, float)) else value for value in data]
    #     elif isinstance(data, dict):  
    #         return {key: round_metrics(value) for key, value in data.items()}
    #     return data  

    # Submit metrics to the API

    submission_data = {
        "positions": metrics["positions"],
        "basket": metrics["basket"],
        "dates": metrics["dates"]
    }
    try:
        submission_response = submit_metrics(submission_data)
        return {"status": "success", "submission_response": submission_response, "request_body": submission_data}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}
