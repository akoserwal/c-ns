from datetime import datetime

from pydantic import BaseModel, Field

"""
Character limits informed by USPS limits listed here:
https://www.serviceobjects.com/blog/character-limits-in-address-lines-for-usps-ups-and-fedex/
"""

RUNTIME_MIN = 1
RUNTIME_MAX = 1000

TITLE_MIN = 1
TITLE_MAX = 200

YEAR_MIN = 1888
YEAR_MAX = datetime.now().year + 1


class Release(BaseModel):
    """Movie identity"""

    title: str = Field(min_length=TITLE_MIN, max_length=TITLE_MAX)
    year: int = Field(ge=YEAR_MIN, le=YEAR_MAX)
    # Current year plus one to prevent boundary issues
    runtime: int = Field(ge=RUNTIME_MIN, le=RUNTIME_MAX)


class Person(BaseModel):
    """Name form"""

    name: str = Field(min_length=1, max_length=20)
    middle_name: str | None = Field(default=None, min_length=1, max_length=25)
    surname: str | None = Field(default=None, min_length=1, max_length=30)


class Genre(BaseModel):
    """Genre form"""

    name: str = Field(min_length=2, max_length=50)


class Movie(Release):
    """Movie form"""

    director: list[Person] = Field(min_length=1)
    genres: list[Genre] | None = None
    stars: list[Person] | None = None


class MovieError(BaseModel):
    """Custom error class"""

    task: str
    id: str
    error: str
    code: int

    @classmethod
    def details(cls, task: str, id: str, error: str, code: int):
        """Construct from positional arguments."""
        return cls(task=task, id=id, error=error, code=code)
