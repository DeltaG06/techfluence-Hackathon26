# models/detector.py
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────
HERE       = Path(__file__).parent
PROJECT    = HERE.parent
DATA_DIR   = PROJECT / "data"
MODELS_DIR = HERE
DATA_DIR.mkdir(exist_ok=True)

# ── STEP 1: Load data ─────────────────────────────────────────
print("Loading data...")
df = pd.read_csv(HERE / "PS_20174392719_1491204439457_log.csv")
print(f"Loaded {len(df):,} rows")
print(f"Actual fraud cases: {df['isFraud'].sum():,}")

# ── STEP 2: Rename + structure ───────────────────────────────
df = df.rename(columns={
    "nameOrig":  "employee",
    "nameDest":  "vendor",
    "type":      "category",
    "amount":    "amount",
    "step":      "step",
})

dept_map = {
    "PAYMENT":  "Marketing",
    "TRANSFER": "Finance",
    "CASH_OUT": "Operations",
    "DEBIT":    "HR",
    "CASH_IN":  "Engineering",
}
df["department"] = df["category"].map(dept_map)

# Time features
df["hour_of_day"] = df["step"] % 24
df["day_of_week"] = (df["step"] // 24) % 7
df["is_weekend"]  = (df["day_of_week"] >= 5).astype(int)

# IDs + timestamps
df["id"] = ["TXN-" + str(i).zfill(7) for i in range(len(df))]
base = pd.Timestamp("2024-01-01")
df["timestamp"] = df["step"].apply(
    lambda s: (base + pd.Timedelta(hours=int(s))).isoformat()
)

# ── STEP 3: Feature Engineering ──────────────────────────────
print("Engineering features...")

dept_avg = df.groupby("department")["amount"].transform("mean")
df["amount_vs_dept_avg"] = df["amount"] / dept_avg.replace(0, 1)

df["vendor_txn_count"] = df.groupby("vendor")["vendor"].transform("count")

df["balance_drain_ratio"] = np.where(
    df["oldbalanceOrg"] > 0,
    (df["oldbalanceOrg"] - df["newbalanceOrig"]) / df["oldbalanceOrg"],
    0
)

df["dest_is_customer"] = df["vendor"].str.startswith("C").astype(int)

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

# ── STEP 4: Train model (sampled) ────────────────────────────
print("Training model...")

sample_idx = df.sample(n=200_000, random_state=42).index
X_sample = X.loc[sample_idx]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_sample)

model = IsolationForest(
    contamination=0.01,
    n_estimators=100,
    random_state=42,
    n_jobs=-1
)
model.fit(X_scaled)

# ── STEP 5: Score ALL data ───────────────────────────────────
print("Scoring transactions...")
X_all_scaled = scaler.transform(X)
raw_scores = -model.score_samples(X_all_scaled)

df["anomaly_score"] = (raw_scores - raw_scores.min()) / \
                     (raw_scores.max() - raw_scores.min())

df["risk"] = pd.cut(
    df["anomaly_score"],
    bins=[0, 0.50, 0.75, 1.01],
    labels=["LOW", "MEDIUM", "HIGH"]
)

# ── STEP 6: Validation ───────────────────────────────────────
print("\n=== VALIDATION ===")
print(df["risk"].value_counts())

high_risk = df[df["risk"] == "HIGH"]
fraud_caught = high_risk["isFraud"].sum()
total_fraud  = df["isFraud"].sum()

print(f"Fraud caught: {fraud_caught}/{total_fraud} "
      f"({(fraud_caught/total_fraud*100):.1f}%)")

# ── STEP 7: CREATE SMALL DEMO DATASET (🔥 IMPORTANT) ─────────
print("\nCreating demo dataset (~2000 rows)...")

output_cols = [
    "id", "amount", "vendor", "department", "employee",
    "timestamp", "category", "hour_of_day", "is_weekend",
    "amount_vs_dept_avg", "vendor_txn_count",
    "balance_drain_ratio", "dest_is_customer",
    "oldbalanceOrg", "newbalanceOrig",
    "anomaly_score", "risk", "isFraud"
]

# Keep all HIGH risk
high_df = df[df["risk"] == "HIGH"]

# Sample others
medium_df = df[df["risk"] == "MEDIUM"].sample(n=800, random_state=42)
low_df    = df[df["risk"] == "LOW"].sample(n=800, random_state=42)

# Combine
final_df = pd.concat([high_df, medium_df, low_df])

# Ensure fraud cases included
fraud_df = df[df["isFraud"] == 1]
final_df = pd.concat([final_df, fraud_df]).drop_duplicates()

# Limit to 2000 rows
final_df = final_df.sample(n=2000, random_state=42)

# Shuffle
final_df = final_df.sample(frac=1, random_state=42)

# Save demo dataset
final_df[output_cols].to_csv(DATA_DIR / "demo_transactions.csv", index=False)

print(f"Saved demo_transactions.csv with {len(final_df)} rows")

# ── STEP 8: Save model ───────────────────────────────────────
joblib.dump(model, MODELS_DIR / "isolation_forest.pkl")
joblib.dump(scaler, MODELS_DIR / "scaler.pkl")

print("Model + scaler saved. Ready for API 🚀")