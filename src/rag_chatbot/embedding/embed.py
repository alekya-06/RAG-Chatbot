import json
from pathlib import Path

from sentence_transformers import SentenceTransformer

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STRUCTURED_DIR = (PROJECT_ROOT/ "data"/ "structured"/ "tmdb"/ "movies")
OUTPUT_DIR = (PROJECT_ROOT/ "data"/ "embeddings"/ "tmdb"/ "movies")

OUTPUT_FILE = OUTPUT_DIR / "embeddings.json"
MODEL_NAME = "BAAI/bge-small-en-v1.5"

def load_movies() -> list[dict]:
    movie_files = sorted(STRUCTURED_DIR.glob("*.json"))
    movies = []

    for movie_file in movie_files:

        with movie_file.open("r",encoding="utf-8",) as file:
            movie = json.load(file)
        movies.append(movie)

    return movies

def generate_embeddings(movies: list[dict],model: SentenceTransformer,) -> list[dict]:
    
    texts = [movie["embedding_text"] for movie in movies]

    embeddings = model.encode(texts,
                              normalize_embeddings=True,
                              show_progress_bar=True)

    results = []

    for movie, embedding in zip(movies,embeddings,):
        results.append(
            {
                "movie_id": movie["movie_id"],
                "embedding": embedding.tolist(),
            }
        )

    return results

def save_embeddings(embeddings: list[dict],) -> None:
    
    OUTPUT_DIR.mkdir(parents=True,exist_ok=True)

    output = {
        "model": MODEL_NAME,
        "embedding_dimension": len(
            embeddings[0]["embedding"]
        ),
        "count": len(embeddings),
        "embeddings": embeddings,
    }

    with OUTPUT_FILE.open("w",encoding="utf-8") as file:
        json.dump(output,file)

def main() -> None:

    print("=" * 60)
    print("TMDB Movie Embedding Pipeline")
    print("=" * 60)

    print(f"\nModel: {MODEL_NAME}")

    print(f"Loading movies from:\n"f"{STRUCTURED_DIR}")

    movies = load_movies()

    print(f"Loaded {len(movies)} movies.")

    if not movies:
        raise RuntimeError("No structured movie files were found.")
    print("\nLoading embedding model...")

    model = SentenceTransformer(MODEL_NAME)
    print("Model loaded.")
    print("\nGenerating embeddings...")

    embeddings = generate_embeddings(movies,model)

    print(f"\nGenerated {len(embeddings)} embeddings.")

    print(f"Embedding dimension: \n"
          f"{len(embeddings[0]['embedding'])}")

    save_embeddings(embeddings)

    print(f"\nSaved embeddings to:\n"
        f"{OUTPUT_FILE}")

    print("\nEmbedding pipeline completed.")


if __name__ == "__main__":
    main()
