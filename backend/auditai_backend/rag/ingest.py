# rag/ingest.py
"""
One-time script to chunk all policy documents and store them in a
persistent ChromaDB vector database on disk.

Run once:  python rag/ingest.py
Re-run any time you add or update policy files in rag/policies/.
"""
from pathlib import Path
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

# ── Paths ─────────────────────────────────────────────────────────────────────
HERE        = Path(__file__).parent          # …/auditai-backend/rag/
POLICIES_DIR = HERE / "policies"
CHROMA_DIR   = HERE / "chroma_db"           # persistent on-disk store
CHROMA_DIR.mkdir(exist_ok=True)

CHUNK_SIZE    = 10   # lines per chunk — tuned for policy paragraphs
CHUNK_OVERLAP = 2    # overlap lines so context isn't cut at boundaries

# ── Helpers ───────────────────────────────────────────────────────────────────

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
    """Split text into overlapping line-based chunks."""
    lines  = [l.strip() for l in text.splitlines() if l.strip()]
    chunks = []
    i = 0
    while i < len(lines):
        chunk = "\n".join(lines[i : i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def ingest_all():
    policy_files = sorted(POLICIES_DIR.glob("*.txt"))
    if not policy_files:
        print(f"No .txt files found in {POLICIES_DIR}")
        return

    print(f"Loading embedding model...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")

    print(f"Opening persistent ChromaDB at {CHROMA_DIR}...")
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Delete existing collection so re-running gives a clean slate
    try:
        client.delete_collection("audit_policies")
        print("Cleared existing 'audit_policies' collection.")
    except Exception:
        pass

    collection = client.create_collection(
        name="audit_policies",
        metadata={"hnsw:space": "cosine"},
    )

    total_chunks = 0
    for policy_file in policy_files:
        print(f"\nIngesting: {policy_file.name}")
        text   = policy_file.read_text(encoding="utf-8")
        chunks = chunk_text(text)
        print(f"  -> {len(chunks)} chunks")

        embeddings = embedder.encode(chunks, show_progress_bar=True).tolist()

        ids = [f"{policy_file.stem}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": policy_file.name, "chunk": i} for i in range(len(chunks))]

        collection.add(
            documents=embeddings and chunks,   # store original text too
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas,
        )
        total_chunks += len(chunks)

    print(f"\nDone! {total_chunks} chunks from {len(policy_files)} files ingested.")
    print(f"   ChromaDB stored at: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_all()
