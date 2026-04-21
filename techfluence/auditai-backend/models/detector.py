# models/detector.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

# ── Resolve paths relative to this file so the script works
# ── regardless of which directory you invoke it from
HERE       = Path(__file__).parent          # …/auditai-backend/models/
PROJECT    = HERE.parent                    # …/auditai-backend/
DATA_DIR   = PROJECT / "data"
MODELS_DIR = HERE
DATA_DIR.mkdir(exist_ok=True)              # create data/ if missing

# ── STEP 1: Load your actual CSV ─────────────────────────────
print("Loading data...")
df = pd.read_csv(HERE / "PS_20174392719_1491204439457_log.csv")
print(f"Loaded {len(df):,} rows")
print(f"Actual fraud cases: {df['isFraud'].sum():,}")

# ── STEP 2: Map PaySim columns → AuditAI schema ──────────────
# Your columns: step, type, amount, nameOrig, oldbalanceOrg,
#               newbalanceOrig, nameDest, oldbalanceDest,
#               newbalanceDest, isFraud, isFlaggedFraud

df = df.rename(columns={
    "nameOrig":  "employee",
    "nameDest":  "vendor",
    "type":      "category",
    "amount":    "amount",
    "step":      "step",
})

# Map transaction type → department (logical grouping)
dept_map = {
    "PAYMENT":  "Marketing",
    "TRANSFER": "Finance",
    "CASH_OUT": "Operations",
    "DEBIT":    "HR",
    "CASH_IN":  "Engineering",
}
df["department"] = df["category"].map(dept_map)

# Convert step (1 hour increments) → hour of day and day
df["hour_of_day"] = df["step"] % 24
df["day_of_week"]  = (df["step"] // 24) % 7
df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)

# Generate transaction ID
df["id"] = ["TXN-" + str(i).zfill(7) for i in range(len(df))]

# Readable timestamp from step
base = pd.Timestamp("2024-01-01")
df["timestamp"] = df["step"].apply(
    lambda s: (base + pd.Timedelta(hours=int(s))).isoformat()
)

# ── STEP 3: Feature engineering ──────────────────────────────
print("Engineering features...")

# How much this transaction deviates from dept average
dept_avg = df.groupby("department")["amount"].transform("mean")
df["amount_vs_dept_avg"] = df["amount"] / dept_avg.replace(0, 1)

# How many times we've transacted with this vendor
df["vendor_txn_count"] = df.groupby("vendor")["vendor"].transform("count")

# Balance drain ratio — key fraud signal in PaySim
# (how much of the original balance was drained)
df["balance_drain_ratio"] = np.where(
    df["oldbalanceOrg"] > 0,
    (df["oldbalanceOrg"] - df["newbalanceOrig"]) / df["oldbalanceOrg"],
    0
)

# Destination account type — C = customer (suspicious), M = merchant (normal)
df["dest_is_customer"] = df["vendor"].str.startswith("C").astype(int)

# Sudden large amount flag
amount_99th = df["amount"].quantile(0.99)
df["is_large_amount"] = (df["amount"] > amount_99th).astype(int)

FEATURES = [
    "amount",
    "amount_vs_dept_avg",
    "hour_of_day",
    "is_weekend",
    "vendor_txn_count",
    "balance_drain_ratio",
    "dest_is_customer",
    "is_large_amount",
    "oldbalanceOrg",
    "newbalanceOrig",
]

X = df[FEATURES].fillna(0)

# ── STEP 4: Train Isolation Forest ───────────────────────────
print("Training model (this may take 1-2 min on 6M rows)...")

# Sample for speed — 200k rows captures all patterns
sample_idx = df.sample(n=200_000, random_state=42).index
X_sample = X.loc[sample_idx]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sample)

model = IsolationForest(
    contamination=0.01,   # ~1% fraud rate matches PaySim actual rate
    n_estimators=100,
    random_state=42,
    n_jobs=-1             # use all CPU cores
)
model.fit(X_scaled)

# ── STEP 5: Score ALL rows ────────────────────────────────────
print("Scoring all transactions...")
X_all_scaled = scaler.transform(X)
raw_scores = -model.score_samples(X_all_scaled)

# Normalize 0–1
df["anomaly_score"] = (raw_scores - raw_scores.min()) / \
                       (raw_scores.max() - raw_scores.min())

df["risk"] = pd.cut(
    df["anomaly_score"],
    bins=[0, 0.50, 0.75, 1.01],
    labels=["LOW", "MEDIUM", "HIGH"]
)

# ── STEP 6: Validate against real fraud labels ───────────────
print("\n=== VALIDATION ===")
print("Risk distribution:")
print(df["risk"].value_counts())
print()

# Check how well our unsupervised model caught real fraud
high_risk = df[df["risk"] == "HIGH"]
fraud_caught = high_risk["isFraud"].sum()
total_fraud  = df["isFraud"].sum()
print(f"Real fraud cases in dataset:     {total_fraud:,}")
print(f"Fraud cases caught in HIGH risk: {fraud_caught:,}")
print(f"Fraud catch rate:                {fraud_caught/total_fraud*100:.1f}%")
print()

print("Top 10 anomalies:")
print(df.nlargest(10, "anomaly_score")[[
    "id","category","amount","department",
    "anomaly_score","risk","isFraud"
]])

# ── STEP 7: Save everything ───────────────────────────────────
joblib.dump(model,  MODELS_DIR / "isolation_forest.pkl")
joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

# Save scored CSV — only keep columns your API needs
output_cols = [
    "id", "amount", "vendor", "department", "employee",
    "timestamp", "category", "hour_of_day", "is_weekend",
    "amount_vs_dept_avg", "vendor_txn_count", "balance_drain_ratio",
    "dest_is_customer", "oldbalanceOrg", "newbalanceOrig",
    "anomaly_score", "risk", "isFraud"
]
df[output_cols].to_csv(DATA_DIR / "scored_transactions.csv", index=False)
print(f"\nSaved scored_transactions.csv with {len(df):,} rows")
print("Done. isolation_forest.pkl and scaler.pkl ready for the API.")