"""
News fetcher + AI sentiment analyzer.
Sources: NewsAPI (headlines) + Alpha Vantage (market news + sentiment scores)
AI analysis: OpenAI GPT-4 for contextual interpretation
"""
import os
import sys
from datetime import datetime, timedelta
from typing import Optional
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from analyzer.config.settings import NEWS_API_KEY, ALPHA_VANTAGE_KEY, OPENAI_API_KEY


def get_news_for_symbol(symbol: str, days_back: int = 3) -> list[dict]:
    """
    Fetch recent news articles for a symbol.
    Uses Alpha Vantage (has built-in sentiment scores) if key available,
    otherwise falls back to NewsAPI.
    """
    if ALPHA_VANTAGE_KEY:
        return _get_alphavantage_news(symbol, days_back)
    elif NEWS_API_KEY:
        return _get_newsapi_articles(symbol, days_back)
    return []


def _get_alphavantage_news(symbol: str, days_back: int = 3) -> list[dict]:
    """Alpha Vantage News & Sentiment API — includes pre-scored sentiment."""
    url = "https://www.alphavantage.co/query"
    time_from = (datetime.now() - timedelta(days=days_back)).strftime("%Y%m%dT0000")
    params = {
        "function": "NEWS_SENTIMENT",
        "tickers": symbol,
        "time_from": time_from,
        "limit": 20,
        "apikey": ALPHA_VANTAGE_KEY,
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    articles = []
    for item in data.get("feed", []):
        ticker_data = next(
            (t for t in item.get("ticker_sentiment", []) if t["ticker"] == symbol), {}
        )
        articles.append({
            "title": item.get("title", ""),
            "summary": item.get("summary", ""),
            "url": item.get("url", ""),
            "published": item.get("time_published", ""),
            "source": item.get("source", ""),
            "sentiment_label": ticker_data.get("ticker_sentiment_label", "Neutral"),
            "sentiment_score": float(ticker_data.get("ticker_sentiment_score", 0)),
            "relevance_score": float(ticker_data.get("relevance_score", 0)),
        })
    return articles


def _get_newsapi_articles(query: str, days_back: int = 3) -> list[dict]:
    """NewsAPI fallback — no sentiment scores, raw articles."""
    url = "https://newsapi.org/v2/everything"
    from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "q": query,
        "from": from_date,
        "sortBy": "relevancy",
        "language": "en",
        "pageSize": 15,
        "apiKey": NEWS_API_KEY,
    }
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    articles = []
    for item in data.get("articles", []):
        articles.append({
            "title": item.get("title", ""),
            "summary": item.get("description", ""),
            "url": item.get("url", ""),
            "published": item.get("publishedAt", ""),
            "source": item.get("source", {}).get("name", ""),
            "sentiment_label": "Unknown",
            "sentiment_score": 0.0,
            "relevance_score": 1.0,
        })
    return articles


def get_macro_news(days_back: int = 2) -> list[dict]:
    """Fetch macro/financial news (Fed, inflation, earnings season, etc.)."""
    queries = [
        "Federal Reserve interest rates",
        "inflation CPI",
        "earnings season",
        "market outlook",
    ]
    all_articles = []
    for q in queries:
        try:
            articles = _get_newsapi_articles(q, days_back=days_back) if NEWS_API_KEY else []
            all_articles.extend(articles[:3])
        except Exception:
            pass
    return all_articles


def analyze_news_with_ai(symbol: str, articles: list[dict]) -> dict:
    """
    Use OpenAI GPT-4 to analyze news articles and generate contextual insights.
    Returns: bias, key risks, catalysts, and a summary.
    """
    if not OPENAI_API_KEY or not articles:
        return {"error": "OpenAI key not configured or no articles available"}

    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)

        headlines = "\n".join(
            f"- [{a['source']}] {a['title']} (sentiment: {a['sentiment_label']})"
            for a in articles[:10]
        )

        prompt = f"""You are a professional market analyst. Analyze these recent news headlines for {symbol} and provide:

Headlines:
{headlines}

Respond in JSON with this exact structure:
{{
  "overall_sentiment": "bullish|bearish|neutral",
  "confidence": 0-100,
  "key_catalysts": ["list of positive drivers"],
  "key_risks": ["list of risks or negative factors"],
  "macro_context": "brief macro environment note",
  "short_term_outlook": "1-2 sentence outlook for next 1-5 days",
  "important_events": ["upcoming events that could move price"],
  "summary": "2-3 sentence overall analysis"
}}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )

        import json
        return json.loads(response.choices[0].message.content)

    except Exception as e:
        return {"error": str(e)}
