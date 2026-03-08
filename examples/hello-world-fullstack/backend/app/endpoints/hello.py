# backend/app/endpoints/hello.py
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

from app.auth.jwt import verify_jwt_token

router = APIRouter()


@router.post("/hello")
def hello(
    authorization: Optional[str] = Header(None, alias="Authorization"),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = verify_jwt_token(token)
        return {
            "message": f"Hello, organisation {payload['organisation_id']}!",
            "user": payload["sub"],
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))