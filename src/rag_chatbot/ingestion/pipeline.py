import json
import time
from pathlib import Path

from tmdb_client import TMDBClient


RAW_MOVIE_DIR = Path("data/raw/tmdb/movies")


class TMDBIngestionPipeline:

    def __init__(self, client: TMDBClient | None = None):
        self.client = client or TMDBClient()

        RAW_MOVIE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

    def discover_movie_ids(
        self,
        strategies: list[dict],
        pages_per_strategy: int = 3,
        page_retries: int = 3,
    ) -> list[int]:

        movie_ids = set()

        for strategy_index, strategy in enumerate(
            strategies,
            start=1,
        ):
            name = strategy.get(
                "name",
                f"Strategy {strategy_index}",
            )

            filters = {
                key: value
                for key, value in strategy.items()
                if key != "name"
            }

            print(
                f"\n{'=' * 60}\n"
                f"Strategy {strategy_index}: {name}\n"
                f"{'=' * 60}"
            )

            for page in range(
                1,
                pages_per_strategy + 1,
            ):

                print(
                    f"Fetching page {page}/"
                    f"{pages_per_strategy}"
                )

                for attempt in range(
                    1,
                    page_retries + 1,
                ):

                    try:
                        result = self.client.discover_movies(
                            page=page,
                            **filters,
                        )

                        new_ids = {
                            movie["id"]
                            for movie in result["results"]
                        }

                        before = len(movie_ids)

                        movie_ids.update(new_ids)

                        added = len(movie_ids) - before

                        print(
                            f"  Retrieved {len(new_ids)} movies "
                            f"({added} new)"
                        )

                        break

                    except RuntimeError as exc:

                        print(
                            f"Discovery page {page} failed "
                            f"(attempt "
                            f"{attempt}/{page_retries}): "
                            f"{exc}"
                        )

                        if attempt == page_retries:
                            raise RuntimeError(
                                f"Failed to fetch strategy "
                                f"'{name}', page {page}"
                            ) from exc

                        time.sleep(2 * attempt)

                time.sleep(0.5)

        movie_ids = list(movie_ids)

        print(
            f"\nDiscovery complete."
            f"\nUnique movies discovered: "
            f"{len(movie_ids)}"
        )

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

    def ingest_movies(
        self,
        movie_ids: list[int],
    ) -> None:

        total = len(movie_ids)
        failed_movie_ids = []

        for index, movie_id in enumerate(
            movie_ids,
            start=1,
        ):

            print(
                f"[{index}/{total}] "
                f"Movie ID: {movie_id}"
            )

            try:
                self.ingest_movie(movie_id)

            except RuntimeError as exc:

                print(
                    f"FAILED movie {movie_id}: {exc}"
                )

                failed_movie_ids.append(movie_id)

            time.sleep(0.5)

        if failed_movie_ids:

            print(
                "\nIngestion completed with failures."
            )

            print(
                f"Failed movies: "
                f"{len(failed_movie_ids)}"
            )

            print(
                f"Movie IDs: "
                f"{failed_movie_ids}"
            )

        else:

            print(
                "\nIngestion completed successfully."
            )