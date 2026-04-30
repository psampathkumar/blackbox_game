# BLACKBOX MULTI-LLM TOURNAMENT

A terminal-based, file-driven multi-agent tournament where agents compete to discover a hidden engine's behavior through experimentation, causal reasoning, and market trading.

No external dependencies are required. Python 3 standard library only.

---

## Quick Start

```bash
cd blackbox_game
python run.py          # initializes shared files
python game/runner.py  # start the core game loop
```

Then open **more terminals** to run as many agents as you want:

```bash
# Terminal 2
python agents/random_agent.py

# Terminal 3
python agents/agent_template.py

# Terminal 4 — start the web dashboard monitor
python server.py
```

Open your browser to [http://localhost:8080](http://localhost:8080) and watch the live dashboard.

---

## Running Multiple Agents

The tournament is designed for concurrent agents, each running in its own terminal (or background process). Agents interact **only through files**—there are no sockets, APIs, or direct communication channels.

### Single Machine, Multiple Terminals

1. **Terminal 1 — Runner (required)**
   ```bash
   cd blackbox_game
   python game/runner.py
   ```
   The runner is the game authority. It must be running for jobs to be processed.

2. **Terminal 2 — Random Agent**
   ```bash
   cd blackbox_game
   python agents/random_agent.py
   ```

3. **Terminal 3 — Template Agent**
   ```bash
   cd blackbox_game
   python agents/agent_template.py
   ```

4. **Terminal 4+ — Custom Agents**
   Copy `agents/agent_template.py` and implement your own strategy:
   ```bash
   cp agents/agent_template.py agents/my_agent.py
   # edit my_agent.py, change PLAYER_NAME, implement logic
   python agents/my_agent.py
   ```

### Running Agents in the Background

If you prefer not to keep many terminals open, use `nohup` or `&`:

```bash
# Start runner in background
python game/runner.py > logs/runner.log 2>&1 &

# Start several agents in background
python agents/random_agent.py > logs/agent1.log 2>&1 &
python agents/my_agent.py > logs/agent2.log 2>&1 &

# Monitor live
tail -f logs/runner.log logs/agent1.log
```

### Different Machines (Shared Filesystem)

If agents run on different machines, mount the `blackbox_game/shared/` directory on a network filesystem (NFS, SSHFS, Dropbox-style sync, etc.). Each machine only needs:

- Read access to `shared/state.json`, `shared/results.jsonl`, `shared/market/*`
- Write access to `shared/jobs.jsonl`

The runner must run on the machine that actually executes the engine.

---

## Monitoring the Game

### 1. Web Dashboard (Recommended)

The included `index.html` + `server.py` provides a real-time browser monitor.

**Start the server:**
```bash
cd blackbox_game
python server.py        # default port 8080
python server.py 9000   # custom port
```

**Open your browser:**
```
http://localhost:8080
```

The dashboard auto-refreshes every 2 seconds and shows:
- **Global State** — tick count, active players, pending jobs, listings, transactions
- **Leaderboard** — all agents ranked by total score with component breakdowns
- **Recent Experiments** — last 20 successful runs with power, vibration, efficiency, heat loss
- **Market Listings** — active reports for sale with seller, price, and age
- **Recent Transactions** — last 30 purchases
- **Pending Jobs** — jobs waiting in the queue
- **Theories & Reports** — every report with client-side claim validation (green ✔ / red ✘)

### 2. Command-Line Monitoring

**Watch live experiment results:**
```bash
tail -f shared/results.jsonl
```

**Watch the market:**
```bash
tail -f shared/market/listings.jsonl
tail -f shared/market/transactions.jsonl
```

**Inspect current scores:**
```bash
cat shared/state.json | python -m json.tool
```

**Count how many experiments an agent has run:**
```bash
grep '"player": "random_agent"' shared/results.jsonl | wc -l
```

**See which reports are owned by an agent:**
```bash
cat shared/ownership/random_agent.json
```

---

## Compiling the Engine (Optional)

To make the engine truly opaque as a binary:

```bash
pip install pyinstaller
pyinstaller --onefile engine/engine.py -n engine.bin
```

Move the generated binary into `engine/engine.bin`. The runner will use it automatically; otherwise it falls back to running `engine.py` directly.

---

## How Agents Interact

Agents interact **only** via files. There is no network, no shared memory, no message passing.

### Read Access
- `shared/state.json` — current scores and energy
- `shared/results.jsonl` — experiment outputs
- `shared/market/listings.jsonl` — reports for sale
- `shared/ownership/<player>.json` — owned report IDs
- `shared/reports/report_<id>.json` — full report content (if owned)

### Write Access
- `shared/jobs.jsonl` — append-only job queue

### Job Types

Agents append JSON lines to `shared/jobs.jsonl`:

#### Run Experiment
```json
{"type": "run", "player": "my_agent", "inputs": {"P": 0.5, "T": 0.5, "F": 0.5, "VA": 0.5, "VB": 0.5, "VC": 0.5, "tau": 0.5, "L": 0.5, "C": 0.5}}
```
Costs 1 energy. Returns engine outputs.

#### Create Report
```json
{"type": "create_report", "player": "my_agent", "report": {"id": 1, "creator": "my_agent", "timestamp": 1234567890, "summary": "Pressure increases power.", "claims": [{"type": "monotonic", "var": "P", "target": "power_output", "direction": "positive"}], "evidence": [{"inputs": {"P": 0.2}, "outputs": {"power_output": 0.21}}], "confidence": 0.8}}
```
Grants ownership. Scored against ground truth in `game/claims.py`.

#### List Report for Sale
```json
{"type": "list_report", "player": "my_agent", "report_id": 1, "price": 10.0}
```

#### Buy Report
```json
{"type": "buy_report", "player": "my_agent", "report_id": 1}
```
Buyer pays energy; seller receives energy. Buyer gains read access.

#### Update Price
```json
{"type": "update_price", "player": "my_agent", "report_id": 1, "price": 5.0}
```

---

## Scoring System

- **Experiment Score:** `power_output - 0.2 * heat_loss - 0.1 * vibration`
- **Market Profit:** energy earned minus energy spent
- **Knowledge Score:** `precision * confidence` for each report (precision = correct_claims / total_claims)
- **Total Score:** sum of all three

---

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
│   ├── reports/           # knowledge artifacts
│   └── ownership/         # access control per player
├── agents/
│   ├── agent_template.py  # example agent structure
│   └── random_agent.py    # random baseline
├── index.html             # web monitor dashboard
├── server.py              # CORS HTTP server for dashboard
└── run.py                 # initializer + instructions
```

---

## Rules

- The runner is the **only** process allowed to call the engine.
- Agents do **not** communicate via APIs or sockets.
- Reports are evaluated against hardcoded ground truth in `game/claims.py`.
- The market is continuous: agents can list, buy, and update prices at any time.
- Winning requires understanding causal structure, not just random optimization.

---

## Extending

You can implement smarter agents (e.g., LLM-driven, Bayesian optimization, causal discovery algorithms) by following the file-based API in `agents/agent_template.py`.
