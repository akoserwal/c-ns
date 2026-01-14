from __future__ import annotations

from typing import Dict, List
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

app = FastAPI(title="Week 1 - Todo (DI solution: list/delete/filter)")


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

    def list(self) -> List[dict]:
        return list(self._store.values())

    def delete(self, todo_id: str) -> bool:
        return self._store.pop(todo_id, None) is not None


class TodoService:
    def __init__(self, repo: TodoRepo):
        self._repo = repo

    def create_todo(self, title: str) -> dict:
        # Domain rules could live here (e.g., uniqueness)
        return self._repo.create(title=title)

    def get_todo(self, todo_id: str) -> dict:
        todo = self._repo.get(todo_id)
        if not todo:
            raise KeyError(todo_id)
        return todo

    def list_todos(self, q: str | None = None) -> List[dict]:
        items = self._repo.list()
        if q is None or not q.strip():
            return items
        qn = q.strip().lower()
        return [t for t in items if qn in t["title"].lower()]

    def delete_todo(self, todo_id: str) -> None:
        deleted = self._repo.delete(todo_id)
        if not deleted:
            raise KeyError(todo_id)


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


@app.get("/todos", response_model=list[TodoOut])
def list_todos(
    q: str | None = Query(default=None, description="Optional title substring filter"),
    svc: TodoService = Depends(get_service),
) -> list[dict]:
    return svc.list_todos(q=q)


@app.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(todo_id: str, svc: TodoService = Depends(get_service)) -> None:
    try:
        svc.delete_todo(todo_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Todo not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

