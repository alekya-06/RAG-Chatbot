import json
from pathlib import Path


RAW_DIR = Path("data/raw/tmdb/movies")
OUTPUT_DIR = Path("data/structured/tmdb/movies")


PLACEHOLDER_VALUES = {
    "???",
    "??",
    "unknown",
    "UNKNOWN",
    "N/A",
    "n/a",
}


def validate_movie(movie: dict) -> list[str]:
    """
    Validate a raw TMDB movie record.

    Returns a list of validation errors.
    An empty list means the record is valid.
    """

    errors = []

    if not isinstance(movie, dict):
        return ["Movie record is not a dictionary."]

    movie_id = movie.get("id")

    if movie_id is None:
        errors.append("Missing movie ID.")

    for field in [
        "title",
        "original_title",
        "overview",
        "release_date",
        "original_language",
        "status",
    ]:
        value = movie.get(field)

        if isinstance(value, str):
            if value.strip() in PLACEHOLDER_VALUES:
                errors.append(
                    f"Placeholder value in '{field}': "
                    f"{value!r}"
                )

    title = movie.get("title")

    if not isinstance(title, str) or not title.strip():
        errors.append("Missing or invalid title.")

    return errors


def get_release_year(
    release_date: str | None,
) -> int | None:
    """
    Extract release year from YYYY-MM-DD.
    """

    if not release_date:
        return None

    try:
        return int(release_date[:4])

    except (ValueError, TypeError):
        return None


def get_names(
    items: list[dict] | None,
    name_key: str = "name",
) -> list[str]:
    """
    Extract non-empty names from a TMDB list of dictionaries.
    """

    if not isinstance(items, list):
        return []

    names = []

    for item in items:
        if not isinstance(item, dict):
            continue

        name = item.get(name_key)

        if isinstance(name, str) and name.strip():
            names.append(name.strip())

    return names


def get_credits(
    movie: dict,
) -> dict:
    """
    Extract useful people information from TMDB credits.

    Returns directors, writers, and top cast members.
    """

    credits = movie.get("credits", {})

    if not isinstance(credits, dict):
        return {
            "directors": [],
            "writers": [],
            "cast": [],
        }

    crew = credits.get("crew", [])
    cast = credits.get("cast", [])

    directors = []
    writers = []

    if isinstance(crew, list):

        for person in crew:

            if not isinstance(person, dict):
                continue

            name = person.get("name")
            job = person.get("job")

            if not isinstance(name, str):
                continue

            name = name.strip()

            if not name:
                continue

            if job == "Director":
                directors.append(name)

            elif job in {
                "Writer",
                "Screenplay",
                "Story",
            }:
                writers.append(name)

    cast_names = []

    if isinstance(cast, list):

        for person in cast:

            if not isinstance(person, dict):
                continue

            name = person.get("name")

            if not isinstance(name, str):
                continue

            name = name.strip()

            if name:
                cast_names.append(name)

            if len(cast_names) >= 10:
                break

    return {
        "directors": directors,
        "writers": writers,
        "cast": cast_names,
    }


def get_keywords(
    movie: dict,
) -> list[str]:
    """
    Extract keyword names from TMDB keyword data.
    """

    keywords_data = movie.get("keywords", {})

    if not isinstance(keywords_data, dict):
        return []

    keywords = keywords_data.get("keywords", [])

    return get_names(keywords)


def build_embedding_text(
    movie: dict,
    credits: dict,
    keywords: list[str],
) -> str:
    """
    Build the semantic text that will later be embedded.

    Numerical/exact fields such as runtime, budget,
    revenue, ratings, and release date are intentionally
    excluded from the embedding text.
    """

    sections = []

    title = movie.get("title")

    if title:
        sections.append(
            f"Title: {title}"
        )

    original_title = movie.get("original_title")

    if (
        original_title
        and original_title != title
    ):
        sections.append(
            f"Original Title: {original_title}"
        )

    tagline = movie.get("tagline")

    if tagline:
        sections.append(
            f"Tagline: {tagline}"
        )

    overview = movie.get("overview")

    if overview:
        sections.append(
            f"Overview: {overview}"
        )

    genres = get_names(
        movie.get("genres")
    )

    if genres:
        sections.append(
            f"Genres: {', '.join(genres)}"
        )

    collection = movie.get(
        "belongs_to_collection"
    )

    if isinstance(collection, dict):

        collection_name = collection.get("name")

        if collection_name:
            sections.append(
                f"Collection: {collection_name}"
            )

    production_companies = get_names(
        movie.get("production_companies")
    )

    if production_companies:
        sections.append(
            "Production Companies: "
            + ", ".join(production_companies)
        )

    production_countries = get_names(
        movie.get("production_countries")
    )

    if production_countries:
        sections.append(
            "Production Countries: "
            + ", ".join(production_countries)
        )

    spoken_languages = get_names(
        movie.get("spoken_languages"),
        name_key="english_name",
    )

    if spoken_languages:
        sections.append(
            "Spoken Languages: "
            + ", ".join(spoken_languages)
        )

    directors = credits.get(
        "directors",
        [],
    )

    if directors:
        sections.append(
            "Director: "
            + ", ".join(directors)
        )

    writers = credits.get(
        "writers",
        [],
    )

    if writers:
        sections.append(
            "Writers: "
            + ", ".join(writers)
        )

    cast = credits.get(
        "cast",
        [],
    )

    if cast:
        sections.append(
            "Cast: "
            + ", ".join(cast)
        )

    if keywords:
        sections.append(
            "Keywords: "
            + ", ".join(keywords)
        )

    return "\n\n".join(sections)


def transform_movie(
    movie: dict,
) -> dict:
    """
    Transform a raw TMDB movie record into the
    structured representation used by the RAG pipeline.
    """

    movie_id = movie["id"]

    credits = get_credits(movie)
    keywords = get_keywords(movie)

    embedding_text = build_embedding_text(
        movie,
        credits,
        keywords,
    )

    metadata = {
        "imdb_id": movie.get("imdb_id"),
        "release_date": movie.get("release_date"),
        "release_year": get_release_year(
            movie.get("release_date")
        ),
        "original_language": movie.get(
            "original_language"
        ),
        "origin_country": movie.get(
            "origin_country",
            [],
        ),
        "runtime_minutes": movie.get(
            "runtime"
        ),
        "status": movie.get("status"),
        "genres": get_names(
            movie.get("genres")
        ),
        "spoken_languages": get_names(
            movie.get("spoken_languages"),
            name_key="english_name",
        ),
        "production_countries": get_names(
            movie.get("production_countries")
        ),
        "budget": movie.get("budget"),
        "revenue": movie.get("revenue"),
        "popularity": movie.get("popularity"),
        "vote_average": movie.get(
            "vote_average"
        ),
        "vote_count": movie.get(
            "vote_count"
        ),
    }

    relationships = {
        "collection": None,
        "production_companies": [],
        "people": credits,
        "keywords": keywords,
    }

    collection = movie.get(
        "belongs_to_collection"
    )

    if isinstance(collection, dict):

        relationships["collection"] = {
            "id": collection.get("id"),
            "name": collection.get("name"),
        }

    production_companies = movie.get(
        "production_companies",
        []
    )

    if isinstance(production_companies, list):

        for company in production_companies:

            if not isinstance(company, dict):
                continue

            relationships[
                "production_companies"
            ].append(
                {
                    "id": company.get("id"),
                    "name": company.get("name"),
                    "origin_country": company.get(
                        "origin_country"
                    ),
                }
            )

    return {
        "movie_id": movie_id,

        "content": {
            "title": movie.get("title"),
            "original_title": movie.get(
                "original_title"
            ),
            "overview": movie.get("overview"),
            "tagline": movie.get("tagline"),
        },

        "embedding_text": embedding_text,

        "metadata": metadata,

        "relationships": relationships,

        "assets": {
            "homepage": movie.get("homepage"),
            "poster_path": movie.get(
                "poster_path"
            ),
            "backdrop_path": movie.get(
                "backdrop_path"
            ),
        },
    }


def main() -> None:

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    raw_files = sorted(
        RAW_DIR.glob("*.json")
    )

    successful = 0
    incomplete = 0
    invalid = 0
    failed = 0

    invalid_records = []

    for raw_file in raw_files:

        try:

            with raw_file.open(
                "r",
                encoding="utf-8",
            ) as file:

                movie = json.load(file)

            errors = validate_movie(movie)

            if errors:

                invalid += 1

                invalid_records.append(
                    {
                        "file": raw_file.name,
                        "errors": errors,
                    }
                )

                print(
                    f"INVALID: {raw_file.name}"
                )

                for error in errors:
                    print(
                        f"  - {error}"
                    )

                continue

            structured_movie = transform_movie(
                movie
            )

            output_path = (
                OUTPUT_DIR
                / raw_file.name
            )

            with output_path.open(
                "w",
                encoding="utf-8",
            ) as file:

                json.dump(
                    structured_movie,
                    file,
                    ensure_ascii=False,
                    indent=2,
                )

            successful += 1

            if not movie.get("overview"):
                incomplete += 1

        except Exception as exc:

            failed += 1

            print(
                f"FAILED: {raw_file.name}: {exc}"
            )

    print(
        "\n"
        + "=" * 60
    )

    print("Structuring complete.")

    print(
        f"Raw files: {len(raw_files)}"
    )

    print(
        f"Successfully structured: "
        f"{successful}"
    )

    print(
        f"Incomplete records: "
        f"{incomplete}"
    )

    print(
        f"Invalid records: "
        f"{invalid}"
    )

    print(
        f"Processing failures: "
        f"{failed}"
    )

    if invalid_records:

        print(
            "\nInvalid records:"
        )

        for record in invalid_records:

            print(
                f"  {record['file']}"
            )

            for error in record["errors"]:
                print(
                    f"    - {error}"
                )


if __name__ == "__main__":
    main()

