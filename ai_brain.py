# ai_brain.py

import json
import requests

from config import GROQ_API_KEY, GROQ_MODEL


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def get_ai_decision(market_data, symbol):
    """
    Send multi-timeframe market data to Groq AI and return
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

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "temperature": 0.1,
        "max_tokens": 500,
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )

        if response.status_code != 200:
            error_text = response.text[:500]
            print(f"[ERROR] Groq API returned {response.status_code}: {error_text}")
            response.raise_for_status()

        response_data = response.json()

        ai_content = response_data["choices"][0]["message"]["content"]

        # Parse the AI response as JSON
        decision = json.loads(ai_content)

        # Validate required fields
        required_fields = {
            "signal",
            "confidence_score",
            "logic",
        }

        if not required_fields.issubset(decision.keys()):
            raise ValueError(
                "AI response is missing required fields."
            )

        # Validate signal
        if decision["signal"] not in {"BUY", "SELL", "HOLD"}:
            raise ValueError(
                f"Invalid signal: {decision['signal']}"
            )

        # Validate confidence score
        confidence = decision["confidence_score"]

        if not isinstance(confidence, int) or not 0 <= confidence <= 100:
            raise ValueError(
                "confidence_score must be an integer between 0 and 100."
            )

        # Validate logic
        if not isinstance(decision["logic"], str):
            raise ValueError("logic must be a string.")

        return {
            "signal": decision["signal"],
            "confidence_score": confidence,
            "logic": decision["logic"],
        }

    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error calling Groq API: {e}")
        return {
            "signal": "HOLD",
            "confidence_score": 0,
            "logic": "Network error - unable to reach Groq API",
        }

    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON from Groq API: {e}")
        return {
            "signal": "HOLD",
            "confidence_score": 0,
            "logic": "AI parsing error - response was not valid JSON",
        }

    except ValueError as e:
        print(f"[ERROR] Validation error: {e}")
        return {
            "signal": "HOLD",
            "confidence_score": 0,
            "logic": f"AI validation failed: {str(e)[:50]}",
        }