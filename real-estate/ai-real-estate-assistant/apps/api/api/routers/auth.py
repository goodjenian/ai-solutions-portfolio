import random
import re
from typing import Optional

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from config.settings import get_settings
from utils.auth_storage import AuthStorage

router = APIRouter(tags=["Auth"])


class RequestCodeBody(BaseModel):
    email: str


class VerifyCodeBody(BaseModel):
    email: str
    code: str


class SessionInfo(BaseModel):
    session_token: str
    user_email: str


_code_re = re.compile(r"^[0-9]{6}$")


@router.post("/auth/request-code", response_model=dict)
async def request_code(body: RequestCodeBody):
    settings = get_settings()
    if not settings.auth_email_enabled:
        raise HTTPException(status_code=400, detail="Email auth disabled")
    email = body.email.strip().lower()
    if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    code = f"{random.randint(0, 999999):06d}"
    storage = AuthStorage(settings.auth_storage_dir)
    storage.set_code(email, code, settings.auth_code_ttl_minutes)
    if settings.environment.strip().lower() == "development":
        return {"status": "code_sent", "code": code}
    return {"status": "code_sent"}


@router.post("/auth/verify-code", response_model=SessionInfo)
async def verify_code(body: VerifyCodeBody):
    settings = get_settings()
    if not settings.auth_email_enabled:
        raise HTTPException(status_code=400, detail="Email auth disabled")
    if not _code_re.match(body.code.strip()):
        raise HTTPException(status_code=400, detail="Invalid code format")
    email = body.email.strip().lower()
    if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    storage = AuthStorage(settings.auth_storage_dir)
    entry = storage.get_code(email)
    if not entry or entry.get("code") != body.code.strip():
        raise HTTPException(status_code=403, detail="Invalid or expired code")
    storage.delete_code(email)
    token = storage.create_session(email, settings.session_ttl_days)
    return SessionInfo(session_token=token, user_email=email)


@router.get("/auth/session", response_model=SessionInfo)
async def get_session(
    x_session_token: Optional[str] = Header(default=None, alias="X-Session-Token"),
):
    settings = get_settings()
    if not settings.auth_email_enabled:
        raise HTTPException(status_code=400, detail="Email auth disabled")
    if not x_session_token:
        raise HTTPException(status_code=401, detail="Missing session token")
    storage = AuthStorage(settings.auth_storage_dir)
    entry = storage.get_session(x_session_token)
    if not entry:
        raise HTTPException(status_code=403, detail="Invalid or expired session")
    user_email = entry.get("email")
    # entry.get() returns Any, validate it's a string
    assert isinstance(user_email, str), f"Expected str for email, got {type(user_email)}"
    return SessionInfo(session_token=x_session_token, user_email=user_email)
