import json
import os
import subprocess
import time
from urllib.parse import urlencode

from dotenv import load_dotenv

load_dotenv()


class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"

    def __init__(
        self,
        max_attempts: int = 5,
        retry_delay: float = 1.0,
    ):
        self.token = os.getenv("TMDB_READ_ACCESS_TOKEN")

        if not self.token:
            raise RuntimeError(
                "TMDB_READ_ACCESS_TOKEN is not set. "
                "Add it to your .env file."
            )

        self.max_attempts = max_attempts
        self.retry_delay = retry_delay

    def _request(self, endpoint: str) -> dict:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        command = [
            "curl.exe",
            "-4",
            "--silent",
            "--show-error",
            "--connect-timeout",
            "10",
            "--max-time",
            "30",
            url,
            "-H",
            f"Authorization: Bearer {self.token}",
            "-H",
            "accept: application/json",
        ]

        last_error = None

        for attempt in range(1, self.max_attempts + 1):
            result = subprocess.run(
                command,
                capture_output=True,
            )

            if result.returncode == 0:
                try:
                    response_text = result.stdout.decode("utf-8")
                    return json.loads(response_text)

                except UnicodeDecodeError as exc:
                    raise RuntimeError(
                        "TMDB returned data that could not be decoded as UTF-8.\n"
                        f"Endpoint: {endpoint}"
                    ) from exc

                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "TMDB returned invalid JSON.\n"
                        f"Endpoint: {endpoint}\n"
                        f"Response: {result.stdout[:500]!r}"
                    ) from exc

            last_error = result.stderr.decode(
                "utf-8",
                errors="replace",
            ).strip()

            if attempt < self.max_attempts:
                delay = self.retry_delay * (2 ** (attempt - 1))

                print(
                    f"TMDB request failed "
                    f"(attempt {attempt}/{self.max_attempts}). "
                    f"Retrying in {delay:.1f}s..."
                )

                time.sleep(delay)

        raise RuntimeError(
            f"TMDB request failed after {self.max_attempts} attempts.\n"
            f"Endpoint: {endpoint}\n"
            f"Last error: {last_error}"
        )

    def discover_movies(
        self,
        page: int = 1,
        **filters,
    ) -> dict:
        params = {
            "page": page,
            **filters,
        }

        query_string = urlencode(
            {
                key: value
                for key, value in params.items()
                if value is not None
            }
        )

        return self._request(
            f"discover/movie?{query_string}"
        )

    def get_movie(self, movie_id: int) -> dict:
        return self._request(f"movie/{movie_id}")