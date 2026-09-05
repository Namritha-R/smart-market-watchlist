const API_URL = "http://127.0.0.1:8000";

async function request(url: string, options?: RequestInit) {
  const response = await fetch(`${API_URL}${url}`, options);

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`);
  }

  return response.json();
}

export function getHealth() {
  return request("/health");
}

export function getChanges() {
  return request("/changes");
}

export function getWatchlist() {
  return request("/watchlist");
}

export function getMarket() {
  return request("/market");
}

export function getPortfolio() {
  return request("/portfolio");
}

export function checkIn() {
  return request("/check-in", {
    method: "POST",
  });
}

export function addToWatchlist(symbol: string) {
  return request(`/watchlist/${symbol}`, {
    method: "POST",
  });
}

export function removeFromWatchlist(symbol: string) {
  return request(`/watchlist/${symbol}`, {
    method: "DELETE",
  });
}

export function saveLastSeen(symbol: string) {
  return request(`/last-seen/${symbol}`, {
    method: "POST",
  });
}

export function saveThesis(symbol: string) {
  return request(`/thesis/${symbol}`, {
    method: "POST",
  });
}

export function prioritizeWithAI() {
  return request("/ai/prioritize", {
    method: "POST",
  });
}