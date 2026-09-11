import json
import subprocess
import requests
import config


def load_learned_rules(symbol: str) -> list[dict]:
    try:
        if not config.RULES_FILE.exists():
            return []
        with open(config.RULES_FILE, "r", encoding="utf-8") as f:
            doc = json.load(f)
        rules = doc.get("rules", [])
        active = [r for r in rules if r.get("affected_symbol") in ("ALL", symbol)]
        return active
    except Exception:
        return []


def _call_puter(system_prompt: str, user_prompt: str) -> str:
    bridge_path = str(config.BASE_DIR / "puter_bridge.js")
    request_data = json.dumps({
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    })

    result = subprocess.run(
        ["node", bridge_path, config.PUTER_AUTH_TOKEN, config.PUTER_MODEL],
        input=request_data,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Puter bridge error: {result.stderr}")

    response = json.loads(result.stdout)
    return response.get("content", "")


def _call_deepseek(system_prompt: str, user_prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.1,
        "max_tokens": 512,
    }

    resp = requests.post(
        f"{config.DEEPSEEK_API_BASE}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()


def _call_groq(system_prompt: str, user_prompt: str) -> str:
    from groq import Groq
    client = Groq(api_key=config.GROQ_API_KEY)
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        model=config.GROQ_MODEL,
        temperature=0.1,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


def _call_llm(system_prompt: str, user_prompt: str) -> str:
    if config.USE_PUTER and config.PUTER_AUTH_TOKEN:
        print("[AI] Using Puter.js free DeepSeek bridge")
        return _call_puter(system_prompt, user_prompt)
    elif config.USE_GROQ and config.GROQ_API_KEY:
        print("[AI] Using Groq free Llama 4")
        return _call_groq(system_prompt, user_prompt)
    elif config.DEEPSEEK_API_KEY:
        print("[AI] Using DeepSeek API")
        return _call_deepseek(system_prompt, user_prompt)
    else:
        raise RuntimeError(
            "No LLM configured. Set GROQ_API_KEY, DEEPSEEK_API_KEY, or USE_PUTER=true"
        )


def get_ai_decision(market_data: dict, symbol: str) -> dict:
    h1 = market_data.get("h1_data", {})
    d1 = market_data.get("daily_data", {})
    bid = market_data.get("bid", 0)
    ask = market_data.get("ask", 0)
    spread = market_data.get("spread", 0)

    learned_rules = load_learned_rules(symbol)
    rules_text = ""
    if learned_rules:
        rules_lines = []
        for r in learned_rules:
            rules_lines.append(
                f"- IF setup matches \"{r.get('setup', '')}\" on {r.get('affected_symbol', 'ALL')}, "
                f"REDUCE confidence by {r.get('confidence_reduction_points', 0)} points. "
                f"Evidence: {r.get('evidence', 'N/A')}"
            )
        rules_text = "\n".join(rules_lines)

    risk_section = ""
    if rules_text:
        risk_section = f"""
ACTIVE RISK AUDIT RULES (MUST APPLY):
{rules_text}
If any condition above matches current setup, reduce confidence_score accordingly.
"""

    system_prompt = f"""You are a senior quantitative hedge fund portfolio manager with strict risk management.
Analyze the market data and produce a raw JSON trading decision.

{risk_section}
RULES:
- ONLY return raw JSON, no markdown, no explanation outside JSON.
- For BUY: stop_loss MUST BE BELOW current price, take_profit MUST BE ABOVE current price.
- For SELL: stop_loss MUST BE ABOVE current price, take_profit MUST BE BELOW current price.
- Use ATR-based dynamic stops if appropriate.

Response format (raw JSON only):
{{"signal": "BUY" or "SELL" or "HOLD", "confidence_score": 0-100 integer, "stop_loss": float, "take_profit": float, "logic": "concise explanation including indicators and any learned-rule deductions"}}"""

    user_prompt = f"""Symbol: {symbol}
Current Bid: {bid} | Ask: {ask} | Spread: {spread}

Daily Timeframe:
- EMA(200): {d1.get('ema_200', 'N/A')}
- RSI(14): {d1.get('rsi', 'N/A')}
- ATR(14): {d1.get('atr', 'N/A')}
- Relative Volume: {d1.get('relative_volume', 'N/A')}
- Trend: {d1.get('price_trend', {})}

H1 Timeframe:
- EMA(200): {h1.get('ema_200', 'N/A')}
- RSI(14): {h1.get('rsi', 'N/A')}
- ATR(14): {h1.get('atr', 'N/A')}
- Relative Volume: {h1.get('relative_volume', 'N/A')}
- Trend: {h1.get('price_trend', {})}

Provide your trading decision as raw JSON."""

    try:
        content = _call_llm(system_prompt, user_prompt)

        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        decision = json.loads(content)
        print(f"[AI] Raw decision for {symbol}: {decision}")

        signal = decision.get("signal", "HOLD").upper()
        confidence = int(decision.get("confidence_score", 0))
        sl = float(decision.get("stop_loss", 0))
        tp = float(decision.get("take_profit", 0))
        logic = decision.get("logic", "")

        if confidence < config.CONFIDENCE_THRESHOLD:
            print(f"[AI] Confidence {confidence} < threshold {config.CONFIDENCE_THRESHOLD} -> HOLD")
            decision["signal"] = "HOLD"
            decision["logic"] = f"{logic} [Below confidence threshold]"

        current_price = ask if signal == "BUY" else bid
        h1_atr = h1.get("atr", 0)

        if signal == "BUY":
            if sl >= current_price or tp <= current_price:
                sl = round(current_price - 1.5 * h1_atr, 6)
                tp = round(current_price + 3.0 * h1_atr, 6)
                print(f"[AI] Fixed BUY geometry: SL={sl}, TP={tp}")
        elif signal == "SELL":
            if sl <= current_price or tp >= current_price:
                sl = round(current_price + 1.5 * h1_atr, 6)
                tp = round(current_price - 3.0 * h1_atr, 6)
                print(f"[AI] Fixed SELL geometry: SL={sl}, TP={tp}")

        decision["signal"] = signal
        decision["confidence_score"] = confidence
        decision["stop_loss"] = sl
        decision["take_profit"] = tp

        return decision

    except Exception as e:
        print(f"[AI] Decision error for {symbol}: {e}")
        return {
            "signal": "HOLD",
            "confidence_score": 0,
            "stop_loss": 0,
            "take_profit": 0,
            "logic": f"Error communicating with LLM: {e}",
        }
