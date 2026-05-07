# rag/retriever.py
"""
RAG context retrieval for AuditAI.
All heavy objects (DataFrame, embedder, ChromaDB) are lazy-loaded on first use
so that `import rag.retriever` never blocks the FastAPI startup.

Run `python rag/ingest.py` once before starting the API to populate the
persistent ChromaDB with real policy documents.
"""
import warnings
import pandas as pd
import chromadb
from sentence_transformers import SentenceTransformer
from pathlib import Path
from functools import lru_cache

# ── Resolve paths relative to this file ──────────────────────────────────────
HERE       = Path(__file__).parent          # …/auditai-backend/rag/
PROJECT    = HERE.parent                    # …/auditai-backend/
DATA_DIR   = PROJECT / "data"
CHROMA_DIR = HERE / "chroma_db"            # persistent on-disk store
SCORED_CSV = DATA_DIR / "scored_transactions.csv"

_SAMPLE_POLICIES = [
    "Transactions above $10,000 require dual approval.",
    "CASH_OUT transactions to customer accounts are high risk.",
    "Payments outside business hours (9–17) require manager sign-off.",
    "Vendors with fewer than 3 prior transactions should be flagged for review.",
    "Balance drain above 90% in a single transaction triggers an automatic hold.",
]

# ── Lazy singletons ───────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_df() -> pd.DataFrame:
    if not SCORED_CSV.exists():
        warnings.warn(
            f"Scored transactions not found at {SCORED_CSV}. "
            "Run models/detector.py first.",
            RuntimeWarning,
        )
        return pd.DataFrame(columns=[
            "id", "amount", "vendor", "department", "employee",
            "timestamp", "category", "hour_of_day", "is_weekend",
            "amount_vs_dept_avg", "vendor_txn_count", "balance_drain_ratio",
            "dest_is_customer", "oldbalanceOrg", "newbalanceOrig",
            "anomaly_score", "risk", "isFraud",
        ])
    print("[retriever] Loading scored_transactions.csv …")
    return pd.read_csv(SCORED_CSV)


@lru_cache(maxsize=1)
def _get_embedder() -> SentenceTransformer:
    print("[retriever] Loading sentence-transformer model …")
    return SentenceTransformer("all-MiniLM-L6-v2")


@lru_cache(maxsize=1)
def _get_collection():
    embedder = _get_embedder()

    # ── Try persistent ChromaDB first (populated by ingest.py) ───────────
    if CHROMA_DIR.exists():
        try:
            client     = chromadb.PersistentClient(path=str(CHROMA_DIR))
            collection = client.get_collection("audit_policies")
            count      = collection.count()
            if count > 0:
                print(f"[retriever] Loaded persistent ChromaDB ({count} chunks).")
                return collection
        except Exception as exc:
            print(f"[retriever] Persistent ChromaDB failed ({exc}), falling back.")

    # ── Fallback: in-memory collection with seed policies ─────────────
    warnings.warn(
        "Persistent ChromaDB not found. Using seed policies. "
        "Run `python rag/ingest.py` for full RAG quality.",
        RuntimeWarning,
    )
    _SEED_POLICIES = [
        "Transactions above $10,000 require a Currency Transaction Report (CTR) under the Bank Secrecy Act.",
        "CASH_OUT transactions to customer accounts are a primary fraud signal in PaySim and must be reviewed.",
        "Balance drain above 90% of the original account balance in a single transaction is a critical fraud indicator.",
        "Payments outside business hours (before 9am or after 5pm) require prior manager authorization.",
        "New vendors with fewer than 3 prior transactions require Director-level approval before payment.",
        "Structuring transactions just below $10,000 to avoid CTR reporting is a federal crime under 31 U.S.C. § 5324.",
        "TRANSFER transactions above $1,000,000 to a customer account must be escalated to the Chief Compliance Officer.",
        "Any transaction where oldbalanceOrg equals newbalanceOrig minus amount indicates a complete account drain, which is HIGH risk.",
        "Transactions in the 99th percentile of amount for the department require mandatory human review.",
        "Weekend transactions above $10,000 must be pre-approved by the CFO.",
    ]
    client     = chromadb.Client()
    collection = client.get_or_create_collection("audit_policies")
    if collection.count() == 0:
        collection.add(
            documents=_SEED_POLICIES,
            embeddings=embedder.encode(_SEED_POLICIES).tolist(),
            ids=[f"seed-policy-{i}" for i in range(len(_SEED_POLICIES))],
        )
    return collection


# ── Public API ────────────────────────────────────────────────────────────────
def retrieve_context(txn: dict) -> dict:
    """Return enriched context for a single transaction dict."""
    df         = _get_df()
    embedder   = _get_embedder()
    collection = _get_collection()

    # Semantic policy search
    query = (
        f"{txn['amount']} payment to {txn['vendor']} "
        f"by {txn['department']} at hour {txn.get('hour_of_day', '')}"
    )
    results = collection.query(
        query_embeddings=embedder.encode([query]).tolist(),
        n_results=3,
    )
    policy_matches = results["documents"][0]

    # Vendor history
    vendor_history       = df[df["vendor"] == txn["vendor"]]
    vendor_count         = len(vendor_history)
    vendor_fraud_history = (
        int(vendor_history["isFraud"].sum())
        if "isFraud" in vendor_history.columns
        else 0
    )

    # Dept baseline
    dept_txns    = df[df["department"] == txn["department"]]
    dept_avg     = round(float(dept_txns["amount"].mean()), 2) if len(dept_txns) else 0.0
    amount_ratio = round(txn["amount"] / dept_avg, 2) if dept_avg else 0

    # Balance drain — key PaySim fraud signal
    old_bal = txn.get("oldbalanceOrg", 0)
    new_bal = txn.get("newbalanceOrig", 0)
    drain   = round((old_bal - new_bal) / old_bal * 100, 1) if old_bal > 0 else 0

    # Destination account type
    dest_type = (
        "customer account"
        if str(txn.get("vendor", "")).startswith("C")
        else "merchant"
    )

    return {
        "vendor_count":         vendor_count,
        "vendor_fraud_history": vendor_fraud_history,
        "dept_avg":             dept_avg,
        "amount_ratio":         amount_ratio,
        "balance_drain_pct":    drain,
        "dest_account_type":    dest_type,
        "policy_matches":       policy_matches,
    }