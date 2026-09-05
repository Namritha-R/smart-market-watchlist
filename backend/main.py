# pyrefly: ignore-file

from sqlalchemy.connectors import aioodbc
import attention_engine

from sqlalchemy.engine import result
from datetime import datetime
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from data_quality import is_stale
from database import get_db, engine
from models import (
    Base,
    LastSeen,
    Watchlist,
    PortfolioPosition,
    PortfolioSnapshot,
    Thesis,
)
from market_data import get_market_data
from attention_engine import calculate_attention
from portfolio_engine import calculate_portfolio_drift
from thesis_data import get_thesis_data
from thesis_engine import evaluate_thesis
from ai_engine import prioritize_market_changes
from news_data import get_news
app = FastAPI(title="Smart Market Watchlist API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
            "attention": calculate_attention(
                stock,
                stale=is_stale(stock["timestamp"]),
            ),
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
            "attention": calculate_attention(
    stock,
    stale=is_stale(stock["timestamp"]),
),
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
        raise HTTPException(status_code=404, detail="Stock not found")

    existing = (
        db.query(Watchlist)
        .filter(
            Watchlist.user_id == 1,
            Watchlist.symbol == symbol,
        )
        .first()
    )

    if existing:
        raise HTTPException(status_code=409, detail="Stock already in watchlist")

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
        raise HTTPException(status_code=404, detail="Stock not in watchlist")

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
        raise HTTPException(status_code=404, detail="Stock not found")

    if quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    if target_weight < 0 or target_weight > 100:
        raise HTTPException(status_code=400, detail="Target weight must be between 0 and 100")

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
        raise HTTPException(status_code=404, detail="Position not found")

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
        raise HTTPException(status_code=404, detail="Stock not found")

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

        stmt = insert(LastSeen).values(
            user_id=1,
            symbol=symbol,
            price=stock["price"],
            timestamp=stock["timestamp"],
        )

        stmt = stmt.on_conflict_do_update(
            constraint="unique_last_seen",
            set_={
                "price": stock["price"],
                "timestamp": stock["timestamp"],
            },
        )

        db.execute(stmt)

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
    # Update thesis state
    theses = (
        db.query(Thesis)
        .filter(Thesis.user_id == 1)
        .all()
    )

    current_thesis_data = get_thesis_data()

    for thesis in theses:

        if thesis.symbol not in current_thesis_data:
            continue

        current_value = current_thesis_data[thesis.symbol]["growth"]

        evaluation = evaluate_thesis(
            thesis.thesis_type,
            current_value,
            thesis.threshold,
        )

        thesis.last_value = current_value
        thesis.last_status = evaluation["status"]
        thesis.timestamp = datetime.utcnow()

    db.commit()

    return {
        "message": "Watchlist and portfolio snapshot saved",
        "checked": checked,
        "portfolio_symbols": [
            item["symbol"] for item in portfolio_values
        ],
    }

@app.post("/thesis/{symbol}")
def save_thesis(
    symbol: str,
    db: Session = Depends(get_db),
):
    symbol = symbol.upper()

    thesis_data = get_thesis_data()

    if symbol not in thesis_data:
        raise HTTPException(status_code=404, detail="Thesis data not available")

    current_value = thesis_data[symbol]["growth"]
    thesis_type = "growth"
    threshold = 15.0

    evaluation = evaluate_thesis(
        thesis_type,
        current_value,
        threshold,
    )

    thesis = (
        db.query(Thesis)
        .filter(
            Thesis.user_id == 1,
            Thesis.symbol == symbol,
        )
        .first()
    )

    if thesis:
        thesis.thesis_type = thesis_type
        thesis.threshold = threshold
        thesis.last_value = current_value
        thesis.last_status = evaluation["status"]
        thesis.timestamp = datetime.utcnow()
    else:
        thesis = Thesis(
            user_id=1,
            symbol=symbol,
            thesis_type=thesis_type,
            threshold=threshold,
            last_value=current_value,
            last_status=evaluation["status"],
        )

        db.add(thesis)

    db.commit()

    return {
        "symbol": symbol,
        "thesis_type": thesis_type,
        "threshold": threshold,
        "value": current_value,
        "status": "BASELINE_SAVED",
        "current_status": evaluation["status"],
        "reason": "Your thesis baseline has been saved.",
    }

@app.get("/changes")
def get_changes(db: Session = Depends(get_db)):
    # Get ONE market snapshot for this entire request
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

        stock = market_data[symbol]

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
                "type": "STOCK",
                "symbol": symbol,
                "name": stock["name"],
                "status": "NEW",
                "reason": "This stock was added to your watchlist after your last check.",
            })
            continue

        percentage_change = (
            (stock["price"] - last_seen.price)
            / last_seen.price
        ) * 100

        attention = calculate_attention(
            stock,
            change_percent=percentage_change,
        )

        if attention["status"] == "WORTH_ATTENTION":
            result.append({
                "type": "STOCK",
                "symbol": symbol,
                "name": stock["name"],
                "previous_price": round(last_seen.price, 2),
                "current_price": stock["price"],
                "change_percent": round(percentage_change, 2),
                "daily_change": stock["daily_change"],
                "status": attention["status"],
                "anomaly_score": attention["anomaly_score"],
                "reason": attention["reason"],
                "last_seen": last_seen.timestamp,
                "current_timestamp": stock["timestamp"],
            })

    # -------------------------
    # Portfolio structural changes
    # -------------------------

    positions = (
        db.query(PortfolioPosition)
        .filter(PortfolioPosition.user_id == 1)
        .all()
    )

    if positions:
        portfolio_values = []
        for position in positions:
            if position.symbol not in market_data:
                continue
            val = position.quantity * market_data[position.symbol]["price"]
            portfolio_values.append({
                "symbol": position.symbol,
                "value": val,
                "target_weight": position.target_weight,
            })

        total_portfolio_val = sum(item["value"] for item in portfolio_values)

        for item in portfolio_values:
            symbol = item["symbol"]
            target_weight = item["target_weight"]
            current_weight = (
                (item["value"] / total_portfolio_val) * 100
                if total_portfolio_val
                else 0
            )

            baseline_snapshot = (
                db.query(PortfolioSnapshot)
                .filter(
                    PortfolioSnapshot.user_id == 1,
                    PortfolioSnapshot.symbol == symbol,
                )
                .order_by(PortfolioSnapshot.timestamp.desc())
                .first()
            )

            if baseline_snapshot:
                previous_weight = baseline_snapshot.actual_weight
            else:
                previous_weight = target_weight

            previous_drift = previous_weight - target_weight
            current_drift = current_weight - target_weight
            drift_change = current_drift - previous_drift

            threshold_crossed = (
                abs(previous_drift) < 5.0
                and abs(current_drift) >= 5.0
            )

            meaningful_change = (
                abs(drift_change) >= 2.0
                or threshold_crossed
                or (not baseline_snapshot and abs(current_drift) >= 5.0)
            )

            if meaningful_change:
                result.append({
                    "type": "PORTFOLIO",
                    "symbol": symbol,
                    "previous_weight": round(previous_weight, 2),
                    "current_weight": round(current_weight, 2),
                    "target_weight": round(target_weight, 2),
                    "drift": round(current_drift, 2),
                    "drift_change": round(drift_change, 2),
                    "status": "WORTH_ATTENTION",
                    "reason": (
                        f"{symbol} is now {abs(current_drift):.2f} percentage points "
                        f"{'above' if current_drift > 0 else 'below'} "
                        f"its target allocation."
                    ),
                })

    # -------------------------
    # Thesis changes
    # -------------------------

    theses = (
        db.query(Thesis)
        .filter(Thesis.user_id == 1)
        .all()
    )

    current_thesis_data = get_thesis_data()

    for thesis in theses:

        if thesis.symbol not in current_thesis_data:
            continue

        current_value = current_thesis_data[thesis.symbol]["growth"]

        evaluation = evaluate_thesis(
            thesis.thesis_type,
            current_value,
            thesis.threshold,
        )

        if evaluation["status"] != thesis.last_status:

            if (
                thesis.last_status == "VALID"
                and evaluation["status"] == "INVALID"
            ):
                status = "THESIS_CHANGED"
                reason = evaluation["reason"]

            elif (
                thesis.last_status == "INVALID"
                and evaluation["status"] == "VALID"
            ):
                status = "THESIS_RECOVERED"
                reason = (
                    f"Growth has recovered to {current_value:.1f}%, "
                    f"meeting your {thesis.threshold:.1f}% thesis threshold again."
                )

            else:
                status = "THESIS_CHANGED"
                reason = evaluation["reason"]

            result.append({
                "type": "THESIS",
                "symbol": thesis.symbol,
                "thesis_type": thesis.thesis_type,
                "previous_value": thesis.last_value,
                "current_value": current_value,
                "threshold": thesis.threshold,
                "status": status,
                "reason": reason,
            })

    result.sort(
        key=lambda item: item.get("anomaly_score", 0),
        reverse=True,
    )

    return result
@app.post("/ai/prioritize")
async def ai_prioritize(db: Session = Depends(get_db)):
    changes = get_changes(db)

    if not changes:
        return {
            "priorities": [],
            "message": "No meaningful changes to prioritize."
        }

    portfolio = get_portfolio(db)

    # Use the user's actual saved theses from DB if present
    user_theses = (
        db.query(Thesis)
        .filter(Thesis.user_id == 1)
        .all()
    )
    current_thesis_data = get_thesis_data()
    theses = {}
    for t in user_theses:
        curr_growth = current_thesis_data.get(t.symbol, {}).get("growth", t.last_value)
        theses[t.symbol] = {
            "growth": curr_growth,
            "threshold": t.threshold,
            "status": t.last_status,
        }

    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == 1)
        .all()
    )

    symbols = [item.symbol for item in watchlist]
    news = get_news(symbols)

    result = await prioritize_market_changes(
        changes=changes,
        portfolio=portfolio,
        theses=theses,
        news=news,
    )

    if not result and changes:
        return {
            "priorities": [],
            "message": "AI prioritization is temporarily unavailable. Your changes are shown below.",
        }

    return {
        "priorities": result
    }

@app.get("/news")
def news(db: Session = Depends(get_db)):
    watchlist = (
        db.query(Watchlist)
        .filter(Watchlist.user_id == 1)
        .all()
    )

    symbols = [item.symbol for item in watchlist]

    if not symbols:
        return []

    return get_news(symbols)