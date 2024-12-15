from datetime import datetime, timedelta
import math

def calculate_is_open(positions, date_range):
    """
    Calculate the `IsOpen` metric for each position and at the basket level.
    
    Args:
        positions (list): List of positions (dictionaries).
        date_range (list): List of dates in the range.

    Returns:
        dict: A dictionary containing `IsOpen` values for each position and the basket.
    """    

    # Initialize results
    position_is_open = {}
    basket_is_open = [0.0] * len(date_range)

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
                is_open = 1.0 if open_date <= current_date < close_date else 0.0
            else:
                is_open = 1.0 if open_date <= current_date else 0.0
            pos_is_open.append(is_open)

        position_is_open[position.id] = pos_is_open
        
        # Update basket-level IsOpen (this will check each current date value for the current position vs any position in basket)
        basket_is_open = [
            max(basket, pos) for basket, pos in zip(basket_is_open, pos_is_open)
        ]

    # Build the result
    return {
        "positions": position_is_open,
        "basket": basket_is_open,
    }

def calculate_price(positions, fx_rates, prices, date_range, target_currency):
    """
    Calculate the `Price` metric for each position. Basket will alays be 0

    Args:
        positions (list): List of positions (dictionaries).
        fx_rates (dict): Forex rates data with dates as keys.
        prices (dict): Local currency prices data with instrument IDs as keys.
        date_range (list): List of dates in the range.
        target_currency (str): The target currency.

    Returns:
        dict: A dictionary containing `Price` values for each position and the basket.
    """    

    # Initialize results
    position_prices = {}   
    basket_prices = [0.0] * len(date_range)  # Basket price is always 0 as per the PDF 

    # Calculate Price for each position
    for position in positions:
        pos_prices = []
        position_id = position.id
        instrument_id = position.instrument_id
        instrument_currency = position.instrument_currency

         # Ensure position ID exists in prices and then check for instrument ID
        # if position_id not in prices or str(instrument_id) not in prices[position_id]:
        #     raise ValueError(
        #         f"Missing price data for position {position_id} with instrument {instrument_id} in currency {instrument_currency}"
        #     )
        # Extract list of daily prices for current instrument
        daily_prices = prices[position_id][str(instrument_id)]

        # Loop through each date in the range
        for t, current_date in enumerate(date_range): # itterate through index (t) and value (current_date)
            # Determine if position has been opened before or on current date
            is_open = datetime.strptime(position.open_date, "%Y-%m-%d").date() <= current_date

            if not is_open:
                price_lc = 0.0
            else:
                # filter list of daily prices to match the current date itteration
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
            
            pos_prices.append(price_tc)  # Apending each price point to the list          

        position_prices[position.id] = pos_prices # Adding the list of prices to the position_prices dictionary

    # Build the result
    return {
        "positions": position_prices,  
        "basket": basket_prices      
    }

def calculate_quantity(positions, date_range, is_open):
    """
    Calculate the quantity metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        is_open (dict): The IsOpen metric calculated for positions.

    Returns:
        dict: A dictionary containing quantities for positions and the basket.
    """

    # Initialize results
    position_quant = {}
    basket_quant = [0.0] * len(date_range)

    for position in positions:        
        quantity = position.quantity
        position_id = position.id
    
        pos_is_open = is_open["positions"][position_id] # Get the list per position id

        quant_list = [open_status * quantity for open_status in pos_is_open]

        position_quant[position.id] = quant_list

        for t, pos_quant in enumerate(quant_list):
            basket_quant[t] += pos_quant


    return {
        "positions": position_quant,
        "basket": basket_quant
    }

def calculate_value(positions, price, quantity, date_range):
    """
    Calculate the `Value` metric for each position and the basket.

    Args:
        positions (list): List of positions.
        price (dict): Price metric for each position.
        quantity (dict): Quantity metric for each position.
        date_range (list): List of dates in the range.

    Returns:
        dict: A dictionary containing Value for each position and the basket.
    """
    
    # Initialize results
    position_value = {}
    basket_value = [0.0] * len(date_range)    

    # Value_tc = Price_tc * Quantity_i,t
    for position in positions:
        position_id = position.id

        quant_list = quantity["positions"][position_id]
        price_list = price["positions"][position_id]

        # Multiply quantity and price for each time step
        value_list = [q * p for q, p in zip(quant_list,price_list)]

        # Store the calculated values for the position
        position_value[position_id] = value_list
        
        # Update basket value by adding position's value for each date
        for t, pos_value in enumerate(value_list):
            basket_value[t] += pos_value

        # basket_value = [basket for basket in basket_value]

    
    return {
        "positions": position_value,
        "basket": basket_value
    }

def calculate_open_price(positions, date_range, fx_rates, target_currency):
    """
    Calculate the `OpenPrice` metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        fx_rates (dict): Forex rates data with dates as keys.
        target_currency (str): The target currency.

    Returns:
        dict: A dictionary containing OpenPrice for each position and the basket.
    """
    # Initilize variables
    position_open_price = {}
    basket_open_price = [0] * len(date_range)

    for position in positions:        
        position_id = position.id
        open_price_lc = position.open_price
        instrument_id = position.instrument_id
        instrument_currency = position.instrument_currency
        open_date = position.open_date

        if instrument_currency == target_currency:
            open_price_tc = open_price_lc
        else:

            daily_rates = fx_rates[f"{instrument_currency}{target_currency}"]
            fx_rate = next((entry["rate"] for entry in daily_rates if entry["date"] == open_date), 1.0)
            # for fx_dict in daily_rates:
            #     if fx_dict["date"] == open_date:
            #         fx_rate = fx_dict["rate"]
            #         break                
                
            open_price_tc = open_price_lc * fx_rate

        position_open_price[position_id] = [open_price_tc] * len(date_range)        

    return {
        "positions": position_open_price,
        "basket": basket_open_price
    }

def calculate_closed_price(positions, fx_rates, date_range, target_currency):
    """
    Calculate the `ClosedPrice` metric for each position and the basket.

    Args:
        positions (list): List of positions.
        fx_rates (dict): Forex rates data with dates as keys.
        date_range (list): List of dates in the range.
        target_currency (str): The target currency.

    Returns:
        dict: A dictionary containing ClosedPrice for each position and the basket.
    """
    # Initialize results
    position_closed_price = {}
    basket_closed_price = [0.0] * len(date_range)

    for position in positions:
        position_id = position.id
        close_date = position.close_date
        close_price_lc = position.close_price  # The provided close price in local currency
        instrument_currency = position.instrument_currency

        # Convert ClosePriceLC to ClosePriceTC using the forex rate on the close date
        if close_price_lc is None:
            close_price_tc = 0.0  # Default to 0 for missing close price (this will not impact any of the required metrics)
        elif instrument_currency == target_currency: 
            close_price_tc = close_price_lc
        else:
            daily_rates = fx_rates[f"{instrument_currency}{target_currency}"]
            fx_rate = next((entry["rate"] for entry in daily_rates if entry["date"] == close_date), 1.0)
            # for fx_dict in daily_rates:
            #     if fx_dict["date"] == close_date:
            #         fx_rate = fx_dict["rate"]
            #         break
            close_price_tc = close_price_lc * fx_rate

        # Store the converted close price
        position_closed_price[position_id] = [close_price_tc] * len(date_range)

    return {
        "positions": position_closed_price,
        "basket": basket_closed_price 
    }

def calculate_open_value(positions, date_range, openPrice_dict):
    """
    Calculate the `OpenValue` metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        openPrice_dict (dict): OpenPrice metric for each position.
        

    Returns:
        dict: A dictionary containing OpenValue for each position and the basket.
    """

    # Initilize variables
    position_open_value = {}
    basket_open_value = [0] * len(date_range)    
    

    for position in positions:
        open_value_list = []
        position_id = position.id
        position_open_date = datetime.strptime(position.open_date, "%Y-%m-%d").date()
        position_quant = position.quantity

        openPrice_list = openPrice_dict["positions"][position_id] # get list of openPrice

        for t, current_date in enumerate(date_range):
            # Multiply quantity and open price for each time step            
            if current_date >= position_open_date:
                open_value = position_quant * openPrice_list[t]
            else:
                open_value = 0
            open_value_list.append(open_value)
            basket_open_value[t] += open_value

        position_open_value[position_id] = open_value_list

        # Update basket value by adding position's value for each date
        # for t, pos_open_value in enumerate(open_value_list):
        #     basket_open_value[t] += pos_open_value

    return {
        "positions": position_open_value,
        "basket": basket_open_value
    }

def calculate_close_value(positions, date_range, closePrice_dict):
    """
    Calculate the `CloseValue` metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        closePrice_dict (dict): ClosePrice metric for each position.

    Returns:
        dict: A dictionary containing CloseValue for each position and the basket.
    """

    # Initilize variables
    position_close_value = {}
    basket_close_value = [0] * len(date_range)   
    

    for position in positions:
        close_value_list = []
        position_id = position.id
        position_close_date = (
            datetime.strptime(position.close_date, "%Y-%m-%d").date()
            if position.close_date
            else None
        )  # Handle None close_date
        position_quant = position.quantity

        closePrice_list = closePrice_dict["positions"][position_id] # get list of openPrice

        for t, current_date in enumerate(date_range):
            # Multiply quantity and open price for each time step            
            if position_close_date and current_date >= position_close_date:
                close_value = position_quant * closePrice_list[t]
            else:
                close_value = 0
            close_value_list.append(close_value)
            basket_close_value[t] += close_value

        position_close_value[position_id] = close_value_list        

        # Update basket value by adding position's value for each date
        # for t, pos_close_value in enumerate(close_value_list):
        #     basket_close_value[t] += pos_close_value

    return {
        "positions": position_close_value,
        "basket": basket_close_value
    }

def calculate_ReturnPerPeriod(positions, date_range, openValue_dict, closeValue_dict, value_dict):
    """
    Calculate the `ReturnPerPeriod` (RPP) metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        openValue_dict (dict): OpenValue metric for each position.
        closeValue_dict (dict): CloseValue metric for each position.
        value_dict (dict): Value metric for each position.

    Returns:
        dict: A dictionary containing RPP for each position and the basket.
    """
    position_RPP = {}
    basket_RPP = [0.0] * len(date_range)   
    

    for position in positions:
        position_id = position.id
        position_open_date = datetime.strptime(position.open_date,"%Y-%m-%d").date()
        position_close_date = datetime.strptime(position.close_date,"%Y-%m-%d").date() if position.close_date else None

        open_value_list = openValue_dict["positions"][position_id]
        close_value_list = closeValue_dict["positions"][position_id]
        value_list = value_dict["positions"][position_id]

        RPP_list = []

        for t, current_date in enumerate(date_range):
            # Check is current date < open date, OR if there is a close date assinged AND current date is > close date
            if current_date < position_open_date or (position_close_date and current_date > position_close_date): 
                rpp = 0.0
            else:
                # Determine ValueTC_Start
                if current_date == position_open_date:
                    ValueTC_Start = open_value_list[t]
                elif current_date == date_range[0]:
                    ValueTC_Start = value_list[t]
                else:
                    ValueTC_Start = value_list[t-1]

                # Determine ValueTC_End
                if position_close_date and current_date == position_close_date:
                    ValueTC_End = close_value_list[t]
                else:
                    ValueTC_End = value_list[t]

                rpp = ValueTC_End - ValueTC_Start
            # rpp = round_down(rpp,8)
            # rpp = rpp.quantize(Decimal('1.00000000'), rounding=ROUND_HALF_UP)
            RPP_list.append(rpp)

            basket_RPP[t] += rpp

        position_RPP[position_id] = RPP_list

        # Update basket value by adding position's value for each date
        # for t, pos_rpp in enumerate(RPP_list):
        #     basket_RPP[t] += pos_rpp        

    return {
        "positions": position_RPP,
        "basket": basket_RPP
    }

def calculate_ReturnPerPeriodPercentage(positions, date_range, openValue_dict, closeValue_dict, value_dict):
    """
    Calculate the `ReturnPerPeriodPercentage` (RPPP) metric for each position and the basket.

    Args:
        positions (list): List of positions.
        date_range (list): List of dates in the range.
        openValue_dict (dict): OpenValue metric for each position.
        closeValue_dict (dict): CloseValue metric for each position.
        value_dict (dict): Value metric for each position.

    Returns:
        dict: A dictionary containing RPPP for each position and the basket.
    """

    # Initialize results
    position_RPPP = {}
    basket_RPPP = [0.0] * len(date_range)

    # Basket-level accumulators for each date
    basket_rpp_sums = [0.0] * len(date_range)
    basket_value_start_sums = [0.0] * len(date_range)

    for position in positions:
        position_id = position.id
        position_open_date = datetime.strptime(position.open_date,"%Y-%m-%d").date()
        position_close_date = datetime.strptime(position.close_date,"%Y-%m-%d").date() if position.close_date else None

        open_value_list = openValue_dict["positions"][position_id]
        close_value_list = closeValue_dict["positions"][position_id]
        value_list = value_dict["positions"][position_id]

        RPPP_list = []

        for t, current_date in enumerate(date_range):

            if current_date < position_open_date or (position_close_date and current_date > position_close_date): 
                rppp = 0.0
                rpp = 0.0
                basket_rpp_sums[t] += rpp
                basket_value_start_sums[t] += 0.0
            else:
                # Determine ValueTC_Start
                if current_date == position_open_date:
                    ValueTC_Start = open_value_list[t]
                elif current_date == date_range[0]:
                    ValueTC_Start = value_list[t]
                else:
                    ValueTC_Start = value_list[t-1]

                # Determine ValueTC_End
                if position_close_date and current_date == position_close_date:
                    ValueTC_End = close_value_list[t]
                else:
                    ValueTC_End = value_list[t]

                if ValueTC_Start != 0:
                    rpp = ValueTC_End - ValueTC_Start
                    rppp = (rpp / ValueTC_Start)

                    # Accumulate for basket-level RPP and start value
                    basket_rpp_sums[t] += rpp
                    basket_value_start_sums[t] += ValueTC_Start
                else:
                    rppp = 0
                    rpp = ValueTC_End - ValueTC_Start
                    basket_rpp_sums[t] += rpp
                    basket_value_start_sums[t] += ValueTC_Start

            RPPP_list.append(rppp)

        position_RPPP[position_id] = RPPP_list

    # Calculate basket-level RPPP for each date
    for t in range(len(date_range)):
        if basket_value_start_sums[t] != 0:
            basket_RPPP[t] = (basket_rpp_sums[t] / basket_value_start_sums[t])
        else:
            basket_RPPP[t] = 0.0   

    return {
        "positions": position_RPPP,
        "basket": basket_RPPP
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
    # Initialize results
    results = {
        "positions": {},
        "basket": {},
        "dates": []
    }

    # Parse the date range (this is used for the itteration through postitions data)
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [(start + timedelta(days=i)).date() for i in range((end - start).days + 1)]

    dates = [str(d) for d in date_range]  # Get the list of dates in string format
    results["dates"] = dates

    # Calculate Metrics
    is_open = calculate_is_open(positions, date_range)    
    price = calculate_price(positions, fx_rates, prices, date_range, target_currency)
    quantity = calculate_quantity(positions, date_range, is_open)
    value = calculate_value(positions, price, quantity, date_range)    
    openPrice = calculate_open_price(positions, date_range, fx_rates, target_currency)
    openValue = calculate_open_value(positions, date_range, openPrice)
    closePrice = calculate_closed_price(positions, fx_rates, date_range, target_currency)
    closeValue = calculate_close_value(positions, date_range, closePrice)
    rpp = calculate_ReturnPerPeriod(positions, date_range, openValue, closeValue, value)
    rppp = calculate_ReturnPerPeriodPercentage(positions, date_range, openValue, closeValue, value)

    # Populate basket metrics
    basket_metrics = {
        "IsOpen": is_open["basket"],
        "Price": price["basket"], # Basket price should always be 0
        "Value": value["basket"],
        "ReturnPerPeriod": rpp["basket"],
        "ReturnPerPeriodPercentage": rppp["basket"]
    }

    # Loop through positions and calculate metrics
    for position in positions:
        position_id = position.id        

        # Calculate metrics for the position
        position_metrics = {
            "IsOpen": is_open["positions"][position_id],
            "Price": price["positions"][position_id],
            "Value": value["positions"][position_id], 
            "ReturnPerPeriod": rpp["positions"][position_id],  
            "ReturnPerPeriodPercentage": rppp["positions"][position_id]  
        }

        # Add position metrics to results
        results["positions"][position_id] = position_metrics        

    # Add basket metrics to results
    results["basket"] = basket_metrics

    return results
