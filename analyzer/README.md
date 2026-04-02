# TradingAnalyzer

Sistema de análisis técnico + contextual para stocks y cripto.

## Setup

```bash
cd analyzer
pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus API keys
streamlit run dashboard/app.py
```

## APIs necesarias

| Servicio | URL | Costo |
|----------|-----|-------|
| Alpaca Markets | https://alpaca.markets | Gratis (paper trading) |
| Binance | https://www.binance.com/en/binance-api | Gratis |
| Alpha Vantage | https://www.alphavantage.co | Free/Paid |
| NewsAPI | https://newsapi.org | Free 100/día |
| OpenAI | https://platform.openai.com | Paid |
| FRED (macro) | https://fred.stlouisfed.org/docs/api/api_key.html | Gratis |
| Telegram Bot | https://t.me/BotFather | Gratis |

## Módulos

- **data/fetchers/stocks.py** — yfinance + Alpaca
- **data/fetchers/crypto.py** — ccxt (Binance)
- **data/fetchers/news.py** — NewsAPI + Alpha Vantage + OpenAI
- **data/fetchers/macro.py** — FRED (Fed, VIX, yield curve, etc.)
- **analysis/technical.py** — RSI, MACD, BB, Ichimoku, EMA, patrones
- **signals/engine.py** — Motor de señales combinadas (técnico + news + macro)
- **backtesting/engine.py** — Backtest sin lookahead con vectorbt
- **backtesting/strategies/base.py** — 5 estrategias incluidas
- **alerts/telegram.py** — Alertas via Telegram Bot
- **dashboard/app.py** — Dashboard Streamlit

## Estrategias incluidas

1. **RSI + MACD** — momentum clásico
2. **EMA Cross** — trend following
3. **BB Mean Reversion** — reversión a la media
4. **Dual Momentum** — Gary Antonacci style
5. **Ichimoku Cloud** — breakout

## Uso CLI (sin dashboard)

```python
from analyzer.signals.engine import scan_watchlist

opportunities = scan_watchlist(
    stocks=["AAPL", "TSLA", "NVDA"],
    crypto=["BTC/USDT", "ETH/USDT"],
    timeframe="1d",
    with_news=True,
)

for opp in opportunities:
    print(f"{opp.symbol}: {opp.bias} (score={opp.score:+.2f})")
```
