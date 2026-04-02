"""
Crypto data fetcher — uses ccxt for multi-exchange support.
Default exchange: Binance (most liquidity, free API).
"""
import pandas as pd
import ccxt
from typing import Optional
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from analyzer.config.settings import BINANCE_API_KEY, BINANCE_SECRET_KEY


def _get_exchange(exchange_id: str = "binance") -> ccxt.Exchange:
    """Initialize a ccxt exchange instance."""
    exchange_class = getattr(ccxt, exchange_id)
    params = {"enableRateLimit": True}
    if exchange_id == "binance" and BINANCE_API_KEY:
        params["apiKey"] = BINANCE_API_KEY
        params["secret"] = BINANCE_SECRET_KEY
    return exchange_class(params)


def get_ohlcv(
    symbol: str,
    timeframe: str = "1d",
    limit: int = 500,
    exchange_id: str = "binance",
) -> pd.DataFrame:
    """
    Fetch OHLCV data for a crypto pair.

    Args:
        symbol: e.g. "BTC/USDT", "ETH/USDT"
        timeframe: "1m","5m","15m","1h","4h","1d","1w"
        limit: number of candles (max ~1000 on Binance)
        exchange_id: any ccxt-supported exchange
    """
    exchange = _get_exchange(exchange_id)
    raw = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["datetime"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True)
    df = df.set_index("datetime").drop(columns=["timestamp"])
    df = df[["open", "high", "low", "close", "volume"]].dropna()
    return df


def get_multiple_ohlcv(
    symbols: list[str],
    timeframe: str = "1d",
    limit: int = 500,
    exchange_id: str = "binance",
) -> dict[str, pd.DataFrame]:
    """Fetch OHLCV for multiple crypto pairs."""
    result = {}
    for symbol in symbols:
        try:
            result[symbol] = get_ohlcv(symbol, timeframe=timeframe, limit=limit, exchange_id=exchange_id)
        except Exception as e:
            print(f"[crypto] Error fetching {symbol}: {e}")
    return result


def get_ticker(symbol: str, exchange_id: str = "binance") -> dict:
    """Get current price + 24h stats for a symbol."""
    exchange = _get_exchange(exchange_id)
    t = exchange.fetch_ticker(symbol)
    return {
        "symbol": symbol,
        "price": t.get("last"),
        "change_24h_pct": t.get("percentage"),
        "high_24h": t.get("high"),
        "low_24h": t.get("low"),
        "volume_24h": t.get("quoteVolume"),
        "bid": t.get("bid"),
        "ask": t.get("ask"),
    }


def get_order_book_depth(symbol: str, exchange_id: str = "binance") -> dict:
    """Fetch bid/ask order book depth as a proxy for market sentiment."""
    exchange = _get_exchange(exchange_id)
    ob = exchange.fetch_order_book(symbol, limit=20)
    total_bid = sum(qty for _, qty in ob["bids"])
    total_ask = sum(qty for _, qty in ob["asks"])
    ratio = total_bid / total_ask if total_ask > 0 else 1.0
    return {
        "bid_volume": total_bid,
        "ask_volume": total_ask,
        "bid_ask_ratio": ratio,  # >1 = more buyers, <1 = more sellers
        "top_bid": ob["bids"][0][0] if ob["bids"] else None,
        "top_ask": ob["asks"][0][0] if ob["asks"] else None,
    }


def list_available_symbols(exchange_id: str = "binance", quote: str = "USDT") -> list[str]:
    """List all USDT-quoted symbols on the exchange."""
    exchange = _get_exchange(exchange_id)
    markets = exchange.load_markets()
    return [s for s in markets if s.endswith(f"/{quote}") and markets[s]["active"]]
