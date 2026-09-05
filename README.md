
# Smart Market Watchlist

> **What meaningfully changed since I last checked, and what deserves my attention now?**

## The Problem

A normal watchlist tells investors what is happening right now. But when they return later, they still have to go through multiple stocks and decide what actually changed and whether it matters.

Not every price movement is important.

A stock moving 3% while its sector also moves 3% is very different from a stock moving 3% while its sector is almost flat.

I built Smart Market Watchlist to reduce this noise and focus the investor on meaningful changes.

---

## The Solution

Instead of simply displaying market movements, the system compares the **current state with what the user last saw** and identifies changes that deserve attention.

```text
Current Market Data
        +
Previous User State
        +
Portfolio
        +
Investment Thesis
        ↓
Meaningful Change Detection
        ↓
Explanation
        ↓
AI Prioritization
```

### What it detects

**1. Unusual stock movement**

A stock is compared with:

* Its sector
* The broader market
* Its normal historical behaviour

This helps distinguish stock-specific movement from normal market-wide movement.

**2. Portfolio drift**

The system compares actual portfolio allocation with the user's target allocation and identifies significant drift.

**3. Thesis changes**

Users can define a simple thesis metric and threshold for a stock. The system detects when that condition changes.

**4. Event context**

Market/event information is used as supporting context when explaining or prioritizing a change.

---

## AI Market Prioritizer

When multiple meaningful changes are detected, the question becomes:

> **Which one should I look at first?**

The **AI Prioritize** feature uses Google Gemini to rank the detected changes using:

* Market signals
* Historical/anomaly information
* Portfolio context
* Investment thesis
* Available event context

It returns:

* Priority
* Why it matters
* Evidence
* Suggested action
* Confidence

The AI **does not decide whether a movement is meaningful**. That is handled by the deterministic attention engine.

It also does not predict prices, execute trades, or make autonomous buy/sell decisions.

```text
Deterministic Engine
"What changed and does it matter?"
              ↓
          Gemini AI
"What should I look at first?"
```

---

## Key Difference

I did not want to build another watchlist that shows investors more information.

The goal is to show **less, but more relevant information**.

```text
What I last saw
       ↓
What changed
       ↓
Does it matter?
       ↓
What should I look at first?
```

---

## Edge Cases

The system handles:

* **New stocks:** treated as `NEW` until a baseline is established.
* **Market-wide movement:** separated from stock-specific movement using sector/market comparison.
* **No meaningful change:** normal movements are filtered out.
* **Stale data:** timestamps are considered when evaluating market information.
* **Portfolio drift:** evaluated separately from stock-level movement.
* **AI failure:** the core change-detection system continues to work without AI.

---

## Tech Stack

**Frontend:** React, TypeScript, Vite
**Backend:** Python, FastAPI, SQLAlchemy
**Database:** PostgreSQL
**AI:** Google Gemini 2.5 Flash

### Project Structure

```text
smart-market-watchlist/
├── backend/
│   ├── main.py
│   ├── attention_engine.py
│   ├── market_data.py
│   ├── historical_data.py
│   ├── thesis_engine.py
│   ├── news_data.py
│   ├── ai_engine.py
│   └── ...
│
├── frontend/
│   └── src/
│       ├── App.tsx
│       ├── App.css
│       └── api.ts
│
└── README.md
```

---

## Run Locally

### Requirements

* Python 3.12+
* Node.js / npm
* PostgreSQL
* Gemini API key

### 1. Clone

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd smart-market-watchlist
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql+psycopg://localhost/smart_market_watchlist
GEMINI_API_KEY=your_gemini_api_key
```

Create the PostgreSQL database:

```bash
createdb smart_market_watchlist
```

Start the backend:

```bash
python -m uvicorn main:app --reload --port 8000
```

### 3. Frontend

Open a new terminal:

```bash
cd smart-market-watchlist/frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## Demo Flow

1. Add a stock to the watchlist.
2. The first check-in establishes the user's baseline.
3. The simulated market state changes.
4. Refresh the market.
5. View **Needs your attention**.
6. Open the explanation for the flagged movement.
7. Check portfolio allocation and drift.
8. Check the investment thesis.
9. Click **✨ AI Prioritize** to see what deserves attention first.

---

## Data Note

The current prototype uses **deterministic simulated market and event data** so the demo is reproducible.

The data layer is separated from the attention engine, allowing live market and news providers to be integrated later.

---

## Future Improvements

* Live market and news data
* Multi-user authentication
* Richer thesis and portfolio analysis
* More historical data
* Cross-device state synchronization
* More robust AI evaluation

---

## Built for Groww ODE

The core idea is simple:

> **A watchlist should not just tell me what is happening. It should tell me what changed since I last checked and what is actually worth my attention.**

```
```
