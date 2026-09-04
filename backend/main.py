from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, engine
from models import Base, LastSeen
from market_data import get_market_data
from attention_engine import calculate_attention

app = FastAPI(title="Smart Market Watchlist API")

Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"message": "Smart Market Watchlist API is running"}


@app.get("/health")
def health_check():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {"status": "healthy", "database": "connected"}


@app.get("/market")
def market():
    market_data = get_market_data()

    result = {}

    for symbol, stock in market_data.items():
        result[symbol] = {
            **stock,
            "attention": calculate_attention(stock),
        }

    return result

@app.post("/last-seen/{symbol}")
def save_last_seen(
    symbol: str,
    db: Session = Depends(get_db),
):
    market_data = get_market_data()

    if symbol not in market_data:
        return {"error": "Stock not found"}

    stock = market_data[symbol]

    last_seen = (
        db.query(LastSeen)
        .filter(LastSeen.user_id == 1, LastSeen.symbol == symbol)
        .first()
    )

    if last_seen:
        last_seen.price = stock["price"]
        last_seen.timestamp = stock["timestamp"]
    else:
        last_seen = LastSeen(
            user_id=1,
            symbol=symbol,
            price=stock["price"],
            timestamp=stock["timestamp"],
        )
        db.add(last_seen)

    db.commit()

    return {
        "symbol": symbol,
        "price": stock["price"],
        "timestamp": stock["timestamp"],
    }

@app.get("/changes")
def get_changes(db: Session = Depends(get_db)):
    market_data = get_market_data()

    last_seen_records = (
        db.query(LastSeen)
        .filter(LastSeen.user_id == 1)
        .all()
    )

    result = []

    for last_seen in last_seen_records:
        symbol = last_seen.symbol

        if symbol not in market_data:
            continue

        stock = market_data[symbol]

        price_change = stock["price"] - last_seen.price

        percentage_change = (
            price_change / last_seen.price
        ) * 100

        attention = calculate_attention(
            stock,
            percentage_change,
        )

        result.append({
            "symbol": symbol,
            "name": stock["name"],
            "previous_price": last_seen.price,
            "current_price": stock["price"],
            "change_percent": round(percentage_change, 2),
            "status": attention["status"],
            "anomaly_score": attention["anomaly_score"],
            "reason": attention["reason"],
            "last_seen": last_seen.timestamp,
            "current_timestamp": stock["timestamp"],
        })

    result.sort(
        key=lambda item: item["anomaly_score"],
        reverse=True,
    )

    return result