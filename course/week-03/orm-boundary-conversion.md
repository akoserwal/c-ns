# The ORM Boundary Problem: Converting Dicts to ORM Objects with Relationships

## The Problem

In a layered architecture, we enforce clean boundaries:

```
API layer  -->  Service layer  -->  Repository (ORM) layer  -->  Database
 Pydantic        dicts/primitives       ORM objects              SQL rows
```

The rule: **Pydantic doesn't leak below the service layer. ORM objects don't leak above the repo layer.** The two layers communicate via plain dicts and primitives.

For flat data this is trivial:

```python
# Service layer
movie_dict = movie_pydantic.model_dump()
repo.save(movie_dict)

# Repo layer
movie_orm = Movie(**movie_dict)     # works fine for columns
db.add(movie_orm)
```

But our Movie has **relationships** --- directors, genres, stars:

```python
# What model_dump() produces:
{
    "title": "Inception",
    "year": 2010,
    "runtime": 148,
    "director": [{"name": "Christopher", "surname": "Nolan"}],
    "genres": [{"name": "Sci-Fi"}, {"name": "Thriller"}],
    "stars": [{"name": "Leonardo", "surname": "DiCaprio"}]
}
```

If you try `Movie(**movie_dict)`, SQLAlchemy will choke. The `director`, `genres`, and `stars` attributes expect **ORM objects**, not dicts. SQLAlchemy needs this:

```python
Movie(
    title="Inception",
    year=2010,
    runtime=148,
    director=[Director(name="Christopher", surname="Nolan")],
    genres=[Genre(name="Sci-Fi"), Genre(name="Thriller")],
    stars=[Star(name="Leonardo", surname="DiCaprio")],
)
```

The same problem exists in reverse: when reading, the ORM hands back objects with relationship attributes full of other ORM objects. You need to flatten everything back to dicts before returning to the service layer.

**This is not a SQLAlchemy weakness.** It is the inherent cost of enforcing a clean layer boundary. Any ORM that manages object graphs (Django ORM, Hibernate, ActiveRecord) has the same requirement: relationship data must be expressed as managed objects, not raw data.

---

## Three Approaches (with trade-offs)

### Approach 1: Hard-coded conversion per model (Don't)

```python
# In the repo layer
def save(self, data: dict):
    directors = [Director(**d) for d in data.pop("director", [])]
    genres = [Genre(**g) for g in data.pop("genres", [])]
    stars = [Star(**s) for s in data.pop("stars", [])]
    movie = Movie(**data, director=directors, genres=genres, stars=stars)
    db.add(movie)
```

**Why this is bad:**
- Every new relationship = new conversion code in every method
- Easy to forget one when the schema changes
- Duplicated in both directions (packing and unpacking)
- Doesn't scale: a model with 6 relationships means 12+ lines of boilerplate per operation

### Approach 2: Generic reflection-based converter (Stepping stone)

This is what the original `utility.py` functions did. They use `sqlalchemy.inspection.inspect()` to discover relationships at runtime and recursively build or flatten ORM objects.

**Good for learning.** But limited: always creates new ORM instances (no get-or-create), the repo interface is an opaque `dict`, and cycle detection can strip data.

### Approach 3: Explicit primitives interface with DTO decomposition (Best practice)

The repo interface accepts **primitives and simple lists** --- no nested dicts, no opaque blobs. The service layer decomposes DTOs into those primitives. The repo implementation builds ORM objects internally, with full control over get-or-create logic.

**This is what production systems converge toward.** The rest of this document walks through the implementation.

---

## Best Practice Architecture

### File layout

```
lab/
  film.py                  # Pydantic DTOs (API boundary)
  movielook.py             # Entry point / FastAPI app
  db/
    errors.py              # Domain exceptions
    repository.py          # Repository Protocol (interface)
    service.py             # Service layer (decomposes DTOs)
    SQLA/
      setup.py             # Engine, session factory
      tables.py            # ORM table classes
      methods.py           # SQLArepo (implements Protocol)
```

### Layer 1: Pydantic DTOs (`film.py`)

These are the **only** place Pydantic appears. They validate input at the API boundary and serve as the contract between the API layer and the service layer.

```python
class Release(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    year: int  = Field(ge=1888, le=datetime.now().year + 1)
    runtime: int = Field(ge=1, le=1000)

class Person(BaseModel):
    name: str = Field(min_length=1, max_length=20)
    middle_name: str | None = Field(default=None, min_length=1, max_length=25)
    surname: str | None = Field(default=None, min_length=1, max_length=30)

class Genre(BaseModel):
    name: str = Field(min_length=2, max_length=50)

class Movie(Release):
    director: list[Person] = Field(min_length=1)
    genres: list[Genre] | None = None
    stars: list[Person] | None = None
```

Key: `Movie` inherits `Release` (title/year/runtime), adds relationships. Validation is handled here by Pydantic field constraints --- the service doesn't re-validate.

### Layer 2: Repository interface (`db/repository.py`)

A `Protocol` class that defines the persistence contract using **only primitives**:

```python
class MovieRepo(Protocol):

    def select(
        self, title: str, year: int, runtime: int, full: bool = False,
    ) -> dict | None: ...

    def create(
        self,
        title: str,
        year: int,
        runtime: int,
        directors: list[dict],            # [{"name": ..., "surname": ...}]
        genres: list[str] | None = None,  # ["Sci-Fi", "Thriller"]
        stars: list[dict] | None = None,
    ) -> dict: ...

    def update(
        self, title: str, year: int, runtime: int, updates: dict,
    ) -> dict | None: ...

    def delete(self, title: str, year: int, runtime: int) -> bool: ...
```

**Why a Protocol and not an ABC?**
- Structural typing: any class with matching method signatures satisfies it, no inheritance required
- The in-memory fake repo for testing doesn't need to import anything from the persistence layer
- Matches Python's duck-typing philosophy

**What crosses this boundary:**

| Direction | What passes | What does NOT pass |
|-----------|-------------|-------------------|
| Into repo | `str`, `int`, `bool`, `list[str]`, `list[dict]` | Pydantic models, ORM objects |
| Out of repo | `dict`, `None`, `bool` | ORM objects, Pydantic models |

### Layer 3: Service layer (`db/service.py`)

The service accepts Pydantic DTOs, **decomposes them into primitives**, and calls the repo:

```python
class MovieService:

    def __init__(self, repo: MovieRepo):
        self._repo = repo

    def save_film(self, movie: Movie) -> dict:
        # Decompose: Pydantic stops here.
        directors = [d.model_dump() for d in movie.director]
        genres = [g.name for g in movie.genres] if movie.genres else None
        stars = [s.model_dump() for s in movie.stars] if movie.stars else None

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
        return Movie(**result)   # dict back into Pydantic on the way out
```

**The critical pattern:** `model_dump()` is called on each **nested** DTO individually (`d.model_dump()` for each director), not on the whole `Movie` object. This gives the service explicit control over what shape the data takes before entering the repo. Genres are reduced to just strings (`g.name`) because that's all the repo needs.

### Layer 4: ORM implementation (`db/SQLA/methods.py`)

The repo implementation is the **only** layer that touches ORM classes. It builds ORM objects from the incoming primitives using private helper methods:

```python
class SQLArepo:

    # ---- Private: ORM construction ----

    @staticmethod
    def _build_director(db, person: dict) -> Director:
        """Get-or-create a Director."""
        existing = db.execute(
            select(Director).where(
                Director.name == person["name"],
                Director.surname == person.get("surname"),
            )
        ).scalar_one_or_none()
        if existing:
            return existing
        return Director(
            name=person["name"],
            middle_name=person.get("middle_name"),
            surname=person.get("surname"),
        )

    @staticmethod
    def _build_genre(db, name: str) -> Genre:
        """Get-or-create a Genre."""
        existing = db.execute(
            select(Genre).where(Genre.name == name)
        ).scalar_one_or_none()
        if existing:
            return existing
        return Genre(name=name)

    @staticmethod
    def _person_to_dict(person) -> dict:
        """ORM Director/Star --> plain dict."""
        return {
            "name": person.name,
            "middle_name": person.middle_name,
            "surname": person.surname,
        }

    @staticmethod
    def _movie_to_dict(movie, full=False) -> dict:
        """ORM Movie --> plain dict."""
        result = {"title": movie.title, "year": movie.year, "runtime": movie.runtime}
        if full:
            result["director"] = [SQLArepo._person_to_dict(d) for d in movie.director]
            result["genres"]   = [{"name": g.name} for g in movie.genres]
            result["stars"]    = [SQLArepo._person_to_dict(s) for s in movie.stars]
        return result

    # ---- Public: matches MovieRepo Protocol ----

    def create(self, title, year, runtime, directors, genres=None, stars=None):
        with get_db() as db:
            director_objs = [self._build_director(db, d) for d in directors]
            genre_objs    = [self._build_genre(db, g) for g in genres] if genres else []
            star_objs     = [self._build_star(db, s) for s in stars] if stars else []

            movie = Movie(
                title=title, year=year, runtime=runtime,
                director=director_objs, genres=genre_objs, stars=star_objs,
            )
            db.add(movie)
            db.commit()
            return {"title": movie.title, "year": movie.year, "runtime": movie.runtime}
```

**Key details:**

1. **Get-or-create:** `_build_genre` checks if "Sci-Fi" already exists before creating it. This prevents the `IntegrityError` that the old `dict_to_orm` approach would hit.

2. **Explicit conversion:** `_movie_to_dict` and `_person_to_dict` convert ORM objects to dicts for the return trip. No reflection, no `inspect()` --- just direct attribute access. Simple, readable, no surprises.

3. **Session scoping:** All ORM work happens inside `with get_db() as db:`. The ORM objects never escape the `with` block.

---

## Data Flow: Complete Round Trip

### Write path (save a movie):

```
API receives JSON
    |
    v
Pydantic validates --> Movie(title="Inception", year=2010, runtime=148,
    |                        director=[Person(name="Christopher", surname="Nolan")],
    |                        genres=[Genre(name="Sci-Fi"), Genre(name="Thriller")])
    v
service.save_film(movie)
    |   Decomposes DTO:
    |     directors = [{"name": "Christopher", "middle_name": None, "surname": "Nolan"}]
    |     genres = ["Sci-Fi", "Thriller"]
    v
repo.create(title="Inception", year=2010, runtime=148,
    |        directors=[...], genres=["Sci-Fi", "Thriller"])
    |
    |   Builds ORM objects:
    |     _build_director(db, {"name": "Christopher", ...}) --> Director ORM
    |     _build_genre(db, "Sci-Fi")                        --> Genre ORM (get-or-create)
    |     _build_genre(db, "Thriller")                      --> Genre ORM (get-or-create)
    |     Movie(title=..., director=[Director], genres=[Genre, Genre])
    v
db.add(movie) --> db.commit() --> rows in movie, movie_dir, movie_genre tables
    |
    v
return {"title": "Inception", "year": 2010, "runtime": 148}
```

### Read path (look up a movie):

```
repo.select("Inception", 2010, 148, full=True)
    |
    |   SQLAlchemy query with selectinload
    v
ORM Movie object with loaded .director, .genres, .stars
    |
    |   _movie_to_dict(movie, full=True)
    v
{"title": "Inception", "year": 2010, "runtime": 148,
 "director": [{"name": "Christopher", "middle_name": None, "surname": "Nolan"}],
 "genres": [{"name": "Sci-Fi"}, {"name": "Thriller"}],
 "stars": [...]}
    |
    v
service.select_film returns Movie(**result) --> Pydantic model to caller
```

---

## Comparison: Before and After

| Aspect | Before (utility.py) | After (explicit interface) |
|--------|--------------------|-----------------------------|
| Service calls repo with | `repo.save(movie.model_dump())` -- opaque dict | `repo.create(title=..., directors=[...], genres=[...])` -- explicit args |
| Repo builds ORM via | `dict_to_orm(Movie, data)` -- generic reflection | `_build_director(db, d)` -- explicit, per-entity helpers |
| Repo returns data via | `orm_to_dict(movie)` -- generic, includes back-refs | `_movie_to_dict(movie)` -- explicit, no surprises |
| Handles duplicate genres | No -- `IntegrityError` | Yes -- get-or-create |
| Repo interface documented | No -- accepts `dict`, unclear what's inside | Yes -- Protocol with typed arguments |
| Testable with fakes | Needs ORM knowledge to build test dicts | Fake repo accepts same primitives, trivial to implement |

---

## Testing with a Fake Repo

Because the Protocol uses only primitives, a fake repo is trivial:

```python
class InMemoryMovieRepo:
    def __init__(self):
        self._movies: dict[tuple, dict] = {}

    def create(self, title, year, runtime, directors, genres=None, stars=None):
        key = (title, year, runtime)
        if key in self._movies:
            raise ConflictError("Already exists")
        self._movies[key] = {
            "title": title, "year": year, "runtime": runtime,
            "director": directors,
            "genres": [{"name": g} for g in (genres or [])],
            "stars": stars or [],
        }
        return {"title": title, "year": year, "runtime": runtime}

    def select(self, title, year, runtime, full=False):
        key = (title, year, runtime)
        movie = self._movies.get(key)
        if movie is None:
            return None
        if full:
            return movie
        return {"title": title, "year": year, "runtime": runtime}

    def update(self, title, year, runtime, updates):
        key = (title, year, runtime)
        movie = self._movies.get(key)
        if movie is None:
            return None
        movie.update(updates)
        return {"title": movie["title"], "year": movie["year"], "runtime": movie["runtime"]}

    def delete(self, title, year, runtime):
        key = (title, year, runtime)
        if key not in self._movies:
            return False
        del self._movies[key]
        return True
```

Now service tests need no database at all:

```python
def test_save_and_retrieve():
    svc = MovieService(InMemoryMovieRepo())

    svc.save_film(Movie(
        title="Inception", year=2010, runtime=148,
        director=[Person(name="Christopher", surname="Nolan")],
        genres=[Genre(name="Sci-Fi")],
    ))

    result = svc.select_film(Release(title="Inception", year=2010, runtime=148), full=True)
    assert result.title == "Inception"
    assert result.director[0].surname == "Nolan"
```

---

## Best Practices Summary

1. **DTOs at the edge, primitives at the core.** Pydantic validates at the API boundary. The service decomposes DTOs into primitives. The repo never sees Pydantic.

2. **The repo interface is a Protocol with explicit parameters.** Not `save(data: dict)` but `create(title, year, runtime, directors, genres, stars)`. Self-documenting, type-checkable, easy to fake.

3. **ORM construction is private to the repo.** The `_build_*` helpers and `_*_to_dict` converters are implementation details. They never appear in the interface.

4. **Get-or-create for shared entities.** Genres, directors, and stars may be shared across movies. The repo checks for existing records before creating new ones.

5. **No generic reflection.** `dict_to_orm` / `orm_to_dict` are clever but opaque. Explicit conversion is a few more lines but is readable, debuggable, and handles edge cases (get-or-create, selective loading, cycle-free output).

6. **Session stays inside the repo.** The `with get_db() as db:` block contains all ORM work. No ORM object escapes the session scope.

7. **Errors are domain errors.** The repo catches `IntegrityError` / `SQLAlchemyError` and re-raises as `ConflictError` / `DatabaseError`. The service never sees SQLAlchemy exceptions.
