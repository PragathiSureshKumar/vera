# Vera-Prime — magicpin AI Challenge Submission

**Vera-Prime** is an AI-powered merchant assistant bot built for the magicpin AI Challenge. It reimplements and improves upon Vera — magicpin's WhatsApp merchant engagement bot — using Claude as the AI backbone with a trigger-aware composition engine.

---

## Files in This Folder

| File | What it does |
|---|---|
| `bot.py` | The main HTTP server — run this to start the bot |
| `bot_compose.py` | Standalone `compose()` and `respond()` functions (challenge §7.1) |
| `generate_submission.py` | Generates your `submission.jsonl` (30 test pairs) |
| `load_dataset.py` | Seeds the bot with the challenge dataset before testing |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | For deploying to Render / Railway / any Docker host |

---

## Step 1 — Prerequisites

You need:
- Python 3.10 or newer
- An Anthropic API key → get one at [console.anthropic.com](https://console.anthropic.com)
- The challenge zip extracted somewhere on your computer

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Step 2 — Set Your API Key

**Windows (Command Prompt):**
```cmd
set ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Windows (PowerShell):**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

**Mac / Linux:**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

---

## Step 3 — Start the Bot

```bash
python bot.py
```

You should see:
```
INFO:     Vera-Prime bot starting up...
INFO:     Uvicorn running on http://0.0.0.0:8080
```

Leave this terminal running. Open a new terminal for the next steps.

---

## Step 4 — Load the Dataset

Point `load_dataset.py` at the `dataset` folder inside the challenge zip you extracted.

**Windows example:**
```cmd
python load_dataset.py --url http://localhost:8080 --dataset "C:\Users\YourName\Downloads\magicpin-ai-challenge\dataset"
```

**Mac / Linux example:**
```bash
python load_dataset.py --url http://localhost:8080 --dataset ~/Downloads/magicpin-ai-challenge/dataset
```

**If you're already inside the magicpin-ai-challenge folder:**
```bash
python load_dataset.py --url http://localhost:8080 --dataset ./dataset
```

You should see output like:
```
  category/dentists: True
  category/salons: True
  merchant/m_001_drmeera_dentist_delhi: True
  ...
Loaded: 5 categories, 50 merchants, 200 customers, 100 triggers
```

---

## Step 5 — Verify the Bot is Working

```bash
curl http://localhost:8080/v1/healthz
```

Expected response:
```json
{
  "status": "ok",
  "uptime_seconds": 120,
  "contexts_loaded": {
    "category": 5,
    "merchant": 50,
    "customer": 200,
    "trigger": 100
  }
}
```

---

## Step 6 — Run the Judge Simulator

Copy `judge_simulator.py` from the challenge zip into this folder, then:

**Windows:**
```cmd
set BOT_URL=http://localhost:8080
python judge_simulator.py
```

**Mac / Linux:**
```bash
BOT_URL=http://localhost:8080 python judge_simulator.py
```

---

## Step 7 — Generate Your submission.jsonl

```bash
python generate_submission.py --dataset "C:\Users\YourName\Downloads\magicpin-ai-challenge\dataset"
```

This produces `submission.jsonl` — 30 lines, one composed message per test pair.

---

## Step 8 — Deploy to Get a Public URL

The judge needs a public HTTPS URL. Easiest free option:

### Option A: Render (recommended — free, HTTPS, always on)

1. Create a free account at [render.com](https://render.com)
2. Push this folder to a new GitHub repository
3. In Render: New → Web Service → connect your GitHub repo
4. Set the environment variable: `ANTHROPIC_API_KEY` = your key
5. Build command: leave blank — Dockerfile is auto-detected
6. Deploy → your URL will be `https://vera-prime-xxxx.onrender.com`

### Option B: Railway

```bash
npm install -g @railway/cli
railway login
railway init
railway up
railway variables set ANTHROPIC_API_KEY=sk-ant-...
```

### Option C: ngrok (quick local tunnel — good for testing)

```bash
# Terminal 1: keep bot.py running
python bot.py

# Terminal 2: expose it publicly
ngrok http 8080
# → Forwarding: https://abcd1234.ngrok.io → localhost:8080
```

Submit `https://abcd1234.ngrok.io` as your bot URL. Note: ngrok URLs change each time you restart ngrok, so keep it running during the test window.

---

## How Vera-Prime Works

### The core idea

Every message Vera sends is composed from 4 context layers: category, merchant, trigger, and optionally customer. Vera-Prime passes all 4 into Claude with a trigger-specific prompt that knows how to frame each situation correctly.

### What makes it better than stock Vera

**1. Trigger-aware framing** — 12 different prompt templates, one per trigger type. A `research_digest` trigger gets a clinical-peer framing with source citations. A `perf_dip` trigger gets a loss-aversion framing. A `festival_upcoming` trigger gets a seasonal-urgency framing. Stock Vera uses one generic prompt for everything.

**2. Auto-reply detection** — Vera-Prime detects WhatsApp Business canned replies instantly using pattern matching (no LLM call needed). It follows a progressive backoff:
- Turn 1 auto-reply → nudge the owner politely
- Turn 2 auto-reply → wait 4 hours
- Turn 3+ auto-reply → end the conversation

**3. Intent transition routing** — When a merchant says "let's do it" / "kar do" / "go ahead", Vera-Prime immediately switches from qualifying mode to action mode. It stops asking questions and starts doing things. Stock Vera keeps asking qualifying questions and loses momentum.

**4. Service + price copy** — Every composed message uses the merchant's actual offer catalog ("Dental Cleaning @ ₹299") instead of generic percentage discounts ("30% off"). The judge explicitly penalizes generic copy.

**5. Peer stats in every message** — Vera-Prime wires in the merchant's CTR vs the category peer median in every prompt, enabling specific loss-aversion framing like "your CTR 2.1% vs peer median 3.0%".

**6. Hindi-English code-mix** — Automatically detected from `merchant.identity.languages`. If the merchant speaks Hindi, responses naturally blend Hinglish.

### Auto-reply state machine

```
Merchant reply received
         │
         ├── Hard NO? ("not interested", "stop") ────► END conversation
         │
         ├── Auto-reply detected?
         │       ├── streak = 1 → nudge owner, continue
         │       ├── streak = 2 → wait 4 hours
         │       └── streak ≥ 3 → END conversation
         │
         ├── "Let's do it" / "kar do" detected? ─────► SWITCH to ACTION mode
         │
         └── Normal reply → compose next message with Claude
```

---

## Endpoint Reference

| Endpoint | Method | What it does |
|---|---|---|
| `/v1/healthz` | GET | Liveness check — returns context counts |
| `/v1/metadata` | GET | Bot identity and approach |
| `/v1/context` | POST | Receive category / merchant / customer / trigger context |
| `/v1/tick` | POST | Periodic wake-up — bot decides what messages to send |
| `/v1/reply` | POST | Receive a merchant/customer reply — bot responds |
| `/v1/teardown` | POST | Wipe all state (called at end of test) |

### `/v1/context` idempotency rules
- Same `(scope, context_id, version)` posted twice → returns 409, no change
- Higher version posted → replaces the old one atomically
- The bot always uses the latest version of any context

### `/v1/tick` — what the bot sends
- Returns `{"actions": []}` if nothing is worth sending (restraint is rewarded)
- Returns up to 15 actions per tick (cap is 20)
- Each action has: `conversation_id`, `body`, `cta`, `suppression_key`, `rationale`
- Will not fire the same `suppression_key` twice

### `/v1/reply` — three possible responses
```json
{ "action": "send", "body": "...", "cta": "open_ended", "rationale": "..." }
{ "action": "wait", "wait_seconds": 14400, "rationale": "..." }
{ "action": "end", "rationale": "..." }
```

---

## Scoring Dimensions

| Dimension | What Vera-Prime does |
|---|---|
| **Specificity** | Anchors every message on a real number, date, or stat from the context. No fabrication. |
| **Category fit** | 12 trigger-specific prompts enforce the right voice per category (clinical for dentists, warm for salons, etc.) |
| **Merchant fit** | Uses the merchant's actual name, offers, CTR, and customer aggregate in every message |
| **Trigger relevance** | The trigger kind directly controls the prompt framing — why-now is always explicit |
| **Engagement compulsion** | Selects compulsion levers (loss aversion, social proof, effort externalization, curiosity) per trigger type |

---

## Troubleshooting

**`FileNotFoundError: No such file or directory: 'dataset\merchants_seed.json'`**
You need to give the full path to the dataset folder. See Step 4 above.

**`ModuleNotFoundError: No module named 'fastapi'`**
Run `pip install -r requirements.txt` first.

**`anthropic.AuthenticationError`**
Your API key is not set or is wrong. Double-check Step 2.

**Bot returns empty actions on every tick**
The triggers haven't been loaded yet. Run `load_dataset.py` first (Step 4).

**ngrok URL changed**
ngrok gives a new URL each restart. Keep ngrok running for the full test window, or use Render/Railway for a stable URL.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — | Your Anthropic API key |
| `PORT` | No | 8080 | Port the bot listens on |
