"""
Telegram alert bot.
Sends formatted trading signals and opportunity alerts.
"""
import asyncio
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from analyzer.config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

BIAS_EMOJI = {
    "STRONG BUY": "🚀",
    "BUY": "📈",
    "NEUTRAL": "⚖️",
    "SELL": "📉",
    "STRONG SELL": "🔴",
}


def send_alert(message: str) -> bool:
    """Send a plain text message via Telegram bot."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[telegram] Not configured. Message: {message}")
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
        }
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"[telegram] Error sending alert: {e}")
        return False


def format_opportunity_alert(opp) -> str:
    """Format an Opportunity object as a readable Telegram message."""
    emoji = BIAS_EMOJI.get(opp.bias, "❓")
    lines = [
        f"{emoji} <b>{opp.symbol}</b> — {opp.bias}",
        f"Price: <b>${opp.price:,.4f}</b> | Score: {opp.score:+.2f}",
        f"Timeframe: {opp.timeframe}",
        "",
    ]

    if opp.rsi:
        lines.append(f"RSI: {opp.rsi:.1f}")

    if opp.stop_loss and opp.take_profit:
        lines.append(f"Stop Loss: ${opp.stop_loss:,.4f}")
        lines.append(f"Take Profit: ${opp.take_profit:,.4f}")
        if opp.risk_reward:
            lines.append(f"R/R: {opp.risk_reward:.2f}x")

    if opp.signals:
        lines.append("")
        lines.append("<b>Signals:</b>")
        for s in opp.signals[:4]:
            sig_emoji = "✅" if s["signal"] == "BUY" else "❌" if s["signal"] == "SELL" else "➡️"
            lines.append(f"{sig_emoji} {s['reason']}")

    if opp.patterns:
        lines.append("")
        lines.append("<b>Patterns:</b>")
        for p in opp.patterns[:3]:
            lines.append(f"📊 {p['pattern']} ({p['signal']})")

    if opp.news_summary:
        lines.append("")
        lines.append(f"<b>News:</b> {opp.news_summary[:200]}")

    if opp.macro_notes:
        lines.append("")
        lines.append("<b>Macro:</b>")
        for note in opp.macro_notes[:2]:
            lines.append(f"🌐 {note}")

    return "\n".join(lines)


def send_opportunity(opp) -> bool:
    """Send a formatted opportunity alert."""
    message = format_opportunity_alert(opp)
    return send_alert(message)


def send_scan_summary(opportunities: list, top_n: int = 5) -> bool:
    """Send a market scan summary with top N opportunities."""
    if not opportunities:
        return send_alert("📡 Market scan complete — no strong signals found.")

    lines = ["<b>📡 Market Scan Complete</b>", ""]
    for i, opp in enumerate(opportunities[:top_n], 1):
        emoji = BIAS_EMOJI.get(opp.bias, "❓")
        lines.append(
            f"{i}. {emoji} <b>{opp.symbol}</b> | {opp.bias} | Score: {opp.score:+.2f} | RSI: {opp.rsi:.1f if opp.rsi else 'N/A'}"
        )

    message = "\n".join(lines)
    return send_alert(message)
