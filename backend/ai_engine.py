# pyrefly: ignore-file
import os
import json
from dotenv import load_dotenv
# pyrefly: ignore [missing-import]
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


async def prioritize_market_changes(changes, portfolio=None, theses=None, news=None):

    prompt = f"""
You are an AI Market Prioritizer for a smart stock watchlist.

Your job is to decide what the user should look at FIRST.

Use ONLY the verified information provided below.

Do NOT:
- predict future stock prices
- recommend buying or selling
- invent news, facts, events, or explanations
- assume information that is not provided
- make investment decisions for the user
- claim that a news event caused a price movement unless the provided news explicitly supports that connection

Consider:
1. How unusual the market movement is
2. Whether the stock is in the user's portfolio
3. Portfolio allocation drift
4. Whether the user's investment thesis may need review
5. Available news
6. Historical/anomaly evidence provided in the market changes
7. How strongly the available evidence supports the priority

Rank the meaningful changes from highest to lowest priority.

IMPORTANT:
- Do not create new market changes that are not present in the input.
- Do not remove meaningful changes from the input.
- If there is insufficient information to determine why something happened, say so.
- Portfolio drift should increase priority when it is significant.
- An unusually large stock-specific movement should increase priority.
- A movement that is normal or market-wide should generally receive lower priority.
- A thesis should only be mentioned if thesis information is actually provided.
- News should only be mentioned if news information is actually provided.

NEWS IS COMPULSORY WHEN AVAILABLE:

- For every prioritized symbol, first check whether verified news exists
  for that symbol in the provided NEWS data.

- If verified news exists for that symbol:
  - You MUST include exactly one news-based evidence item.
  - This MUST be the SECOND evidence item.
  - The evidence MUST use the provided headline or summary.
  - You MUST NOT omit the news even if the market and portfolio
    evidence are sufficient.
  - You MUST NOT invent or expand the news.
  - You MUST NOT claim that the news caused the price movement unless
    the provided news explicitly establishes that connection.

- If no verified news exists for that symbol:
  - Do NOT create or infer news.
  - Do NOT include a news evidence item.

EVIDENCE ORDER IS MANDATORY:

1. Market-derived evidence
2. News-derived evidence, IF verified news exists
3. Portfolio or thesis evidence, IF relevant

FAILSAFE:
If verified news exists for a prioritized symbol but the generated
output does not contain a news-based SECOND evidence item, the output
is considered invalid. Regenerate the output before returning it.

OUTPUT FORMAT:

Return ONLY valid JSON.

Do NOT use markdown.
Do NOT use ```json.
Do NOT add an introduction.
Do NOT add an explanation after the JSON.

Return exactly this structure:

[
  {{
    "symbol": "INFY",
    "priority": 1,
    "label": "Short descriptive label",
    "why_it_matters": "Maximum 2 concise sentences explaining why this deserves attention.",
    "evidence": [
      "Short market-derived evidence",
      "Short news-derived evidence",
      "Short portfolio or thesis evidence"
    ],
    "suggested_action": "One concise review-oriented action.",
    "confidence": "High"
  }}
]

OUTPUT RULES:

- "symbol" must exactly match a symbol from the provided information.
- "priority" must be an integer starting from 1.
- Lower priority number means more important.
- "label" must be short and specific.
- "why_it_matters" must contain at most 2 concise sentences.
- "evidence" must contain 2 or 3 short items.
- The FIRST evidence item MUST be based on market-derived information.
- If verified news exists for the prioritized symbol, the SECOND evidence item MUST be based on that news.
- If relevant portfolio or thesis information exists, use the THIRD evidence item for that context.
- Do not invent evidence.
- Do not invent relationships between market movement, news, portfolio, or thesis.
- Evidence must come directly from the provided information.
- Do not repeat the same information unnecessarily.
- If a required evidence type is unavailable, do not fabricate it.
- "suggested_action" must be a review-oriented action.
- Never suggest buying or selling.
- "confidence" must be one of: "High", "Medium", "Low".
- Use "Medium" or "Low" confidence when evidence is incomplete or conflicting.
- If there are no meaningful changes, return [].

NEWS USAGE:

- If verified news exists for a prioritized symbol, you MUST include one evidence item based on the news.
- Use the provided headline or summary only.
- Clearly identify the information as news.
- Do not claim that the news caused the price movement unless the provided news explicitly establishes that connection.
- Do not invent additional details about the news.

PORTFOLIO USAGE:

- If the prioritized symbol is currently held in the portfolio, mention this when relevant.
- If significant portfolio drift exists, use it as evidence.
- Do not describe normal portfolio allocation as significant drift.
- Use the exact portfolio information provided.

THESIS USAGE:

- If a thesis exists for the prioritized symbol, mention it when relevant.
- Do not claim that a thesis is invalidated unless the provided information actually supports invalidation.
- Do not invent thesis details.
- A thesis can be mentioned as context even when there is not enough evidence to say it has changed.

PRIORITY LOGIC:

Prioritize a change more highly when multiple verified signals support attention.

For example:
- Unusual stock-specific movement + relevant news + portfolio holding → high priority.
- Unusual movement + relevant news → high priority.
- Unusual movement alone → lower confidence.
- Significant portfolio drift → increase priority.
- Thesis evidence suggesting the user's reason for watching the stock needs review → increase priority.
- Market-wide movement without stock-specific evidence → lower priority.

The AI must prioritize the provided meaningful changes. It must NOT create new changes.
MARKET CHANGES:
{changes}

PORTFOLIO:
{portfolio}

USER THESES:
{theses}

NEWS:
{news}
"""

    models_to_try = ["gemini-3.5-flash-lite", "gemini-3.5-flash"]
    response = None
    last_err = None

    for model_name in models_to_try:
        try:
            response = await client.aio.models.generate_content(
                model=model_name,
                contents=prompt,
            )
            if response and response.text:
                break
        except Exception as e:
            last_err = e
            print(f"[AI Engine] Error with model {model_name}: {e}")
            continue

    if not response or not response.text:
        print(f"[AI Engine] All Gemini models failed. Last error: {last_err}")
        return []

    text = response.text.strip()

    # Extract JSON array safely even if surrounded by markdown or explanatory text
    cleaned = text
    if "```" in cleaned:
        parts = cleaned.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("[") and part.endswith("]"):
                cleaned = part
                break

    if not (cleaned.startswith("[") and cleaned.endswith("]")):
        start = cleaned.find("[")
        end = cleaned.rfind("]")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    try:
        result = json.loads(cleaned)
    except json.JSONDecodeError as err:
        print(f"[AI Engine] JSON decode error: {err}. Raw text: {text[:200]}")
        return []

    # ---------------------------------------------------------
    # Deterministic news safeguard
    # ---------------------------------------------------------
    # Gemini may occasionally omit news even when verified news
    # is available. The backend guarantees that verified news
    # cannot be lost.
    if isinstance(result, list) and news:
        news_by_symbol = {}

        for item in news:
            for symbol in item.get("symbols", []):
                news_by_symbol[symbol] = item

        for item in result:
            symbol = item.get("symbol")

            if symbol not in news_by_symbol:
                continue

            verified_news = news_by_symbol[symbol]
            headline = verified_news.get("headline", "")

            evidence = item.get("evidence", [])

            if not isinstance(evidence, list):
                evidence = []

            # Check whether Gemini already included the news
            evidence_text = " ".join(str(e) for e in evidence)

            if headline and headline.lower() not in evidence_text.lower():
                news_evidence = f"News: {headline}"

                # Keep market evidence first.
                # Insert verified news as the second item.
                if len(evidence) >= 1:
                    evidence.insert(1, news_evidence)
                else:
                    evidence.append(news_evidence)

                # Keep maximum 3 evidence items.
                item["evidence"] = evidence[:3]

    return result