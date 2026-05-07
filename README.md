# AuditAI - Autonomous Audit & Transaction Monitoring Engine

AuditAI is a real-time transaction monitoring and anomaly detection engine developed for the techfluence Hackathon. It bridges the gap between raw financial data and actionable auditing insights using cutting-edge Machine Learning (ML) pipelines and state-of-the-art Generative AI. 

By analyzing live streams, webhooks, and seamlessly polling incoming banking emails via Gmail OAuth2, AuditAI instantly detects structuring, velocity spikes, and irregular payments, delivering visual evidence trails directly to a boardroom-ready dashboard.

---

## 🚀 Key Features

*   **Real-Time Transaction Scoring:** Automatically scores incoming transactions against a trained `IsolationForest` model to detect high-risk deviations and immediately pushes them to the dashboard via WebSockets.
*   **Gmail Email Ingestion:** A robust OAuth2 scraper seamlessly polls your Gmail for incoming bank transaction alerts from the last 30 days. It uses LLMs to extract monetary details and feed them into the ML scoring loop continuously.
*   **Gemini + RAG Narratives:** Generates executive audit summaries and evidence threads automatically using Google Gemini. The integrated RAG core handles historical context lookup to minimize false-positive rates and structure complex transaction patterns.
*   **Interactive Analytics Dashboard:** A Next.js-powered live interface integrating `Recharts` for interactive temporal visualizations. Features immediate escalations, rule-based fallbacks, AI Chat interfaces (`/api/chat`), and "Demo Fraud" injection triggers built for presentations.

---

## 📁 Project Architecture

The repository uses a split structure for maximum modularity, deploying a high-speed React app and a robust Python REST/Websocket server.

```text
c:\finaltry\techfluence-Hackathon26\
│
├── auditai/                        # Frontend: Next.js React Application
│   ├── src/app                     # Application router, UI pages, layouts
│   ├── public/                     # Static frontend assets
│   ├── package.json                # Node dependencies
│   ├── .env.local                  # Frontend environment variables
│   └── ...    
│
├── techfluence/                    # Backend: Python Application Services
│   ├── auditai_backend/
│   │   ├── engine/                 # Core logic: alert queue, transaction scoring
│   │   ├── scraper/                # email ingestion & Gmail scrapers
│   │   ├── rag/                    # Retrieval-Augmented Generation configuration (Gemini)
│   │   ├── routes/                 # FastAPI router endpoints
│   │   ├── models/                 # Model artifacts (e.g., trained IsolationForest)
│   │   ├── data/                   # Simulation datasets
│   │   └── main.py                 # FastAPI application entrypoint
│   ├── .env                        # Backend environment configuration (GEMINI_API_KEY, etc)
│   └── README.md                   # Backend specific documentation
│
└── start_backend.bat               # Windows batch script to spool up backend
```

---

## ⚙️ Setup & Installation

To run AuditAI locally, you will need to spin up both the Front-End User Interface and Back-End Transaction Services.

### 1. Backend Setup (FastAPI / Machine Learning)
1. Navigate to the Python workspace:
   ```bash
   cd techfluence
   ```
2. Open or create the `.venv` and activate it:
   ```bash
   # Windows
   .\.venv\Scripts\activate
   ```
3. Install required Python packages:
   ```bash
   pip install -r auditai_backend/requirements.txt
   ```
4. Ensure your `.env` is configured with all required keys (such as `GEMINI_API_KEY` for AI functionalities).
5. Start the engine explicitly (or launch `start_backend.bat` from root):
   ```bash
   python -m auditai_backend.main
   ```

### 2. Frontend Setup (Next.js)
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd auditai
   ```
2. Install the necessary Node packages:
   ```bash
   npm install
   # or yarn install // pnpm install
   ```
3. Populate `.env.local` to point to the correct backend ports and define any public keys needed (e.g. Clerk for User Auth, if configured).
4. Spin up the dev server:
   ```bash
   npm run dev
   ```
5. Navigate to **http://localhost:3000** in your browser.

---

## 📡 API Overview

The backend exposes several core endpoints interacting directly with the Frontend.
*   `ws://...` **WebSocket Channel:** Connects live frontend sessions to the `alert_queue`, forwarding flagged anomalies and demo alerts instantly without needing to poll.
*   **POST** `/api/chat`: Acts as the dialogue interface for the Chatbot agent allowing contextual Q&A regarding tracked anomalies.
*   **POST** `/api/ingest/email` : Manual ingestion pipeline allowing users to paste banking email contents directly for breakdown and pattern scoring.
*   **GET/POST** `/api/ingest/gmail` : Automatically interfaces with Gmail to fetch and scan alert contents asynchronously. 
