import requests

BASE_URL = "https://api.challenges.performativ.com"
API_KEY = "FSPkaSbQA55Do0nXhSZkH9eKWVlAMmNP7OKlI2oA" 

# def test_api_key():
#     url = f"{BASE_URL}/fx-rates"
#     headers = {
#         "x-api-key": API_KEY,
#         "Accept": "application/json"
#     }
#     params = {
#         "pairs" : "EURUSD",
#         "start_date": "20240101",
#         "end_date": "20240102"
#     }

#     response = requests.get(url, headers=headers, params=params)

#     if response.status_code == 200:
#         return {"status": "success", "data": response.json()}
#     else:
#         return {"status": "error", "code": response.status_code, "message": response.text}


def get_fx_rates(positions, start_date, end_date, target_currency):

    start_date = start_date.replace("-", "")
    end_date = end_date.replace("-", "")

    local_currencies = {pos.instrument_currency for pos in positions if pos.instrument_currency != target_currency}
    pairs = ",".join([f"{lc}{target_currency}" for lc in local_currencies])
    
    url = f"{BASE_URL}/fx-rates"
    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    params = {"pairs": pairs, "start_date": start_date, "end_date": end_date}
    
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_prices(positions, start_date, end_date):

    start_date = start_date.replace("-", "")
    end_date = end_date.replace("-", "")

    prices = {}
    headers = {"x-api-key": API_KEY, "Accept": "application/json"}
    for pos in positions:
        url = f"{BASE_URL}/prices"
        params = {"instrument_id": pos.instrument_id, "start_date": start_date, "end_date": end_date}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        prices[pos.id] = response.json()
    return prices

