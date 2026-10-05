import json
from pathlib import Path

from src.rag_chatbot.database.mongodb import movies

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MOVIES_DIR = PROJECT_ROOT / "data" / "structured" / "tmdb" / "movies"

def load_movies() -> None:
    movie_files = list(MOVIES_DIR.glob("*.json"))

    if not movie_files:
        raise FileNotFoundError(f"No movie JSON files found in {MOVIES_DIR}")

    inserted = 0
    updated = 0

    for file_path in movie_files:
        with open(file_path, "r", encoding="utf-8") as f:
            movie = json.load(f)

        movie_id = movie.get("movie_id")

        if movie_id is None:
            print(f"Skipping {file_path.name}: missing movie ID")
            continue

        result = movies.replace_one(
            {"_id": movie_id},
            movie,
            upsert=True,
        )

        if result.upserted_id is not None:
            inserted += 1
        else:
            updated += 1

    print(f"Processed: {inserted + updated}")
    print(f"Inserted: {inserted}")
    print(f"Updated: {updated}")


if __name__ == "__main__":
    load_movies()