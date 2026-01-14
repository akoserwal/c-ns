from __future__ import annotations

import sqlite3

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS movie (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  year INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS genre (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS movie_genre (
  movie_id INTEGER NOT NULL,
  genre_id INTEGER NOT NULL,
  PRIMARY KEY (movie_id, genre_id),
  FOREIGN KEY (movie_id) REFERENCES movie(id) ON DELETE CASCADE,
  FOREIGN KEY (genre_id) REFERENCES genre(id) ON DELETE CASCADE
);
"""


def main() -> None:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)

    # Insert a movie
    con.execute("INSERT INTO movie(title, year) VALUES (?, ?)", ("Inception", 2010))
    movie_id = con.execute("SELECT id FROM movie WHERE title = ?", ("Inception",)).fetchone()[
        "id"
    ]

    # Insert genres
    con.execute("INSERT INTO genre(name) VALUES (?)", ("Sci-Fi",))
    con.execute("INSERT INTO genre(name) VALUES (?)", ("Thriller",))

    sci_fi_id = con.execute("SELECT id FROM genre WHERE name = ?", ("Sci-Fi",)).fetchone()[
        "id"
    ]
    thriller_id = con.execute(
        "SELECT id FROM genre WHERE name = ?", ("Thriller",)
    ).fetchone()["id"]

    # Associate movie <-> genres
    con.execute("INSERT INTO movie_genre(movie_id, genre_id) VALUES (?, ?)", (movie_id, sci_fi_id))
    con.execute(
        "INSERT INTO movie_genre(movie_id, genre_id) VALUES (?, ?)", (movie_id, thriller_id)
    )

    # Join query: movie -> genres
    rows = con.execute(
        """
        SELECT m.title, m.year, g.name AS genre
        FROM movie m
        JOIN movie_genre mg ON mg.movie_id = m.id
        JOIN genre g ON g.id = mg.genre_id
        WHERE m.id = ?
        ORDER BY g.name
        """,
        (movie_id,),
    ).fetchall()

    print("Movie with genres:")
    for r in rows:
        print(f"- {r['title']} ({r['year']}): {r['genre']}")


if __name__ == "__main__":
    main()

