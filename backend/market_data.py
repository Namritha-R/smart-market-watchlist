from datetime import datetime, timezone


MARKET_DATA = {
    "INFY": {
        "name": "Infosys",
        "sector": "IT",
        "price": 1800.00,
        "previous_close": 1505.00,
        "sector_change": 0.40,
        "volume": 4200000,
    },
    "TCS": {
        "name": "TCS",
        "sector": "IT",
        "price": 3540.00,
        "previous_close": 3510.00,
        "sector_change": 0.40,
        "volume": 2800000,
    },
    "RELIANCE": {
        "name": "Reliance Industries",
        "sector": "Energy",
        "price": 1420.00,
        "previous_close": 1405.00,
        "sector_change": 0.80,
        "volume": 5100000,
    },
    "HDFCBANK": {
        "name": "HDFC Bank",
        "sector": "Banking",
        "price": 1680.00,
        "previous_close": 1665.00,
        "sector_change": 0.90,
        "volume": 3500000,
    },
    "ICICIBANK": {
        "name": "ICICI Bank",
        "sector": "Banking",
        "price": 1250.00,
        "previous_close": 1242.00,
        "sector_change": 0.90,
        "volume": 3900000,
    },
    "ITC": {
        "name": "ITC",
        "sector": "FMCG",
        "price": 520.00,
        "previous_close": 518.00,
        "sector_change": 0.20,
        "volume": 6100000,
    },
    "HINDUNILVR": {
        "name": "Hindustan Unilever",
        "sector": "FMCG",
        "price": 2650.00,
        "previous_close": 2642.00,
        "sector_change": 0.20,
        "volume": 1800000,
    },
    "SUNPHARMA": {
        "name": "Sun Pharma",
        "sector": "Pharma",
        "price": 1780.00,
        "previous_close": 1770.00,
        "sector_change": 0.30,
        "volume": 2200000,
    },
    "MARUTI": {
        "name": "Maruti Suzuki",
        "sector": "Auto",
        "price": 12500.00,
        "previous_close": 12420.00,
        "sector_change": 0.50,
        "volume": 900000,
    },
    "BHARTIARTL": {
        "name": "Bharti Airtel",
        "sector": "Telecom",
        "price": 1920.00,
        "previous_close": 1905.00,
        "sector_change": 0.60,
        "volume": 2500000,
    },
}


NIFTY_CHANGE = 0.50


def get_market_data():
    timestamp = datetime.now(timezone.utc)

    result = {}

    for symbol, stock in MARKET_DATA.items():
        daily_change = (
            (stock["price"] - stock["previous_close"])
            / stock["previous_close"]
        ) * 100

        result[symbol] = {
            **stock,
            "symbol": symbol,
            "daily_change": round(daily_change, 2),
            "nifty_change": NIFTY_CHANGE,
            "timestamp": timestamp,
        }

    return result