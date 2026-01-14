from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Session, relationship


class Base(DeclarativeBase):
    pass


class MovieGenre(Base):
    __tablename__ = "movie_genre"
    movie_id = Column(Integer, ForeignKey("movie.id"), primary_key=True)
    genre_id = Column(Integer, ForeignKey("genre.id"), primary_key=True)


class Movie(Base):
    __tablename__ = "movie"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    genres = relationship("Genre", secondary="movie_genre", back_populates="movies")


class Genre(Base):
    __tablename__ = "genre"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    movies = relationship("Movie", secondary="movie_genre", back_populates="genres")


def main() -> None:
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        sci_fi = Genre(name="Sci-Fi")
        thriller = Genre(name="Thriller")
        inception = Movie(title="Inception", year=2010, genres=[sci_fi, thriller])
        db.add(inception)
        db.commit()

        stmt = select(Movie).where(Movie.title == "Inception")
        movie = db.execute(stmt).scalar_one()

        print(f"Movie: {movie.title} ({movie.year})")
        print("Genres:")
        for g in sorted(movie.genres, key=lambda x: x.name):
            print(f"- {g.name}")


if __name__ == "__main__":
    main()

