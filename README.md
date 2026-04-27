# BLACKBOX MULTI-LLM TOURNAMENT

A terminal-based, file-driven multi-agent tournament where agents compete to discover a hidden engine's behavior through experimentation, causal reasoning, and market trading.

## Setup

No external dependencies are required. Python 3 standard library only.

```bash
cd blackbox_game
python run.py
```

This initializes the shared files (`shared/`) and prints instructions.

## Running the System

Open multiple terminals:

1. **Start the runner** (the game authority):
   ```bash
   python game/runner.py
   ```

2. **Start agents** (one per terminal):
   ```bash
   python agents/random_agent.py
   python agents/agent_template.py
   ```

You can run as many agents as you like. Each agent operates independently.

## Compiling the Engine (Optional)

To make the engine opaque as a binary:

```bash
pip install pyinstaller
pyinstaller --onefile engine/engine.py -n engine.bin
```

Move the generated binary into `engine/engine.bin`. The runner will use it automatically; otherwise it falls back to running `engine.py` directly.

## Monitoring

Watch results in real time:
```bash
tail -f shared/results.jsonl
```

Watch market listings:
```bash
tail -f shared/market/listings.jsonl
```

Watch transactions:
```bash
tail -f shared/market/transactions.jsonl
```

Inspect scores and energy:
```bash
cat shared/state.json
```

## How Agents Interact

Agents interact **only** via files:

- **Read:**
  - `shared/state.json` — current scores and energy
  - `shared/results.jsonl` — experiment outputs
  - `shared/market/listings.jsonl` — reports for sale
  - `shared/ownership/<player>.json` — owned report IDs

- **Write:**
  - `shared/jobs.jsonl` — append-only job queue

## Job Types

Agents submit JSON lines to `shared/jobs.jsonl`:

### Run Experiment
```json
{"type": "run", "player": "my_agent", "inputs": {"P": 0.5, "T": 0.5, "F": 0.5, "VA": 0.5, "VB": 0.5, "VC": 0.5, "tau": 0.5, "L": 0.5, "C": 0.5}}
```

### Create Report
```json
{"type": "create_report", "player": "my_agent", "report": {"id": 1, "creator": "my_agent", "timestamp": 123.4, "summary": "...", "claims": [...], "evidence": [...], "confidence": 0.8}}
```

### List Report for Sale
```json
{"type": "list_report", "player": "my_agent", "report_id": 1, "price": 10.0}
```

### Buy Report
```json
{"type": "buy_report", "player": "my_agent", "report_id": 1}
```

### Update Price
```json
{"type": "update_price", "player": "my_agent", "report_id": 1, "price": 5.0}
```

## Scoring

- **Experiment Score:** `power_output - 0.2 * heat_loss - 0.1 * vibration`
- **Market Profit:** energy earned minus energy spent
- **Knowledge Score:** `precision * confidence` for each report
- **Total Score:** sum of all three

## Architecture

```
blackbox_game/
├── engine/
│   ├── engine.py          # hidden nonlinear system
│   └── engine.bin         # compiled opaque binary (optional)
├── game/
│   ├── runner.py          # main authority loop
│   ├── engine_wrapper.py  # invokes engine
│   ├── scoring.py         # score computation
│   ├── market.py          # continuous-time market
│   └── claims.py          # ground truth + evaluation
├── shared/
│   ├── jobs.jsonl         # agent submissions
│   ├── results.jsonl      # experiment outputs
│   ├── state.json         # scores & energy
│   ├── market/
│   │   ├── listings.jsonl # active listings
│   │   └── transactions.jsonl
│   ├── reports/
│   └── ownership/
├── agents/
│   ├── agent_template.py  # example agent structure
│   └── random_agent.py    # random baseline
└── run.py                 # initializer + instructions
```

## Rules

- The runner is the **only** process allowed to call the engine.
- Agents do **not** communicate via APIs or sockets.
- Reports are evaluated against hardcoded ground truth in `game/claims.py`.
- The market is continuous: agents can list, buy, and update prices at any time.
- Winning requires understanding causal structure, not just random optimization.

## Extending

You can implement smarter agents (e.g., LLM-driven, Bayesian optimization, causal discovery algorithms) by following the file-based API in `agents/agent_template.py`.
