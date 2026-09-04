import numpy as np
from historical_data import get_normal_volatility

def calculate_attention(stock):
    """
    Determine whether a stock's movement deserves attention.
    """

    daily_change = stock["daily_change"]
    sector_change = stock["sector_change"]
    nifty_change = stock["nifty_change"]

    # How much the stock moved differently from its sector
    relative_to_sector = daily_change - sector_change

    # Temporary historical volatility for our simulation.
    # Later this will come from real historical market data.
    normal_volatility = get_normal_volatility(stock["symbol"])

    # How unusual today's movement is
    anomaly_score = abs(daily_change) / normal_volatility

    # Conditions for attention
    unusually_large = anomaly_score >= 2.0
    stock_specific = abs(relative_to_sector) >= 1.5

    if unusually_large and stock_specific:
        status = "WORTH_ATTENTION"
        reason = (
            f"Movement is unusually large for this stock "
            f"({daily_change:+.2f}%) and significantly different "
            f"from its sector ({sector_change:+.2f}%)."
        )

    elif abs(daily_change - nifty_change) < 1.0:
        status = "MARKET_WIDE"
        reason = (
            f"Stock moved {daily_change:+.2f}%, while Nifty moved "
            f"{nifty_change:+.2f}%, suggesting the movement is "
            f"largely aligned with the broader market."
        )

    else:
        status = "NORMAL"
        reason = (
            f"Movement of {daily_change:+.2f}% is within the "
            f"expected range or is not sufficiently different "
            f"from its sector."
        )

    return {
        "status": status,
        "relative_to_sector": round(relative_to_sector, 2),
        "anomaly_score": round(anomaly_score, 2),
        "reason": reason,
    }