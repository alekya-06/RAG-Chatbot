from pipeline import TMDBIngestionPipeline

DISCOVERY_STRATEGIES = [
    {
        "name": "Popular movies",
        "sort_by": "popularity.desc",
    },

    {
        "name": "Highly rated movies",
        "sort_by": "vote_average.desc",
        "vote_count_gte": 100,
    },

    {
        "name": "Action",
        "with_genres": 28,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Comedy",
        "with_genres": 35,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Drama",
        "with_genres": 18,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Science Fiction",
        "with_genres": 878,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Animation",
        "with_genres": 16,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Horror",
        "with_genres": 27,
        "sort_by": "popularity.desc",
    },

    {
        "name": "Japanese movies",
        "with_original_language": "ja",
        "sort_by": "popularity.desc",
    },

    {
        "name": "Korean movies",
        "with_original_language": "ko",
        "sort_by": "popularity.desc",
    },

    {
        "name": "French movies",
        "with_original_language": "fr",
        "sort_by": "popularity.desc",
    },

    {
        "name": "Indian movies",
        "with_original_language": "hi",
        "sort_by": "popularity.desc",
    },

    {
        "name": "Older movies",
        "primary_release_date_lte": "1980-12-31",
        "sort_by": "popularity.desc",
    },

    {
        "name": "1990s movies",
        "primary_release_date_gte": "1990-01-01",
        "primary_release_date_lte": "1999-12-31",
        "sort_by": "popularity.desc",
    },

    {
        "name": "2000s movies",
        "primary_release_date_gte": "2000-01-01",
        "primary_release_date_lte": "2009-12-31",
        "sort_by": "popularity.desc",
    },

    {
        "name": "Recent movies",
        "primary_release_date_gte": "2020-01-01",
        "sort_by": "popularity.desc",
    },
]

def main():
    pipeline = TMDBIngestionPipeline()
    movie_ids = pipeline.discover_movie_ids(strategies=DISCOVERY_STRATEGIES,
                                            pages_per_strategy=3)
    print(f"Discovered {len(movie_ids)} movies.")
    pipeline.ingest_movies(movie_ids, force=True)

if __name__ == "__main__":
    main()