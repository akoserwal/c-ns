from sqlalchemy import ForeignKey, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Movie(Base):
    __tablename__ = "movie"
    title: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    runtime: Mapped[int] = mapped_column(primary_key=True)
    director: Mapped[list["Director"]] = relationship(
        "Director", secondary="movie_dir", back_populates="movies"
    )
    genres: Mapped[list["Genre"]] = relationship(
        "Genre", secondary="movie_genre", back_populates="movies"
    )
    stars: Mapped[list["Star"]] = relationship(
        "Star", secondary="movie_star", back_populates="movies"
    )


class MovieDirector(Base):
    __tablename__ = "movie_dir"
    title: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    runtime: Mapped[int] = mapped_column(primary_key=True)
    director_id: Mapped[int] = mapped_column(
        ForeignKey("director.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["title", "year", "runtime"],
            ["movie.title", "movie.year", "movie.runtime"],
            ondelete="CASCADE",
        ),
    )


class Director(Base):
    __tablename__ = "director"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    middle_name: Mapped[str | None] = mapped_column()
    surname: Mapped[str | None] = mapped_column()
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary="movie_dir", back_populates="director"
    )

    __table_args__ = (
        UniqueConstraint("name", "middle_name", "surname"),
    )


class MovieGenre(Base):
    __tablename__ = "movie_genre"
    title: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    runtime: Mapped[int] = mapped_column(primary_key=True)
    genre: Mapped[int] = mapped_column(
        ForeignKey("genre.name", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["title", "year", "runtime"],
            ["movie.title", "movie.year", "movie.runtime"],
            ondelete="CASCADE",
        ),
    )


class Genre(Base):
    __tablename__ = "genre"
    name: Mapped[str] = mapped_column(primary_key=True)
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary="movie_genre", back_populates="genres"
    )


class MovieStar(Base):
    __tablename__ = "movie_star"
    title: Mapped[str] = mapped_column(primary_key=True)
    year: Mapped[int] = mapped_column(primary_key=True)
    runtime: Mapped[int] = mapped_column(primary_key=True)
    star_id: Mapped[int] = mapped_column(
        ForeignKey("star.id", ondelete="CASCADE"), primary_key=True
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["title", "year", "runtime"],
            ["movie.title", "movie.year", "movie.runtime"],
            ondelete="CASCADE",
        ),
    )


class Star(Base):
    __tablename__ = "star"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    middle_name: Mapped[str | None] = mapped_column()
    surname: Mapped[str | None] = mapped_column()
    movies: Mapped[list["Movie"]] = relationship(
        "Movie", secondary="movie_star", back_populates="stars"
    )

    __table_args__ = (
        UniqueConstraint("name", "middle_name", "surname"),
    )
