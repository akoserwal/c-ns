### Week 2 — Lab Solution (reference)

#### Goal
Demonstrate relational thinking first (raw SQL), then show SQLAlchemy mapping obeying the schema.

---

## Part A — Schema + raw SQL (solution)

### 1) Use the reference schema
You can use the schema embedded in:
- `course/code/week-02/raw_sql_movies.py`

Or extract it into a `.sql` file (recommended):
- `course/code/week-02/schema.sql`

### 2) Use the reference queries
Example join query shape (one row per movie-genre):

```sql
SELECT m.title, m.year, g.name AS genre
FROM movie m
JOIN movie_genre mg ON mg.movie_id = m.id
JOIN genre g ON g.id = mg.genre_id
ORDER BY m.title, g.name;
```

### 3) Run the reference raw SQL solution

```bash
python course/code/week-02/raw_sql_movies.py
```

Expected output (example):
- `Inception (2010): Sci-Fi`
- `Inception (2010): Thriller`

---

## Part B — SQLAlchemy ORM mapping (solution)

### 1) Mapping strategy
For many-to-many:
- define an association table (`movie_genre`)
- define relationships using `secondary="movie_genre"`

### 2) Run the reference ORM solution

```bash
python course/code/week-02/sqlalchemy_movies_orm.py
```

Expected output (example):
- `Movie: Inception (2010)`
- `Genres:`
  - `Sci-Fi`
  - `Thriller`

---

## Part C — Explain the mental model (solution prompts)

### “Tables are truth, ORM is projection”
Good explanation:
- the DB schema defines identity and constraints
- the ORM must match that schema
- the ORM cannot “fix” a bad relational design; it can only map what exists

### “What is a Session?”
Good explanation:
- request-scoped unit-of-work + identity map + transaction boundary
- commit persists changes, rollback discards changes

---

## Optional extension (stars)
Extend the same pattern for `movie_star`:
- association table with composite PK (`movie_id`, `star_id`)
- relationship `Movie.stars` / `Star.movies`

