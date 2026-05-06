from fastapi import FastAPI

from db.service import MovieService
from db.SQLA.methods import SQLArepo, init_db
from db.SQLA.setup import engine
from film import Movie, Person

app = FastAPI()

init_db(engine)
repo = SQLArepo()
svc = MovieService(repo)


if __name__ == "__main__":

    temp = Movie(
        title="The Temp",
        year=1993,
        runtime=96,
        director=[Person(name="Tom", surname="Holland")],
    )
    # worked = svc.save_film(temp)
    worked = svc.select_film(temp)

    print(worked)
