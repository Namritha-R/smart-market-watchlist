from fastapi import FastAPI
from sqlalchemy import text

from database import engine
from models import Base
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