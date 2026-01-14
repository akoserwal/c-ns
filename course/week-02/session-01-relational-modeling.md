### Week 2 / Session 1 — Relational modeling: tables are truth

#### Goal
Design a schema and write joins confidently *before* touching SQLAlchemy.

---

### Why this matters (reasoning)
ORM confusion is usually **relational confusion**. If you can reason about:
- keys
- constraints
- join tables
- query shapes

…then SQLAlchemy becomes “just a mapping layer”, not a mystery box.

Platform/IAM work depends on this because permissions and identity data are inherently relational:
users ↔ roles, users ↔ groups, clients ↔ scopes, policies ↔ resources.

---

### Theory (must know)

#### Core ideas
- **Tables are truth**: the DB enforces constraints; your code must respect them.
- **Primary keys** identify rows.
- **Foreign keys** encode relationships.
- **Many-to-many** requires an **association table**.
- **Composite primary keys** are common in association tables to prevent duplicates.

#### Normalization (only what you need)
- **Avoid duplication** of facts (e.g., don’t store genre names inside `movie` rows).
- Put repeated entities in their own table (e.g., `genre`).
- Use association tables for many-to-many.

#### Why composite keys exist (concrete)
In `movie_genre(movie_id, genre_id)`, the *pair* must be unique:
- It prevents duplicate associations (“Inception is Sci-Fi” twice).
- It creates a natural primary key without inventing a meaningless ID.

If you later need attributes on the association (e.g., “billing role assigned_at”), you might move to:
- a surrogate `id` PK, plus a `UNIQUE(movie_id, genre_id)` constraint.

---

### Architecture (ER diagram)

```mermaid
erDiagram
  MOVIE ||--o{ MOVIE_GENRE : has
  GENRE ||--o{ MOVIE_GENRE : includes
  MOVIE ||--o{ MOVIE_STAR : has
  STAR  ||--o{ MOVIE_STAR : appears_in

  MOVIE {
    int id PK
    string title
    int year
  }
  GENRE {
    int id PK
    string name
  }
  STAR {
    int id PK
    string name
  }
  MOVIE_GENRE {
    int movie_id FK
    int genre_id FK
    PK movie_id, genre_id
  }
  MOVIE_STAR {
    int movie_id FK
    int star_id FK
    PK movie_id, star_id
  }
```

---

### Do / Don’t
- **Do**: add `UNIQUE` constraints for natural uniqueness (e.g., `genre.name`)
  - Reason: correctness belongs in the DB; app-level checks are not enough under concurrency.
- **Do**: add composite PKs in join tables to prevent duplicates
  - Reason: it encodes the true uniqueness of the relationship.
- **Do**: decide “ownership” of relationships explicitly
  - Reason: it affects cascade deletes and data integrity.
- **Don’t**: model many-to-many with arrays/CSV columns
  - Reason: you lose constraints, joinability, and indexing power.
- **Don’t**: let ORM defaults design your database
  - Reason: schema design is a data integrity decision, not a convenience decision.

---

### Query shapes (joins multiply rows)
When you join `movie` to `genre` through `movie_genre`, the result is:
- one row per (movie, genre) pair

So if a movie has 3 genres, you’ll get 3 rows for that movie. This is normal and is why “grouping” is often done in application code or via SQL aggregation (`group_concat`, `json_agg` in Postgres).

#### Worked example: join result shape
This query returns one row per (movie, genre):

```sql
SELECT m.title, m.year, g.name AS genre
FROM movie m
JOIN movie_genre mg ON mg.movie_id = m.id
JOIN genre g ON g.id = mg.genre_id
ORDER BY m.title, g.name;
```

If `Inception` has 2 genres, you will see 2 rows with the same title/year.

#### Solution pattern: enforce integrity where it belongs
- Put uniqueness in the DB:
  - `genre.name UNIQUE`
  - `PRIMARY KEY (movie_id, genre_id)` on `movie_genre`
- In the API:
  - translate constraint violations into **409 Conflict**

---

### Practical session (raw SQL)

You will implement this using SQLite for convenience (Postgres mindset still applies).

Run:
- `python course/code/week-02/raw_sql_movies.py`

What you’ll see:
- schema creation
- inserts
- a join query returning “movie → genres”

---

### Reflection prompts (5 minutes)
- Why does `movie_genre` use a **composite primary key**?
- What query shape do you get back from a join (rows multiply)?

---

### Common failure modes (and solutions)
- **Symptom**: “I can’t delete a movie because of foreign key errors.”
  - **Cause**: association rows still exist.
  - **Solution**: decide cascade strategy (`ON DELETE CASCADE`) or delete associations explicitly.
- **Symptom**: “Duplicates appear in many-to-many links.”
  - **Cause**: missing composite PK/unique constraint.
  - **Solution**: enforce uniqueness at the DB level; then handle conflicts in the API as 409.
