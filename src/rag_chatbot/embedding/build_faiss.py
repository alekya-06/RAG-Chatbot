import json
from pathlib import Path
import faiss
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[3]

EMBEDDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
    / "tmdb"
    / "movies"
    / "embeddings.json"
)

INDEX_DIR = (
    PROJECT_ROOT
    / "data"
    / "vector_store"
)

INDEX_FILE = INDEX_DIR / "movies.faiss"
MANIFEST_FILE = INDEX_DIR / "index_info.json"

EXPECTED_MODEL = "BAAI/bge-small-en-v1.5"

def load_embeddings() -> tuple[dict, np.ndarray, np.ndarray]:
    """
    Load embedding records and convert them to FAISS-compatible arrays.

    Returns:
        data: Original embedding JSON data
        vectors: Float32 matrix of embeddings
        movie_ids: Int64 array of TMDB movie IDs
    """

    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {EMBEDDINGS_FILE}"
        )

    with EMBEDDINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if data.get("model") != EXPECTED_MODEL:
        raise ValueError(
            f"Unexpected embedding model: {data.get('model')}"
        )

    records = data["embeddings"]

    vectors = np.asarray(
        [record["embedding"] for record in records],
        dtype=np.float32,
    )

    movie_ids = np.asarray(
        [record["movie_id"] for record in records],
        dtype=np.int64,
    )

    if vectors.ndim != 2:
        raise ValueError(
            f"Expected a 2D vector matrix, got shape {vectors.shape}"
        )

    if len(vectors) != len(movie_ids):
        raise ValueError(
            "Vector count does not match movie ID count."
        )

    if len(set(movie_ids.tolist())) != len(movie_ids):
        raise ValueError("Duplicate movie IDs found.")

    if not np.isfinite(vectors).all():
        raise ValueError("Non-finite values found in embeddings.")

    if not np.allclose(
        np.linalg.norm(vectors, axis=1),
        1.0,
        atol=1e-4,
    ):
        raise ValueError("Embeddings are not normalized.")

    return data, np.ascontiguousarray(vectors), movie_ids

def build_index(
    vectors: np.ndarray,
    movie_ids: np.ndarray,
) -> faiss.Index:
    """
    Build an exact inner-product index with explicit movie IDs.

    Because vectors are normalized, inner product is equivalent
    to cosine similarity.
    """

    dimension = vectors.shape[1]

    base_index = faiss.IndexFlatIP(dimension)

    index = faiss.IndexIDMap2(base_index)

    index.add_with_ids(
        vectors,
        movie_ids,
    )

    return index

def save_index(
    index: faiss.Index,
    model_name: str,
    dimension: int,
) -> None:
    """
    Persist the FAISS index and its configuration manifest.
    """

    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    faiss.write_index(
        index,
        str(INDEX_FILE),
    )

    manifest = {
        "model": model_name,
        "dimension": dimension,
        "metric": "inner_product",
        "normalized": True,
        "index_type": "IndexIDMap2(IndexFlatIP)",
        "count": index.ntotal,
    }

    with MANIFEST_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            manifest,
            file,
            indent=2,
        )


def main() -> None:
    print("=" * 60)
    print("FAISS Index Builder")
    print("=" * 60)

    data, vectors, movie_ids = load_embeddings()

    print(f"\nModel: {data['model']}")
    print(f"Vectors loaded: {len(vectors)}")
    print(f"Vector dimension: {vectors.shape[1]}")

    print("\nBuilding FAISS index...")

    index = build_index(
        vectors,
        movie_ids,
    )

    print(f"Index type: {type(index).__name__}")
    print(f"Indexed vectors: {index.ntotal}")

    save_index(
        index,
        data["model"],
        vectors.shape[1],
    )

    print("\nIndex saved successfully.")
    print(f"FAISS index: {INDEX_FILE}")
    print(f"Manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()