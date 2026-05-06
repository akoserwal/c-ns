"""
SQLAlchemy repository implementation.

This is the ONLY layer that knows about ORM classes.
It accepts primitives/dicts from the service layer and returns primitives/dicts.
All ORM object construction happens here -- never leaks out.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload

from ..errors import ConflictError, DatabaseError
from .setup import get_db
from .tables import Base, Director, Genre, Movie, Star

# Updatable scalar attributes -- prevents arbitrary attribute injection
_UPDATABLE_FIELDS = {"title", "year", "runtime"}


def init_db(engine) -> None:
    """Create all tables. Call explicitly at app startup, not on import."""
    Base.metadata.create_all(bind=engine)


class SQLArepo:
    """Repository implementation backed by SQLAlchemy ORM."""

    # ==================================================================
    # Private helpers -- ORM construction lives here, nowhere else
    # ==================================================================

    @staticmethod
    def _get_or_create_person(db, model_cls, person: dict):
        """Get-or-create a Director or Star by full name."""
        existing = db.execute(
            select(model_cls).where(
                model_cls.name == person["name"],
                model_cls.middle_name == person.get("middle_name"),
                model_cls.surname == person.get("surname"),
            )
        ).scalar_one_or_none()

        if existing:
            return existing

        return model_cls(
            name=person["name"],
            middle_name=person.get("middle_name"),
            surname=person.get("surname"),
        )

    @staticmethod
    def _build_genre(db, name: str) -> Genre:
        """Find an existing genre or create a new one."""
        existing = db.execute(
            select(Genre).where(Genre.name == name)
        ).scalar_one_or_none()

        if existing:
            return existing

        return Genre(name=name)

    @staticmethod
    def _person_to_dict(person: Director | Star) -> dict:
        """Convert a Director or Star ORM object to a plain dict."""
        return {
            "name": person.name,
            "middle_name": person.middle_name,
            "surname": person.surname,
        }

    @staticmethod
    def _movie_to_dict(movie: Movie, full: bool = False) -> dict:
        """Convert a Movie ORM object to a plain dict.

        When full=True, includes relationship data (director, genres, stars).
        When full=False, returns only the scalar identity columns.
        """
        result = {
            "title": movie.title,
            "year": movie.year,
            "runtime": movie.runtime,
        }

        if full:
            result["director"] = [
                SQLArepo._person_to_dict(d) for d in movie.director
            ]
            result["genres"] = [
                {"name": g.name} for g in movie.genres
            ]
            result["stars"] = [
                SQLArepo._person_to_dict(s) for s in movie.stars
            ]

        return result

    # ==================================================================
    # Public interface -- matches the MovieRepo Protocol
    # ==================================================================

    def select(
        self, title: str, year: int, runtime: int, full: bool = False
    ) -> dict | None:
        """Look up a movie by composite key."""

        query = select(Movie).where(
            Movie.title == title, Movie.year == year, Movie.runtime == runtime
        )

        if full:
            query = query.options(
                selectinload(Movie.director),
                selectinload(Movie.genres),
                selectinload(Movie.stars),
            )

        with get_db() as db:
            try:
                movie = db.execute(query).scalar_one_or_none()
            except SQLAlchemyError as e:
                raise DatabaseError(
                    "Failure while looking up movie; status unknown"
                ) from e

            if movie is None:
                return None

            return self._movie_to_dict(movie, full=full)

    def create(
        self,
        title: str,
        year: int,
        runtime: int,
        directors: list[dict],
        genres: list[str] | None = None,
        stars: list[dict] | None = None,
    ) -> dict:
        """Persist a new movie with all its relationships.

        ORM objects are built here from the incoming primitives.
        Get-or-create logic prevents duplicate IntegrityErrors
        on related entities (directors, genres, stars).
        """

        with get_db() as db:
            # Build related ORM objects from primitives
            director_objs = [
                self._get_or_create_person(db, Director, d) for d in directors
            ]
            genre_objs = [self._build_genre(db, g) for g in genres] if genres else []
            star_objs = [
                self._get_or_create_person(db, Star, s) for s in stars
            ] if stars else []

            # Build the movie -- all ORM construction in one place
            movie = Movie(
                title=title,
                year=year,
                runtime=runtime,
                director=director_objs,
                genres=genre_objs,
                stars=star_objs,
            )

            try:
                db.add(movie)
                db.commit()
            except IntegrityError as e:
                db.rollback()
                raise ConflictError(
                    "A film with this name, year and runtime already exists"
                ) from e
            except SQLAlchemyError as e:
                db.rollback()
                raise DatabaseError("Unable to store movie; reason unknown") from e

            db.refresh(movie)
            return {"title": movie.title, "year": movie.year, "runtime": movie.runtime}

    def update(
        self, title: str, year: int, runtime: int, updates: dict
    ) -> dict | None:
        """Update scalar attributes on an existing movie."""

        with get_db() as db:
            try:
                movie = db.execute(
                    select(Movie).where(
                        Movie.title == title,
                        Movie.year == year,
                        Movie.runtime == runtime,
                    )
                ).scalar_one_or_none()
            except SQLAlchemyError as e:
                raise DatabaseError(
                    "Update failed; error while looking up film"
                ) from e

            if movie is None:
                return None

            for attr, value in updates.items():
                if attr in _UPDATABLE_FIELDS:
                    setattr(movie, attr, value)

            try:
                db.commit()
            except SQLAlchemyError as e:
                db.rollback()
                raise ConflictError("Found movie but update failed") from e

            return {"title": movie.title, "year": movie.year, "runtime": movie.runtime}

    def delete(self, title: str, year: int, runtime: int) -> bool:
        """Delete a movie by its composite key."""

        with get_db() as db:
            try:
                movie = db.execute(
                    select(Movie).where(
                        Movie.title == title,
                        Movie.year == year,
                        Movie.runtime == runtime,
                    )
                ).scalar_one_or_none()
            except SQLAlchemyError as e:
                raise DatabaseError("Failed to look up movie for deletion") from e

            if movie is None:
                return False

            try:
                db.delete(movie)
                db.commit()
            except IntegrityError as e:
                db.rollback()
                raise ConflictError(
                    "Not able to delete movie, perhaps due to data restrictions"
                ) from e
            except SQLAlchemyError as e:
                db.rollback()
                raise DatabaseError("Failed to delete movie") from e

            return True
