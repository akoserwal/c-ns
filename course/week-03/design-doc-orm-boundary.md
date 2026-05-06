# Design Document: ORM Relationship Conversion in Clean Architecture

**Status:** Reference  
**Domain:** Movielook -- movie catalog service (Week 3 lab)  
**Problem area:** Converting between Pydantic DTOs and SQLAlchemy ORM objects when relationship attributes (many-to-many, one-to-many) are present

---

## 1. Context

We are building a movie catalog API with FastAPI. The data model has a central `Movie` entity with three many-to-many relationships:

```
Movie  ──M:N──  Director    (via movie_dir junction table)
Movie  ──M:N──  Genre       (via movie_genre junction table)
Movie  ──M:N──  Star        (via movie_star junction table)
```

The course exercise imposes a clean architecture constraint:

- **Pydantic** must not appear deeper than the service layer
- **SQLAlchemy ORM objects** must not appear above the repository layer

This means the service and repository communicate using only **primitives, plain dicts, and lists**.

---

## 2. The Problem

### 2.1 Flat data works out of the box

For a movie with no relationships, the conversion is trivial:

```python
# Service layer: Pydantic --> dict
movie_dict = movie_pydantic.model_dump()
# {"title": "Inception", "year": 2010, "runtime": 148}

# Repo layer: dict --> ORM
movie_orm = MovieORM(**movie_dict)   # works fine
db.add(movie_orm)
```

### 2.2 Relationships break it

When a Pydantic model contains nested objects (director, genres, stars), `model_dump()` produces nested dicts:

```python
movie_pydantic.model_dump()
# {
#     "title": "Inception",
#     "year": 2010,
#     "runtime": 148,
#     "director": [{"name": "Christopher", "middle_name": None, "surname": "Nolan"}],
#     "genres": [{"name": "Sci-Fi"}, {"name": "Thriller"}],
#     "stars": [{"name": "Leonardo", "middle_name": None, "surname": "DiCaprio"}]
# }
```

Passing this to the ORM constructor fails:

```python
MovieORM(**movie_dict)
# AttributeError: 'dict' object has no attribute '_sa_instance_state'
```

SQLAlchemy relationship attributes require **managed ORM instances**, not dicts. It needs:

```python
MovieORM(
    title="Inception", year=2010, runtime=148,
    director=[DirectorORM(name="Christopher", surname="Nolan")],
    genres=[GenreORM(name="Sci-Fi"), GenreORM(name="Thriller")],
)
```

### 2.3 The reverse is the same problem

When querying, SQLAlchemy returns ORM objects whose relationship attributes contain other ORM objects:

```python
movie = db.execute(select(MovieORM)).scalar_one()
type(movie.genres[0])   # <class 'GenreORM'> -- not a dict
```

Returning this directly to the service layer leaks ORM into a layer that should not know about it.

### 2.4 Why this is not a bug or a weakness

This is the **inherent cost of enforcing a clean layer boundary**. Any ORM that manages object identity and relationships (SQLAlchemy, Django ORM, Hibernate, ActiveRecord) has the same requirement. The ORM tracks which objects belong to which session, manages lazy loading, and handles cascading saves -- all of which require actual managed instances, not raw data.

The conversion must happen somewhere. The design question is: **where and how.**

---

## 3. Approaches Considered

### 3.1 Hard-coded conversion per model

Pop each relationship key from the dict, construct ORM objects inline:

```python
def save(self, data: dict):
    directors = [DirectorORM(**d) for d in data.pop("director", [])]
    genres    = [GenreORM(**g) for g in data.pop("genres", [])]
    stars     = [StarORM(**s) for s in data.pop("stars", [])]
    movie = MovieORM(**data, director=directors, genres=genres, stars=stars)
```

**Rejected.** Every new relationship requires new conversion code in every method. Easy to forget. Duplicated in both directions. Does not handle get-or-create for shared entities.

### 3.2 Generic reflection-based converter

Use `sqlalchemy.inspection.inspect()` to discover columns and relationships at runtime, recursively converting dicts to ORM objects and back:

```python
def dict_to_orm(model_cls, data: dict):
    mapper = inspect(model_cls)
    obj = model_cls()
    for key, value in data.items():
        attr = mapper.attrs.get(key)
        if attr and hasattr(attr, "mapper"):        # relationship
            target_cls = attr.mapper.class_
            setattr(obj, key, [dict_to_orm(target_cls, v) for v in value])
        elif attr:                                   # column
            setattr(obj, key, value)
    return obj
```

**Viable as a stepping stone.** Works for any model without modification. But:

- Always creates **new** ORM instances. A second movie with genre "Sci-Fi" causes `IntegrityError` because `dict_to_orm` creates a second `GenreORM(name="Sci-Fi")` instead of reusing the existing row.
- The repo interface is `save(data: dict)` -- opaque. Callers cannot tell what shape the dict must have.
- Cycle detection in `orm_to_dict` drops back-references as `None`, which may strip wanted data.
- Uses runtime reflection, which is harder to debug and invisible to type checkers.

### 3.3 Explicit primitives interface with DTO decomposition

The service decomposes each DTO into typed primitives. The repo interface declares exactly what it accepts. The repo implementation builds ORM objects internally with full control.

**Adopted.** Detailed below.

---

## 4. Solution: Clean Architecture with Explicit Boundaries

### 4.1 Architecture overview

```
                    ┌─────────────────────────────────┐
                    │          API / Router            │
                    │  (FastAPI, receives JSON,        │
                    │   validates via Pydantic DTOs)   │
                    └──────────────┬──────────────────┘
                                   │
                         MovieDTO (Pydantic)
                                   │
                    ┌──────────────▼──────────────────┐
                    │        Service Layer             │
                    │  (MovieService)                  │
                    │                                  │
                    │  Accepts: Pydantic DTOs          │
                    │  Returns: Pydantic DTOs          │
                    │  Decomposes DTOs into primitives  │
                    │  before calling repo              │
                    └──────────────┬──────────────────┘
                                   │
                    str, int, list[str], list[dict]
                       (no Pydantic, no ORM)
                                   │
                    ┌──────────────▼──────────────────┐
                    │     Repository Interface         │
                    │  (MovieRepo Protocol)            │
                    │                                  │
                    │  Contract: primitives in,         │
                    │            dicts out              │
                    └──────────────┬──────────────────┘
                                   │
                      Implemented by SQLArepo
                      (or InMemoryRepo for tests)
                                   │
                    ┌──────────────▼──────────────────┐
                    │     ORM Implementation           │
                    │  (SQLArepo)                      │
                    │                                  │
                    │  Builds ORM objects from          │
                    │  primitives (get-or-create)       │
                    │  Converts ORM objects back to     │
                    │  dicts before returning           │
                    │  Session stays inside this layer  │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │         Database                 │
                    │  (SQLite via SQLAlchemy engine)   │
                    └─────────────────────────────────┘
```

### 4.2 Boundary rules

| Boundary | What crosses | What does NOT cross |
|----------|-------------|---------------------|
| API --> Service | Pydantic DTOs (`Movie`, `Release`, `Person`, `Genre`) | raw JSON, HTTP objects |
| Service --> Repo | `str`, `int`, `bool`, `list[str]`, `list[dict]` | Pydantic models, ORM objects |
| Repo --> Service | `dict`, `None`, `bool` | ORM objects |
| Repo --> DB | ORM objects, SQLAlchemy Session | dicts, primitives |

The critical boundary is **Service --> Repo**. This is where the DTO decomposition happens.

### 4.3 Layer implementations

#### DTOs (`film.py`)

Pydantic models that validate input. They are the **only** place Pydantic appears.

```python
class Release(BaseModel):
    """Identity of a movie -- used for lookups."""
    title: str = Field(min_length=1, max_length=200)
    year: int  = Field(ge=1888, le=datetime.now().year + 1)
    runtime: int = Field(ge=1, le=1000)

class Person(BaseModel):
    """A person's name, used for directors and stars."""
    name: str
    middle_name: str | None = None
    surname: str | None = None

class Genre(BaseModel):
    name: str

class Movie(Release):
    """Full movie data including relationships."""
    director: list[Person] = Field(min_length=1)
    genres: list[Genre] | None = None
    stars: list[Person] | None = None
```

#### Repository interface (`db/repository.py`)

A Protocol that defines the persistence contract using only primitives:

```python
class MovieRepo(Protocol):

    def select(
        self, title: str, year: int, runtime: int, full: bool = False
    ) -> dict | None: ...

    def create(
        self,
        title: str,
        year: int,
        runtime: int,
        directors: list[dict],
        genres: list[str] | None = None,
        stars: list[dict] | None = None,
    ) -> dict: ...

    def update(
        self, title: str, year: int, runtime: int, updates: dict
    ) -> dict | None: ...

    def delete(self, title: str, year: int, runtime: int) -> bool: ...
```

Key design decisions:

- **`directors` is `list[dict]`** because a person has multiple fields (name, middle_name, surname). A dict is the simplest container that doesn't require importing anything.
- **`genres` is `list[str]`** because a genre is just a name. No need for a dict wrapper.
- **Returns `dict`**, not a DTO. The service wraps the dict back into Pydantic on the way out.
- **Protocol, not ABC.** Structural typing: any class with matching signatures satisfies it. No import dependency from the fake repo to the persistence layer.

#### Service layer (`db/service.py`)

Accepts Pydantic DTOs. Decomposes them. Calls the repo with primitives. Re-wraps the result.

```python
class MovieService:

    def __init__(self, repo: MovieRepo):
        self._repo = repo

    def save_film(self, movie: Movie) -> dict:
        # Decompose the DTO into primitives for the repo
        directors = [d.model_dump() for d in movie.director]
        genres    = [g.name for g in movie.genres] if movie.genres else None
        stars     = [s.model_dump() for s in movie.stars] if movie.stars else None

        return self._repo.create(
            title=movie.title,
            year=movie.year,
            runtime=movie.runtime,
            directors=directors,
            genres=genres,
            stars=stars,
        )

    def select_film(self, movie: Release, full: bool = False) -> Movie | None:
        result = self._repo.select(movie.title, movie.year, movie.runtime, full)
        if result is None:
            return None
        return Movie(**result)
```

**Critical pattern:** `model_dump()` is called on each nested DTO individually (`d.model_dump()` per director), not on the entire `Movie`. This gives the service explicit control. Genres are reduced to bare strings (`g.name`) because that is all the repo needs.

#### ORM implementation (`db/SQLA/methods.py`)

The only layer that imports ORM classes. Builds ORM objects from primitives using private helpers. Converts ORM objects to dicts before returning.

```python
class SQLArepo:

    # -- Private: build ORM objects from primitives --

    @staticmethod
    def _build_director(db, person: dict) -> DirectorORM:
        """Get-or-create pattern."""
        existing = db.execute(
            select(DirectorORM).where(
                DirectorORM.name == person["name"],
                DirectorORM.surname == person.get("surname"),
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        return DirectorORM(
            name=person["name"],
            middle_name=person.get("middle_name"),
            surname=person.get("surname"),
        )

    @staticmethod
    def _build_genre(db, name: str) -> GenreORM:
        """Get-or-create pattern."""
        existing = db.execute(
            select(GenreORM).where(GenreORM.name == name)
        ).scalar_one_or_none()
        if existing:
            return existing
        return GenreORM(name=name)

    # -- Private: convert ORM objects to dicts --

    @staticmethod
    def _person_to_dict(person) -> dict:
        return {
            "name": person.name,
            "middle_name": person.middle_name,
            "surname": person.surname,
        }

    @staticmethod
    def _movie_to_dict(movie, full=False) -> dict:
        result = {"title": movie.title, "year": movie.year, "runtime": movie.runtime}
        if full:
            result["director"] = [SQLArepo._person_to_dict(d) for d in movie.director]
            result["genres"]   = [{"name": g.name} for g in movie.genres]
            result["stars"]    = [SQLArepo._person_to_dict(s) for s in movie.stars]
        return result

    # -- Public: implements MovieRepo Protocol --

    def create(self, title, year, runtime, directors, genres=None, stars=None):
        with get_db() as db:
            director_objs = [self._build_director(db, d) for d in directors]
            genre_objs    = [self._build_genre(db, g) for g in genres] if genres else []
            star_objs     = [self._build_star(db, s) for s in stars] if stars else []

            movie = MovieORM(
                title=title, year=year, runtime=runtime,
                director=director_objs, genres=genre_objs, stars=star_objs,
            )
            db.add(movie)
            db.commit()
            return {"title": movie.title, "year": movie.year, "runtime": movie.runtime}

    def select(self, title, year, runtime, full=False):
        with get_db() as db:
            query = select(MovieORM).where(
                MovieORM.title == title,
                MovieORM.year == year,
                MovieORM.runtime == runtime,
            )
            if full:
                query = query.options(
                    selectinload(MovieORM.director),
                    selectinload(MovieORM.genres),
                    selectinload(MovieORM.stars),
                )
            movie = db.execute(query).scalar_one_or_none()
            if movie is None:
                return None
            return self._movie_to_dict(movie, full=full)
```

---

## 5. Data Flow Diagrams

### 5.1 Write path: saving a movie

```
     POST /movies  {"title": "Inception", "year": 2010, ...}
            │
     ┌──────▼──────────────────────────────────────────────────────────────┐
     │  API layer                                                         │
     │  Pydantic validates JSON --> Movie DTO                             │
     │  movie = Movie(title="Inception", year=2010, runtime=148,          │
     │                director=[Person(name="Christopher",                 │
     │                                 surname="Nolan")],                  │
     │                genres=[Genre(name="Sci-Fi"),                        │
     │                        Genre(name="Thriller")])                     │
     └──────┬──────────────────────────────────────────────────────────────┘
            │  Movie DTO (Pydantic)
     ┌──────▼──────────────────────────────────────────────────────────────┐
     │  Service layer                                                     │
     │                                                                    │
     │  Decomposes the DTO into primitives:                               │
     │    directors = [{"name": "Christopher",                            │
     │                  "middle_name": None,                               │
     │                  "surname": "Nolan"}]                               │
     │    genres    = ["Sci-Fi", "Thriller"]                               │
     │    stars     = None                                                 │
     │                                                                    │
     │  Calls: repo.create(title="Inception", year=2010, runtime=148,     │
     │                      directors=[...], genres=[...], stars=None)     │
     └──────┬──────────────────────────────────────────────────────────────┘
            │  str, int, list[dict], list[str]
     ┌──────▼──────────────────────────────────────────────────────────────┐
     │  Repository (SQLArepo)                                             │
     │                                                                    │
     │  Builds ORM objects from primitives:                               │
     │    _build_director(db, {"name":"Christopher", ...})                │
     │      --> SELECT director WHERE name='Christopher'                  │
     │          AND surname='Nolan'                                       │
     │      --> not found --> DirectorORM(name="Christopher",             │
     │                                    surname="Nolan")                │
     │    _build_genre(db, "Sci-Fi")                                      │
     │      --> SELECT genre WHERE name='Sci-Fi'                          │
     │      --> not found --> GenreORM(name="Sci-Fi")                     │
     │    _build_genre(db, "Thriller")                                    │
     │      --> SELECT genre WHERE name='Thriller'                        │
     │      --> not found --> GenreORM(name="Thriller")                   │
     │                                                                    │
     │  Assembles: MovieORM(title="Inception", year=2010, runtime=148,   │
     │                       director=[DirectorORM],                      │
     │                       genres=[GenreORM, GenreORM])                 │
     │  db.add(movie)                                                     │
     │  db.commit()                                                       │
     │                                                                    │
     │  Returns: {"title": "Inception", "year": 2010, "runtime": 148}    │
     └──────┬──────────────────────────────────────────────────────────────┘
            │  dict
     ┌──────▼──────────────────────────────────────────────────────────────┐
     │  Database                                                          │
     │                                                                    │
     │  Rows created:                                                     │
     │    movie:       ("Inception", 2010, 148)                           │
     │    director:    (1, "Christopher", None, "Nolan")                  │
     │    genre:       ("Sci-Fi"), ("Thriller")                           │
     │    movie_dir:   ("Inception", 2010, 148, 1)                        │
     │    movie_genre: ("Inception", 2010, 148, "Sci-Fi")                │
     │    movie_genre: ("Inception", 2010, 148, "Thriller")              │
     └────────────────────────────────────────────────────────────────────┘
```

### 5.2 Write path with shared entity: second movie reuses "Sci-Fi"

```
     repo.create(title="Interstellar", year=2014, runtime=169,
                 directors=[{"name": "Christopher", "surname": "Nolan"}],
                 genres=["Sci-Fi", "Drama"], stars=None)

     _build_director(db, {"name": "Christopher", "surname": "Nolan"})
       --> SELECT ... WHERE name='Christopher' AND surname='Nolan'
       --> FOUND (id=1) --> reuse existing DirectorORM     <-- no duplicate

     _build_genre(db, "Sci-Fi")
       --> SELECT ... WHERE name='Sci-Fi'
       --> FOUND --> reuse existing GenreORM                <-- no duplicate

     _build_genre(db, "Drama")
       --> SELECT ... WHERE name='Drama'
       --> NOT FOUND --> create new GenreORM(name="Drama")

     MovieORM(title="Interstellar", ...,
              director=[existing DirectorORM],
              genres=[existing GenreORM("Sci-Fi"), new GenreORM("Drama")])

     db.add(movie) --> db.commit() --> no IntegrityError
```

Without get-or-create (`dict_to_orm` approach), this would fail:

```
     dict_to_orm creates GenreORM(name="Sci-Fi")  -- a NEW instance
     db.add(movie)
     db.commit()
     --> IntegrityError: UNIQUE constraint failed: genre.name
```

### 5.3 Read path: looking up a movie

```
     ┌────────────────────────────────────────────────────────────────────┐
     │  Service layer                                                    │
     │  svc.select_film(Release(title="Inception", year=2010,           │
     │                          runtime=148), full=True)                  │
     │                                                                   │
     │  Calls: repo.select("Inception", 2010, 148, full=True)           │
     └──────┬────────────────────────────────────────────────────────────┘
            │  str, int, bool
     ┌──────▼────────────────────────────────────────────────────────────┐
     │  Repository (SQLArepo)                                            │
     │                                                                   │
     │  Executes:                                                        │
     │    SELECT movie.* FROM movie                                      │
     │    WHERE title='Inception' AND year=2010 AND runtime=148          │
     │    + selectinload(director, genres, stars)                         │
     │                                                                   │
     │  Gets back: MovieORM object                                       │
     │    .title = "Inception"                                           │
     │    .director = [DirectorORM(name="Christopher", ...)]             │
     │    .genres = [GenreORM(name="Sci-Fi"), GenreORM(name="Thriller")] │
     │                                                                   │
     │  Converts via _movie_to_dict(movie, full=True):                   │
     │    {"title": "Inception", "year": 2010, "runtime": 148,           │
     │     "director": [{"name": "Christopher", "middle_name": None,     │
     │                   "surname": "Nolan"}],                           │
     │     "genres": [{"name": "Sci-Fi"}, {"name": "Thriller"}],         │
     │     "stars": []}                                                  │
     └──────┬────────────────────────────────────────────────────────────┘
            │  dict (plain, no ORM objects)
     ┌──────▼────────────────────────────────────────────────────────────┐
     │  Service layer                                                    │
     │                                                                   │
     │  Wraps: Movie(**result)                                           │
     │  Returns: Movie(title="Inception", year=2010, runtime=148,        │
     │                 director=[Person(name="Christopher",               │
     │                                  surname="Nolan")],               │
     │                 genres=[Genre(name="Sci-Fi"),                      │
     │                         Genre(name="Thriller")])                  │
     └────────────────────────────────────────────────────────────────────┘
```

---

## 6. Why This Design Solves Each Problem

| Problem | How it is solved |
|---------|-----------------|
| `model_dump()` produces nested dicts that ORM rejects | Service decomposes DTOs into primitives; repo builds ORM objects from those primitives |
| ORM objects leak into service layer on read | Repo converts ORM to plain dicts via `_movie_to_dict` before returning |
| `IntegrityError` when saving shared entities (Genre "Sci-Fi" exists) | Repo uses get-or-create (`_build_genre`) to reuse existing rows |
| Repo interface is opaque (`save(data: dict)`) | Protocol declares typed parameters: `create(title: str, year: int, ..., genres: list[str])` |
| Bidirectional relationships cause infinite recursion in serialization | No reflection. `_movie_to_dict` explicitly picks which attributes to include |
| Service layer tightly coupled to ORM | Service depends on Protocol, not on SQLArepo. Tests use InMemoryRepo |
| ORM objects used outside their session scope cause `DetachedInstanceError` | All ORM work stays inside `with get_db() as db:`. Only plain dicts leave the block |

---

## 7. Trade-offs and Alternatives

### 7.1 More verbose repo signatures

The explicit interface means `create()` has 6 parameters instead of 1. For models with many relationships, signatures get wide.

**Mitigation:** Group related parameters into a `TypedDict` if the parameter count becomes unwieldy:

```python
class CreateMovieParams(TypedDict):
    title: str
    year: int
    runtime: int
    directors: list[dict]
    genres: list[str] | None
    stars: list[dict] | None

class MovieRepo(Protocol):
    def create(self, params: CreateMovieParams) -> dict: ...
```

This keeps the interface explicit (typed keys) while reducing parameter count.

### 7.2 Conversion code per entity

Each entity (Director, Genre, Star) needs a `_build_*` method and a `_*_to_dict` method. This is more code than the generic `dict_to_orm`.

**Why it's worth it:**
- Each method is 5-10 lines, readable, debuggable
- Get-or-create logic differs per entity (Genre matches on name; Director matches on name + surname)
- New relationships are rare; when they happen, a new method is a small cost for clear behavior

### 7.3 When generic conversion is acceptable

The generic `dict_to_orm` / `orm_to_dict` approach is fine when:
- The schema is stable and unlikely to have shared entities
- It's a learning project or prototype
- You don't need get-or-create behavior
- You accept the opaque dict interface

It is a valid stepping stone toward the explicit approach.

---

## 8. Testing Strategy

### 8.1 Service tests use a fake repo

Because the Protocol accepts only primitives, the fake repo is a plain dict store:

```python
class InMemoryMovieRepo:
    def __init__(self):
        self._movies = {}

    def create(self, title, year, runtime, directors, genres=None, stars=None):
        key = (title, year, runtime)
        self._movies[key] = {
            "title": title, "year": year, "runtime": runtime,
            "director": directors,
            "genres": [{"name": g} for g in (genres or [])],
            "stars": stars or [],
        }
        return {"title": title, "year": year, "runtime": runtime}

    def select(self, title, year, runtime, full=False):
        movie = self._movies.get((title, year, runtime))
        if movie is None:
            return None
        if full:
            return movie
        return {"title": title, "year": year, "runtime": runtime}
```

```python
def test_save_and_select():
    svc = MovieService(InMemoryMovieRepo())
    svc.save_film(Movie(
        title="Inception", year=2010, runtime=148,
        director=[Person(name="Christopher", surname="Nolan")],
        genres=[Genre(name="Sci-Fi")],
    ))
    result = svc.select_film(
        Release(title="Inception", year=2010, runtime=148), full=True
    )
    assert result.title == "Inception"
    assert result.director[0].surname == "Nolan"
    assert result.genres[0].name == "Sci-Fi"
```

No database, no ORM, no SQLAlchemy imports. Tests run in milliseconds.

### 8.2 Repo tests use a real database

The SQLArepo itself is tested with an in-memory SQLite database to verify ORM behavior, get-or-create logic, and error handling:

```python
def test_create_reuses_existing_genre():
    repo = SQLArepo(engine=create_engine("sqlite:///:memory:"))
    repo.create("Inception", 2010, 148,
                directors=[{"name": "Nolan"}], genres=["Sci-Fi"])
    repo.create("Interstellar", 2014, 169,
                directors=[{"name": "Nolan"}], genres=["Sci-Fi", "Drama"])
    # No IntegrityError -- "Sci-Fi" was reused, not duplicated
```

---

## 9. File Layout

```
lab/
  film.py                     # Pydantic DTOs
  movielook.py                # FastAPI app / entry point
  db/
    __init__.py
    errors.py                 # ConflictError, DatabaseError
    repository.py             # MovieRepo Protocol
    service.py                # MovieService (decomposes DTOs)
    SQLA/
      __init__.py
      setup.py                # Engine, session factory
      tables.py               # ORM table classes
      methods.py              # SQLArepo (implements Protocol)
```

**Dependency direction:**

```
film.py  <--  service.py  -->  repository.py (Protocol)
                                     ^
                                     |
                               methods.py (implements Protocol)
                                     |
                                     v
                               tables.py, setup.py
```

The service depends on the Protocol (interface), not on the SQLAlchemy implementation. The implementation depends on the Protocol. This is the **Dependency Inversion Principle**: both layers depend on the abstraction, not on each other.

---

## 10. Summary

The ORM boundary conversion problem arises whenever a clean architecture separates DTOs from ORM objects and the data model includes relationships. The solution is:

1. **Decompose DTOs into primitives in the service layer** -- don't pass `model_dump()` as a blob
2. **Declare an explicit repo interface** -- typed parameters, not opaque dicts
3. **Build ORM objects inside the repo** -- private helpers with get-or-create logic
4. **Convert ORM objects to dicts before returning** -- explicit attribute access, not reflection
5. **Scope the session to the repo** -- no ORM object escapes the `with` block

The conversion is unavoidable. Clean architecture means paying for it at the boundary. The design choice is whether that payment is a generic utility (less code, less control) or explicit per-method logic (more code, full control). Production systems converge toward the explicit approach because real-world entities have per-entity logic (matching rules, deduplication, conditional creation) that a generic converter cannot express.
