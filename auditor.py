import json
import requests
from datetime import datetime, timedelta
import config
import memory_store


def load_rules_document() -> dict:
    try:
        if not config.RULES_FILE.exists():
            return {"rules": [], "last_audit_at": None, "trades_analyzed": 0}
        with open(config.RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"rules": [], "last_audit_at": None, "trades_analyzed": 0}


def save_rules_document(doc: dict) -> None:
    with open(config.RULES_FILE, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, default=str)
    print(f"[LEARNING] Saved {len(doc.get('rules', []))} rules to {config.RULES_FILE}")


def run_audit(force: bool = False) -> dict:
    print("[AUDITOR] Starting audit cycle...")
    reconciled = memory_store.reconcile_closed_trades()
    if reconciled > 0:
        print(f"[AUDITOR] Reconciled {reconciled} newly closed trades")

    doc = load_rules_document()

    if not force and doc.get("last_audit_at"):
        last_audit = datetime.fromisoformat(doc["last_audit_at"])
        cooldown = timedelta(hours=config.AUDIT_COOLDOWN_HOURS)
        if datetime.now() - last_audit < cooldown:
            remaining = cooldown - (datetime.now() - last_audit)
            print(f"[AUDITOR] Cooldown active. Next audit in {remaining}")
            return {
                "status": "cooldown",
                "next_audit_in": str(remaining),
                "rules_count": len(doc.get("rules", [])),
            }

    memory = memory_store.load_trade_memory()
    closed = [t for t in memory if t.get("status") == "CLOSED"]

    if len(closed) < 3:
        print(f"[AUDITOR] Only {len(closed)} closed trades. Need at least 3.")
        return {
            "status": "insufficient_trades",
            "closed_count": len(closed),
            "rules_count": len(doc.get("rules", [])),
        }

    recent = closed[-50:]
    losses = [t for t in recent if t.get("outcome") == "LOSS"]

    if not losses:
        print("[AUDITOR] No losses found in recent trades. No new rules generated.")
        doc["last_audit_at"] = datetime.now().isoformat()
        doc["trades_analyzed"] = len(recent)
        save_rules_document(doc)
        return {
            "status": "no_losses",
            "trades_analyzed": len(recent),
            "rules_count": len(doc.get("rules", [])),
        }

    print(f"[AUDITOR] Found {len(losses)} losing trades to analyze")

    loss_summaries = []
    for t in losses:
        mc = t.get("market_context", {})
        h1 = mc.get("h1_data", {})
        d1 = mc.get("daily_data", {})
        loss_summaries.append({
            "symbol": t.get("symbol"),
            "side": t.get("side"),
            "entry_price": t.get("entry_price"),
            "exit_price": t.get("exit_price"),
            "sl": t.get("sl"),
            "tp": t.get("tp"),
            "realized_pnl": t.get("realized_pnl"),
            "h1_atr": h1.get("atr"),
            "d1_atr": d1.get("atr"),
            "h1_rsi": h1.get("rsi"),
            "d1_rsi": d1.get("rsi"),
            "h1_relative_volume": h1.get("relative_volume"),
            "d1_relative_volume": d1.get("relative_volume"),
            "correlated_prices": mc.get("correlated_prices", {}),
        })

    try:
        headers = {
            "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json",
        }

        system_prompt = """You are the Chief Risk Officer and Quantitative Auditor of a hedge fund.
Analyze the losing trades below and identify recurring loss patterns.

Look for:
1. Low-volume breakouts/breakdowns
2. Overextended ATR / volatility traps
3. Adverse cross-asset correlations
4. Trend continuation after exhaustion
5. Counter-trend entries at extremes

Return ONLY raw JSON array of rules, no markdown. Each rule must have:
- "affected_symbol": specific symbol or "ALL"
- "setup": description of the setup pattern
- "confidence_reduction_points": integer 15-30
- "sample_size": number of losing trades matching this pattern
- "evidence": concise evidence summary

Example:
[{"affected_symbol": "EURUSDm", "setup": "Buy on low-volume spike with RSI > 70", "confidence_reduction_points": 20, "sample_size": 3, "evidence": "3 losses on high RSI low-volume entries"}]"""

        user_prompt = f"Losing trades:\n{json.dumps(loss_summaries, indent=2)}\n\nReturn ONLY the JSON array of audit rules."

        payload = {
            "model": config.DEEPSEEK_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 1024,
        }

        resp = requests.post(
            f"{config.DEEPSEEK_API_BASE}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"].strip()

        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        new_rules = json.loads(content)

        if isinstance(new_rules, dict):
            new_rules = new_rules.get("rules", [new_rules])
        if not isinstance(new_rules, list):
            new_rules = [new_rules]

        existing_rules = doc.get("rules", [])
        for rule in new_rules:
            rule["discovered_at"] = datetime.now().isoformat()
            rule["status"] = "ACTIVE"
            existing_rules.append(rule)
            print(
                f"[LEARNING] New rule: {rule.get('setup', '')[:60]} "
                f"| Penalty: {rule.get('confidence_reduction_points', 0)} pts"
            )

        doc["rules"] = existing_rules
        doc["last_audit_at"] = datetime.now().isoformat()
        doc["trades_analyzed"] = len(recent)
        save_rules_document(doc)

        return {
            "status": "completed",
            "trades_analyzed": len(recent),
            "losses_analyzed": len(losses),
            "new_rules_count": len(new_rules),
            "total_rules_count": len(existing_rules),
            "new_rules": new_rules,
        }

    except Exception as e:
        print(f"[AUDITOR] Audit error: {e}")
        return {
            "status": "error",
            "error": str(e),
            "trades_analyzed": len(recent),
        }
