from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Movie:
    id: int
    title: str
    year: int


class MovieRepo(Protocol):
    def create(self, title: str, year: int) -> Movie: ...
    def get_by_id(self, movie_id: int) -> Movie | None: ...


class MovieService:
    """
    Service owns business rules and invariants. It should be framework-free.
    """

    def __init__(self, repo: MovieRepo):
        self._repo = repo

    def create_movie(self, title: str, year: int) -> Movie:
        title = title.strip()
        if not title:
            raise ValueError("title must be non-empty")
        if year < 1888:
            raise ValueError("year must be >= 1888")
        return self._repo.create(title=title, year=year)

    def get_movie(self, movie_id: int) -> Movie:
        m = self._repo.get_by_id(movie_id)
        if not m:
            raise KeyError(movie_id)
        return m


class InMemoryMovieRepo:
    """
    Simple repo implementation used for demo/testing.
    """

    def __init__(self) -> None:
        self._items: dict[int, Movie] = {}
        self._next_id = 1

    def create(self, title: str, year: int) -> Movie:
        m = Movie(id=self._next_id, title=title, year=year)
        self._items[m.id] = m
        self._next_id += 1
        return m

    def get_by_id(self, movie_id: int) -> Movie | None:
        return self._items.get(movie_id)


def main() -> None:
    repo = InMemoryMovieRepo()
    svc = MovieService(repo)

    created = svc.create_movie("Inception", 2010)
    print("Created:", created)

    fetched = svc.get_movie(created.id)
    print("Fetched:", fetched)


if __name__ == "__main__":
    main()

