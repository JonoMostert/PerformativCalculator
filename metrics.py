from datetime import datetime, timedelta

def calculate_is_open(positions, start_date, end_date):
    """
    Calculate the `IsOpen` metric for each position and at the basket level.
    
    Args:
        positions (list): List of positions (dictionaries or Pydantic models).
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.

    Returns:
        dict: A dictionary containing `IsOpen` values for each position and the basket.
    """
    # Parse the date range (this is used for the itteration through postitions data)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]

    # Initialize results
    position_is_open = {}
    basket_is_open = [0] * len(date_range)

    # Calculate IsOpen for each position
    for position in positions:
        pos_is_open = []
        open_date = datetime.strptime(position.open_date, "%Y-%m-%d").date()
        close_date = (
            datetime.strptime(position.close_date, "%Y-%m-%d").date()
            if position.close_date
            else None
        )
        # This checks the current date itteration and assigns 1 for open or 0 for closed
        for current_date in date_range:
            if close_date:
                is_open = 1 if open_date <= current_date < close_date else 0
            else:
                is_open = 1 if open_date <= current_date else 0
            pos_is_open.append(is_open)

        position_is_open[position.id] = pos_is_open
        
        # Update basket-level IsOpen (this will check each current data value for the current position vs any position in basket)
        basket_is_open = [
            max(basket, pos) for basket, pos in zip(basket_is_open, pos_is_open)
        ]

    # Build the result
    return {
        "positions": position_is_open,
        "basket": basket_is_open,
        "dates": [str(d) for d in date_range],
    }

def calculate_price(positions, fx_rates, prices, start_date, end_date, target_currency):
    """
    Calculate the `Price` metric for each position and at the basket level.

    Args:
        positions (list): List of positions (dictionaries or Pydantic models).
        fx_rates (dict): Forex rates data with dates as keys.
        prices (dict): Local currency prices data with instrument IDs as keys.
        start_date (str): Start date in "YYYY-MM-DD" format.
        end_date (str): End date in "YYYY-MM-DD" format.

    Returns:
        dict: A dictionary containing `Price` values for each position and the basket.
    """    

    # Parse the date range
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]

    # Initialize results
    position_prices = {}
    basket_prices = [0.0] * len(date_range)

    # Calculate Price for each position
    for position in positions:
        pos_prices = []
        position_id = position.id
        instrument_id = position.instrument_id
        instrument_currency = position.instrument_currency

         # Ensure position ID exists in prices and then check for instrument ID
        if position_id not in prices or str(instrument_id) not in prices[position_id]:
            raise ValueError(
                f"Missing price data for position {position_id} with instrument {instrument_id} in currency {instrument_currency}"
            )

            # Loop through each date in the range
        for t, current_date in enumerate(date_range):
            # Find the price for the current date
            daily_prices = prices[position_id][str(instrument_id)]
            price_lc = next(
                (entry["price"] for entry in daily_prices if entry["date"] == str(current_date)), 0.0
            )  # Default to 0 if no price for the date

            if instrument_currency == target_currency:
                price_tc = price_lc
            else:
                daily_rates = fx_rates[f"{instrument_currency}{target_currency}"]
                fx_rate = next(
                    (entry["rate"] for entry in daily_rates if entry["date"] == str(current_date)), 1.0
            )  # Default to 1.0 if the date is missing
                price_tc = price_lc * fx_rate
            
            pos_prices.append(price_tc)

            # Update basket-level Price
            basket_prices[t] += price_tc

        position_prices[position.id] = pos_prices

    # Build the result
    return {
        "positions": position_prices,
        "basket": basket_prices,
        "dates": [str(d) for d in date_range],
    }





def calculate_metrics(positions, fx_rates, prices, start_date, end_date, target_currency):
    """
    Main function to calculate all required financial metrics.
    
    Args:
        positions (list): List of positions.
        fx_rates (dict): FX rates data.
        prices (dict): Prices data.
        start_date (str): Start date.
        end_date (str): End date.
        target_currency (str): Target currency.

    Returns:
        dict: The calculated metrics for positions and the basket.
    """
    results = {}

    # Calculate IsOpen metric
    is_open = calculate_is_open(positions, start_date, end_date)
    results["IsOpen"] = is_open

    # Calculate Price metric
    price = calculate_price(positions, fx_rates, prices, start_date, end_date, target_currency)
    results["Price"] = price

    # Placeholder for other metrics
    # e.g., Price, Value, ReturnPerPeriod, ReturnPerPeriodPercentage
    
    return results
