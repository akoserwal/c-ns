from __future__ import annotations

from dataclasses import dataclass

import pytest


@dataclass(frozen=True)
class Movie:
    id: int
    title: str
    year: int


class InMemoryMovieRepo:
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


class MovieService:
    def __init__(self, repo: InMemoryMovieRepo):
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


def test_create_movie_valid() -> None:
    svc = MovieService(InMemoryMovieRepo())
    m = svc.create_movie("Inception", 2010)
    assert m.id == 1
    assert m.title == "Inception"
    assert m.year == 2010


def test_create_movie_rejects_empty_title() -> None:
    svc = MovieService(InMemoryMovieRepo())
    with pytest.raises(ValueError):
        svc.create_movie("   ", 2010)


def test_create_movie_rejects_too_old_year() -> None:
    svc = MovieService(InMemoryMovieRepo())
    with pytest.raises(ValueError):
        svc.create_movie("Ancient", 1200)


def test_get_movie_not_found() -> None:
    svc = MovieService(InMemoryMovieRepo())
    with pytest.raises(KeyError):
        svc.get_movie(999)

