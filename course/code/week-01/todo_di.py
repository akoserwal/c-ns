from __future__ import annotations

from typing import Dict
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Week 1 - Todo (DI: service + repo)")


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TodoOut(BaseModel):
    id: str
    title: str


class TodoRepo:
    def __init__(self, store: Dict[str, dict]):
        self._store = store

    def create(self, title: str) -> dict:
        todo_id = str(uuid4())
        todo = {"id": todo_id, "title": title}
        self._store[todo_id] = todo
        return todo

    def get(self, todo_id: str) -> dict | None:
        return self._store.get(todo_id)


class TodoService:
    def __init__(self, repo: TodoRepo):
        self._repo = repo

    def create_todo(self, title: str) -> dict:
        # Domain rules would live here (e.g., no duplicate titles, length rules, etc.)
        return self._repo.create(title=title)

    def get_todo(self, todo_id: str) -> dict:
        todo = self._repo.get(todo_id)
        if not todo:
            raise KeyError(todo_id)
        return todo


_store: Dict[str, dict] = {}


def get_repo() -> TodoRepo:
    return TodoRepo(_store)


def get_service(repo: TodoRepo = Depends(get_repo)) -> TodoService:
    return TodoService(repo)


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(payload: TodoCreate, svc: TodoService = Depends(get_service)) -> dict:
    return svc.create_todo(payload.title)


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: str, svc: TodoService = Depends(get_service)) -> dict:
    try:
        return svc.get_todo(todo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Todo not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

