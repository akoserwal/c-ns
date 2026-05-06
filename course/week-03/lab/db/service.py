"""
Service / use-case layer.

Accepts Pydantic DTOs from the API layer.
Decomposes them into primitives before calling the repository.
Returns Pydantic DTOs back to the caller.

Pydantic lives here and above -- never deeper.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from film import Movie, Release

if TYPE_CHECKING:
    from .repository import MovieRepo


class MovieService:
    """Movie lookup service class"""

    def __init__(self, repo: MovieRepo):
        self._repo = repo

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def select_film(self, movie: Release, full: bool = False) -> Movie | None:
        """Select a movie by its identity (title, year, runtime)."""

        result = self._repo.select(movie.title, movie.year, movie.runtime, full)

        if result is None:
            return None

        return Movie(**result)

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def save_film(self, movie: Movie) -> Release:
        """Save a film. Director is required (enforced by Pydantic)."""

        # Decompose the DTO into primitives for the repo.
        # Pydantic stops here -- only plain values cross into the repo.
        directors = [d.model_dump() for d in movie.director]
        genres = [g.name for g in movie.genres] if movie.genres else None
        stars = [s.model_dump() for s in movie.stars] if movie.stars else None

        result = self._repo.create(
            title=movie.title,
            year=movie.year,
            runtime=movie.runtime,
            directors=directors,
            genres=genres,
            stars=stars,
        )
        return Release(**result)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update_film(self, movie: Release, updates: Release) -> Release | None:
        """Update movie scalar attributes."""

        # Only send non-None update fields as a plain dict
        updates_dict = updates.model_dump(exclude_unset=True)

        result = self._repo.update(
            movie.title, movie.year, movie.runtime, updates_dict
        )
        if result is None:
            return None
        return Release(**result)

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def delete_film(self, movie: Release) -> bool:
        """Delete movie by identity."""

        return self._repo.delete(movie.title, movie.year, movie.runtime)
