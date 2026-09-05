from market_data import get_market_data


NEWS_EVENTS = {
    0: {
        "INFY": {
            "headline": "Infosys sees steady trading activity",
            "summary": "No major company-specific development is affecting Infosys at the moment.",
        },
        "TCS": {
            "headline": "TCS trading remains broadly stable",
            "summary": "TCS is seeing normal market activity with no major company-specific development.",
        },
        "RELIANCE": {
            "headline": "Reliance trading remains stable",
            "summary": "Reliance Industries is seeing routine market activity without a major new company-specific event.",
        },
        "HDFCBANK": {
            "headline": "HDFC Bank sees normal trading activity",
            "summary": "HDFC Bank is trading without a significant new company-specific development.",
        },
        "ICICIBANK": {
            "headline": "ICICI Bank trading remains steady",
            "summary": "ICICI Bank is seeing normal market activity with no major company-specific development.",
        },
        "ITC": {
            "headline": "ITC sees stable market activity",
            "summary": "ITC is trading normally without a significant company-specific development.",
        },
        "HINDUNILVR": {
            "headline": "Hindustan Unilever trading remains stable",
            "summary": "Hindustan Unilever is seeing routine market activity without a major new development.",
        },
        "SUNPHARMA": {
            "headline": "Sun Pharma sees normal trading activity",
            "summary": "Sun Pharma is trading normally with no significant company-specific development.",
        },
        "MARUTI": {
            "headline": "Maruti Suzuki trading remains steady",
            "summary": "Maruti Suzuki is seeing normal market activity without a major company-specific event.",
        },
        "BHARTIARTL": {
            "headline": "Bharti Airtel trading remains stable",
            "summary": "Bharti Airtel is trading normally without a significant company-specific development.",
        },
    },

    1: {
        "INFY": {
            "headline": "Infosys announces major technology contract",
            "summary": "Infosys announces a major technology contract, creating a company-specific development for investors to review.",
        },
        "TCS": {
            "headline": "TCS expands enterprise technology partnership",
            "summary": "TCS announces an expansion of an enterprise technology partnership, attracting investor attention.",
        },
        "RELIANCE": {
            "headline": "Reliance announces expansion of digital operations",
            "summary": "Reliance announces an expansion of its digital operations as investors assess its growth plans.",
        },
        "HDFCBANK": {
            "headline": "HDFC Bank reports strong credit growth",
            "summary": "Strong credit growth increases investor attention toward HDFC Bank.",
        },
        "ICICIBANK": {
            "headline": "ICICI Bank reports healthy loan growth",
            "summary": "Healthy loan growth provides a new company-specific development for investors to review.",
        },
        "ITC": {
            "headline": "ITC reports stronger-than-expected demand",
            "summary": "Improving demand across key consumer categories draws attention to ITC.",
        },
        "HINDUNILVR": {
            "headline": "Hindustan Unilever sees improving consumer demand",
            "summary": "Improving consumer demand becomes a notable development for Hindustan Unilever.",
        },
        "SUNPHARMA": {
            "headline": "Sun Pharma receives positive regulatory update",
            "summary": "A positive regulatory development draws investor attention toward Sun Pharma.",
        },
        "MARUTI": {
            "headline": "Maruti Suzuki reports strong vehicle bookings",
            "summary": "Strong vehicle bookings create a company-specific development for Maruti Suzuki.",
        },
        "BHARTIARTL": {
            "headline": "Bharti Airtel reports strong subscriber additions",
            "summary": "Strong subscriber additions increase investor attention toward Bharti Airtel.",
        },
    },

    2: {
        "INFY": {
            "headline": "Infosys faces weaker technology demand outlook",
            "summary": "A weaker technology demand outlook raises concerns around near-term growth expectations for Infosys.",
        },
        "TCS": {
            "headline": "TCS sees cautious enterprise spending outlook",
            "summary": "A cautious enterprise spending outlook creates a development investors may want to review.",
        },
        "RELIANCE": {
            "headline": "Reliance faces pressure from weaker energy prices",
            "summary": "Weaker energy prices create a potential pressure point for Reliance Industries.",
        },
        "HDFCBANK": {
            "headline": "HDFC Bank faces tighter margin outlook",
            "summary": "A tighter margin outlook becomes a factor investors may want to review for HDFC Bank.",
        },
        "ICICIBANK": {
            "headline": "ICICI Bank sees cautious credit outlook",
            "summary": "A cautious credit outlook creates a new development for ICICI Bank investors to assess.",
        },
        "ITC": {
            "headline": "ITC faces higher input cost concerns",
            "summary": "Higher input costs become a potential pressure point for ITC.",
        },
        "HINDUNILVR": {
            "headline": "Hindustan Unilever faces cautious demand outlook",
            "summary": "A cautious consumer demand outlook becomes a development investors may want to review.",
        },
        "SUNPHARMA": {
            "headline": "Sun Pharma faces regulatory uncertainty",
            "summary": "Regulatory uncertainty becomes a factor investors may want to review for Sun Pharma.",
        },
        "MARUTI": {
            "headline": "Maruti Suzuki sees cautious auto demand outlook",
            "summary": "A cautious auto demand outlook creates a new development for Maruti Suzuki.",
        },
        "BHARTIARTL": {
            "headline": "Bharti Airtel faces competitive pricing pressure",
            "summary": "Competitive pricing pressure becomes a factor investors may want to review for Bharti Airtel.",
        },
    },
}


def get_news(symbols=None):
    market_data = get_market_data()

    if symbols is None:
        symbols = list(market_data.keys())

    news = []

    for symbol in symbols:

        if symbol not in market_data:
            continue

        stock = market_data[symbol]
        scenario = stock["scenario"]

        event = NEWS_EVENTS.get(scenario, {}).get(symbol)

        if not event:
            continue

        news.append({
            "symbols": [symbol],
            "headline": event["headline"],
            "summary": event["summary"],
            "source": "Simulated Market Event",
            "url": "",
            "published_at": stock["timestamp"],
            "scenario": scenario,
        })

    return news