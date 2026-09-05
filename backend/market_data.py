from datetime import datetime, timezone
import time


MARKET_DATA = {
    "INFY": {
        "name": "Infosys",
        "sector": "IT",
        "price": 1505.00,
        "previous_close": 1505.00,
        "sector_change": 0.40,
        "volume": 4200000,
    },
    "TCS": {
        "name": "TCS",
        "sector": "IT",
        "price": 3510.00,
        "previous_close": 3510.00,
        "sector_change": 0.40,
        "volume": 2800000,
    },
    "RELIANCE": {
        "name": "Reliance Industries",
        "sector": "Energy",
        "price": 1405.00,
        "previous_close": 1405.00,
        "sector_change": 0.80,
        "volume": 5100000,
    },
    "HDFCBANK": {
        "name": "HDFC Bank",
        "sector": "Banking",
        "price": 1665.00,
        "previous_close": 1665.00,
        "sector_change": 0.90,
        "volume": 3500000,
    },
    "ICICIBANK": {
        "name": "ICICI Bank",
        "sector": "Banking",
        "price": 1242.00,
        "previous_close": 1242.00,
        "sector_change": 0.90,
        "volume": 3900000,
    },
    "ITC": {
        "name": "ITC",
        "sector": "FMCG",
        "price": 518.00,
        "previous_close": 518.00,
        "sector_change": 0.20,
        "volume": 6100000,
    },
    "HINDUNILVR": {
        "name": "Hindustan Unilever",
        "sector": "FMCG",
        "price": 2642.00,
        "previous_close": 2642.00,
        "sector_change": 0.20,
        "volume": 1800000,
    },
    "SUNPHARMA": {
        "name": "Sun Pharma",
        "sector": "Pharma",
        "price": 1770.00,
        "previous_close": 1770.00,
        "sector_change": 0.30,
        "volume": 2200000,
    },
    "MARUTI": {
        "name": "Maruti Suzuki",
        "sector": "Auto",
        "price": 12420.00,
        "previous_close": 12420.00,
        "sector_change": 0.50,
        "volume": 900000,
    },
    "BHARTIARTL": {
        "name": "Bharti Airtel",
        "sector": "Telecom",
        "price": 1905.00,
        "previous_close": 1905.00,
        "sector_change": 0.60,
        "volume": 2500000,
    },
}


NIFTY_CHANGE = 0.50

SIMULATION_INTERVAL_SECONDS = 15


SIMULATION_MOVEMENTS = {
    # Scenario 0 — Calm market
    0: {
        "INFY": 0.0,
        "TCS": 0.1,
        "RELIANCE": 0.1,
        "HDFCBANK": 0.0,
        "ICICIBANK": 0.1,
        "ITC": 0.0,
        "HINDUNILVR": 0.1,
        "SUNPHARMA": 0.0,
        "MARUTI": 0.1,
        "BHARTIARTL": 0.0,
    },

    # Scenario 1 — Multiple positive company-specific movers
    1: {
        "INFY": 3.5,
        "TCS": 2.8,
        "RELIANCE": 2.4,
        "HDFCBANK": 2.1,
        "SUNPHARMA": 1.9,
        "ICICIBANK": 0.3,
        "ITC": 0.2,
        "HINDUNILVR": 0.1,
        "MARUTI": 0.3,
        "BHARTIARTL": 0.2,
    },

    # Scenario 2 — Multiple negative company-specific movers
    2: {
        "INFY": -3.2,
        "TCS": -2.7,
        "RELIANCE": -2.4,
        "HDFCBANK": -2.1,
        "MARUTI": -1.9,
        "ICICIBANK": -0.2,
        "ITC": 0.0,
        "HINDUNILVR": 0.1,
        "SUNPHARMA": -0.2,
        "BHARTIARTL": 0.1,
    },
}


def get_market_data():
    timestamp = datetime.now(timezone.utc)

    tick = int(time.time() // SIMULATION_INTERVAL_SECONDS)

    scenario = tick % len(SIMULATION_MOVEMENTS)

    movements = SIMULATION_MOVEMENTS[scenario]

    result = {}

    for symbol, stock in MARKET_DATA.items():

        movement = movements.get(symbol, 0.0)

        simulated_price = (
            stock["price"] * (1 + movement / 100)
        )

        daily_change = (
            (simulated_price - stock["previous_close"])
            / stock["previous_close"]
        ) * 100

        result[symbol] = {
            **stock,
            "symbol": symbol,
            "price": round(simulated_price, 2),
            "daily_change": round(daily_change, 2),
            "nifty_change": NIFTY_CHANGE,
            "timestamp": timestamp,
            "scenario": scenario,
        }

    return result