"""
Repository interface (Protocol).

Defines the persistence contract using only primitives and plain dicts.
No Pydantic, no ORM -- just Python built-ins.

Any implementation (SQLAlchemy, in-memory, MongoDB) must satisfy this shape.
"""

from __future__ import annotations

from typing import Protocol


class MovieRepo(Protocol):
    """Persistence operations for movies.

    All inputs and outputs are primitives or plain dicts.
    - Person data: {"name": str, "middle_name": str | None, "surname": str | None}
    - Genre data: just a str (the genre name)
    - Movie identity: (title, year, runtime)
    - Full movie dict: {"title", "year", "runtime", "director": [...], "genres": [...], "stars": [...]}
    """

    def select(
        self,
        title: str,
        year: int,
        runtime: int,
        full: bool = False,
    ) -> dict | None:
        """Look up a movie by its composite key.

        When full=True, include director/genres/stars in the returned dict.
        Returns None if not found.
        """
        ...

    def create(
        self,
        title: str,
        year: int,
        runtime: int,
        directors: list[dict],
        genres: list[str] | None = None,
        stars: list[dict] | None = None,
    ) -> dict:
        """Persist a new movie with its relationships.

        directors: [{"name": ..., "middle_name": ..., "surname": ...}, ...]
        genres:    ["Sci-Fi", "Thriller", ...]
        stars:     [{"name": ..., "middle_name": ..., "surname": ...}, ...]

        Returns the movie identity dict: {"title", "year", "runtime"}.
        Raises ConflictError if the movie already exists.
        """
        ...

    def update(
        self,
        title: str,
        year: int,
        runtime: int,
        updates: dict,
    ) -> dict | None:
        """Update a movie's scalar attributes.

        Returns updated identity dict, or None if not found.
        Raises ConflictError if the update violates a constraint.
        """
        ...

    def delete(self, title: str, year: int, runtime: int) -> bool:
        """Delete a movie by its composite key.

        Returns True if deleted, False if not found.
        """
        ...
