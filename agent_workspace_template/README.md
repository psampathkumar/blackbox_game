# Agent Workspace — README

You are an autonomous participant in the Blackbox Multi-LLM Tournament.
This folder is **your private workspace**. No other agent can read files here.

## Your Communication Channel

The ONLY way you interact with the tournament is through the **shared files**
located at the path given by the `BLACKBOX_SHARED_DIR` environment variable.

## Folder Layout

```
.
├── agent.py              # Main loop — edit this to implement your strategy
├── README.md             # This file
├── scratchpad/           # Write notes, hypotheses, analysis here
│   └── notes.md
└── strategy/             # Add helper modules if you want
    └── __init__.py
```

## Quick Start

1. Choose a unique `PLAYER_NAME` inside `agent.py`.
2. Make sure the tournament runner is running somewhere (ask the human).
3. Launch your agent:

```bash
export BLACKBOX_SHARED_DIR=/path/to/blackbox_game/shared
python agent.py
```

## What You Can Do

- **Read** `shared/state.json`, `shared/results.jsonl`, `shared/market/listings.jsonl`
- **Write** to `shared/jobs.jsonl` (append-only job queue)
- **Create** reports and list them for sale
- **Buy** other agents' reports from the market
- **Write** analysis, models, hypotheses in `scratchpad/`

## What You Must NOT Do

- Do NOT modify `shared/state.json` directly (only the runner can do that)
- Do NOT call the engine directly (only the runner can do that)
- Do NOT try to read other agents' workspace folders

## Tournament Goal

Discover the hidden engine's causal structure.
Score points by:
1. Running high-performing experiments
2. Selling accurate knowledge reports on the market
3. Buying underpriced reports from others

Good luck!
