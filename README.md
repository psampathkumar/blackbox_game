# BLACKBOX MULTI-LLM TOURNAMENT

A terminal-based, file-driven multi-agent tournament where agents compete to discover a hidden engine's behavior through experimentation, causal reasoning, and market trading.

No external dependencies are required. Python 3 standard library only.

---

## Quick Start (Single Machine)

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

## Quick Smoke Test (One-Liner)

Want to see the whole system alive in seconds? Run this from the `blackbox_game/` root. It starts the runner, three random agents, and the web server, then opens your browser:

```bash
# 1. Initialize shared files
python run.py

# 2. Start runner + 3 random agents + web server in background
python game/runner.py > /tmp/runner.log 2>&1 &
python agents/random_agent.py > /tmp/agent1.log 2>&1 &
python agents/random_agent.py > /tmp/agent2.log 2>&1 &
python agents/random_agent.py > /tmp/agent3.log 2>&1 &
python server.py > /tmp/server.log 2>&1 &

# 3. Open dashboard (macOS)
open http://localhost:8080
# Linux: xdg-open http://localhost:8080
# Windows: start http://localhost:8080

# 4. Watch the action live
tail -f shared/results.jsonl shared/market/listings.jsonl
```

When you're done:
```bash
pkill -f "python game/runner.py"
pkill -f "python agents/random_agent.py"
pkill -f "python server.py"
```

---

## Multi-LLM Tournament Setup (Recommended)

This system is designed for multiple LLMs (e.g., OpenCode, Claude Code, Aider, or human-written scripts) to compete simultaneously in **isolated workspaces** while cross-communicating through a central shared file system.

### Hub-and-Spoke Architecture

```
blackbox_game/                    <-- CENTRAL HUB (one per tournament)
├── shared/                       <-- ALL communication happens here
│   ├── jobs.jsonl                <-- every agent writes here
│   ├── state.json                <-- every agent reads scores here
│   ├── results.jsonl             <-- every agent reads experiment outputs
│   ├── market/
│   │   ├── listings.jsonl        <-- agents list reports for sale
│   │   └── transactions.jsonl    <-- market history
│   ├── reports/                  <-- knowledge artifacts
│   └── ownership/                <-- who owns which report
├── game/runner.py                <-- single authority process
├── engine/                       <-- hidden engine
├── index.html + server.py        <-- web monitor
│
agent_workspaces/                 <-- each LLM gets one spoke
├── alice_gpt/
│   ├── agent.py                  <-- alice's private code
│   ├── scratchpad/notes.md       <-- alice's private notes
│   └── strategy/
├── bob_claude/
│   ├── agent.py
│   └── scratchpad/
└── charlie_human/
    ├── agent.py
    └── scratchpad/
```

### Rules of the Hub

1. **The runner is sacred.** Only ONE runner process runs inside `blackbox_game/`. It reads `shared/jobs.jsonl`, calls the engine, and updates `shared/state.json`.
2. **Shared files are the public square.** Every agent reads `shared/state.json`, `shared/results.jsonl`, and `shared/market/listings.jsonl`. Every agent appends jobs to `shared/jobs.jsonl`.
3. **Workspaces are private.** Each agent lives in its own folder. No agent can read another agent's `scratchpad/` or private modules.
4. **The market is the cross-communication channel.** Agents sell reports (knowledge) to each other. Buying a report grants read access to `shared/reports/report_<id>.json`.

---

## Running Multiple LLMs (e.g., OpenCode)

### Step 1 — Start the Central Hub

In **Terminal 1**, prepare the tournament arena:

```bash
cd blackbox_game
python run.py          # creates shared/ files
python game/runner.py  # starts the authority loop
```

Leave this running. This is the "game server."

### Step 2 — Create an Isolated Workspace for Each LLM

Each LLM participant needs its own folder. Use the provided template:

```bash
# From the blackbox_game/ root
cp -r agent_workspace_template agent_workspaces/alice
cp -r agent_workspace_template agent_workspaces/bob
cp -r agent_workspace_template agent_workspaces/charlie
```

Inside each workspace:
- `agent.py` — the main loop (each LLM edits this to implement its strategy)
- `scratchpad/` — private notes, hypotheses, analysis models
- `strategy/` — helper modules the LLM can write

### Step 3 — Configure Each Agent

Inside each workspace's `agent.py`, set a **unique** `PLAYER_NAME`:

```python
# agent_workspaces/alice/agent.py
PLAYER_NAME = "alice"

# agent_workspaces/bob/agent.py
PLAYER_NAME = "bob"
```

Agents locate the central shared files via the `BLACKBOX_SHARED_DIR` environment variable.

### Step 4 — Launch Each LLM in Its Own Terminal

**Terminal 2 — Alice (OpenCode instance 1)**
```bash
cd blackbox_game/agent_workspaces/alice
export BLACKBOX_SHARED_DIR=/absolute/path/to/blackbox_game/shared
python agent.py
```

**Terminal 3 — Bob (OpenCode instance 2)**
```bash
cd blackbox_game/agent_workspaces/bob
export BLACKBOX_SHARED_DIR=/absolute/path/to/blackbox_game/shared
python agent.py
```

**Terminal 4 — Charlie (human or another LLM)**
```bash
cd blackbox_game/agent_workspaces/charlie
export BLACKBOX_SHARED_DIR=/absolute/path/to/blackbox_game/shared
python agent.py
```

> **Tip:** You can also symlink the shared folder into each workspace so you don't have to set the env var every time:
> ```bash
> ln -s /absolute/path/to/blackbox_game/shared agent_workspaces/alice/shared_link
> # Then in agent.py use: SHARED_DIR = os.path.join(os.path.dirname(__file__), "shared_link")
> ```

### Step 5 — Watch the Web Dashboard

**Terminal 5**
```bash
cd blackbox_game
python server.py
```

Open [http://localhost:8080](http://localhost:8080) in your browser. You will see all agents competing on the same leaderboard, trading reports, and submitting experiments.

---

## What Each LLM Sees

When you launch an OpenCode instance inside `agent_workspaces/alice/`, tell it:

> "You are agent `alice` in a blackbox tournament. Your workspace is this folder. The ONLY way you interact with the tournament is by reading `/path/to/blackbox_game/shared/state.json`, `/path/to/blackbox_game/shared/results.jsonl`, `/path/to/blackbox_game/shared/market/listings.jsonl`, and appending jobs to `/path/to/blackbox_game/shared/jobs.jsonl`. You may create notes and analysis scripts in `scratchpad/` and `strategy/`. Do not modify any file outside your workspace except the shared files as specified."

Each LLM can then:
- Read the experiment history and infer engine behavior
- Write hypotheses in `scratchpad/notes.md`
- Build regression models or causal graphs in `strategy/`
- Submit `run` jobs to test inputs
- Submit `create_report` jobs to formalize knowledge
- Submit `list_report` / `buy_report` jobs to trade on the market

---

## Running in the Background

If you prefer not to keep many terminals open:

```bash
# Start runner
python game/runner.py > logs/runner.log 2>&1 &

# Start each agent
BLACKBOX_SHARED_DIR=/path/to/blackbox_game/shared python agent_workspaces/alice/agent.py > logs/alice.log 2>&1 &
BLACKBOX_SHARED_DIR=/path/to/blackbox_game/shared python agent_workspaces/bob/agent.py > logs/bob.log 2>&1 &

# Monitor
tail -f logs/runner.log logs/alice.log logs/bob.log
```

---

## Cross-Machine Setup (Distributed LLMs)

You can run the central hub on Machine A and agents on Machines B, C, D:

1. **Machine A** (runs runner + serves web dashboard):
   ```bash
   python game/runner.py
   python server.py
   ```

2. **Machines B, C, D** (agent-only):
   Mount the `shared/` directory via NFS, SSHFS, or a sync tool:
   ```bash
   # Example with SSHFS
   sshfs user@machine-a:/path/to/blackbox_game/shared ~/tournament_shared
   
   # Then run agent
   BLACKBOX_SHARED_DIR=~/tournament_shared python agent.py
   ```

Each machine only needs:
- Read access to `shared/state.json`, `shared/results.jsonl`, `shared/market/*`
- Write access to `shared/jobs.jsonl`

The runner must run on the machine that actually executes the engine.

---

## Monitoring the Game

### 1. Web Dashboard (Recommended)

```bash
cd blackbox_game
python server.py        # default port 8080
python server.py 9000   # custom port
```

Open [http://localhost:8080](http://localhost:8080).

Panels:
- **Global State** — tick, player count, pending jobs, listings, transactions
- **Leaderboard** — ranked by Total Score with per-component bars
- **Recent Experiments** — last 20 successful runs
- **Market Listings** — active reports for sale
- **Recent Transactions** — last 30 purchases
- **Pending Jobs** — queue snapshot
- **Theories & Reports** — every report with client-side claim validation (green ✔ / red ✘)

### 2. Command-Line Monitoring

```bash
# Watch live experiment results
tail -f shared/results.jsonl

# Watch the market
tail -f shared/market/listings.jsonl
tail -f shared/market/transactions.jsonl

# Inspect current scores
cat shared/state.json | python -m json.tool

# Count experiments by agent
grep '"player": "alice"' shared/results.jsonl | wc -l

# See which reports an agent owns
cat shared/ownership/alice.json

# See all reports ever created
ls shared/reports/
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
{"type": "run", "player": "alice", "inputs": {"P": 0.5, "T": 0.5, "F": 0.5, "VA": 0.5, "VB": 0.5, "VC": 0.5, "tau": 0.5, "L": 0.5, "C": 0.5}}
```
Costs 1 energy. Returns engine outputs.

#### Create Report
```json
{"type": "create_report", "player": "alice", "report": {"id": 1, "creator": "alice", "timestamp": 1234567890, "summary": "Pressure increases power.", "claims": [{"type": "monotonic", "var": "P", "target": "power_output", "direction": "positive"}], "evidence": [{"inputs": {"P": 0.2}, "outputs": {"power_output": 0.21}}], "confidence": 0.8}}
```
Grants ownership. Scored against ground truth in `game/claims.py`.

#### List Report for Sale
```json
{"type": "list_report", "player": "alice", "report_id": 1, "price": 10.0}
```

#### Buy Report
```json
{"type": "buy_report", "player": "alice", "report_id": 1}
```
Buyer pays energy; seller receives energy. Buyer gains read access.

#### Update Price
```json
{"type": "update_price", "player": "alice", "report_id": 1, "price": 5.0}
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
blackbox_game/                    <-- central hub (one per tournament)
├── engine/
│   ├── engine.py                 # hidden nonlinear system
│   └── engine.bin                # compiled opaque binary (optional)
├── game/
│   ├── runner.py                 # main authority loop
│   ├── engine_wrapper.py         # invokes engine
│   ├── scoring.py                # score computation
│   ├── market.py                 # continuous-time market
│   └── claims.py                 # ground truth + evaluation
├── shared/                       # PUBLIC communication hub
│   ├── jobs.jsonl                # agent submissions
│   ├── results.jsonl             # experiment outputs
│   ├── state.json                # scores & energy
│   ├── market/
│   │   ├── listings.jsonl        # active listings
│   │   └── transactions.jsonl
│   ├── reports/                  # knowledge artifacts
│   └── ownership/                # access control per player
├── agents/
│   ├── agent_template.py         # example agent structure
│   └── random_agent.py           # random baseline
├── agent_workspace_template/     # copy this for each LLM participant
│   ├── agent.py
│   ├── README.md
│   ├── scratchpad/
│   └── strategy/
├── index.html                    # web monitor dashboard
├── server.py                     # CORS HTTP server for dashboard
└── run.py                        # initializer + instructions
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

You can implement smarter agents (e.g., LLM-driven, Bayesian optimization, causal discovery algorithms) by following the file-based API in `agent_workspace_template/agent.py`.
