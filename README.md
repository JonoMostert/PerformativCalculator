# Performativ Tech Challenge Calculator

This repository implements a solution for the Performativ technical challenge. It calculates various financial metrics such as `isOpen`, `Price`, `Value`, `ReturnPerPeriod (RPP)`, and `ReturnPerPeriodPercentage (RPPP)` for positions and their corresponding basket metrics.

## Project Structure

### 1. `main.py`
The entry point of the application. Implements the FastAPI server with the /calculate endpoint to compute metrics and submit the results.

Key functionalities:
* Loads positions from a JSON file.
* Fetches FX rates and prices using utility functions.
* Calls the calculate_metrics function to compute metrics.

### 2. `metrics.py`
Contains all financial metric calculations.

Key functions:
* `calculate_is_open`: Computes whether a position is open on each date within the date range.
* `calculate_price`: Converts instrument prices into the target currency.
* `calculate_quantity`: Calculates the position quantities based on the IsOpen metric.
* `calculate_value`: Multiplies Price and Quantity to compute the monetary value of positions.
* `calculate_open_price and calculate_closed_price`: Converts open_price and close_price to the target currency.
* `calculate_open_value and calculate_close_value`: Computes values based on the open_price and close_price, respectively.
* `calculate_ReturnPerPeriod`: Calculates the monetary return per period for each position and basket.
* `calculate_ReturnPerPeriodPercentage`: Computes the percentage return per period for positions and the basket.

### 3. `utils.py`
Contains utility functions for GET requests to API endpoints. Essentially gets FX-rates and Prices.

Key functions:
* `get_fx_rates`: Fetches foreign exchange rates for converting prices.
* `get_prices`: Fetches instrument prices for the specified date range.
* `submit_metrics`: Submits the calculated metrics to the Performativ API submission endpoint.

# Run Application
Run the following commands:

## Set up project and install dependancies
```shell script
git clone https://github.com/JonoMostert/PerformativCalculator.git
cd PerformativCalculator
python -m venv .venv
.venv\Scripts\activate # on mac: source .venv/bin/activate
pip install -r requirements.txt
```
For use of a different API key, some modifications would need to be made to either the utils.py file, or create a .env file.

## Start FastAPI server
```shell script
uvicorn main:app --reload
```

## Send the POST request
I used Postman to send my POST request to the submit API endpoint.

