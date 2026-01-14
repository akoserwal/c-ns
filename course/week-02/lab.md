### Week 2 — Lab (self-paced)

#### Goal
Become confident with joins and make SQLAlchemy feel predictable.

---

### Tasks
- Create the Movies schema (Movie, Genre, Star + join tables)
- Write raw SQL queries:
  - insert movie + genre association
  - query movie by title/year
  - list movies with all genres (join)
  - list movies featuring a star (join)
- Implement the same schema in SQLAlchemy ORM
- Write a short explanation:
  - “Tables are truth, ORM is projection—what does that mean here?”
  - “What does a Session represent?”

---

### Do / Don’t
- **Do**: enforce uniqueness in the DB (`UNIQUE`, composite PKs)
- **Do**: practice joins until the row-shapes are intuitive
- **Don’t**: change ORM mappings until you can describe the schema they should reflect

---

### Solution checklist (definition of done)
- You have a schema that supports:
  - Movie ↔ Genre (many-to-many)
  - Movie ↔ Star (many-to-many)
- Raw SQL:
  - you can insert at least 2 movies and 2 genres
  - you can query one movie and list its genres via joins
- SQLAlchemy ORM:
  - you can insert a movie with multiple genres via relationships
  - you can query and print `movie.genres` successfully
- You can explain:
  - why the join table has a composite primary key (or a unique constraint)
  - what “join multiplies rows” means

---

### Expected outputs (examples)
- Raw SQL script prints something like:
  - `Inception (2010): Sci-Fi`
  - `Inception (2010): Thriller`
- ORM script prints:
  - `Movie: Inception (2010)`
  - `Genres: Sci-Fi, Thriller`

---

### Evidence artifacts
- `schema.md` with an ER diagram (mermaid is fine)
- `queries.sql` (or a Python script) that prints join results
