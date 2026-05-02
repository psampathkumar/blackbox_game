#!/usr/bin/env python3
"""
run.py: initializes the shared file system and prints startup instructions.
"""

import json
import os

def init_shared_files():
    base = os.path.dirname(__file__)
    shared = os.path.join(base, "shared")
    market = os.path.join(shared, "market")
    reports = os.path.join(shared, "reports")
    ownership = os.path.join(shared, "ownership")

    os.makedirs(shared, exist_ok=True)
    os.makedirs(market, exist_ok=True)
    os.makedirs(reports, exist_ok=True)
    os.makedirs(ownership, exist_ok=True)

    state_path = os.path.join(shared, "state.json")
    if not os.path.exists(state_path):
        with open(state_path, "w") as f:
            json.dump({"tick": 0, "players": {}}, f, indent=2)

    jobs_path = os.path.join(shared, "jobs.jsonl")
    if not os.path.exists(jobs_path):
        with open(jobs_path, "w") as f:
            pass

    results_path = os.path.join(shared, "results.jsonl")
    if not os.path.exists(results_path):
        with open(results_path, "w") as f:
            pass

    listings_path = os.path.join(market, "listings.jsonl")
    if not os.path.exists(listings_path):
        with open(listings_path, "w") as f:
            pass

    transactions_path = os.path.join(market, "transactions.jsonl")
    if not os.path.exists(transactions_path):
        with open(transactions_path, "w") as f:
            pass

    score_history_path = os.path.join(shared, "score_history.jsonl")
    if not os.path.exists(score_history_path):
        with open(score_history_path, "w") as f:
            pass

    print("[run.py] Shared files initialized.")


def print_instructions():
    print("""
========================================
BLACKBOX MULTI-AGENT TOURNAMENT SYSTEM
========================================

SETUP COMPLETE.

To start the game:

1. In one terminal, run the runner:
   python game/runner.py

2. In other terminals, run agents:
   python agents/random_agent.py
   python agents/agent_template.py

You can run multiple agents simultaneously.

MONITORING:

- Watch live results:
   tail -f shared/results.jsonl

- Watch market listings:
   tail -f shared/market/listings.jsonl

- Watch market transactions:
   tail -f shared/market/transactions.jsonl

- Inspect game state:
   cat shared/state.json

HOW IT WORKS:

- Agents read shared/state.json and shared/results.jsonl
- Agents write jobs to shared/jobs.jsonl
- The runner processes jobs, calls the engine, updates scores
- Agents can create, list, and buy knowledge reports
- Scoring rewards: experiment performance, market profit, causal understanding

Enjoy the tournament!
""")


def main():
    init_shared_files()
    print_instructions()


if __name__ == "__main__":
    main()
