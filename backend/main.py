from datetime import datetime
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db, engine
from models import (
    Base,
    LastSeen,
    Watchlist,
    PortfolioPosition,
    PortfolioSnapshot,
)
from market_data import get_market_data
from attention_engine import calculate_attention
from portfolio_engine import calculate_portfolio_drift

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
@app.get("/watchlist")
def get_watchlist(db: Session = Depends(get_db)):
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == 1)
        .all()
    )

    market_data = get_market_data()

    result = []

    for item in watchlist:
        if item.symbol not in market_data:
            continue

        stock = market_data[item.symbol]

        result.append({
            "symbol": item.symbol,
            "name": stock["name"],
            "sector": stock["sector"],
            "price": stock["price"],
            "daily_change": stock["daily_change"],
            "attention": calculate_attention(stock),
            "timestamp": stock["timestamp"],
        })

    return result


@app.post("/watchlist/{symbol}")
def add_to_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()

    market_data = get_market_data()

    if symbol not in market_data:
        return {"error": "Stock not found"}

    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == 1,
            Watchlist.symbol == symbol,
        )
        .first()
    )

    if existing:
        return {"message": "Stock already in watchlist"}

    watchlist_item = Watchlist(
        user_id=1,
        symbol=symbol,
    )

    db.add(watchlist_item)
    db.commit()

    return {
        "message": "Stock added to watchlist",
        "symbol": symbol,
    }


@app.delete("/watchlist/{symbol}")
def remove_from_watchlist(
    symbol: str,
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()

    watchlist_item = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == 1,
            Watchlist.symbol == symbol,
        )
        .first()
    )

    if not watchlist_item:
        return {"error": "Stock not in watchlist"}

    db.delete(watchlist_item)

    last_seen = (
        db.query(LastSeen)
        .filter(
            LastSeen.user_id == 1,
            LastSeen.symbol == symbol,
        )
        .first()
    )

    if last_seen:
        db.delete(last_seen)

    db.commit()

    return {
        "message": "Stock removed from watchlist",
        "symbol": symbol,
    }

@app.get("/portfolio")
def get_portfolio(
    db: Session = Depends(get_db),
):
    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.user_id == 1)
        .all()
    )

    market_data = get_market_data()

    result = []
    total_value = 0

    for position in positions:
        if position.symbol not in market_data:
            continue

        stock = market_data[position.symbol]

        value = position.quantity * stock["price"]
        total_value += value

        result.append({
            "symbol": position.symbol,
            "name": stock["name"],
            "quantity": position.quantity,
            "price": stock["price"],
            "value": round(value, 2),
            "target_weight": position.target_weight,
        })

    for item in result:
        item["actual_weight"] = round(
            (item["value"] / total_value) * 100,
            2,
        ) if total_value else 0

        item["drift"] = calculate_portfolio_drift(item)

    return {
        "total_value": round(total_value, 2),
        "positions": result,
    }


@app.post("/portfolio/{symbol}")
def add_portfolio_position(
    symbol: str,
    quantity: float,
    target_weight: float,
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()

    market_data = get_market_data()

    if symbol not in market_data:
        return {"error": "Stock not found"}

    if quantity <= 0:
        return {"error": "Quantity must be greater than 0"}

    if target_weight < 0 or target_weight > 100:
        return {"error": "Target weight must be between 0 and 100"}

    existing = (
        db.query(PortfolioPosition)
        .filter(
            PortfolioPosition.user_id == 1,
            PortfolioPosition.symbol == symbol,
        )
        .first()
    )

    if existing:
        existing.quantity = quantity
        existing.target_weight = target_weight
    else:
        position = PortfolioPosition(
            user_id=1,
            symbol=symbol,
            quantity=quantity,
            target_weight=target_weight,
        )

        db.add(position)

    db.commit()

    return {
        "message": "Portfolio position saved",
        "symbol": symbol,
        "quantity": quantity,
        "target_weight": target_weight,
    }


@app.delete("/portfolio/{symbol}")
def remove_portfolio_position(
    symbol: str,
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()

    position = (
        db.query(PortfolioPosition)
        .filter(
            PortfolioPosition.user_id == 1,
            PortfolioPosition.symbol == symbol,
        )
        .first()
    )

    if not position:
        return {"error": "Position not found"}

    db.delete(position)
    db.commit()

    return {
        "message": "Portfolio position removed",
        "symbol": symbol,
    }

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

@app.post("/check-in")
def check_in(
    db: Session = Depends(get_db),
):
    market_data = get_market_data()

    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == 1)
        .all()
    )

    # Save stock-level snapshot
    checked = []

    for item in watchlist:
        symbol = item.symbol

        if symbol not in market_data:
            continue

        stock = market_data[symbol]

        last_seen = (
            db.query(LastSeen)
            .filter(
                LastSeen.user_id == 1,
                LastSeen.symbol == symbol,
            )
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

        checked.append(symbol)

    # Calculate current portfolio allocation
    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.user_id == 1)
        .all()
    )

    portfolio_values = []

    for position in positions:
        if position.symbol not in market_data:
            continue

        value = position.quantity * market_data[position.symbol]["price"]

        portfolio_values.append({
            "symbol": position.symbol,
            "value": value,
        })

    total_value = sum(
        item["value"] for item in portfolio_values
    )

    snapshot_timestamp = datetime.utcnow()

    for item in portfolio_values:
        actual_weight = (
            item["value"] / total_value * 100
            if total_value
            else 0
        )

        snapshot = PortfolioSnapshot(
            user_id=1,
            symbol=item["symbol"],
            actual_weight=round(actual_weight, 2),
            timestamp=snapshot_timestamp,
        )

        db.add(snapshot)

    db.commit()

    return {
        "message": "Watchlist and portfolio snapshot saved",
        "checked": checked,
        "portfolio_symbols": [
            item["symbol"] for item in portfolio_values
        ],
    }


@app.get("/changes")
def get_changes(db: Session = Depends(get_db)):
    market_data = get_market_data()

    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == 1)
        .all()
    )

    result = []

    # -------------------------
    # Stock-level changes
    # -------------------------

    for item in watchlist:
        symbol = item.symbol

        if symbol not in market_data:
            continue

        last_seen = (
            db.query(LastSeen)
            .filter(
                LastSeen.user_id == 1,
                LastSeen.symbol == symbol,
            )
            .first()
        )

        if not last_seen:
            result.append({
                "symbol": symbol,
                "name": market_data[symbol]["name"],
                "status": "NEW",
                "reason": "This stock was added to your watchlist after your last check.",
            })
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
            "type": "STOCK",
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

    # -------------------------
    # Portfolio structural changes
    # -------------------------

    snapshots = (
        db.query(PortfolioSnapshot)
        .filter(PortfolioSnapshot.user_id == 1)
        .order_by(PortfolioSnapshot.timestamp.desc())
        .all()
    )

    # Get the two most recent portfolio snapshot times
    snapshot_times = sorted(
        {snapshot.timestamp for snapshot in snapshots},
        reverse=True,
    )

    if len(snapshot_times) >= 2:

        current_time = snapshot_times[0]
        previous_time = snapshot_times[1]

        current_snapshots = {
            snapshot.symbol: snapshot.actual_weight
            for snapshot in snapshots
            if snapshot.timestamp == current_time
        }

        previous_snapshots = {
            snapshot.symbol: snapshot.actual_weight
            for snapshot in snapshots
            if snapshot.timestamp == previous_time
        }

        positions = (
            db.query(PortfolioPosition)
            .filter(PortfolioPosition.user_id == 1)
            .all()
        )

        targets = {
            position.symbol: position.target_weight
            for position in positions
        }

        for symbol, current_weight in current_snapshots.items():

            target_weight = targets.get(symbol)

            if target_weight is None:
                continue

            previous_weight = previous_snapshots.get(
                symbol,
                current_weight,
            )

            drift = current_weight - target_weight

            if abs(drift) >= 5:

                result.append({
                    "type": "PORTFOLIO",
                    "symbol": symbol,
                    "previous_weight": previous_weight,
                    "current_weight": current_weight,
                    "target_weight": target_weight,
                    "drift": round(drift, 2),
                    "status": "WORTH_ATTENTION",
                    "reason": (
                        f"{symbol} is {abs(drift):.2f} percentage points "
                        f"{'above' if drift > 0 else 'below'} "
                        f"its target allocation."
                    ),
                })

    result.sort(
        key=lambda item: item.get("anomaly_score", 0),
        reverse=True,
    )

    return result