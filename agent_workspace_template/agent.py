#!/usr/bin/env python3
"""
Autonomous agent for the Blackbox Tournament.
This file lives in an isolated workspace. It talks to the central tournament
via the shared files pointed to by BLACKBOX_SHARED_DIR.

You may edit this file, create helper modules in ./strategy/, and keep notes
in ./scratchpad/ — everything here is private to YOUR agent.
"""

import json
import os
import time
import random

# ---------------------------------------------------------------------------
# CONFIG — change PLAYER_NAME to your agent's unique name
# ---------------------------------------------------------------------------
PLAYER_NAME = "llm_agent"

# The shared tournament folder is set via environment variable so this agent
# can live in its own directory anywhere on disk.
SHARED_DIR = os.environ.get("BLACKBOX_SHARED_DIR")
if not SHARED_DIR:
    raise RuntimeError(
        "BLACKBOX_SHARED_DIR is not set. "
        "Run with: BLACKBOX_SHARED_DIR=/path/to/blackbox_game/shared python agent.py"
    )

JOBS_PATH = os.path.join(SHARED_DIR, "jobs.jsonl")
STATE_PATH = os.path.join(SHARED_DIR, "state.json")
RESULTS_PATH = os.path.join(SHARED_DIR, "results.jsonl")
MARKET_DIR = os.path.join(SHARED_DIR, "market")
LISTINGS_PATH = os.path.join(MARKET_DIR, "listings.jsonl")
OWNERSHIP_DIR = os.path.join(SHARED_DIR, "ownership")

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def read_state():
    if not os.path.exists(STATE_PATH):
        return {}
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def read_results_tail(n=20):
    if not os.path.exists(RESULTS_PATH):
        return []
    lines = []
    with open(RESULTS_PATH, "r") as f:
        for line in f:
            lines.append(json.loads(line))
    return lines[-n:]


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


def read_report(report_id: int):
    report_path = os.path.join(SHARED_DIR, "reports", f"report_{report_id}.json")
    if not os.path.exists(report_path):
        return None
    with open(report_path, "r") as f:
        return json.load(f)


def submit_job(job: dict):
    """Append a job to the central queue."""
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


def update_price(report_id: int, price: float):
    submit_job({"type": "update_price", "player": PLAYER_NAME, "report_id": report_id, "price": price})

# ---------------------------------------------------------------------------
# STRATEGY (customise below)
# ---------------------------------------------------------------------------

def decide_action(state, results, listings, owned):
    """
    Implement your strategy here.
    
    Available data:
      state    -> dict from shared/state.json (scores, energy, etc.)
      results  -> last 20 results from shared/results.jsonl
      listings -> active market listings
      owned    -> list of report IDs you own
    """
    my_state = state.get("players", {}).get(PLAYER_NAME, {})
    energy = my_state.get("energy", 100.0)

    # Example: run a random experiment if we have energy
    if energy > 5.0:
        inputs = {
            "P": round(random.random(), 2),
            "T": round(random.random(), 2),
            "F": round(random.random(), 2),
            "VA": round(random.random(), 2),
            "VB": round(random.random(), 2),
            "VC": round(random.random(), 2),
            "tau": round(random.random(), 2),
            "L": round(random.random(), 2),
            "C": round(random.random(), 2),
        }
        run_experiment(inputs)
        print(f"[{PLAYER_NAME}] Submitted experiment: {inputs}")
        return

    # Example: buy a cheap report if we see one under 3 energy
    for listing in listings:
        if listing.get("active") and listing.get("price", 999) < 3.0:
            rid = listing["report_id"]
            if rid not in owned:
                buy_report(rid)
                print(f"[{PLAYER_NAME}] Attempted to buy report {rid} for {listing['price']}")
                return

    print(f"[{PLAYER_NAME}] Idle (energy={energy:.1f}).")


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def main():
    print(f"[{PLAYER_NAME}] Workspace agent started.")
    print(f"[{PLAYER_NAME}] SHARED_DIR = {SHARED_DIR}")
    while True:
        state = read_state()
        results = read_results_tail()
        listings = read_listings()
        owned = read_owned_reports()

        decide_action(state, results, listings, owned)
        time.sleep(3.0)


if __name__ == "__main__":
    main()
