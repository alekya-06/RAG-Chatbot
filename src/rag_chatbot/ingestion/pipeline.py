import json
import time
from pathlib import Path
from .tmdb_client import TMDBClient

RAW_MOVIE_DIR = Path("data/raw/tmdb/movies")

class TMDBIngestionPipeline:
    def __init__(self, client: TMDBClient | None = None):
        self.client = client or TMDBClient()

        RAW_MOVIE_DIR.mkdir(
            parents=True,
            exist_ok=True,)

    def discover_movie_ids(
        self,
        max_pages: int | None = None,
        page_retries: int = 3,
    ) -> list[int]:
        first_page = self.client.discover_movies(page=1)
    
        total_pages = first_page["total_pages"]
    
        if max_pages is not None:
            total_pages = min(total_pages, max_pages)
    
        movie_ids = [movie["id"] for movie in first_page["results"]]
    
        print(f"Discovering {total_pages} page(s)...")
    
        for page in range(2, total_pages + 1):
            print(f"Fetching discovery page {page}/{total_pages}")
    
            for attempt in range(1, page_retries + 1):
                try:
                    result = self.client.discover_movies(page=page)
    
                    movie_ids.extend(
                        movie["id"]
                        for movie in result["results"]
                    )
    
                    break
    
                except RuntimeError as exc:
                    print(
                        f"Discovery page {page} failed "
                        f"(attempt {attempt}/{page_retries}): {exc}"
                    )
    
                    if attempt == page_retries:
                        raise RuntimeError(
                            f"Failed to fetch discovery page {page} "
                            f"after {page_retries} attempts."
                        ) from exc
    
                    time.sleep(2 * attempt)
    
            time.sleep(0.5)
    
        return movie_ids
    
    def save_movie(
        self,
        movie: dict,
    ) -> None:

        movie_id = movie["id"]

        output_path = (
            RAW_MOVIE_DIR / f"{movie_id}.json"
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                movie,
                file,
                ensure_ascii=False,
                indent=2,
            )

    def ingest_movie(
        self,
        movie_id: int,
    ) -> None:

        output_path = (
            RAW_MOVIE_DIR / f"{movie_id}.json"
        )

        if output_path.exists():
            return

        movie = self.client.get_movie(movie_id)

        self.save_movie(movie)

    def ingest_movies(self, movie_ids: list[int]) -> None:
        total = len(movie_ids)
        failed_movie_ids = []
    
        for index, movie_id in enumerate(movie_ids, start=1):
            print(f"[{index}/{total}] Movie ID: {movie_id}")
    
            try:
                self.ingest_movie(movie_id)
            except RuntimeError as exc:
                print(f"FAILED movie {movie_id}: {exc}")
                failed_movie_ids.append(movie_id)
    
            time.sleep(0.5)
    
        if failed_movie_ids:
            print("\nIngestion completed with failures.")
            print(f"Failed movies: {len(failed_movie_ids)}")
            print(f"Movie IDs: {failed_movie_ids}")
        else:
            print("\nIngestion completed successfully.")