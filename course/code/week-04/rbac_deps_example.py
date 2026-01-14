from __future__ import annotations

from typing import Callable

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Week 4 - RBAC via dependencies (mock auth)")


class Principal(BaseModel):
    sub: str
    roles: set[str]


def get_current_user(authorization: str | None = Header(default=None)) -> Principal:
    """
    Learning-only mock auth:
    - Authorization: Bearer admin  -> roles={"admin"}
    - Authorization: Bearer user   -> roles={"user"}
    - Authorization missing/other  -> 401
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing token")

    token = authorization.removeprefix("Bearer ").strip()
    if token == "admin":
        return Principal(sub="user-1", roles={"admin"})
    if token == "user":
        return Principal(sub="user-2", roles={"user"})

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


def require_role(role: str) -> Callable[[Principal], Principal]:
    def dep(p: Principal = Depends(get_current_user)) -> Principal:
        if role not in p.roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
        return p

    return dep


@app.get("/me")
def me(p: Principal = Depends(get_current_user)) -> dict:
    return {"sub": p.sub, "roles": sorted(p.roles)}


@app.get("/admin")
def admin_only(_p: Principal = Depends(require_role("admin"))) -> dict:
    return {"ok": True, "message": "you are admin"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8004)

