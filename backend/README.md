# AuditAI — Real-Time Financial Anomaly Detection Platform

AuditAI is an AI-powered monitoring platform built for finance and compliance teams to detect suspicious transactions in real time, explain why they were flagged, and generate human-friendly risk briefs.

## Problem Statement

Finance teams process a large volume of transactions every day. Traditional rule systems often:

- miss complex cross-transaction fraud patterns,
- flood teams with noisy alerts,
- and provide weak explanations that are hard for business users to act on.

This makes it difficult to quickly separate real risk from false positives.

## Our Solution

AuditAI combines ML scoring, cross-transaction pattern intelligence, policy context, and AI explanations in a single monitoring workflow.

The platform:

- ingests and scores transactions continuously,
- detects advanced temporal behaviors (e.g., high-value chains, rapid escalation, split bursts),
- produces explainable alerts with evidence trails,
- and offers an assistant interface for normal Q&A plus daily/weekly/monthly brief reports.

## Tech Stack

### Frontend (`auditai/`)

- **Next.js 16** (App Router)
- **React 19**
- **Tailwind CSS 4**
- **Recharts** (spend trend visualization)
- **Lucide React** icons

### Backend (`techfluence/auditai_backend/`)

- **FastAPI** + **Uvicorn**
- **Pydantic** for schema models
- **Pandas / NumPy** for data processing
- **scikit-learn** (Isolation Forest anomaly scoring)
- **Sentence Transformers + ChromaDB** for RAG policy context
- **WebSocket + REST** for real-time and fallback data delivery

### AI Layer

- **OpenRouter** via OpenAI-compatible SDK
- Model: **`openai/gpt-oss-120b:free`**
- Employee-friendly summaries and chatbot responses with reason + risk framing

## Key Features

- Real-time Risk Feed with live alert stream
- Explainable anomaly detection (because X -> risk Y)
- Temporal pattern intelligence:
  - rapid high-value chain
  - micro split burst
  - rapid escalation
- Spend trend analytics from real transaction aggregates
- On-demand AI audit report for a transaction
- Daily/weekly/monthly brief report generation
- Assistant-style chat for natural language audit queries
- Recent report/chat persistence on frontend

## High-Level Architecture

1. Transaction enters pipeline (`process_transaction`)
2. ML score computed (Isolation Forest)
3. Pattern memory checks temporal and behavioral signals
4. RAG fetches relevant policy context
5. Alert engine assembles severity, action, and evidence
6. Alert is pushed to queue and streamed via WebSocket/REST
7. User requests AI narrative/briefs -> OpenRouter generates plain-language output

## Project Structure

```text
techfluence-Hackathon26/
|- auditai/                    # Next.js frontend
|  |- src/app/                 # App routes: /risk-feed, /spend-trend, /daily-summary
|  |- src/components/          # Dashboard, RiskFeed, SpendTrend, DailySummary, etc.
|  |- src/lib/api.js           # Frontend API client
|
|- techfluence/
|  |- .env                     # Backend env vars (OpenRouter key)
|  |- auditai_backend/
|  |  |- main.py               # FastAPI app entry
|  |  |- engine/               # Scoring, pattern memory, alert assembly
|  |  |- routes/               # monitor, chat, analyze, transactions, websocket
|  |  |- rag/                  # Retrieval and embeddings
|  |  |- data/                 # scored_transactions.csv
```

## API Highlights

- `GET /` health and engine status
- `GET /api/monitor/alerts` recent alerts
- `POST /api/analyze/{txn_id}` transaction-level AI report
- `POST /api/chat` assistant Q&A
- `POST /api/chat/period-summary` daily/weekly/monthly brief
- `GET /api/transactions/spend-trend` chart data

## Environment Variables

Create `techfluence/.env`:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

## Local Setup

### 1) Backend setup (FastAPI)

From `techfluence/`:

```bash
# Create and activate virtual env (optional but recommended)
python -m venv .venv
.venv\\Scripts\\activate   # Windows PowerShell

pip install -r auditai_backend/requirements.txt
uvicorn auditai_backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend runs at: `http://localhost:8000`

### 2) Frontend setup (Next.js)

From `auditai/`:

```bash
npm install
npm run dev
```

Frontend runs at: `http://localhost:3000`

## Main Routes (Frontend)

- `http://localhost:3000/risk-feed`
- `http://localhost:3000/spend-trend`
- `http://localhost:3000/daily-summary`

## Why this is effective

AuditAI does not only flag anomalies — it links behavior to evidence, explains possible business impact, and gives users actionable next steps in plain language.

This closes the gap between raw detection and real operational decision-making for finance teams.
