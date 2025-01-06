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

# Define the Position model (I will use this to map the dictionary keys of the positions to the models parameters)
# Pydantic was used to insure all data types conform to what is expected. It is easy to work with in code (dot indexing)
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

# Calculate endpoint
@app.post("/calculate")
async def calculate(
    positions: List[Position] = Depends(load_positions), # will trigger load_positions on endpoint call. Output is list of dictionaries
    target_currency: str = TARGET_CURRENCY,
    start_date: str = START_DATE,
    end_date: str = END_DATE
):
    # Parse positions to the Pydantic model
    parsed_positions = [Position(**pos) for pos in positions] # iterate through dictionaries and unpack dictionaries into Position objects

    # Fetch required data
    fx_rates = get_fx_rates(parsed_positions, start_date, end_date, target_currency)
    prices = get_prices(parsed_positions, start_date, end_date)
    
    # Calculate metrics
    metrics = calculate_metrics(parsed_positions, fx_rates, prices, start_date, end_date, target_currency) 

    # Submit metrics to the API

    submission_data = {
        "positions": metrics["positions"],
        "basket": metrics["basket"],
        "dates": metrics["dates"]
    }
    try:
        submission_response = submit_metrics(submission_data)

        # Save the API response to a JSON file
        response_file_path = "submission_response.json"
        with open(response_file_path, "w") as file:
            json.dump(submission_response, file, indent=4)

        # Save the API request to a JSON file
        request_file_path = "submission_request.json"
        with open(request_file_path, "w") as file:
            json.dump(submission_data, file, indent=4)

        return {"status": "success", "submission_response": submission_response, "request_body": submission_data}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "message": str(e)}
