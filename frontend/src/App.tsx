import { useEffect, useRef, useState } from "react";
import "./App.css";
import {
  getChanges,
  getWatchlist,
  getPortfolio,
  getMarket,
  getHealth,
  checkIn,
  addToWatchlist,
  removeFromWatchlist,
  prioritizeWithAI,
} from "./api";
type AIPriority = {
  symbol: string;
  priority: number;
  label: string;
  why_it_matters: string;
  evidence: string[];
  suggested_action: string;
  confidence: string;
};
function App() {
    const [changes, setChanges] = useState<any[]>([]);
    const sessionStarting = useRef(false);
    const [watchlist, setWatchlist] = useState<any[]>([]);
    const [portfolio, setPortfolio] = useState<any>(null);
    const [market, setMarket] = useState<any>(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [backendConnected, setBackendConnected] = useState(false);
    const [showAddStock, setShowAddStock] = useState(false);
    const [selectedSymbol, setSelectedSymbol] = useState("");
    const [actionLoading, setActionLoading] = useState(false);
    const [aiResult, setAiResult] = useState<AIPriority[] | null>(null);
    const [aiMessage, setAiMessage] = useState<string | null>(null);
    const [aiLoading, setAiLoading] = useState(false);
    const aiPriorities = aiResult ?? [];

    async function loadData() {
      try {
        setLoading(true);
        setError("");

        const [
          changesData,
          watchlistData,
          portfolioData,
          marketData,
          healthData,
        ] = await Promise.all([
          getChanges(),
          getWatchlist(),
          getPortfolio(),
          getMarket(),
          getHealth(),
        ]);

        setChanges(changesData);
        setWatchlist(watchlistData);
        setPortfolio(portfolioData);
        setMarket(marketData);
        setBackendConnected(healthData.status === "healthy");

        // Record check-in once per session so baseline is updated
        const isNewSession = sessionStorage.getItem("market_session_active") !== "true";
        if (isNewSession && !sessionStarting.current) {
          sessionStarting.current = true;
          sessionStorage.setItem("market_session_active", "true");
          await checkIn();
        }
      } catch (error) {
        console.error(error);
        setError("Unable to connect to the market engine.");
      } finally {
        setLoading(false);
      }
    }

    // Lightweight refresh — only polls market-driven data every 15s.
    // Directly uses fresh backend responses without sessionStorage interference.
    async function refreshData() {
      try {
        const [
          changesData,
          watchlistData,
          portfolioData,
          marketData,
        ] = await Promise.all([
          getChanges(),
          getWatchlist(),
          getPortfolio(),
          getMarket(),
        ]);

        setChanges(changesData);
        setWatchlist(watchlistData);
        setPortfolio(portfolioData);
        setMarket(marketData);
      } catch (error) {
        console.error(error);
      }
    }

    async function handleRefreshMarket() {
      try {
        setLoading(true);
        await checkIn();
        const [
          changesData,
          watchlistData,
          portfolioData,
          marketData,
        ] = await Promise.all([
          getChanges(),
          getWatchlist(),
          getPortfolio(),
          getMarket(),
        ]);

        setChanges(changesData);
        setWatchlist(watchlistData);
        setPortfolio(portfolioData);
        setMarket(marketData);
        setAiResult(null);
        setAiMessage(null);
      } catch (error) {
        console.error(error);
        setError("Unable to refresh market data.");
      } finally {
        setLoading(false);
      }
    }

    useEffect(() => {
      loadData();

      const interval = setInterval(refreshData, 15000);
      return () => clearInterval(interval);
    }, []);
    async function handleAIPrioritize() {
      setAiLoading(true);
      setAiMessage(null);
      try {
        const result = await prioritizeWithAI();
        if (Array.isArray(result.priorities)) {
          setAiResult(result.priorities);
        } else {
          setAiResult([]);
          setAiMessage(result.message || "No priorities returned.");
        }
      } catch (error) {
        setAiResult([]);
        setAiMessage("AI prioritization failed.");
      } finally {
        setAiLoading(false);
      }
    }

    async function handleAddStock() {
      if (!selectedSymbol) return;

      try {
        setActionLoading(true);
        setError("");

        await addToWatchlist(selectedSymbol);

        setSelectedSymbol("");
        setShowAddStock(false);

        await loadData();
      } catch (error) {
        console.error(error);
        setError("Unable to add stock.");
      } finally {
        setActionLoading(false);
      }
    }

    async function handleRemoveStock(symbol: string) {
      try {
        setActionLoading(true);
        setError("");

        await removeFromWatchlist(symbol);

        await loadData();
      } catch (error) {
        console.error(error);
        setError("Unable to remove stock.");
      } finally {
        setActionLoading(false);
      }
    }


  return (
    <div className="app">
      <header className="topbar">
        <div className="logo">groww<span>.</span></div>

        <nav>
          <a className="active">Watchlist</a>
          <a>Stocks</a>
          <a>Portfolio</a>
        </nav>

        <div className="profile">
          <span className={backendConnected ? "status-dot online" : "status-dot"} />
          N
        </div>
      </header>

      <main className="container">
        <section className="hero">
          <p className="eyebrow">SMART MARKET WATCHLIST</p>

          <h1>What changed<br />since you last checked?</h1>

          <p className="subtitle">
          We filtered the market for changes that actually deserve your attention.
        </p>

          {market && (
            <p className="market-status">
              Market data available for {Object.keys(market).length} stocks
            </p>
          )}

          <button
            className="refresh-market-button"
            onClick={handleRefreshMarket}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh market"}
          </button> 
          <button  className="ai-prioritize-button" onClick={handleAIPrioritize} disabled={aiLoading}>
            {aiLoading ? "Analyzing..." : "✨ AI Prioritize"}
          </button>
           {aiResult !== null && (
  <section className="ai-priority-section">
    <div className="ai-priority-header">
      <div>
        <div className="ai-eyebrow">SMART ATTENTION</div>
        <h2>What deserves your attention</h2>
        <p>
          AI ranked the meaningful changes using your market signals and portfolio context.
        </p>
      </div>
    </div>

    {aiPriorities.length > 0 ? (
      <div className="ai-priority-list">
        {aiPriorities.map((item) => (
          <div className="ai-priority-item" key={item.symbol}>
            <div className="ai-priority-top">
              <div className="ai-stock-info">
                <span className="ai-rank">#{item.priority}</span>

                <div>
                  <div className="ai-symbol">{item.symbol}</div>
                  <div className="ai-label">{item.label}</div>
                </div>
              </div>

              <span className="ai-confidence">
                {item.confidence} confidence
              </span>
            </div>

            <div className="ai-why">
              <strong>Why this matters</strong>
              <p>{item.why_it_matters}</p>
            </div>

            {item.evidence?.length > 0 && (
              <div className="ai-evidence">
                <strong>Evidence</strong>

                <ul>
                  {item.evidence.map((evidence, index) => (
                    <li key={index}>{evidence}</li>
                  ))}
                </ul>
              </div>
            )}

            <div className="ai-action">
              <span>Suggested action</span>
              <p>{item.suggested_action}</p>
            </div>
          </div>
        ))}
      </div>
    ) : (
      <div className="ai-empty">
        {aiMessage || "No meaningful changes to prioritize."}
      </div>
    )}
  </section>
)}
        </section>

        <section className="attention-section">
          <div className="section-header">
            <div>
              <h2>Needs your attention</h2>
              <p>Meaningful changes in your watchlist</p>
            </div>

            <span className="count">
              {changes.length}
            </span>
          </div>

          {loading && (
            <div className="empty-state">
              Checking for meaningful changes...
            </div>
          )}

          {error && (
            <div className="empty-state error">
              {error}
            </div>
          )}

          {!loading && !error && changes.length === 0 && (
            <div className="empty-state">
              <strong>Nothing needs your attention.</strong>
              <p>Your watchlist hasn't meaningfully changed since your last check.</p>
            </div>
          )}

          {!loading && !error && changes.length > 0 && (
            <div className="changes-list">
              {changes.map((change, index) => (
                <div key={`${change.type}-${change.symbol}-${index}`}>
                  <div className="attention-card">
                    <div className="stock-left">
                      <div className="stock-icon">
                        {change.symbol?.charAt(0)}
                      </div>

                      <div>
                        <h3>
                          {change.name || change.symbol}
                        </h3>

                        <p>
                          {change.symbol}
                          {change.type === "PORTFOLIO" && " · Portfolio"}
                          {change.type === "THESIS" && " · Thesis"}
                        </p>
                      </div>
                    </div>

                    <div className="stock-change">
                      <strong>
                        {change.status === "NEW" && "New"}

                        {change.type === "STOCK" &&
                          change.status !== "NEW" &&
                          `${change.change_percent > 0 ? "+" : ""}${change.change_percent}%`}

                        {change.type === "PORTFOLIO" &&
                          `${change.drift > 0 ? "+" : ""}${change.drift} pp`}

                        {change.type === "THESIS" &&
                          (change.status === "THESIS_RECOVERED"
                            ? "Recovered"
                            : "Changed")}
                      </strong>

                      <span>
                        {change.status === "NEW" &&
                          "New to your watchlist"}

                        {change.status === "WORTH_ATTENTION" &&
                          "Unusual movement"}

                        {change.status === "THESIS_CHANGED" &&
                          "Thesis changed"}

                        {change.status === "THESIS_RECOVERED" &&
                          "Thesis recovered"}
                      </span>
                    </div>

                    
                  </div>

                  <div className="reason">
                    <span>Why this was flagged</span>
                    <p>{change.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        <section className="watchlist-section">
          <div className="section-header">
            <div>
              <h2>Your watchlist</h2>
              <p>Stocks you're keeping an eye on</p>
            </div>

            <button
              className="add-button"
              onClick={() => setShowAddStock(!showAddStock)}
            >
              + Add stock
            </button>
            {showAddStock && market && (
              <div className="add-stock-panel">
                <select
                  value={selectedSymbol}
                  onChange={(e) => setSelectedSymbol(e.target.value)}
                >
                  <option value="">Choose a stock</option>

                  {Object.keys(market).map((symbol) => (
                    <option key={symbol} value={symbol}>
                      {symbol} — {market[symbol].name}
                    </option>
                  ))}
                </select>

                <button
                  onClick={handleAddStock}
                  disabled={!selectedSymbol || actionLoading}
                >
                  {actionLoading ? "Adding..." : "Add"}
                </button>
              </div>
            )}
          </div>

          <div className="stock-list">
            {loading && (
              <div className="empty-state">
                Loading your watchlist...
              </div>
            )}

            {!loading && watchlist.length === 0 && (
              <div className="empty-state">
                <strong>Your watchlist is empty.</strong>
                <p>Add a stock to start tracking meaningful changes.</p>
              </div>
            )}

            {!loading &&
              watchlist.map((stock) => (
                <div className="stock-row" key={stock.symbol}>
                  <div className="stock-left">
                    <div className="stock-icon">
                      {stock.symbol.charAt(0)}
                    </div>

                    <div>
                      <h3>{stock.name}</h3>
                      <p>
                        {stock.symbol} · {stock.sector}
                      </p>
                    </div>
                  </div>

                  <div className="price">
                    <strong>
                      ₹{Number(stock.price).toLocaleString("en-IN", {
                        minimumFractionDigits: 2,
                      })}
                    </strong>

                    <span className={stock.daily_change >= 0 ? "positive" : "negative"}>
                      {stock.daily_change > 0 ? "+" : ""}
                      {stock.daily_change}%
                    </span>
                  </div>
                  <button
                    className="remove-button"
                    onClick={() => handleRemoveStock(stock.symbol)}
                    disabled={actionLoading}
                    aria-label={`Remove ${stock.symbol}`}
                  >
                    ×
                  </button>
                </div>
              ))}
          </div>
        </section>

        <section className="portfolio-section">
          <div className="section-header">
            <div>
              <h2>Portfolio</h2>
              <p>Changes in your allocation</p>
            </div>
          </div>

          <div className="portfolio-card">
            {portfolio && (
              <>
                <p>Total portfolio value</p>

                <h2>
                  ₹{Number(portfolio.total_value).toLocaleString("en-IN")}
                </h2>

                {portfolio.positions.map((position: any) => (
                  <div className="portfolio-row" key={position.symbol}>
                    <span>{position.symbol}</span>

                    <span>
                      {position.actual_weight}%
                    </span>

                    <span>
                      Target {position.target_weight}%
                    </span>

                    <strong>
                      {position.drift.drift > 0 ? "+" : ""}
                      {position.drift.drift} pp
                    </strong>
                  </div>
                ))}
              </>
            )}
          </div>
        </section>
      </main>

      <footer className="bottom-nav">
        <a className="active">Watchlist</a>
        <a>Stocks</a>
        <a>Portfolio</a>
        <a>Profile</a>
      </footer>
    </div>
  );
}

export default App;