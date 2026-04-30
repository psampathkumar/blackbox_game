#!/usr/bin/env python3
"""
Crude Bayesian / bandit-style agent for the Blackbox Tournament.

Strategy:
- Maintains a simple belief about which inputs matter.
- Runs experiments, tracking mean power_output for each variable band (low/high).
- Creates reports when it believes it has found a monotonic relationship.
- Lists reports on the market.
- Buys cheap reports from others if it has surplus energy.
"""

import json
import os
import time
import random

# --- Shared directory resolution (same pattern as other agents) ---
SHARED_DIR = os.environ.get("BLACKBOX_SHARED_DIR")
if not SHARED_DIR:
    SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "shared")

JOBS_PATH = os.path.join(SHARED_DIR, "jobs.jsonl")
STATE_PATH = os.path.join(SHARED_DIR, "state.json")
RESULTS_PATH = os.path.join(SHARED_DIR, "results.jsonl")
MARKET_DIR = os.path.join(SHARED_DIR, "market")
LISTINGS_PATH = os.path.join(MARKET_DIR, "listings.jsonl")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")

PLAYER_NAME = os.environ.get("BLACKBOX_PLAYER_NAME", "bayesian_agent")

INPUT_VARS = ["P", "T", "F", "VA", "VB", "VC", "tau", "L", "C"]

# ---------------------------------------------------------------------------
# FILE I/O HELPERS
# ---------------------------------------------------------------------------

def read_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def read_results_all():
    if not os.path.exists(RESULTS_PATH):
        return []
    lines = []
    with open(RESULTS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))
    return lines


def read_listings():
    if not os.path.exists(LISTINGS_PATH):
        return []
    items = []
    with open(LISTINGS_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def read_owned_reports():
    own_path = os.path.join(OWNERSHIP_DIR, f"{PLAYER_NAME}.json")
    if not os.path.exists(own_path):
        return []
    with open(own_path, "r") as f:
        return json.load(f)


def submit_job(job: dict):
    with open(JOBS_PATH, "a") as f:
        f.write(json.dumps(job) + "\n")


def run_experiment(inputs: dict):
    submit_job({"type": "run", "player": PLAYER_NAME, "inputs": inputs})


def create_report(report_id: int, summary: str, claims: list, evidence: list, confidence: float):
    submit_job({
        "type": "create_report",
        "player": PLAYER_NAME,
        "report": {
            "id": report_id,
            "creator": PLAYER_NAME,
            "timestamp": time.time(),
            "summary": summary,
            "claims": claims,
            "evidence": evidence,
            "confidence": confidence,
        },
    })


def list_report(report_id: int, price: float):
    submit_job({"type": "list_report", "player": PLAYER_NAME, "report_id": report_id, "price": price})


def buy_report(report_id: int):
    submit_job({"type": "buy_report", "player": PLAYER_NAME, "report_id": report_id})


# ---------------------------------------------------------------------------
# BELIEF / BANDIT LOGIC
# ---------------------------------------------------------------------------

def bandit_inputs(belief: dict) -> dict:
    """
    Pick inputs by slightly biasing toward high values for variables
    that have historically produced higher power_output.
    """
    inputs = {}
    for var in INPUT_VARS:
        b = belief.get(var, {"high_mean": 0.5, "low_mean": 0.5})
        # If high values did better, bias high; else unbiased
        diff = b.get("high_mean", 0.5) - b.get("low_mean", 0.5)
        if diff > 0.05:
            inputs[var] = round(random.uniform(0.6, 1.0), 2)
        elif diff < -0.05:
            inputs[var] = round(random.uniform(0.0, 0.4), 2)
        else:
            inputs[var] = round(random.random(), 2)
    return inputs


def update_belief(belief: dict, inputs: dict, outputs: dict):
    """Online update of low/high band means per variable."""
    power = outputs.get("power_output", 0.0)
    for var in INPUT_VARS:
        val = inputs[var]
        b = belief.setdefault(var, {"high_sum": 0.0, "high_n": 0, "low_sum": 0.0, "low_n": 0})
        if val >= 0.5:
            b["high_sum"] += power
            b["high_n"] += 1
            b["high_mean"] = b["high_sum"] / b["high_n"]
        else:
            b["low_sum"] += power
            b["low_n"] += 1
            b["low_mean"] = b["low_sum"] / b["low_n"]


# ---------------------------------------------------------------------------
# STRATEGY
# ---------------------------------------------------------------------------

def decide_action(state, results, listings, owned, belief: dict):
    my_state = state.get("players", {}).get(PLAYER_NAME, {})
    energy = my_state.get("energy", 100.0)

    # 1. BUY cheap reports from market (information arbitrage)
    for listing in listings:
        if not listing.get("active"):
            continue
        rid = listing["report_id"]
        price = listing.get("price", 999)
        if rid not in owned and price <= 5.0 and energy >= price + 5.0:
            buy_report(rid)
            print(f"[{PLAYER_NAME}] Attempted to buy report {rid} for {price} energy.")
            return

    # 2. RUN experiment if we have energy
    if energy >= 2.0:
        inputs = bandit_inputs(belief)
        run_experiment(inputs)
        print(f"[{PLAYER_NAME}] Submitted experiment.")
        return

    # 3. CREATE + LIST a report if we have a confident belief
    if energy >= 5.0:
        best_var = None
        best_diff = 0.0
        best_direction = "positive"
        evidence = []
        for var in INPUT_VARS:
            b = belief.get(var, {})
            hm = b.get("high_mean", 0.5)
            lm = b.get("low_mean", 0.5)
            diff = abs(hm - lm)
            if diff > best_diff and (b.get("high_n", 0) + b.get("low_n", 0)) >= 4:
                best_var = var
                best_diff = diff
                best_direction = "positive" if hm > lm else "negative"
                evidence = [
                    {"inputs": {var: 0.8}, "outputs": {"power_output": round(hm, 3)}},
                    {"inputs": {var: 0.2}, "outputs": {"power_output": round(lm, 3)}},
                ]

        if best_var and best_diff >= 0.05:
            report_id = hash(f"{PLAYER_NAME}_{best_var}_{int(time.time())}") % 1000000
            summary = f"Belief: {best_var} has a {best_direction} effect on power_output (diff={best_diff:.3f})."
            claims = [
                {"type": "monotonic", "var": best_var, "target": "power_output", "direction": best_direction},
            ]
            create_report(report_id, summary, claims, evidence, confidence=min(0.95, best_diff * 3))
            # Immediately list it
            list_report(report_id, price=3.0)
            print(f"[{PLAYER_NAME}] Created and listed report {report_id} about {best_var}.")
            return

    print(f"[{PLAYER_NAME}] Idle (energy={energy:.1f}).")


def main():
    print(f"[{PLAYER_NAME}] Bayesian agent started.")
    belief = {}
    while True:
        state = read_state()
        results = read_results_all()
        listings = read_listings()
        owned = read_owned_reports()

        # Update belief from all historic results by this player
        for r in results:
            if r.get("type") == "run" and r.get("ok") and r.get("player") == PLAYER_NAME:
                update_belief(belief, r["inputs"], r["outputs"])

        decide_action(state, results, listings, owned, belief)
        time.sleep(3.0)


if __name__ == "__main__":
    main()
