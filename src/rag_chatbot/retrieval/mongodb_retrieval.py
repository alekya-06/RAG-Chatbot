from typing import Any
from src.rag_chatbot.database.mongodb import movies

def get_movie_by_id(movie_id: int) -> dict[str, Any] | None:
    return movies.find_one({"_id": movie_id})


def search_by_title(title: str) -> list[dict[str, Any]]:
    return list(
        movies.find(
            {
                "content.title": {
                    "$regex": title,
                    "$options": "i",
                }
            }
        )
    )


def get_movies_by_year(year: int) -> list[dict[str, Any]]:
    return list(
        movies.find(
            {
                "metadata.release_year": year
            }
        )
    )


def get_movies_by_genre(genre: str) -> list[dict[str, Any]]:
    return list(
        movies.find(
            {
                "metadata.genres": {
                    "$regex": f"^{genre}$",
                    "$options": "i",
                }
            }
        )
    )


def get_movies_by_director(director: str) -> list[dict[str, Any]]:
    return list(
        movies.find(
            {
                "relationships.people.directors": {
                    "$regex": director,
                    "$options": "i",
                }
            }
        )
    )