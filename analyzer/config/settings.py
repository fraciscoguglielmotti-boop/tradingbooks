import os
from dotenv import load_dotenv

load_dotenv()

# === API KEYS ===
ALPACA_API_KEY = os.getenv("ALPACA_API_KEY", "")
ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY", "")
ALPACA_BASE_URL = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")

BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# === DEFAULT WATCHLISTS ===
DEFAULT_STOCKS = ["AAPL", "MSFT", "TSLA", "NVDA", "SPY", "QQQ", "AMZN", "META", "GOOGL"]
DEFAULT_CRYPTO = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT"]

# === TECHNICAL ANALYSIS DEFAULTS ===
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2
ATR_PERIOD = 14
EMA_PERIODS = [9, 21, 50, 200]

# === SIGNAL THRESHOLDS ===
RSI_OVERSOLD = 30
RSI_OVERBOUGHT = 70
SIGNAL_MIN_SCORE = 2  # min confirmed signals to trigger alert

# === TIMEFRAMES ===
TIMEFRAMES = {
    "1m": "1min",
    "5m": "5min",
    "15m": "15min",
    "1h": "1hour",
    "4h": "4hour",
    "1d": "1day",
    "1w": "1week",
}

# === BACKTESTING ===
BACKTEST_INITIAL_CASH = 100_000
BACKTEST_FEES = 0.001  # 0.1% per trade
