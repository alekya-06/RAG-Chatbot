import json
from pathlib import Path

RAW_DIR = Path("data/raw/tmdb/movies")
OUTPUT_DIR = Path("data/structured/tmdb/movies")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_release_year(release_date):
    """Extract release year from YYYY-MM-DD."""
    if not release_date:
        return None

    try:
        return int(release_date[:4])
    except (ValueError, TypeError):
        return None


def get_names(items, name_key="name"):
    """Extract names from a list of dictionaries."""
    if not items:
        return []

    return [
        item.get(name_key)
        for item in items
        if item.get(name_key)
    ]


def build_embedding_text(movie):
    """
    Build the text that will eventually be embedded.

    Numerical/exact fields such as runtime, budget, ratings,
    release date, etc. are intentionally NOT included.
    """

    title = movie.get("title")
    original_title = movie.get("original_title")
    overview = movie.get("overview")
    tagline = movie.get("tagline")

    genres = get_names(movie.get("genres"))
    collection = movie.get("belongs_to_collection")
    collection_name = collection.get("name") if collection else None

    production_companies = get_names(
        movie.get("production_companies")
    )

    production_countries = get_names(
        movie.get("production_countries")
    )

    spoken_languages = [
        lang.get("english_name") or lang.get("name")
        for lang in movie.get("spoken_languages", [])
        if lang.get("english_name") or lang.get("name")
    ]

    parts = []

    if title:
        parts.append(f"Title: {title}")

    if original_title and original_title != title:
        parts.append(f"Original Title: {original_title}")

    if tagline:
        parts.append(f"Tagline: {tagline}")

    if overview:
        parts.append(f"Overview: {overview}")

    if genres:
        parts.append(f"Genres: {', '.join(genres)}")

    if collection_name:
        parts.append(f"Collection: {collection_name}")

    if production_companies:
        parts.append(
            f"Production Companies: {', '.join(production_companies)}"
        )

    if production_countries:
        parts.append(
            f"Production Countries: {', '.join(production_countries)}"
        )

    if spoken_languages:
        parts.append(
            f"Spoken Languages: {', '.join(spoken_languages)}"
        )

    return "\n\n".join(parts)


def transform_movie(movie):
    """Convert raw TMDB movie JSON into our structured schema."""

    release_date = movie.get("release_date")

    content = {
        "title": movie.get("title"),
        "original_title": movie.get("original_title"),
        "overview": movie.get("overview"),
        "tagline": movie.get("tagline"),
    }

    metadata = {
        "imdb_id": movie.get("imdb_id"),

        "release_date": release_date,
        "release_year": get_release_year(release_date),

        "original_language": movie.get("original_language"),

        "origin_country": movie.get("origin_country", []),

        "runtime_minutes": movie.get("runtime"),

        "status": movie.get("status"),

        "genres": get_names(movie.get("genres")),

        "spoken_languages": [
            lang.get("english_name") or lang.get("name")
            for lang in movie.get("spoken_languages", [])
            if lang.get("english_name") or lang.get("name")
        ],

        "production_countries": get_names(
            movie.get("production_countries")
        ),

        "budget": movie.get("budget"),

        "revenue": movie.get("revenue"),

        "popularity": movie.get("popularity"),

        "vote_average": movie.get("vote_average"),

        "vote_count": movie.get("vote_count"),
    }

    collection = movie.get("belongs_to_collection")

    relationships = {
        "collection": None,
        "production_companies": []
    }

    if collection:
        relationships["collection"] = {
            "id": collection.get("id"),
            "name": collection.get("name"),
        }

    for company in movie.get("production_companies", []):
        relationships["production_companies"].append({
            "id": company.get("id"),
            "name": company.get("name"),
            "origin_country": company.get("origin_country"),
        })


    assets = {
        "homepage": movie.get("homepage"),
        "poster_path": movie.get("poster_path"),
        "backdrop_path": movie.get("backdrop_path"),
    }


    structured_movie = {
        "movie_id": movie.get("id"),

        "content": content,

        "embedding_text": build_embedding_text(movie),

        "metadata": metadata,

        "relationships": relationships,

        "assets": assets,
    }

    return structured_movie

def main():

    json_files = list(RAW_DIR.glob("*.json"))

    print(f"Found {len(json_files)} raw movie files.")

    successful = 0
    failed = 0

    for file_path in json_files:

        try:
            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as f:
                movie = json.load(f)

            structured_movie = transform_movie(movie)

            movie_id = movie.get("id")

            if movie_id is None:
                print(f" No movie ID: {file_path.name}")
                failed += 1
                continue

            output_path = OUTPUT_DIR / f"{movie_id}.json"


            with open(
                output_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    structured_movie,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            successful += 1

        except Exception as e:

            failed += 1

            print(
                f" Failed: {file_path.name}"
            )
            print(
                f"   Error: {e}"
            )


    print("\n" + "=" * 50)
    print("TRANSFORMATION COMPLETE")
    print("=" * 50)

    print(f"Total files : {len(json_files)}")
    print(f"Successful  : {successful}")
    print(f"Failed      : {failed}")
    print(f"Output      : {OUTPUT_DIR}")


if __name__ == "__main__":
    main()