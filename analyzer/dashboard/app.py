"""
TradingAnalyzer — Streamlit Dashboard
Run with: streamlit run analyzer/dashboard/app.py
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

st.set_page_config(
    page_title="TradingAnalyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── SIDEBAR ────────────────────────────────────────────────────────────────

st.sidebar.title("📈 TradingAnalyzer")
st.sidebar.markdown("---")

mode = st.sidebar.radio(
    "Mode",
    ["🔍 Single Asset", "📡 Market Scan", "⚙️ Backtesting", "🌐 Macro Dashboard"],
    label_visibility="collapsed",
)

# ─── HELPERS ────────────────────────────────────────────────────────────────

BIAS_COLOR = {
    "STRONG BUY": "#00d4a0",
    "BUY": "#26a69a",
    "NEUTRAL": "#9e9e9e",
    "SELL": "#ef5350",
    "STRONG SELL": "#b71c1c",
}

BIAS_EMOJI = {
    "STRONG BUY": "🚀",
    "BUY": "📈",
    "NEUTRAL": "⚖️",
    "SELL": "📉",
    "STRONG SELL": "🔴",
}


def score_to_gauge(score: float) -> go.Figure:
    """Render a gauge chart for the composite signal score."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score,
        domain={"x": [0, 1], "y": [0, 1]},
        title={"text": "Signal Score", "font": {"size": 18}},
        delta={"reference": 0},
        gauge={
            "axis": {"range": [-6, 6], "tickwidth": 1},
            "bar": {"color": "white"},
            "steps": [
                {"range": [-6, -3], "color": "#b71c1c"},
                {"range": [-3, -1], "color": "#ef5350"},
                {"range": [-1, 1], "color": "#9e9e9e"},
                {"range": [1, 3], "color": "#26a69a"},
                {"range": [3, 6], "color": "#00d4a0"},
            ],
            "threshold": {
                "line": {"color": "white", "width": 4},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(height=220, margin=dict(t=40, b=10, l=10, r=10))
    return fig


def candlestick_chart(df: pd.DataFrame, symbol: str, indicators: list) -> go.Figure:
    """Full interactive candlestick chart with indicators."""
    rows = 3
    row_heights = [0.55, 0.25, 0.20]
    specs = [[{"secondary_y": False}], [{"secondary_y": False}], [{"secondary_y": False}]]

    fig = make_subplots(
        rows=rows, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        specs=specs,
    )

    # Candlesticks
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["open"], high=df["high"],
        low=df["low"], close=df["close"],
        name=symbol, increasing_line_color="#26a69a", decreasing_line_color="#ef5350",
    ), row=1, col=1)

    # EMAs
    ema_colors = {"ema_9": "#ffd700", "ema_21": "#ff8c00", "ema_50": "#00bfff", "ema_200": "#ff69b4"}
    for ema, color in ema_colors.items():
        if ema in df.columns and "EMA" in indicators:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[ema], name=ema.upper(),
                line=dict(color=color, width=1.2), opacity=0.8,
            ), row=1, col=1)

    # Bollinger Bands
    if "bb_upper" in df.columns and "BB Bands" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_upper"], name="BB Upper",
                                  line=dict(color="#7c7c7c", dash="dot", width=1)), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_lower"], name="BB Lower",
                                  line=dict(color="#7c7c7c", dash="dot", width=1),
                                  fill="tonexty", fillcolor="rgba(124,124,124,0.07)"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["bb_mid"], name="BB Mid",
                                  line=dict(color="#7c7c7c", width=0.8, dash="dash")), row=1, col=1)

    # Volume
    colors = ["#26a69a" if c >= o else "#ef5350"
              for c, o in zip(df["close"], df["open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["volume"], name="Volume",
                          marker_color=colors, opacity=0.7), row=2, col=1)
    if "vol_sma_20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["vol_sma_20"], name="Vol SMA20",
                                  line=dict(color="#ffd700", width=1.2)), row=2, col=1)

    # RSI
    if "rsi" in df.columns and "RSI" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["rsi"], name="RSI",
                                  line=dict(color="#ab47bc", width=1.5)), row=3, col=1)
        fig.add_hline(y=70, line_color="#ef5350", line_dash="dot", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_color="#26a69a", line_dash="dot", line_width=1, row=3, col=1)

    # MACD (alternative to RSI)
    elif "macd" in df.columns and "MACD" in indicators:
        fig.add_trace(go.Scatter(x=df.index, y=df["macd"], name="MACD",
                                  line=dict(color="#2196f3", width=1.5)), row=3, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df["macd_signal"], name="Signal",
                                  line=dict(color="#ff9800", width=1.2)), row=3, col=1)
        colors_hist = ["#26a69a" if v >= 0 else "#ef5350"
                       for v in df["macd_hist"].fillna(0)]
        fig.add_trace(go.Bar(x=df.index, y=df["macd_hist"], name="Histogram",
                              marker_color=colors_hist, opacity=0.6), row=3, col=1)

    fig.update_layout(
        template="plotly_dark",
        height=650,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis_rangeslider_visible=False,
        margin=dict(t=20, b=10, l=0, r=0),
    )
    fig.update_yaxes(title_text="Price", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_yaxes(title_text="RSI" if "RSI" in indicators else "MACD", row=3, col=1)

    return fig


# ─── PAGE: SINGLE ASSET ─────────────────────────────────────────────────────

if "🔍 Single Asset" in mode:
    st.title("Asset Analyzer")

    col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
    with col1:
        symbol = st.text_input("Symbol", value="AAPL", help="Stock: AAPL, BTC — Crypto: BTC/USDT").upper().strip()
    with col2:
        asset_type = st.selectbox("Type", ["Stock", "Crypto"])
    with col3:
        if asset_type == "Stock":
            period_options = ["1mo", "3mo", "6mo", "1y", "2y"]
            period = st.selectbox("Period", period_options, index=2)
            interval = st.selectbox("Interval", ["1d", "1wk", "1h"])
        else:
            period = st.selectbox("Candles", [100, 200, 300, 500], index=2)
            interval = st.selectbox("Timeframe", ["1d", "4h", "1h", "15m"])
    with col4:
        with_news = st.toggle("News AI", value=False)
        with_macro = st.toggle("Macro", value=False)

    indicators = st.multiselect(
        "Indicators",
        ["EMA", "BB Bands", "RSI", "MACD", "Volume"],
        default=["EMA", "BB Bands", "RSI"],
    )

    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

    if analyze_btn or "df_cache" in st.session_state:
        with st.spinner(f"Fetching data for {symbol}..."):
            try:
                if asset_type == "Stock":
                    from analyzer.data.fetchers.stocks import get_ohlcv, get_fundamentals
                    df = get_ohlcv(symbol, period=period, interval=interval)
                    fundamentals = get_fundamentals(symbol)
                else:
                    from analyzer.data.fetchers.crypto import get_ohlcv
                    df = get_ohlcv(symbol, timeframe=interval, limit=int(period))
                    fundamentals = None

                from analyzer.analysis.technical import add_all_indicators
                df = add_all_indicators(df)
                st.session_state["df_cache"] = df

                from analyzer.signals.engine import analyze_asset
                news_data = None
                macro_data = None

                if with_news:
                    from analyzer.data.fetchers.news import get_news_for_symbol, analyze_news_with_ai
                    base_sym = symbol.split("/")[0] if "/" in symbol else symbol
                    articles = get_news_for_symbol(base_sym)
                    news_data = analyze_news_with_ai(base_sym, articles)

                if with_macro:
                    from analyzer.data.fetchers.macro import get_macro_dashboard
                    macro_data = get_macro_dashboard()

                opp = analyze_asset(
                    symbol, asset_type.lower(), df,
                    news_data=news_data, macro_data=macro_data, timeframe=interval
                )

            except Exception as e:
                st.error(f"Error: {e}")
                st.stop()

        # ── Layout ──
        col_chart, col_info = st.columns([3, 1])

        with col_chart:
            fig = candlestick_chart(df, symbol, indicators)
            st.plotly_chart(fig, use_container_width=True)

        with col_info:
            # Bias badge
            bias_color = BIAS_COLOR.get(opp.bias, "#9e9e9e")
            st.markdown(
                f"<div style='background:{bias_color};padding:12px;border-radius:8px;text-align:center'>"
                f"<h2 style='color:white;margin:0'>{BIAS_EMOJI.get(opp.bias,'')} {opp.bias}</h2>"
                f"<p style='color:white;margin:4px 0'>Score: {opp.score:+.2f}</p>"
                f"</div>",
                unsafe_allow_html=True,
            )
            st.plotly_chart(score_to_gauge(opp.score), use_container_width=True)

            # Key metrics
            st.markdown("**Key Metrics**")
            m1, m2 = st.columns(2)
            m1.metric("Price", f"${opp.price:,.4f}")
            m2.metric("RSI", f"{opp.rsi:.1f}" if opp.rsi else "N/A",
                      delta="Oversold" if opp.rsi and opp.rsi < 30 else "Overbought" if opp.rsi and opp.rsi > 70 else None)
            if opp.stop_loss:
                m1.metric("Stop Loss", f"${opp.stop_loss:,.4f}")
                m2.metric("Take Profit", f"${opp.take_profit:,.4f}")
            if opp.risk_reward:
                st.metric("Risk/Reward", f"{opp.risk_reward:.2f}x")

        # ── Signals ──
        st.markdown("---")
        col_sig, col_pat, col_news = st.columns(3)

        with col_sig:
            st.subheader("Signals")
            for s in opp.signals:
                if s["signal"] == "BUY":
                    st.success(s["reason"])
                elif s["signal"] == "SELL":
                    st.error(s["reason"])
                else:
                    st.info(s["reason"])

        with col_pat:
            st.subheader("Patterns")
            if opp.patterns:
                for p in opp.patterns:
                    if p["signal"] == "BUY":
                        st.success(f"{p['pattern']}")
                    elif p["signal"] == "SELL":
                        st.error(f"{p['pattern']}")
                    else:
                        st.warning(f"{p['pattern']}: {p['signal']}")
            else:
                st.info("No patterns detected")

        with col_news:
            st.subheader("News & Context")
            if news_data and not news_data.get("error"):
                sentiment = news_data.get("overall_sentiment", "neutral")
                st.markdown(f"**Sentiment:** {sentiment.upper()}")
                st.markdown(f"**Confidence:** {news_data.get('confidence', 0)}%")
                if news_data.get("summary"):
                    st.markdown(news_data["summary"])
                if news_data.get("key_risks"):
                    st.markdown("**Risks:**")
                    for r in news_data["key_risks"][:3]:
                        st.markdown(f"- {r}")
                if news_data.get("key_catalysts"):
                    st.markdown("**Catalysts:**")
                    for c in news_data["key_catalysts"][:3]:
                        st.markdown(f"- {c}")
            else:
                st.info("Enable News AI toggle to see contextual analysis")

        # ── Fundamentals (stocks only) ──
        if fundamentals and asset_type == "Stock":
            st.markdown("---")
            st.subheader("Fundamentals")
            fc = st.columns(4)
            fc[0].metric("Market Cap", f"${fundamentals.get('market_cap', 0)/1e9:.1f}B" if fundamentals.get("market_cap") else "N/A")
            fc[1].metric("P/E Ratio", f"{fundamentals.get('pe_ratio', 'N/A'):.1f}" if fundamentals.get("pe_ratio") else "N/A")
            fc[2].metric("EPS", f"${fundamentals.get('eps', 0):.2f}" if fundamentals.get("eps") else "N/A")
            fc[3].metric("Beta", f"{fundamentals.get('beta', 'N/A'):.2f}" if fundamentals.get("beta") else "N/A")

        # ── Macro ──
        if macro_data and not macro_data.get("error"):
            st.markdown("---")
            st.subheader("Macro Context")
            interp = macro_data.get("interpretation", {})
            bias = interp.get("bias", "neutral")
            st.markdown(f"**Macro Bias:** {bias.upper()}")
            for note in interp.get("signals", []):
                st.markdown(f"🌐 {note}")

        # ── Alert button ──
        if st.button("📱 Send Telegram Alert"):
            from analyzer.alerts.telegram import send_opportunity
            success = send_opportunity(opp)
            if success:
                st.success("Alert sent to Telegram!")
            else:
                st.warning("Telegram not configured (check .env)")


# ─── PAGE: MARKET SCAN ──────────────────────────────────────────────────────

elif "📡 Market Scan" in mode:
    st.title("Market Scan")
    st.markdown("Scan multiple assets and rank by signal strength.")

    col1, col2, col3 = st.columns(3)
    with col1:
        scan_stocks = st.text_area(
            "Stocks (one per line)",
            "AAPL\nMSFT\nNVDA\nTSLA\nSPY\nQQQ\nAMZN\nMETA",
            height=160,
        )
    with col2:
        scan_crypto = st.text_area(
            "Crypto (one per line)",
            "BTC/USDT\nETH/USDT\nSOL/USDT\nBNB/USDT",
            height=160,
        )
    with col3:
        scan_tf = st.selectbox("Timeframe", ["1d", "1wk"], index=0)
        scan_news = st.toggle("Include News AI", value=False)
        scan_macro = st.toggle("Include Macro", value=False)
        top_n = st.slider("Show top N", 3, 20, 8)

    if st.button("Run Scan", type="primary", use_container_width=True):
        stocks_list = [s.strip().upper() for s in scan_stocks.split("\n") if s.strip()]
        crypto_list = [s.strip().upper() for s in scan_crypto.split("\n") if s.strip()]

        with st.spinner(f"Scanning {len(stocks_list)} stocks + {len(crypto_list)} crypto..."):
            from analyzer.signals.engine import scan_watchlist
            opportunities = scan_watchlist(
                stocks=stocks_list,
                crypto=crypto_list,
                timeframe=scan_tf,
                with_news=scan_news,
                with_macro=scan_macro,
            )

        if not opportunities:
            st.warning("No opportunities found.")
        else:
            # Summary table
            data = []
            for opp in opportunities:
                data.append({
                    "Symbol": opp.symbol,
                    "Type": opp.asset_type.upper(),
                    "Price": f"${opp.price:,.4f}",
                    "Bias": f"{BIAS_EMOJI.get(opp.bias,'')} {opp.bias}",
                    "Score": f"{opp.score:+.2f}",
                    "Tech": f"{opp.technical_score:+.2f}",
                    "News": f"{opp.news_score:+.2f}",
                    "RSI": f"{opp.rsi:.1f}" if opp.rsi else "N/A",
                    "R/R": f"{opp.risk_reward:.2f}x" if opp.risk_reward else "N/A",
                    "Stop": f"${opp.stop_loss:,.4f}" if opp.stop_loss else "N/A",
                    "Target": f"${opp.take_profit:,.4f}" if opp.take_profit else "N/A",
                })
            df_table = pd.DataFrame(data)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            # Bar chart: scores
            scores_df = pd.DataFrame({
                "Symbol": [o.symbol for o in opportunities[:top_n]],
                "Score": [o.score for o in opportunities[:top_n]],
                "Bias": [o.bias for o in opportunities[:top_n]],
            })
            fig = px.bar(
                scores_df, x="Symbol", y="Score", color="Bias",
                color_discrete_map={
                    "STRONG BUY": "#00d4a0", "BUY": "#26a69a",
                    "NEUTRAL": "#9e9e9e", "SELL": "#ef5350", "STRONG SELL": "#b71c1c",
                },
                title="Signal Scores — Top Opportunities",
                template="plotly_dark",
            )
            st.plotly_chart(fig, use_container_width=True)

            # Telegram summary
            if st.button("📱 Send Summary to Telegram"):
                from analyzer.alerts.telegram import send_scan_summary
                send_scan_summary(opportunities, top_n=5)
                st.success("Sent!")


# ─── PAGE: BACKTESTING ──────────────────────────────────────────────────────

elif "⚙️ Backtesting" in mode:
    st.title("Backtesting Engine")
    st.markdown("No-lookahead simulation — signals execute on the *next candle's open*.")

    col1, col2, col3 = st.columns(3)
    with col1:
        bt_symbol = st.text_input("Symbol", "BTC/USDT")
        bt_type = st.selectbox("Type", ["Crypto", "Stock"])
    with col2:
        if bt_type == "Stock":
            bt_period = st.selectbox("Period", ["1y", "2y", "5y"], index=1)
            bt_interval = st.selectbox("Interval", ["1d", "1wk"])
        else:
            bt_limit = st.selectbox("Candles", [500, 1000], index=0)
            bt_interval = st.selectbox("Timeframe", ["1d", "4h", "1h"])
        initial_cash = st.number_input("Initial Capital ($)", value=100000, step=10000)
    with col3:
        from analyzer.backtesting.strategies.base import STRATEGIES
        strategy_options = list(STRATEGIES.keys())
        selected_strategies = st.multiselect("Strategies", strategy_options, default=strategy_options)
        fees = st.slider("Fees (%)", 0.0, 0.5, 0.1, step=0.05) / 100

    if st.button("Run Backtest", type="primary", use_container_width=True):
        with st.spinner("Running backtests..."):
            try:
                if bt_type == "Stock":
                    from analyzer.data.fetchers.stocks import get_ohlcv
                    df_bt = get_ohlcv(bt_symbol, period=bt_period, interval=bt_interval)
                else:
                    from analyzer.data.fetchers.crypto import get_ohlcv
                    df_bt = get_ohlcv(bt_symbol, timeframe=bt_interval, limit=bt_limit)

                from analyzer.backtesting.engine import compare_strategies
                results = compare_strategies(
                    df_bt,
                    symbol=bt_symbol,
                    timeframe=bt_interval,
                    strategy_names=selected_strategies,
                    initial_cash=initial_cash,
                    fees=fees,
                )
            except Exception as e:
                st.error(f"Backtest error: {e}")
                st.stop()

        # Results table
        st.subheader("Strategy Comparison")
        table_data = []
        for r in results:
            table_data.append({
                "Strategy": r.strategy_name,
                "Return %": f"{r.total_return_pct:+.2f}%",
                "Sharpe": f"{r.sharpe_ratio:.2f}" if r.sharpe_ratio else "N/A",
                "Max DD %": f"{r.max_drawdown_pct:.2f}%",
                "Win Rate": f"{r.win_rate_pct:.1f}%",
                "Trades": r.total_trades,
                "P. Factor": f"{r.profit_factor:.2f}" if r.profit_factor else "N/A",
                "Final Value": f"${r.final_value:,.0f}",
            })
        st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

        # Equity curves
        st.subheader("Equity Curves")
        fig_eq = go.Figure()
        for r in results:
            if r.equity_curve is not None:
                fig_eq.add_trace(go.Scatter(
                    x=r.equity_curve.index,
                    y=r.equity_curve.values,
                    name=r.strategy_name,
                    mode="lines",
                ))
        fig_eq.add_hline(y=initial_cash, line_dash="dot", line_color="gray")
        fig_eq.update_layout(template="plotly_dark", height=400, yaxis_title="Portfolio Value ($)")
        st.plotly_chart(fig_eq, use_container_width=True)

        # Bar: returns comparison
        fig_bar = px.bar(
            pd.DataFrame({"Strategy": [r.strategy_name for r in results],
                          "Return": [r.total_return_pct for r in results]}),
            x="Strategy", y="Return", title="Return % by Strategy",
            color="Return", color_continuous_scale=["#ef5350", "#9e9e9e", "#26a69a"],
            template="plotly_dark",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

        # Trade details (best strategy)
        best = results[0] if results else None
        if best and best.trades is not None and not best.trades.empty:
            st.subheader(f"Trade Log — {best.strategy_name}")
            st.dataframe(best.trades, use_container_width=True)


# ─── PAGE: MACRO DASHBOARD ──────────────────────────────────────────────────

elif "🌐 Macro Dashboard" in mode:
    st.title("Macro Dashboard")
    st.markdown("Federal Reserve data, yield curve, VIX, and key economic indicators.")

    if st.button("Fetch Macro Data", type="primary"):
        from analyzer.data.fetchers.macro import get_macro_dashboard, MACRO_SERIES, get_fred_series
        with st.spinner("Fetching FRED data..."):
            macro = get_macro_dashboard()

        if macro.get("error"):
            st.error(f"Error: {macro['error']} — Set FRED_API_KEY in .env")
        else:
            interp = macro.get("interpretation", {})
            bias = interp.get("bias", "neutral")
            bias_color = {"bullish": "#26a69a", "bearish": "#ef5350", "neutral": "#9e9e9e"}.get(bias, "#9e9e9e")
            st.markdown(
                f"<div style='background:{bias_color};padding:10px;border-radius:6px'>"
                f"<h3 style='color:white;margin:0'>Macro Bias: {bias.upper()}</h3></div>",
                unsafe_allow_html=True,
            )
            st.markdown("")

            for note in interp.get("signals", []):
                st.info(f"🌐 {note}")

            st.markdown("---")
            cols = st.columns(4)
            indicators_display = [
                ("fed_funds_rate", "Fed Funds Rate", "%"),
                ("cpi", "CPI (Inflation)", ""),
                ("unemployment", "Unemployment", "%"),
                ("yield_curve_10y2y", "Yield Curve (10Y-2Y)", "%"),
                ("vix", "VIX Fear Index", ""),
                ("treasury_10y", "10Y Treasury", "%"),
                ("usd_index", "USD Index", ""),
                ("pce_inflation", "PCE Inflation", ""),
            ]
            for i, (key, label, unit) in enumerate(indicators_display):
                val = macro.get(key, {})
                if not val.get("error"):
                    delta = val.get("change", 0)
                    cols[i % 4].metric(
                        label,
                        f"{val['value']:.2f}{unit}",
                        delta=f"{delta:+.4f}",
                    )

            # Historical chart for selected series
            st.markdown("---")
            st.subheader("Historical Chart")
            selected_series = st.selectbox("Select Series", list(MACRO_SERIES.keys()))
            try:
                series_data = get_fred_series(MACRO_SERIES[selected_series])
                fig_macro = px.line(
                    series_data, title=selected_series.replace("_", " ").title(),
                    template="plotly_dark",
                )
                fig_macro.update_layout(height=350, yaxis_title=selected_series)
                st.plotly_chart(fig_macro, use_container_width=True)
            except Exception as e:
                st.error(str(e))
    else:
        st.info("Click 'Fetch Macro Data' to load Federal Reserve indicators. Requires FRED_API_KEY in .env")
