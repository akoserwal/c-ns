from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import text, create_engine
from sqlalchemy.orm import Session, sessionmaker

engine = create_engine("sqlite:///./week2.db", echo=False)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(title="Week 2 - FastAPI DB dependency")


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db.execute(text("SELECT 1"))
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)

