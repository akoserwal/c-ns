from __future__ import annotations

from typing import Dict
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Week 1 - Todo (in-memory)")

_db: Dict[str, dict] = {}


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TodoOut(BaseModel):
    id: str
    title: str


@app.post("/todos", response_model=TodoOut, status_code=201)
def create_todo(payload: TodoCreate) -> dict:
    todo_id = str(uuid4())
    todo = {"id": todo_id, "title": payload.title}
    _db[todo_id] = todo
    return todo


@app.get("/todos/{todo_id}", response_model=TodoOut)
def get_todo(todo_id: str) -> dict:
    todo = _db.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)

