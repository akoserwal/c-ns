"""
ORM Boundary Problem: Worked Examples
======================================

Run this file directly:  python examples-orm-boundary.py

Each section prints its output so you can see exactly what happens
at each layer boundary when relationships are involved.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import DeclarativeBase, Session, relationship


# =====================================================================
# SETUP: Pydantic DTOs and ORM tables for a Movie with Genres
# =====================================================================

# --- Pydantic (API boundary) ---

class GenreDTO(BaseModel):
    name: str

class MovieDTO(BaseModel):
    title: str
    year: int
    genres: list[GenreDTO] | None = None


# --- SQLAlchemy ORM (persistence boundary) ---

class Base(DeclarativeBase):
    pass

class MovieGenre(Base):
    __tablename__ = "movie_genre"
    movie_id = Column(Integer, ForeignKey("movie.id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.id"), primary_key=True)

class MovieORM(Base):
    __tablename__ = "movie"
    id    = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    year  = Column(Integer, nullable=False)
    genres = relationship("GenreORM", secondary="movie_genre", back_populates="movies")

class GenreORM(Base):
    __tablename__ = "genre"
    id   = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    movies = relationship("MovieORM", secondary="movie_genre", back_populates="genres")


def fresh_db():
    """Create a fresh in-memory database for each example."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


# =====================================================================
# EXAMPLE 1: The problem — model_dump() into ORM constructor
# =====================================================================

def example_1_the_problem():
    """
    What happens when you model_dump() a Pydantic object with
    relationships and try to pass it straight to the ORM.
    """
    print("=" * 60)
    print("EXAMPLE 1: The Problem")
    print("=" * 60)

    movie_dto = MovieDTO(
        title="Inception",
        year=2010,
        genres=[GenreDTO(name="Sci-Fi"), GenreDTO(name="Thriller")],
    )

    dumped = movie_dto.model_dump()
    print(f"\nmodel_dump() produces:\n{dumped}")
    print(f"\nType of genres[0]: {type(dumped['genres'][0])}")
    print("  --> It's a dict, not a GenreORM object.")

    engine = fresh_db()
    with Session(engine) as db:
        try:
            # This is what you'd want to do — but it fails
            movie = MovieORM(**dumped)
            db.add(movie)
            db.commit()
            print("\nResult: SUCCESS (this won't print)")
        except Exception as e:
            print(f"\nResult: FAILED --> {type(e).__name__}: {e}")
            print("\nSQLAlchemy cannot accept a dict where it expects")
            print("a GenreORM object. The relationship attribute requires")
            print("actual ORM instances.")

    # What SQLAlchemy actually needs:
    print("\n--- What SQLAlchemy needs instead ---")
    with Session(engine) as db:
        movie = MovieORM(
            title="Inception",
            year=2010,
            genres=[GenreORM(name="Sci-Fi"), GenreORM(name="Thriller")],
        )
        db.add(movie)
        db.commit()
        print(f"Saved: {movie.title} with {len(movie.genres)} genres")
        print("Each genre is a GenreORM instance, not a dict.\n")


# =====================================================================
# EXAMPLE 2: The reverse problem — ORM objects coming back out
# =====================================================================

def example_2_the_reverse():
    """
    When you query the ORM, relationship attributes contain
    ORM objects — not dicts. You can't return these to the
    service layer without leaking ORM knowledge.
    """
    print("=" * 60)
    print("EXAMPLE 2: The Reverse Problem")
    print("=" * 60)

    engine = fresh_db()
    with Session(engine) as db:
        movie = MovieORM(
            title="Inception",
            year=2010,
            genres=[GenreORM(name="Sci-Fi"), GenreORM(name="Thriller")],
        )
        db.add(movie)
        db.commit()

        # Query it back
        result = db.execute(select(MovieORM)).scalar_one()

        print(f"\nQueried movie: {result.title}")
        print(f"Type of result: {type(result)}")
        print(f"Type of result.genres[0]: {type(result.genres[0])}")
        print(f"  --> GenreORM object, not a dict or a string")

        # Can't pass this to Pydantic
        try:
            dto = MovieDTO(
                title=result.title,
                year=result.year,
                genres=result.genres,  # these are ORM objects
            )
            print(f"\nPydantic accepted ORM objects: {dto}")
        except Exception as e:
            print(f"\nPydantic validation: {type(e).__name__}")
            print("  --> Pydantic may or may not accept ORM objects")
            print("  --> Either way, you're leaking ORM into the service layer")

        # You must convert explicitly
        genres_as_dicts = [{"name": g.name} for g in result.genres]
        dto = MovieDTO(title=result.title, year=result.year, genres=genres_as_dicts)
        print(f"\nAfter explicit conversion: {dto}")
        print(f"Type of dto.genres[0]: {type(dto.genres[0])} -- clean Pydantic\n")


# =====================================================================
# EXAMPLE 3: Approach A — generic dict_to_orm / orm_to_dict
# =====================================================================

def dict_to_orm(model_cls, data: dict):
    """Generic converter using SQLAlchemy inspect()."""
    mapper = inspect(model_cls)
    obj = model_cls()
    for key, value in data.items():
        if key not in mapper.attrs:
            continue
        attr = mapper.attrs[key]
        if hasattr(attr, "mapper"):
            target_cls = attr.mapper.class_
            if isinstance(value, list):
                setattr(obj, key, [
                    dict_to_orm(target_cls, v) if isinstance(v, dict) else v
                    for v in value
                ])
            elif isinstance(value, dict):
                setattr(obj, key, dict_to_orm(target_cls, value))
            else:
                setattr(obj, key, value)
        else:
            setattr(obj, key, value)
    return obj


def orm_to_dict(obj, seen=None):
    """Generic converter with cycle detection."""
    if seen is None:
        seen = set()
    if id(obj) in seen:
        return None
    seen.add(id(obj))
    mapper = inspect(obj).mapper
    result = {}
    for col in mapper.columns:
        result[col.key] = getattr(obj, col.key)
    for name, rel in mapper.relationships.items():
        value = getattr(obj, name)
        if value is None:
            result[name] = None
        elif rel.uselist:
            result[name] = [orm_to_dict(child, seen) for child in value]
        else:
            result[name] = orm_to_dict(value, seen)
    return result


def example_3_generic_converter():
    """
    The generic reflection approach: dict_to_orm and orm_to_dict.
    Works, but has a critical limitation with duplicates.
    """
    print("=" * 60)
    print("EXAMPLE 3: Generic Converter (dict_to_orm / orm_to_dict)")
    print("=" * 60)

    engine = fresh_db()

    movie_dto = MovieDTO(
        title="Inception", year=2010,
        genres=[GenreDTO(name="Sci-Fi"), GenreDTO(name="Thriller")],
    )
    data = movie_dto.model_dump()

    # --- Save ---
    with Session(engine) as db:
        movie_orm = dict_to_orm(MovieORM, data)
        print(f"\ndict_to_orm produced: {type(movie_orm).__name__}")
        print(f"  genres: {[type(g).__name__ for g in movie_orm.genres]}")
        db.add(movie_orm)
        db.commit()
        print(f"  Saved successfully: {movie_orm.title}")

    # --- Read back ---
    with Session(engine) as db:
        movie = db.execute(select(MovieORM)).scalar_one()
        result = orm_to_dict(movie)
        print(f"\norm_to_dict produced:\n  {result}")
        # Note: 'movies' back-reference on Genre shows up as None (cycle detection)

    # --- The duplicate problem ---
    print("\n--- Duplicate problem ---")
    movie2_dto = MovieDTO(
        title="Interstellar", year=2014,
        genres=[GenreDTO(name="Sci-Fi")],  # "Sci-Fi" already exists!
    )
    data2 = movie2_dto.model_dump()

    with Session(engine) as db:
        movie2_orm = dict_to_orm(MovieORM, data2)
        db.add(movie2_orm)
        try:
            db.commit()
            print("Saved second movie with shared genre: SUCCESS")
        except IntegrityError:
            db.rollback()
            print("FAILED: IntegrityError -- 'Sci-Fi' genre already exists!")
            print("dict_to_orm always creates NEW ORM objects.")
            print("It doesn't check if the genre already exists in the DB.\n")


# =====================================================================
# EXAMPLE 4: Approach B — explicit primitives (best practice)
# =====================================================================

def example_4_explicit_primitives():
    """
    The best practice: repo accepts primitives, builds ORM internally,
    uses get-or-create for shared entities.
    """
    print("=" * 60)
    print("EXAMPLE 4: Explicit Primitives (Best Practice)")
    print("=" * 60)

    engine = fresh_db()

    # --- The repo ---
    class MovieRepo:

        def __init__(self, engine):
            self._engine = engine

        def _get_or_create_genre(self, db: Session, name: str) -> GenreORM:
            """Check DB first. Create only if missing."""
            existing = db.execute(
                select(GenreORM).where(GenreORM.name == name)
            ).scalar_one_or_none()
            if existing:
                print(f"    Genre '{name}' already exists, reusing it")
                return existing
            print(f"    Genre '{name}' is new, creating it")
            return GenreORM(name=name)

        def _movie_to_dict(self, movie: MovieORM, full: bool = False) -> dict:
            result = {"title": movie.title, "year": movie.year}
            if full:
                result["genres"] = [{"name": g.name} for g in movie.genres]
            return result

        def create(
            self,
            title: str,
            year: int,
            genre_names: list[str] | None = None,
        ) -> dict:
            """Accepts primitives only. Builds ORM objects here."""
            with Session(self._engine) as db:
                genres = [
                    self._get_or_create_genre(db, name)
                    for name in (genre_names or [])
                ]
                movie = MovieORM(title=title, year=year, genres=genres)
                db.add(movie)
                db.commit()
                return {"title": movie.title, "year": movie.year}

        def select(self, title: str, full: bool = False) -> dict | None:
            """Returns a plain dict, never an ORM object."""
            with Session(self._engine) as db:
                movie = db.execute(
                    select(MovieORM).where(MovieORM.title == title)
                ).scalar_one_or_none()
                if movie is None:
                    return None
                return self._movie_to_dict(movie, full=full)

    # --- The service ---
    class MovieService:

        def __init__(self, repo: MovieRepo):
            self._repo = repo

        def save_film(self, movie: MovieDTO) -> dict:
            # Decompose DTO into primitives
            genre_names = [g.name for g in movie.genres] if movie.genres else None
            return self._repo.create(
                title=movie.title,
                year=movie.year,
                genre_names=genre_names,
            )

        def get_film(self, title: str) -> MovieDTO | None:
            result = self._repo.select(title, full=True)
            if result is None:
                return None
            return MovieDTO(**result)

    # --- Run it ---
    repo = MovieRepo(engine)
    svc = MovieService(repo)

    print("\n--- Save first movie ---")
    movie1 = MovieDTO(
        title="Inception", year=2010,
        genres=[GenreDTO(name="Sci-Fi"), GenreDTO(name="Thriller")],
    )
    result1 = svc.save_film(movie1)
    print(f"  Saved: {result1}")

    print("\n--- Save second movie sharing 'Sci-Fi' ---")
    movie2 = MovieDTO(
        title="Interstellar", year=2014,
        genres=[GenreDTO(name="Sci-Fi"), GenreDTO(name="Drama")],
    )
    result2 = svc.save_film(movie2)
    print(f"  Saved: {result2}")
    print("  No IntegrityError! Get-or-create handled it.")

    print("\n--- Read back with full details ---")
    fetched = svc.get_film("Inception")
    print(f"  {fetched}")
    print(f"  Type: {type(fetched).__name__} -- clean Pydantic DTO")

    fetched2 = svc.get_film("Interstellar")
    print(f"  {fetched2}")

    # --- Verify what crossed each boundary ---
    print("\n--- What crossed each boundary ---")
    print("  API --> Service:  MovieDTO (Pydantic)")
    print("  Service --> Repo: title='Inception', year=2010, genre_names=['Sci-Fi', 'Thriller']")
    print("  Repo internally:  GenreORM(name='Sci-Fi'), MovieORM(title=..., genres=[GenreORM, ...])")
    print("  Repo --> Service: {'title': 'Inception', 'year': 2010, 'genres': [{'name': 'Sci-Fi'}, ...]}")
    print("  Service --> API:  MovieDTO (Pydantic)\n")


# =====================================================================
# EXAMPLE 5: Side-by-side — what each layer sees
# =====================================================================

def example_5_layer_trace():
    """
    Trace a single save operation showing exactly what data
    looks like at each layer boundary.
    """
    print("=" * 60)
    print("EXAMPLE 5: Layer-by-Layer Trace")
    print("=" * 60)

    movie = MovieDTO(
        title="The Matrix", year=1999,
        genres=[GenreDTO(name="Sci-Fi"), GenreDTO(name="Action")],
    )

    print("\n[1] API layer receives validated Pydantic DTO:")
    print(f"    type  = {type(movie).__name__}")
    print(f"    value = {movie}")
    print(f"    movie.genres[0] is GenreDTO: {isinstance(movie.genres[0], GenreDTO)}")

    print("\n[2] Service decomposes into primitives:")
    title = movie.title
    year = movie.year
    genre_names = [g.name for g in movie.genres]
    print(f"    title       = {title!r}  (str)")
    print(f"    year        = {year!r}  (int)")
    print(f"    genre_names = {genre_names!r}  (list[str])")
    print(f"    No Pydantic objects cross this line.")

    print("\n[3] Repo builds ORM objects from primitives:")
    engine = fresh_db()
    with Session(engine) as db:
        genre_objs = [GenreORM(name=n) for n in genre_names]
        movie_orm = MovieORM(title=title, year=year, genres=genre_objs)
        print(f"    movie_orm type   = {type(movie_orm).__name__}")
        print(f"    genres[0] type   = {type(movie_orm.genres[0]).__name__}")
        print(f"    genres[0].name   = {movie_orm.genres[0].name!r}")

        db.add(movie_orm)
        db.commit()
        print(f"    Committed to DB.")

    print("\n[4] Repo converts ORM back to dict for return:")
    with Session(engine) as db:
        loaded = db.execute(select(MovieORM)).scalar_one()
        result_dict = {
            "title": loaded.title,
            "year": loaded.year,
            "genres": [{"name": g.name} for g in loaded.genres],
        }
        print(f"    {result_dict}")
        print(f"    type = dict  (no ORM objects)")

    print("\n[5] Service wraps dict back into Pydantic DTO:")
    returned = MovieDTO(**result_dict)
    print(f"    {returned}")
    print(f"    type = {type(returned).__name__}  (clean Pydantic)")
    print()


# =====================================================================
# RUN ALL EXAMPLES
# =====================================================================

if __name__ == "__main__":
    example_1_the_problem()
    example_2_the_reverse()
    example_3_generic_converter()
    example_4_explicit_primitives()
    example_5_layer_trace()
