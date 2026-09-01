# ai_brain.py

import json

import g4f

from config import G4F_MODEL, G4F_PROVIDER_NAME


def _extract_json_from_text(text):
    """Pull the first JSON object from a raw LLM response."""
    if not isinstance(text, str):
        raise ValueError("AI response is not a string.")

    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start : end + 1]

    return text


def get_ai_decision(market_data, symbol):
    """
    Send multi-timeframe market data to a free G4F model and return
    a structured trading decision.

    Args:
        market_data (dict): Output from fetch_multi_timeframe_data()
        symbol (str): Trading symbol, e.g. XAUUSDm

    Returns:
        dict: {
            "signal": "BUY",
            "confidence_score": 85,
            "logic": "..."
        }
    """

    daily_data = market_data["daily_data"]
    hourly_data = market_data["hourly_data"]

    system_prompt = f"""
You are an elite quantitative trader analyzing {symbol}.

Analyze the provided Daily and H1 market data carefully.

Your analysis must consider:
- Price action
- Market structure
- Trend direction
- Momentum
- Support and resistance
- Breakouts and reversals
- Higher-timeframe Daily context
- Lower-timeframe H1 confirmation

Based ONLY on the supplied market data, determine the best trading signal.

You MUST return your decision in EXACTLY this JSON format:

{{
    "signal": "BUY",
    "confidence_score": 85,
    "logic": "2 sentences explaining your reasoning"
}}

Rules:
- "signal" MUST be exactly one of: "BUY", "SELL", "HOLD"
- "confidence_score" MUST be an integer from 0 to 100.
- "logic" MUST contain exactly 2 sentences explaining the reasoning.
- Do NOT include Markdown.
- Do NOT include code fences.
- Do NOT include any text before or after the JSON.
- Return valid JSON only.
"""

    user_prompt = f"""
Analyze the following market data for {symbol}.

=== DAILY (D1) - MACRO TREND ===
{daily_data}

=== H1 - MICRO MOMENTUM ===
{hourly_data}

Return ONLY the required JSON decision.
"""

    provider_map = {
        "Gemini": g4f.Provider.Gemini,
        "OpenRouterFree": g4f.Provider.OpenRouterFree,
        "Groq": g4f.Provider.Groq,
        "DeepSeek": g4f.Provider.DeepSeek,
    }

    provider = provider_map.get(G4F_PROVIDER_NAME, g4f.Provider.Gemini)

    try:
        ai_content = g4f.ChatCompletion.create(
            model=G4F_MODEL,
            provider=provider,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
        )

        if isinstance(ai_content, list):
            ai_content = "".join(str(part) for part in ai_content)

        clean_text = _extract_json_from_text(ai_content)
        decision = json.loads(clean_text)

        required_fields = {"signal", "confidence_score", "logic"}
        if not required_fields.issubset(decision.keys()):
            raise ValueError("AI response is missing required fields.")

        if decision["signal"] not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(f"Invalid signal: {decision['signal']}")

        confidence = decision["confidence_score"]
        if not isinstance(confidence, int) or not 0 <= confidence <= 100:
            raise ValueError("confidence_score must be an integer between 0 and 100.")

        if not isinstance(decision["logic"], str):
            raise ValueError("logic must be a string.")

        return {
            "signal": decision["signal"],
            "confidence_score": confidence,
            "logic": decision["logic"],
        }

    except Exception as e:
        print(f"[ERROR] G4F AI decision failed: {type(e).__name__}: {e}")
        return {
            "signal": "HOLD",
            "confidence_score": 0,
            "logic": f"AI error: {type(e).__name__} - {str(e)[:60]}",
        }