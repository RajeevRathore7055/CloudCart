from urllib.parse import quote
from fastapi import HTTPException, Request


class RedirectException(Exception):
    def __init__(self, url: str):
        self.url = url


def flash(request: Request, message: str, category: str = "info"):
    request.session["flash"] = request.session.get("flash", []) + [[category, message]]


def get_current_user(request: Request):
    uid = request.session.get("user_id")
    if not uid:
        return None
    return {"id": uid, "name": request.session.get("name"), "role": request.session.get("role")}


def login_required(request: Request):
    user = get_current_user(request)
    if not user:
        flash(request, "Please login to continue.", "error")
        raise RedirectException("/login?next=" + quote(request.url.path))
    return user


def admin_required(request: Request):
    user = login_required(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access only")
    return user


def safe_next(url: str, default: str = "/") -> str:
    """Only allow local redirects (prevents open-redirect attacks)."""
    if url and url.startswith("/") and not url.startswith("//"):
        return url
    return default
