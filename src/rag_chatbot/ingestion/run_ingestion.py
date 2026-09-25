from .pipeline import TMDBIngestionPipeline

def main():
    pipeline = TMDBIngestionPipeline()

    movie_ids = pipeline.discover_movie_ids(max_pages=5)
    print(f"Discovered {len(movie_ids)} movies.")
    pipeline.ingest_movies(movie_ids)


if __name__ == "__main__":
    main()