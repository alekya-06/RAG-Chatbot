import json
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

EMBEDDINGS_FILE = (
    PROJECT_ROOT
    / "data"
    / "embeddings"
    / "tmdb"
    / "movies"
    / "embeddings.json"
)

EXPECTED_COUNT = 547
EXPECTED_DIMENSION = 384
NORM_TOLERANCE = 1e-4


def validate_embeddings() -> None:
    print("=" * 60)
    print("Embedding Validation")
    print("=" * 60)

    if not EMBEDDINGS_FILE.exists():
        raise FileNotFoundError(
            f"Embeddings file not found: {EMBEDDINGS_FILE}"
        )

    with EMBEDDINGS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    records = data.get("embeddings", [])

    print(f"\nModel: {data.get('model')}")
    print(f"Declared count: {data.get('count')}")
    print(f"Actual count: {len(records)}")
    print(f"Declared dimension: {data.get('embedding_dimension')}")

    # 1. Count check
    count_ok = len(records) == EXPECTED_COUNT
    print(f"\n[{'PASS' if count_ok else 'FAIL'}] Embedding count")

    # 2. Dimension check
    dimension_errors = []
    for record in records:
        vector = record.get("embedding", [])
        if len(vector) != EXPECTED_DIMENSION:
            dimension_errors.append(record.get("movie_id"))

    dimension_ok = not dimension_errors
    print(
        f"[{'PASS' if dimension_ok else 'FAIL'}] "
        f"Vector dimensions ({EXPECTED_DIMENSION})"
    )
    if dimension_errors:
        print(f"  Invalid movie IDs: {dimension_errors[:10]}")

    # 3. Unique movie ID check
    movie_ids = [record.get("movie_id") for record in records]
    unique_ids_ok = (
        None not in movie_ids
        and len(movie_ids) == len(set(movie_ids))
    )
    print(f"[{'PASS' if unique_ids_ok else 'FAIL'}] Unique movie IDs")

    # 4. Numeric and finite value check
    invalid_vectors = []
    for record in records:
        vector = record.get("embedding", [])
        if not all(
            isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
            for value in vector
        ):
            invalid_vectors.append(record.get("movie_id"))

    finite_ok = not invalid_vectors
    print(f"[{'PASS' if finite_ok else 'FAIL'}] Finite numeric values")
    if invalid_vectors:
        print(f"  Invalid movie IDs: {invalid_vectors[:10]}")

    # 5. Normalization check
    norm_errors = []
    norms = []

    if dimension_ok and finite_ok:
        for record in records:
            vector = record["embedding"]
            norm = math.sqrt(sum(value * value for value in vector))
            norms.append(norm)

            if abs(norm - 1.0) > NORM_TOLERANCE:
                norm_errors.append(
                    (record.get("movie_id"), norm)
                )

    normalization_ok = (
        dimension_ok
        and finite_ok
        and not norm_errors
    )
    print(
        f"[{'PASS' if normalization_ok else 'FAIL'}] "
        "Normalized vectors (L2 norm ≈ 1)"
    )

    if norms:
        print(f"  Minimum norm: {min(norms):.8f}")
        print(f"  Maximum norm: {max(norms):.8f}")

    if norm_errors:
        print(f"  First few norm errors: {norm_errors[:10]}")

    # 6. Duplicate IDs and metadata consistency
    declared_count_ok = data.get("count") == len(records)
    declared_dimension_ok = (
        data.get("embedding_dimension") == EXPECTED_DIMENSION
    )

    print(
        f"[{'PASS' if declared_count_ok else 'FAIL'}] "
        "Declared count matches actual count"
    )
    print(
        f"[{'PASS' if declared_dimension_ok else 'FAIL'}] "
        "Declared dimension matches expected dimension"
    )

    all_checks_passed = all([
        count_ok,
        dimension_ok,
        unique_ids_ok,
        finite_ok,
        normalization_ok,
        declared_count_ok,
        declared_dimension_ok,
    ])

    print("\n" + "=" * 60)
    print(
        "RESULT: "
        + ("All checks passed." if all_checks_passed
           else "Some checks failed.")
    )
    print("=" * 60)

    if not all_checks_passed:
        raise ValueError(
            "Embedding validation failed. Review the errors above."
        )


if __name__ == "__main__":
    validate_embeddings()

